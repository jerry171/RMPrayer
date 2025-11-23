import unittest
from datetime import datetime, timedelta, timezone

from prayer_tracker.models import Completion, Frequency, PrayerEntry
from prayer_tracker.scheduling import (
    compute_next_due_date,
    days_until_due,
    is_due,
    mark_completion,
)


class TestScheduling(unittest.TestCase):
    def test_compute_next_due_date_daily(self):
        now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        next_due = compute_next_due_date(Frequency.DAILY, reference_time=now)
        expected = datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(next_due, expected)

    def test_compute_next_due_date_weekly(self):
        now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        next_due = compute_next_due_date(Frequency.WEEKLY, reference_time=now)
        expected = datetime(2024, 1, 22, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(next_due, expected)

    def test_compute_next_due_date_monthly(self):
        now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        next_due = compute_next_due_date(Frequency.MONTHLY, reference_time=now)
        expected = datetime(2024, 2, 15, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(next_due, expected)

    def test_compute_next_due_date_monthly_edge_case(self):
        jan31 = datetime(2024, 1, 31, 10, 0, tzinfo=timezone.utc)
        next_due = compute_next_due_date(Frequency.MONTHLY, reference_time=jan31)
        expected = datetime(2024, 2, 29, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(next_due, expected)

    def test_compute_next_due_date_custom(self):
        now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        next_due = compute_next_due_date(Frequency.CUSTOM, custom_interval_days=5, reference_time=now)
        expected = datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(next_due, expected)

    def test_compute_next_due_date_custom_invalid(self):
        now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            compute_next_due_date(Frequency.CUSTOM, reference_time=now)

    def test_mark_completion(self):
        entry = PrayerEntry(
            id="entry1",
            category_id="cat1",
            title="Test Prayer",
            frequency=Frequency.DAILY,
        )
        now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        updated_entry = mark_completion(entry, completion_time=now, note="Done")
        self.assertEqual(updated_entry.last_completed, now)
        self.assertIsNotNone(updated_entry.next_due)
        expected_next_due = datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(updated_entry.next_due, expected_next_due)
        self.assertEqual(len(updated_entry.completion_history), 1)
        self.assertEqual(updated_entry.completion_history[0].note, "Done")

    def test_is_due(self):
        entry = PrayerEntry(
            id="entry1",
            category_id="cat1",
            title="Test Prayer",
            next_due=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        )
        now = datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc)
        self.assertTrue(is_due(entry, reference_time=now))
        now_before = datetime(2024, 1, 14, 10, 0, tzinfo=timezone.utc)
        self.assertFalse(is_due(entry, reference_time=now_before))

    def test_is_due_when_next_due_is_none(self):
        entry = PrayerEntry(
            id="entry1",
            category_id="cat1",
            title="Test Prayer",
            next_due=None,
        )
        self.assertTrue(is_due(entry))

    def test_days_until_due(self):
        entry = PrayerEntry(
            id="entry1",
            category_id="cat1",
            title="Test Prayer",
            next_due=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
        )
        now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        days = days_until_due(entry, reference_time=now)
        self.assertIsNotNone(days)
        self.assertAlmostEqual(days, 5.0, delta=0.001)

    def test_days_until_due_none(self):
        entry = PrayerEntry(
            id="entry1",
            category_id="cat1",
            title="Test Prayer",
            next_due=None,
        )
        days = days_until_due(entry)
        self.assertIsNone(days)


if __name__ == "__main__":
    unittest.main()
