#!/usr/bin/env python3
"""Example usage demonstrating the Prayer Tracker data layer API."""
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from prayer_tracker import PrayerRepository, Frequency
from prayer_tracker.persistence import PersistenceService
from prayer_tracker.scheduling import is_due


def main():
    print("=" * 70)
    print("Prayer Tracker Data Layer - Example Usage")
    print("=" * 70)
    print()

    temp_dir = TemporaryDirectory()
    temp_path = Path(temp_dir.name)
    persistence = PersistenceService(data_directory=temp_path)
    repo = PrayerRepository(persistence_service=persistence)

    print("1. Creating organizational structure...")
    family_section = repo.create_section("Family")
    friends_section = repo.create_section("Friends")
    church_section = repo.create_section("Church")
    print(f"   ✓ Created {len(repo.list_sections())} sections")
    print()

    print("2. Adding categories...")
    parents_category = repo.create_category(family_section.id, "Parents")
    siblings_category = repo.create_category(family_section.id, "Siblings")
    close_friends_category = repo.create_category(friends_section.id, "Close Friends")
    leaders_category = repo.create_category(church_section.id, "Leaders")
    print(f"   ✓ Created {len(repo.list_categories())} categories")
    print()

    print("3. Adding prayer entries with different frequencies...")
    
    daily_entry = repo.create_entry(
        category_id=parents_category.id,
        title="Pray for dad's health",
        description="Daily prayer for strength and healing",
        frequency=Frequency.DAILY,
    )
    print(f"   ✓ Created daily prayer: '{daily_entry.title}'")
    print(f"     Next due: {daily_entry.next_due.strftime('%Y-%m-%d %H:%M')}")
    
    weekly_entry = repo.create_entry(
        category_id=leaders_category.id,
        title="Pray for pastor",
        description="Weekly prayer for church leadership",
        frequency=Frequency.WEEKLY,
    )
    print(f"   ✓ Created weekly prayer: '{weekly_entry.title}'")
    print(f"     Next due: {weekly_entry.next_due.strftime('%Y-%m-%d %H:%M')}")
    
    monthly_entry = repo.create_entry(
        category_id=siblings_category.id,
        title="Pray for sister's job search",
        description="Monthly check-in prayer",
        frequency=Frequency.MONTHLY,
    )
    print(f"   ✓ Created monthly prayer: '{monthly_entry.title}'")
    print(f"     Next due: {monthly_entry.next_due.strftime('%Y-%m-%d %H:%M')}")
    
    custom_entry = repo.create_entry(
        category_id=close_friends_category.id,
        title="Pray for John's business",
        description="Prayer every 3 days",
        frequency=Frequency.CUSTOM,
        custom_interval_days=3,
    )
    print(f"   ✓ Created custom prayer (every 3 days): '{custom_entry.title}'")
    print(f"     Next due: {custom_entry.next_due.strftime('%Y-%m-%d %H:%M')}")
    print()

    print("4. Marking a prayer as completed...")
    completion_time = datetime.now(timezone.utc)
    updated_entry = repo.mark_entry_completed(
        daily_entry.id,
        completion_time=completion_time,
        note="Prayed this morning",
    )
    print(f"   ✓ Marked '{updated_entry.title}' as completed")
    print(f"     Last completed: {updated_entry.last_completed.strftime('%Y-%m-%d %H:%M')}")
    print(f"     Next due updated to: {updated_entry.next_due.strftime('%Y-%m-%d %H:%M')}")
    print(f"     Completion history: {len(updated_entry.completion_history)} entries")
    print()

    print("5. Filtering and querying entries...")
    all_entries = repo.list_entries()
    print(f"   ✓ Total entries: {len(all_entries)}")
    
    family_entries = repo.list_entries(section_id=family_section.id)
    print(f"   ✓ Family section entries: {len(family_entries)}")
    for entry in family_entries:
        print(f"     - {entry.title} ({entry.frequency.value})")
    print()

    print("6. Checking due entries...")
    for entry in repo.list_entries():
        due_status = "✓ DUE" if is_due(entry) else "○ Not due yet"
        print(f"   {due_status}: {entry.title}")
    print()

    print("7. Reordering entries in a category...")
    entries_before = repo.list_entries(category_id=parents_category.id)
    print(f"   Before reordering: {[e.title for e in entries_before]}")
    
    entry2 = repo.create_entry(
        category_id=parents_category.id,
        title="Pray for mom's peace",
        frequency=Frequency.DAILY,
    )
    entry3 = repo.create_entry(
        category_id=parents_category.id,
        title="Pray for parents' marriage",
        frequency=Frequency.WEEKLY,
    )
    
    reordered = repo.reorder_entries(
        parents_category.id,
        [entry3.id, daily_entry.id, entry2.id],
    )
    print(f"   After reordering: {[e.title for e in reordered]}")
    print()

    print("8. Testing persistence across sessions...")
    entries_count_before = len(repo.list_entries())
    print(f"   Entries before reload: {entries_count_before}")
    
    new_repo = PrayerRepository(
        persistence_service=PersistenceService(data_directory=temp_path)
    )
    entries_count_after = len(new_repo.list_entries())
    print(f"   Entries after reload: {entries_count_after}")
    print(f"   ✓ Data persisted successfully!")
    print()

    print("9. Archiving an entry...")
    repo.update_entry(monthly_entry.id, archived=True)
    active_entries = repo.list_entries(include_archived=False)
    all_entries_with_archived = repo.list_entries(include_archived=True)
    print(f"   Active entries: {len(active_entries)}")
    print(f"   Total entries (including archived): {len(all_entries_with_archived)}")
    print()

    print("10. Searching entries...")
    search_results = repo.list_entries(search="pray for")
    print(f"   Found {len(search_results)} entries matching 'pray for'")
    for entry in search_results[:3]:
        print(f"     - {entry.title}")
    print()

    print("=" * 70)
    print("Example completed successfully!")
    print("=" * 70)
    
    temp_dir.cleanup()


if __name__ == "__main__":
    main()
