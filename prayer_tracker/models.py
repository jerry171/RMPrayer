"""Core data models for the Prayer Tracker data layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def datetime_to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    normalized = _ensure_utc(dt)
    return normalized.isoformat().replace("+00:00", "Z")


def datetime_from_iso(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def generate_id() -> str:
    return uuid.uuid4().hex


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class Section:
    id: str
    name: str
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "order": self.order}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Section":
        return cls(id=data["id"], name=data["name"], order=data.get("order", 0))


@dataclass
class Category:
    id: str
    section_id: str
    name: str
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "section_id": self.section_id,
            "name": self.name,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Category":
        return cls(
            id=data["id"],
            section_id=data["section_id"],
            name=data["name"],
            order=data.get("order", 0),
        )


@dataclass
class Completion:
    timestamp: datetime
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": datetime_to_iso(self.timestamp), "note": self.note}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Completion":
        return cls(timestamp=datetime_from_iso(data["timestamp"]), note=data.get("note", ""))


@dataclass
class PrayerEntry:
    id: str
    category_id: str
    title: str
    description: str = ""
    frequency: Frequency = Frequency.DAILY
    custom_interval_days: Optional[int] = None
    last_completed: Optional[datetime] = None
    next_due: Optional[datetime] = None
    archived: bool = False
    order: int = 0
    completion_history: List[Completion] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category_id": self.category_id,
            "title": self.title,
            "description": self.description,
            "frequency": self.frequency.value,
            "custom_interval_days": self.custom_interval_days,
            "last_completed": datetime_to_iso(self.last_completed),
            "next_due": datetime_to_iso(self.next_due),
            "archived": self.archived,
            "order": self.order,
            "completion_history": [item.to_dict() for item in self.completion_history],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrayerEntry":
        return cls(
            id=data["id"],
            category_id=data["category_id"],
            title=data["title"],
            description=data.get("description", ""),
            frequency=Frequency(data.get("frequency", Frequency.DAILY.value)),
            custom_interval_days=data.get("custom_interval_days"),
            last_completed=datetime_from_iso(data.get("last_completed")),
            next_due=datetime_from_iso(data.get("next_due")),
            archived=data.get("archived", False),
            order=data.get("order", 0),
            completion_history=[
                Completion.from_dict(item)
                for item in data.get("completion_history", [])
            ],
        )


@dataclass
class PrayerData:
    sections: List[Section] = field(default_factory=list)
    categories: List[Category] = field(default_factory=list)
    entries: List[PrayerEntry] = field(default_factory=list)
    schema_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sections": [section.to_dict() for section in self.sections],
            "categories": [category.to_dict() for category in self.categories],
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrayerData":
        return cls(
            sections=[Section.from_dict(item) for item in data.get("sections", [])],
            categories=[
                Category.from_dict(item) for item in data.get("categories", [])
            ],
            entries=[PrayerEntry.from_dict(item) for item in data.get("entries", [])],
            schema_version=data.get("schema_version", 1),
        )
