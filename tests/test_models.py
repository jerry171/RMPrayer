import unittest
from datetime import datetime, timezone

from prayer_tracker.models import (
    Category,
    Completion,
    Frequency,
    PrayerData,
    PrayerEntry,
    Section,
)


class TestModels(unittest.TestCase):
    def test_section_serialization(self):
        section = Section(id="sec1", name="Family", order=1)
        data = section.to_dict()
        restored = Section.from_dict(data)
        self.assertEqual(section, restored)

    def test_category_serialization(self):
        category = Category(id="cat1", section_id="sec1", name="Parents", order=2)
        data = category.to_dict()
        restored = Category.from_dict(data)
        self.assertEqual(category, restored)

    def test_prayer_entry_serialization(self):
        timestamp = datetime(2024, 1, 15, 6, 30, tzinfo=timezone.utc)
        completion = Completion(timestamp=timestamp, note="Answered")
        entry = PrayerEntry(
            id="entry1",
            category_id="cat1",
            title="Pray for strength",
            description="Daily guidance",
            frequency=Frequency.DAILY,
            last_completed=timestamp,
            next_due=timestamp,
            completion_history=[completion],
        )
        data = entry.to_dict()
        restored = PrayerEntry.from_dict(data)
        self.assertEqual(entry.id, restored.id)
        self.assertEqual(entry.frequency, restored.frequency)
        self.assertEqual(entry.last_completed, restored.last_completed)
        self.assertEqual(entry.next_due, restored.next_due)
        self.assertEqual(len(restored.completion_history), 1)
        self.assertEqual(restored.completion_history[0].note, "Answered")

    def test_prayer_data_serialization(self):
        section = Section(id="sec1", name="Family", order=0)
        category = Category(id="cat1", section_id=section.id, name="Parents", order=0)
        entry = PrayerEntry(id="entry1", category_id=category.id, title="Pray for dad")
        data = PrayerData(sections=[section], categories=[category], entries=[entry])
        serialized = data.to_dict()
        restored = PrayerData.from_dict(serialized)
        self.assertEqual(len(restored.sections), 1)
        self.assertEqual(len(restored.categories), 1)
        self.assertEqual(len(restored.entries), 1)


if __name__ == "__main__":
    unittest.main()
