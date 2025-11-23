"""Central logging configuration utilities."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
import os

DEFAULT_LOG_DIR = Path.home() / ".rmprayer" / "logs"


def configure_logging(log_level: str | None = None, log_dir: str | Path | None = None) -> Path:
    """Configure application-wide logging.

    Parameters
    ----------
    log_level:
        Optional log level override (e.g. "DEBUG").
    log_dir:
        Directory where the rotating file handler should write.

    Returns
    -------
    Path
        Absolute path to the log file used by the file handler.
    """

    resolved_level = (log_level or os.getenv("RMP_LOG_LEVEL", "INFO")).upper()
    base_dir = Path(log_dir or os.getenv("RMP_LOG_DIR", DEFAULT_LOG_DIR)).expanduser()
    base_dir.mkdir(parents=True, exist_ok=True)
    log_file = base_dir / "rmprayer.log"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": resolved_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": str(log_file),
                "maxBytes": 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
                "level": resolved_level,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": resolved_level,
        },
    }

    logging.config.dictConfig(logging_config)
    logging.getLogger(__name__).debug("Logging initialised at %s", resolved_level)

    return log_file
