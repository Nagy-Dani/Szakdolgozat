"""myBikeFit — main entry point."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from views.main_window import MainWindow
from controllers.app_controller import AppController


def load_stylesheet() -> str:
    qss_path = Path(__file__).parent / "assets" / "styles" / "app.qss"
    if qss_path.exists():
        return qss_path.read_text()
    return ""


def main() -> None:
    """Main entry point of the application."""
    
    app = QApplication(sys.argv)
    app.setApplicationName("myBikeFit")
    app.setOrganizationName("myBikeFit")

    font = QFont("Arial", 11)
    app.setFont(font)

    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = MainWindow()
    controller = AppController(window)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
