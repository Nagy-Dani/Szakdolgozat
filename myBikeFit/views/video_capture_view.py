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
    """Upload a side-view video or record from webcam"""

    video_ready = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._video_path: str | None = None
        self._facing = "left"
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

        facing_row = QHBoxLayout()
        facing_label = QLabel("Cyclist facing:")
        facing_label.setObjectName("pageSubtitle")
        facing_row.addWidget(facing_label)

        self._btn_left = QPushButton("← Left")
        self._btn_right = QPushButton("Right →")
        self._btn_left.setFixedSize(100, 32)
        self._btn_right.setFixedSize(100, 32)
        self._btn_left.setCheckable(True)
        self._btn_right.setCheckable(True)
        self._btn_left.setChecked(True)

        self._btn_left.clicked.connect(lambda: self._set_facing("left"))
        self._btn_right.clicked.connect(lambda: self._set_facing("right"))
        self._update_facing_buttons()

        facing_row.addWidget(self._btn_left)
        facing_row.addWidget(self._btn_right)
        facing_row.addStretch()
        layout.addLayout(facing_row)

        self._player = VideoPlayer()
        layout.addWidget(self._player, stretch=1)

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

    def _set_facing(self, side: str) -> None:
        self._facing = side
        self._update_facing_buttons()

    def _update_facing_buttons(self) -> None:
        self._btn_left.setChecked(self._facing == "left")
        self._btn_right.setChecked(self._facing == "right")
        
        active_style = "background-color: #7aa2f7; color: #1e1e2e;"
        self._btn_left.setStyleSheet(active_style if self._facing == "left" else "")
        self._btn_right.setStyleSheet(active_style if self._facing == "right" else "")

    @property
    def facing_side(self) -> str:
        """Return 'left' or 'right' depending on which way the cyclist faces."""
        return self._facing

    @property
    def video_path(self) -> str | None:
        return self._video_path

    @property
    def player(self) -> VideoPlayer:
        return self._player

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
