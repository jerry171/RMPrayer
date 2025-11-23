"""Application entry point."""

from __future__ import annotations

import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout

from .logging_config import configure_logging
from .settings import AppSettings, load_settings


class MainWindow(QMainWindow):
    """Minimal main window used as a placeholder for future features."""

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings

        self.setWindowTitle(f"{settings.app_name} v{settings.version}")
        self.resize(640, 400)

        content = QWidget(self)
        layout = QVBoxLayout(content)

        message = QLabel(
            "RMPrayer desktop client is under construction.\n"
            "Future releases will add reporting, scheduling, and automation features."
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)

        self.setCentralWidget(content)


def bootstrap_qt_application(settings: AppSettings) -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setApplicationVersion(settings.version)
    return app


def main() -> int:
    """Configure supporting services and launch the GUI."""

    settings = load_settings()
    configure_logging(log_dir=settings.data_dir / "logs")

    logger = logging.getLogger(__name__)
    logger.info("Starting %s v%s", settings.app_name, settings.version)

    app = bootstrap_qt_application(settings)

    window = MainWindow(settings)
    window.show()

    exit_code = app.exec()
    logger.info("Application closed with exit code %s", exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
