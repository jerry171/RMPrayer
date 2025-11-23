"""RMPrayer desktop application package."""

from .settings import AppSettings, load_settings
from .logging_config import configure_logging

__all__ = ["AppSettings", "load_settings", "configure_logging"]
__version__ = "0.1.0"
