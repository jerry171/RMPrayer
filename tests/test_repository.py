import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from prayer_tracker.models import Frequency
from prayer_tracker.persistence import PersistenceService
from prayer_tracker.repository import (
    PrayerRepository,
    RepositoryError,
)


class PrayerRepositoryTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        temp_path = Path(self._temp_dir.name)
        self.persistence = PersistenceService(data_directory=temp_path)
        self.repository = PrayerRepository(persistence_service=self.persistence)

    def tearDown(self):
        self._temp_dir.cleanup()

    def test_create_and_persist_entry(self):
        section = self.repository.create_section("Family")
        category = self.repository.create_category(section.id, "Parents")
        entry = self.repository.create_entry(category_id=category.id, title="Pray for parents")
        self.assertEqual(entry.title, "Pray for parents")

        reloaded_repo = PrayerRepository(
            persistence_service=PersistenceService(data_directory=Path(self._temp_dir.name))
        )
        entries = reloaded_repo.list_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].title, "Pray for parents")

    def test_reorder_entries(self):
        section = self.repository.create_section("Friends")
        category = self.repository.create_category(section.id, "Close Friends")
        entry1 = self.repository.create_entry(category_id=category.id, title="Pray for John")
        entry2 = self.repository.create_entry(category_id=category.id, title="Pray for Jane")
        entry3 = self.repository.create_entry(category_id=category.id, title="Pray for Alex")

        ordered = self.repository.reorder_entries(category.id, [entry3.id, entry1.id, entry2.id])
        self.assertEqual([entry.title for entry in ordered], ["Pray for Alex", "Pray for John", "Pray for Jane"])

    def test_mark_entry_completed(self):
        section = self.repository.create_section("Family")
        category = self.repository.create_category(section.id, "Parents")
        entry = self.repository.create_entry(category_id=category.id, title="Pray for healing")
        completion_time = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        updated_entry = self.repository.mark_entry_completed(entry.id, completion_time=completion_time, note="Done")
        self.assertEqual(updated_entry.last_completed, completion_time)
        self.assertIsNotNone(updated_entry.next_due)
        self.assertEqual(len(updated_entry.completion_history), 1)

    def test_delete_section_cascades(self):
        section = self.repository.create_section("Church")
        category = self.repository.create_category(section.id, "Leaders")
        entry = self.repository.create_entry(category_id=category.id, title="Pray for pastor")
        self.repository.delete_section(section.id)
        categories = self.repository.list_categories(section.id)
        self.assertEqual(len(categories), 0)
        entries = self.repository.list_entries()
        self.assertEqual(len(entries), 0)

    def test_custom_frequency_validation(self):
        section = self.repository.create_section("Special")
        category = self.repository.create_category(section.id, "One-off")
        with self.assertRaises(RepositoryError):
            self.repository.create_entry(
                category_id=category.id,
                title="Custom",
                frequency=Frequency.CUSTOM,
            )

    def test_update_entry_frequency(self):
        section = self.repository.create_section("Family")
        category = self.repository.create_category(section.id, "Parents")
        entry = self.repository.create_entry(category_id=category.id, title="Pray for parents")
        updated = self.repository.update_entry(entry.id, frequency=Frequency.WEEKLY)
        self.assertEqual(updated.frequency, Frequency.WEEKLY)


if __name__ == "__main__":
    unittest.main()
