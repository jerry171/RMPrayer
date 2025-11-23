"""Repository API for managing sections, categories, and prayer entries."""
from __future__ import annotations

import copy
from datetime import datetime
from threading import RLock
from typing import Any, Iterable, List, Optional, Sequence

from prayer_tracker.models import (
    Category,
    Frequency,
    PrayerData,
    PrayerEntry,
    Section,
    generate_id,
)
from prayer_tracker.persistence import PersistenceService
from prayer_tracker.scheduling import compute_next_due_date, mark_completion, get_current_time


class RepositoryError(Exception):
    """Base class for repository errors."""


class EntityNotFoundError(RepositoryError):
    """Raised when an entity cannot be found."""


class PrayerRepository:
    def __init__(self, persistence_service: Optional[PersistenceService] = None) -> None:
        self._lock = RLock()
        self._persistence = persistence_service or PersistenceService()
        self._data: PrayerData = self._persistence.load()
        self._ensure_integrity()

    # ------------------------------------------------------------------
    # Public API - Sections
    # ------------------------------------------------------------------
    def list_sections(self) -> List[Section]:
        with self._lock:
            return [copy.deepcopy(section) for section in self._sorted_sections()]

    def create_section(self, name: str, order: Optional[int] = None) -> Section:
        with self._lock:
            order_value = order if order is not None else self._next_order(self._data.sections)
            section = Section(id=generate_id(), name=name, order=order_value)
            self._data.sections.append(section)
            self._reindex_sections()
            self._persist()
            return copy.deepcopy(section)

    def update_section(self, section_id: str, *, name: Optional[str] = None, order: Optional[int] = None) -> Section:
        with self._lock:
            section = self._get_section(section_id)
            if name is not None:
                section.name = name
            if order is not None:
                section.order = order
                self._reindex_sections()
            self._persist()
            return copy.deepcopy(section)

    def delete_section(self, section_id: str) -> None:
        with self._lock:
            self._ensure_section_exists(section_id)
            self._data.sections = [section for section in self._data.sections if section.id != section_id]
            removed_category_ids = {category.id for category in self._data.categories if category.section_id == section_id}
            self._data.categories = [category for category in self._data.categories if category.section_id != section_id]
            if removed_category_ids:
                self._data.entries = [entry for entry in self._data.entries if entry.category_id not in removed_category_ids]
            self._reindex_sections()
            self._reindex_categories()
            self._reindex_entries()
            self._persist()

    # ------------------------------------------------------------------
    # Public API - Categories
    # ------------------------------------------------------------------
    def list_categories(self, section_id: Optional[str] = None) -> List[Category]:
        with self._lock:
            categories = self._sorted_categories()
            if section_id:
                categories = [category for category in categories if category.section_id == section_id]
            return [copy.deepcopy(category) for category in categories]

    def create_category(self, section_id: str, name: str, order: Optional[int] = None) -> Category:
        with self._lock:
            self._ensure_section_exists(section_id)
            order_value = order if order is not None else self._next_order(
                [category for category in self._data.categories if category.section_id == section_id]
            )
            category = Category(
                id=generate_id(),
                section_id=section_id,
                name=name,
                order=order_value,
            )
            self._data.categories.append(category)
            self._reindex_categories(section_id)
            self._persist()
            return copy.deepcopy(category)

    def update_category(
        self,
        category_id: str,
        *,
        name: Optional[str] = None,
        order: Optional[int] = None,
        section_id: Optional[str] = None,
    ) -> Category:
        with self._lock:
            category = self._get_category(category_id)
            original_section_id = category.section_id
            if section_id and section_id != category.section_id:
                self._ensure_section_exists(section_id)
                category.section_id = section_id
            if name is not None:
                category.name = name
            if order is not None:
                category.order = order
            self._reindex_categories(original_section_id)
            if category.section_id != original_section_id:
                self._reindex_categories(category.section_id)
            self._persist()
            return copy.deepcopy(category)

    def delete_category(self, category_id: str) -> None:
        with self._lock:
            category = self._get_category(category_id)
            self._data.categories = [c for c in self._data.categories if c.id != category_id]
            self._data.entries = [entry for entry in self._data.entries if entry.category_id != category_id]
            self._reindex_categories(category.section_id)
            self._persist()

    # ------------------------------------------------------------------
    # Public API - Entries
    # ------------------------------------------------------------------
    def list_entries(
        self,
        *,
        section_id: Optional[str] = None,
        category_id: Optional[str] = None,
        include_archived: bool = False,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> List[PrayerEntry]:
        with self._lock:
            entries = list(self._data.entries)
            if section_id:
                categories = {category.id for category in self._data.categories if category.section_id == section_id}
                entries = [entry for entry in entries if entry.category_id in categories]
            if category_id:
                entries = [entry for entry in entries if entry.category_id == category_id]
            if not include_archived:
                entries = [entry for entry in entries if not entry.archived]
            if due_before:
                entries = [entry for entry in entries if entry.next_due and entry.next_due <= due_before]
            if due_after:
                entries = [entry for entry in entries if entry.next_due and entry.next_due >= due_after]
            if search:
                lowered = search.lower()
                entries = [
                    entry
                    for entry in entries
                    if lowered in entry.title.lower() or lowered in entry.description.lower()
                ]
            entries.sort(key=lambda entry: (entry.category_id, entry.order, entry.title.lower()))
            return [copy.deepcopy(entry) for entry in entries]

    def create_entry(
        self,
        *,
        category_id: str,
        title: str,
        description: str = "",
        frequency: Frequency = Frequency.DAILY,
        custom_interval_days: Optional[int] = None,
        order: Optional[int] = None,
    ) -> PrayerEntry:
        with self._lock:
            category = self._get_category(category_id)
            if isinstance(frequency, str):
                frequency = Frequency(frequency)
            self._validate_custom_frequency(frequency, custom_interval_days)
            order_value = order if order is not None else self._next_order(
                [entry for entry in self._data.entries if entry.category_id == category.id]
            )
            entry = PrayerEntry(
                id=generate_id(),
                category_id=category.id,
                title=title,
                description=description,
                frequency=frequency,
                custom_interval_days=custom_interval_days,
                order=order_value,
            )
            entry.next_due = compute_next_due_date(
                entry.frequency,
                entry.last_completed,
                entry.custom_interval_days,
                get_current_time(),
            )
            self._data.entries.append(entry)
            self._reindex_entries(category.id)
            self._persist()
            return copy.deepcopy(entry)

    def update_entry(self, entry_id: str, **updates: Any) -> PrayerEntry:
        with self._lock:
            entry = self._get_entry(entry_id)
            original_category_id = entry.category_id
            allowed_fields = {
                "title",
                "description",
                "frequency",
                "custom_interval_days",
                "archived",
                "category_id",
                "order",
                "last_completed",
                "next_due",
            }

            for key in updates:
                if key not in allowed_fields:
                    raise RepositoryError(f"Unsupported field for update: {key}")

            if "category_id" in updates and updates["category_id"] != entry.category_id:
                new_category_id = updates["category_id"]
                self._ensure_category_exists(new_category_id)
                entry.category_id = new_category_id
                if "order" not in updates:
                    siblings = [
                        e for e in self._data.entries if e.category_id == new_category_id and e.id != entry.id
                    ]
                    entry.order = self._next_order(siblings)

            if "frequency" in updates:
                frequency = updates["frequency"]
                if isinstance(frequency, str):
                    frequency = Frequency(frequency)
                entry.frequency = frequency

            if "custom_interval_days" in updates:
                entry.custom_interval_days = updates["custom_interval_days"]

            if "archived" in updates:
                entry.archived = bool(updates["archived"])

            if "title" in updates:
                entry.title = updates["title"]

            if "description" in updates:
                entry.description = updates["description"]

            if "last_completed" in updates:
                entry.last_completed = updates["last_completed"]

            if "next_due" in updates:
                entry.next_due = updates["next_due"]

            if "order" in updates:
                entry.order = updates["order"]

            if entry.frequency != Frequency.CUSTOM:
                entry.custom_interval_days = None

            self._validate_custom_frequency(entry.frequency, entry.custom_interval_days)

            should_recompute = any(
                key in updates for key in ("frequency", "custom_interval_days", "last_completed")
            )
            if should_recompute and "next_due" not in updates:
                reference_time = get_current_time()
                entry.next_due = compute_next_due_date(
                    entry.frequency,
                    entry.last_completed,
                    entry.custom_interval_days,
                    reference_time,
                )

            if original_category_id != entry.category_id:
                self._reindex_entries()
            else:
                self._reindex_entries(entry.category_id)
            self._persist()
            return copy.deepcopy(entry)

    def delete_entry(self, entry_id: str) -> None:
        with self._lock:
            entry = self._get_entry(entry_id)
            self._data.entries = [e for e in self._data.entries if e.id != entry_id]
            self._reindex_entries(entry.category_id)
            self._persist()

    def reorder_entries(self, category_id: str, ordered_entry_ids: Sequence[str]) -> List[PrayerEntry]:
        with self._lock:
            self._ensure_category_exists(category_id)
            entries = [entry for entry in self._data.entries if entry.category_id == category_id]
            id_to_entry = {entry.id: entry for entry in entries}

            new_order: List[PrayerEntry] = []
            for entry_id in ordered_entry_ids:
                entry = id_to_entry.pop(entry_id, None)
                if entry:
                    new_order.append(entry)

            new_order.extend(id_to_entry.values())

            for index, entry in enumerate(new_order):
                entry.order = index

            self._reindex_entries(category_id)
            self._persist()
            return [copy.deepcopy(entry) for entry in new_order]

    def mark_entry_completed(
        self, entry_id: str, completion_time: Optional[datetime] = None, note: str = ""
    ) -> PrayerEntry:
        with self._lock:
            entry = self._get_entry(entry_id)
            updated_entry = mark_completion(entry, completion_time, note)
            self._persist()
            return copy.deepcopy(updated_entry)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def reload(self) -> None:
        with self._lock:
            self._data = self._persistence.load()
            self._ensure_integrity()

    def clear_all(self) -> None:
        with self._lock:
            self._persistence.delete_all_data()
            self._data = PrayerData()

    # Internal helpers -------------------------------------------------
    def _persist(self) -> None:
        self._persistence.save(self._data)

    def _ensure_integrity(self) -> None:
        self._reindex_sections()
        for section in self._data.sections:
            self._reindex_categories(section.id)
        for category in self._data.categories:
            self._reindex_entries(category.id)

    def _sorted_sections(self) -> List[Section]:
        return sorted(self._data.sections, key=lambda section: (section.order, section.name.lower()))

    def _sorted_categories(self) -> List[Category]:
        return sorted(
            self._data.categories,
            key=lambda category: (category.section_id, category.order, category.name.lower()),
        )

    def _next_order(self, items: Iterable) -> int:
        orders = [item.order for item in items]
        return max(orders) + 1 if orders else 0

    def _ensure_section_exists(self, section_id: str) -> None:
        if not any(section.id == section_id for section in self._data.sections):
            raise EntityNotFoundError(f"Section {section_id} not found")

    def _ensure_category_exists(self, category_id: str) -> None:
        if not any(category.id == category_id for category in self._data.categories):
            raise EntityNotFoundError(f"Category {category_id} not found")

    def _ensure_section_exists_by_category(self, section_id: str) -> None:
        self._ensure_section_exists(section_id)

    def _get_section(self, section_id: str) -> Section:
        for section in self._data.sections:
            if section.id == section_id:
                return section
        raise EntityNotFoundError(f"Section {section_id} not found")

    def _get_category(self, category_id: str) -> Category:
        for category in self._data.categories:
            if category.id == category_id:
                return category
        raise EntityNotFoundError(f"Category {category_id} not found")

    def _get_entry(self, entry_id: str) -> PrayerEntry:
        for entry in self._data.entries:
            if entry.id == entry_id:
                return entry
        raise EntityNotFoundError(f"Entry {entry_id} not found")

    def _reindex_sections(self) -> None:
        self._data.sections.sort(key=lambda section: (section.order, section.name.lower()))
        for index, section in enumerate(self._data.sections):
            section.order = index

    def _reindex_categories(self, section_id: Optional[str] = None) -> None:
        categories = self._data.categories
        categories.sort(key=lambda category: (category.section_id, category.order, category.name.lower()))
        section_groups = {}
        for category in categories:
            section_groups.setdefault(category.section_id, []).append(category)
        for sec_id, group in section_groups.items():
            if section_id is None or section_id == sec_id:
                for index, category in enumerate(group):
                    category.order = index

    def _reindex_entries(self, category_id: Optional[str] = None) -> None:
        entries = self._data.entries
        entries.sort(key=lambda entry: (entry.category_id, entry.order, entry.title.lower()))
        category_groups = {}
        for entry in entries:
            category_groups.setdefault(entry.category_id, []).append(entry)
        for cat_id, group in category_groups.items():
            if category_id is None or category_id == cat_id:
                for index, entry in enumerate(group):
                    entry.order = index

    def _validate_custom_frequency(self, frequency: Frequency, custom_interval_days: Optional[int]) -> None:
        if frequency == Frequency.CUSTOM:
            if custom_interval_days is None or custom_interval_days <= 0:
                raise RepositoryError("Custom frequency requires a positive custom_interval_days value")
        else:
            if custom_interval_days is not None:
                raise RepositoryError("custom_interval_days is only valid when frequency is set to CUSTOM")
