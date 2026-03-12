"""Video capture / upload view."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from views.widgets.video_player import VideoPlayer


class VideoCaptureView(QWidget):
    """Upload a side-view video or record from webcam (MVP: upload only)."""

    video_ready = pyqtSignal(str)  # Emits the file path of the loaded video

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._video_path: str | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        header = QLabel("Video Input")
        header.setObjectName("pageHeader")
        layout.addWidget(header)

        subtitle = QLabel(
            "Upload a side-view video of yourself pedaling on the bike. "
            "Ensure the camera captures your full body from the side, "
            "with at least 5 seconds of steady pedaling."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        # Tips
        tips = QLabel(
            "<b>Tips for best results:</b><br>"
            "• Place the camera at hip height, perpendicular to the bike<br>"
            "• Ensure good lighting — avoid backlight<br>"
            "• Wear fitted clothing so joints are visible<br>"
            "• Pedal at a steady cadence for 10–20 seconds"
        )
        tips.setObjectName("tipsBox")
        tips.setWordWrap(True)
        layout.addWidget(tips)

        # --- Video player ---
        self._player = VideoPlayer()
        layout.addWidget(self._player, stretch=1)

        # --- Buttons ---
        btn_row = QHBoxLayout()

        self._btn_upload = QPushButton("Upload Video")
        self._btn_upload.setFixedSize(180, 40)
        self._btn_upload.setProperty("class", "secondary")
        self._btn_upload.clicked.connect(self._on_upload)
        btn_row.addWidget(self._btn_upload)

        btn_row.addStretch()

        self._btn_analyze = QPushButton("Analyze  →")
        self._btn_analyze.setFixedSize(160, 40)
        self._btn_analyze.setEnabled(False)
        self._btn_analyze.setProperty("class", "primary")
        self._btn_analyze.clicked.connect(self._on_analyze)
        btn_row.addWidget(self._btn_analyze)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------ API

    @property
    def video_path(self) -> str | None:
        return self._video_path

    @property
    def player(self) -> VideoPlayer:
        return self._player

    # ------------------------------------------------------------------ Slots

    def _on_upload(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)",
        )
        if not path:
            return
        if not self._player.load_video(path):
            QMessageBox.critical(self, "Error", f"Could not open video:\n{path}")
            return
        self._video_path = path
        self._btn_analyze.setEnabled(True)

    def _on_analyze(self) -> None:
        if self._video_path:
            self.video_ready.emit(self._video_path)
