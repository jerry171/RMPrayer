"""Persistence service with JSON storage and schema migrations."""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from prayer_tracker.models import PrayerData


CURRENT_SCHEMA_VERSION = 1


def get_user_data_directory() -> Path:
    override = os.getenv("PRAYER_TRACKER_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base_dir = os.getenv("APPDATA")
        if base_dir:
            return Path(base_dir) / "PrayerTracker"
    
    home = Path.home()
    if os.name == "posix":
        xdg_data_home = os.getenv("XDG_DATA_HOME")
        if xdg_data_home:
            return Path(xdg_data_home) / "prayer_tracker"
        return home / ".local" / "share" / "prayer_tracker"
    
    return home / ".prayer_tracker"


class MigrationError(Exception):
    pass


def migrate_schema(data: Dict[str, Any], from_version: int, to_version: int) -> Dict[str, Any]:
    current_version = from_version
    
    while current_version < to_version:
        if current_version == 0 and to_version >= 1:
            data = _migrate_0_to_1(data)
            current_version = 1
        else:
            raise MigrationError(
                f"No migration path from version {current_version} to {current_version + 1}"
            )
    
    return data


def _migrate_0_to_1(data: Dict[str, Any]) -> Dict[str, Any]:
    if "schema_version" not in data:
        data["schema_version"] = 1
    
    if "sections" not in data:
        data["sections"] = []
    if "categories" not in data:
        data["categories"] = []
    if "entries" not in data:
        data["entries"] = []
    
    return data


class PersistenceService:
    def __init__(self, data_directory: Optional[Path] = None, filename: str = "prayer_data.json"):
        self.data_directory = data_directory or get_user_data_directory()
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.filepath = self.data_directory / filename
        self.backup_directory = self.data_directory / "backups"
        self.backup_directory.mkdir(parents=True, exist_ok=True)

    def load(self) -> PrayerData:
        if not self.filepath.exists():
            return PrayerData()
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            schema_version = data.get("schema_version", 0)
            
            if schema_version < CURRENT_SCHEMA_VERSION:
                data = migrate_schema(data, schema_version, CURRENT_SCHEMA_VERSION)
                self._create_backup(f"before_migration_to_{CURRENT_SCHEMA_VERSION}")
            
            prayer_data = PrayerData.from_dict(data)
            if schema_version < CURRENT_SCHEMA_VERSION:
                self.save(prayer_data)
            return prayer_data
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self._create_backup("corrupted")
            raise IOError(f"Failed to load prayer data: {e}") from e

    def save(self, prayer_data: PrayerData) -> None:
        prayer_data.schema_version = CURRENT_SCHEMA_VERSION
        data_dict = prayer_data.to_dict()
        
        temp_filepath = self.filepath.with_suffix(".tmp")
        
        try:
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            
            if self.filepath.exists():
                backup_path = self.backup_directory / f"prayer_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2(self.filepath, backup_path)
                self._cleanup_old_backups()
            
            shutil.move(str(temp_filepath), str(self.filepath))
        
        except Exception as e:
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise IOError(f"Failed to save prayer data: {e}") from e

    def _create_backup(self, suffix: str) -> None:
        if self.filepath.exists():
            backup_path = self.backup_directory / f"prayer_data_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(self.filepath, backup_path)

    def _cleanup_old_backups(self, max_backups: int = 10) -> None:
        backups = sorted(self.backup_directory.glob("prayer_data_*.json"), key=lambda p: p.stat().st_mtime)
        
        while len(backups) > max_backups:
            oldest = backups.pop(0)
            oldest.unlink()

    def delete_all_data(self) -> None:
        if self.filepath.exists():
            self._create_backup("before_deletion")
            self.filepath.unlink()
