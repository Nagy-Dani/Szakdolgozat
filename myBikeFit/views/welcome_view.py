"""Welcome page — the first screen shown when the application starts."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

from config import APP_NAME, APP_VERSION


# ── Edit this text to customise the welcome page description ──────────────────
_DESCRIPTION = (
    "Welcome to myBikeFit! This application analyses a short video of you riding and uses computer vision to "
    "measure your key cycling angles — knee extension, hip angle, back angle, and more. "
    "In five steps you'll get a personalised fit score and concrete adjustment recommendations tailored to your riding style."
    "Hit 'Start New Session' to get started."
)
# ─────────────────────────────────────────────────────────────────────────────


class WelcomeView(QWidget):
    """Landing page that introduces myBikeFit and lets the user start a session."""

    start_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 40, 60, 40)
        root.setSpacing(0)

        root.addStretch(1)

        title = QLabel(APP_NAME)
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        tagline = QLabel("AI-powered bike fitting — right from your desktop.")
        tagline.setObjectName("welcomeTagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(tagline)

        root.addSpacing(32)

        desc = QLabel(_DESCRIPTION)
        desc.setObjectName("welcomeDesc")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setMaximumWidth(680)
        desc_row = QHBoxLayout()
        desc_row.addStretch()
        desc_row.addWidget(desc)
        desc_row.addStretch()
        root.addLayout(desc_row)

        root.addSpacing(40)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        start_btn = QPushButton("Start New Session →")
        start_btn.setObjectName("welcomeStartBtn")
        start_btn.setProperty("class", "primary")
        start_btn.setFixedSize(240, 48)
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.clicked.connect(self.start_requested.emit)
        btn_row.addWidget(start_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        root.addSpacing(16)

        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("welcomeVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(version)

        root.addStretch(1)
