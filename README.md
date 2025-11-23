# Prayer Tracker Data Layer

A flexible data layer for managing prayer entries with scheduling, persistence, and categorization.

## Features

- **Data Models**: Structured models for sections, categories, and prayer entries
- **Frequency Support**: Daily, weekly, monthly, and custom interval scheduling
- **Persistence**: JSON-based storage with schema versioning and migrations
- **Scheduling Utilities**: Automatic next due date computation and completion tracking
- **Repository API**: Full CRUD operations with filtering, reordering, and archiving
- **Session Persistence**: Data automatically saved and restored between sessions

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from prayer_tracker import PrayerRepository, Frequency

# Create repository instance
repo = PrayerRepository()

# Create organizational structure
section = repo.create_section("Family")
category = repo.create_category(section.id, "Parents")

# Add prayer entries
entry = repo.create_entry(
    category_id=category.id,
    title="Pray for mom's health",
    description="Daily prayer for healing",
    frequency=Frequency.DAILY
)

# Mark as completed
repo.mark_entry_completed(entry.id, note="Prayed this morning")

# List all entries
entries = repo.list_entries()

# Filter due entries
from prayer_tracker.scheduling import is_due
due_entries = [e for e in entries if is_due(e)]
```

## Data Models

### Section
Top-level organizational unit (e.g., "Family", "Church", "Friends")

### Category
Mid-level grouping within sections (e.g., "Parents", "Siblings", "Leaders")

### PrayerEntry
Individual prayer items with:
- Title and description
- Frequency (daily/weekly/monthly/custom)
- Completion history
- Next due date tracking
- Archiving support

## Scheduling

The scheduling system automatically:
- Computes next due dates based on frequency
- Tracks completion history with timestamps
- Supports custom intervals (e.g., every 3 days)
- Handles edge cases (e.g., monthly on Jan 31 → Feb 28/29)

## Persistence

Data is stored in JSON format in a user-specific directory:
- **Windows**: `%APPDATA%\PrayerTracker`
- **Linux/Unix**: `~/.local/share/prayer_tracker`
- **macOS**: `~/.local/share/prayer_tracker`

Features:
- Atomic writes with temporary files
- Automatic backups before saves
- Schema versioning and migrations
- Corruption detection and recovery

## Repository API

### Sections
- `list_sections()` - Get all sections
- `create_section(name, order)` - Create new section
- `update_section(id, name, order)` - Update section
- `delete_section(id)` - Delete section (cascades to categories/entries)

### Categories
- `list_categories(section_id)` - Get categories (optionally filtered)
- `create_category(section_id, name, order)` - Create new category
- `update_category(id, name, order, section_id)` - Update category
- `delete_category(id)` - Delete category (cascades to entries)

### Entries
- `list_entries(...)` - List with filtering options
- `create_entry(...)` - Create new entry
- `update_entry(id, **updates)` - Update entry fields
- `delete_entry(id)` - Delete entry
- `reorder_entries(category_id, ordered_ids)` - Custom ordering
- `mark_entry_completed(id, completion_time, note)` - Mark complete

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Or run individual test files:

```bash
python -m pytest tests/test_models.py
python -m pytest tests/test_scheduling.py
python -m pytest tests/test_repository.py
python -m pytest tests/test_persistence.py
```

## License

MIT
