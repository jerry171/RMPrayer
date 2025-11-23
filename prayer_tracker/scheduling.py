"""Scheduling utilities for computing next due dates and managing completions."""
import calendar
from datetime import datetime, timedelta, timezone
from typing import Optional

from prayer_tracker.models import Frequency, PrayerEntry, Completion


def get_current_time() -> datetime:
    return datetime.now(timezone.utc)


def compute_next_due_date(
    frequency: Frequency,
    last_completed: Optional[datetime] = None,
    custom_interval_days: Optional[int] = None,
    reference_time: Optional[datetime] = None,
) -> datetime:
    if reference_time is None:
        reference_time = get_current_time()
    
    base_date = last_completed if last_completed else reference_time
    
    if frequency == Frequency.DAILY:
        return base_date + timedelta(days=1)
    elif frequency == Frequency.WEEKLY:
        return base_date + timedelta(weeks=1)
    elif frequency == Frequency.MONTHLY:
        month = base_date.month
        year = base_date.year
        day = base_date.day
        
        month += 1
        if month > 12:
            month = 1
            year += 1
        
        last_day_of_month = calendar.monthrange(year, month)[1]
        day = min(day, last_day_of_month)
        
        return base_date.replace(year=year, month=month, day=day)
    elif frequency == Frequency.CUSTOM:
        if custom_interval_days is None or custom_interval_days <= 0:
            raise ValueError("Custom frequency requires a positive custom_interval_days")
        return base_date + timedelta(days=custom_interval_days)
    else:
        raise ValueError(f"Unknown frequency: {frequency}")


def mark_completion(
    entry: PrayerEntry,
    completion_time: Optional[datetime] = None,
    note: str = "",
) -> PrayerEntry:
    if completion_time is None:
        completion_time = get_current_time()
    
    completion = Completion(timestamp=completion_time, note=note)
    entry.completion_history.append(completion)
    entry.last_completed = completion_time
    entry.next_due = compute_next_due_date(
        entry.frequency,
        entry.last_completed,
        entry.custom_interval_days,
        completion_time,
    )
    
    return entry


def is_due(entry: PrayerEntry, reference_time: Optional[datetime] = None) -> bool:
    if reference_time is None:
        reference_time = get_current_time()
    
    if entry.next_due is None:
        return True
    
    return entry.next_due <= reference_time


def days_until_due(entry: PrayerEntry, reference_time: Optional[datetime] = None) -> Optional[float]:
    if reference_time is None:
        reference_time = get_current_time()
    
    if entry.next_due is None:
        return None
    
    delta = entry.next_due - reference_time
    return delta.total_seconds() / 86400


def initialize_next_due_date(entry: PrayerEntry, reference_time: Optional[datetime] = None) -> PrayerEntry:
    if entry.next_due is None:
        if reference_time is None:
            reference_time = get_current_time()
        entry.next_due = reference_time
    return entry
