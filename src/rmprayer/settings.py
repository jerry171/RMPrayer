"""Application settings helpers."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

DEFAULT_APP_NAME = "RMPrayer"
DEFAULT_VERSION = "0.1.0"
DEFAULT_DATA_DIR = Path.home() / ".rmprayer"


@dataclass(frozen=True)
class AppSettings:
    """Strongly-typed configuration for the desktop client."""

    app_name: str
    version: str
    data_dir: Path


def _prepare_data_dir(path_value: str | None) -> Path:
    path = Path(path_value or DEFAULT_DATA_DIR).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_settings() -> AppSettings:
    """Load runtime settings from environment variables with sane defaults."""

    app_name = os.getenv("RMP_APP_NAME", DEFAULT_APP_NAME)
    version = os.getenv("RMP_APP_VERSION", DEFAULT_VERSION)
    data_dir = _prepare_data_dir(os.getenv("RMP_DATA_DIR"))

    return AppSettings(app_name=app_name, version=version, data_dir=data_dir)
