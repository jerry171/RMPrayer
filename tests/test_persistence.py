import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from prayer_tracker.models import Category, PrayerData, Section
from prayer_tracker.persistence import PersistenceService, migrate_schema


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self.temp_path = Path(self._temp_dir.name)
        self.service = PersistenceService(data_directory=self.temp_path)

    def tearDown(self):
        self._temp_dir.cleanup()

    def test_save_and_load(self):
        section = Section(id="sec1", name="Family", order=0)
        category = Category(id="cat1", section_id=section.id, name="Parents", order=0)
        data = PrayerData(sections=[section], categories=[category])
        self.service.save(data)
        loaded_data = self.service.load()
        self.assertEqual(len(loaded_data.sections), 1)
        self.assertEqual(loaded_data.sections[0].name, "Family")
        self.assertEqual(len(loaded_data.categories), 1)
        self.assertEqual(loaded_data.categories[0].name, "Parents")

    def test_load_empty_file(self):
        data = self.service.load()
        self.assertEqual(len(data.sections), 0)
        self.assertEqual(len(data.categories), 0)
        self.assertEqual(len(data.entries), 0)

    def test_schema_migration_0_to_1(self):
        old_data = {}
        migrated_data = migrate_schema(old_data, 0, 1)
        self.assertEqual(migrated_data["schema_version"], 1)
        self.assertIn("sections", migrated_data)
        self.assertIn("categories", migrated_data)
        self.assertIn("entries", migrated_data)

    def test_backup_creation(self):
        section = Section(id="sec1", name="Test", order=0)
        data = PrayerData(sections=[section])
        self.service.save(data)
        section2 = Section(id="sec2", name="Test 2", order=1)
        data2 = PrayerData(sections=[section, section2])
        self.service.save(data2)
        backups = list(self.service.backup_directory.glob("*.json"))
        self.assertGreaterEqual(len(backups), 1)

    def test_corrupted_file_creates_backup(self):
        corrupted_json = '{"sections": ["invalid"'
        self.service.filepath.write_text(corrupted_json, encoding="utf-8")
        with self.assertRaises(IOError):
            self.service.load()
        backups = list(self.service.backup_directory.glob("*corrupted*.json"))
        self.assertGreaterEqual(len(backups), 1)


if __name__ == "__main__":
    unittest.main()
