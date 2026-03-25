"""Video capture / upload view — upload Side, Front, and Back videos."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from views.widgets.video_player import VideoPlayer


class _VideoSlot(QWidget):
    """A single upload slot with a label, status, and upload/clear buttons."""

    video_changed = pyqtSignal()  # emitted on upload or clear

    def __init__(
        self,
        title: str,
        description: str,
        required: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._title = title
        self._required = required
        self._video_path: str | None = None
        self._setup_ui(title, description)

    def _setup_ui(self, title: str, description: str) -> None:
        group = QGroupBox(title + ("  ✱" if self._required else "  (optional)"))
        group.setObjectName("videoSlotGroup")
        inner = QVBoxLayout(group)

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setObjectName("videoSlotDesc")
        inner.addWidget(desc)

        # Status + buttons row
        row = QHBoxLayout()

        self._status_label = QLabel("No video selected")
        self._status_label.setObjectName("videoSlotStatus")
        row.addWidget(self._status_label, stretch=1)

        self._btn_upload = QPushButton("Upload")
        self._btn_upload.setFixedSize(100, 32)
        self._btn_upload.setProperty("class", "secondary")
        self._btn_upload.clicked.connect(self._on_upload)
        row.addWidget(self._btn_upload)

        self._btn_clear = QPushButton("✕")
        self._btn_clear.setFixedSize(32, 32)
        self._btn_clear.setToolTip("Remove video")
        self._btn_clear.clicked.connect(self._on_clear)
        self._btn_clear.setEnabled(False)
        row.addWidget(self._btn_clear)

        inner.addLayout(row)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(group)

    # --- API ---

    @property
    def video_path(self) -> str | None:
        return self._video_path

    @video_path.setter
    def video_path(self, path: str | None) -> None:
        self._video_path = path
        if path:
            self._status_label.setText(f"✔  {Path(path).name}")
            self._status_label.setStyleSheet("color: #22c55e;")
            self._btn_clear.setEnabled(True)
        else:
            self._status_label.setText("No video selected")
            self._status_label.setStyleSheet("")
            self._btn_clear.setEnabled(False)
        self.video_changed.emit()

    @property
    def is_filled(self) -> bool:
        return self._video_path is not None

    # --- Slots ---

    def _on_upload(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {self._title} Video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)",
        )
        if path:
            self.video_path = path

    def _on_clear(self) -> None:
        self.video_path = None


class VideoCaptureView(QWidget):
    """Upload up to three videos: Side (required), Front and Back (optional)."""

    # Emits a dict: {"side": path, "front": path|None, "back": path|None, "facing": "left"|"right"}
    videos_ready = pyqtSignal(dict)
    # Keep the old signal alive so VideoController still connects (single side path)
    video_ready = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._facing = "left"
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        header = QLabel("Video Input")
        header.setObjectName("pageHeader")
        layout.addWidget(header)

        subtitle = QLabel(
            "Upload your cycling videos for analysis. "
            "A side-view video is required; front and back views are optional "
            "and provide additional stability insights."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        # Tips
        tips = QLabel(
            "<b>Tips for best results:</b><br>"
            "• Good lighting — avoid backlight<br>"
            "• Wear fitted clothing so joints are visible<br>"
            "• Pedal at a steady cadence for 10–20 seconds"
        )
        tips.setObjectName("tipsBox")
        tips.setWordWrap(True)
        layout.addWidget(tips)

        # --- Facing side toggle (applies to side video) ---
        facing_row = QHBoxLayout()
        facing_label = QLabel("Side-view cyclist facing:")
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

        # --- Video upload slots ---
        self._side_slot = _VideoSlot(
            "Side View",
            "Camera at hip height, perpendicular to the bike. "
            "Captures knee extension, hip angle, and back position.",
            required=True,
        )
        self._front_slot = _VideoSlot(
            "Front View",
            "Camera placed in front of the bike at handlebar height. "
            "Captures knee tracking and shoulder symmetry.",
        )
        self._back_slot = _VideoSlot(
            "Back View",
            "Camera placed behind the bike at saddle height. "
            "Captures pelvic stability and pedaling symmetry.",
        )

        for slot in (self._side_slot, self._front_slot, self._back_slot):
            slot.video_changed.connect(self._update_analyze_button)
            layout.addWidget(slot)

        layout.addStretch()

        # --- Analyze button ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_analyze = QPushButton("Analyze  →")
        self._btn_analyze.setFixedSize(160, 40)
        self._btn_analyze.setEnabled(False)
        self._btn_analyze.setProperty("class", "primary")
        self._btn_analyze.clicked.connect(self._on_analyze)
        btn_row.addWidget(self._btn_analyze)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------ API

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
        return self._facing

    @property
    def video_path(self) -> str | None:
        """Backwards-compatible: returns the side video path."""
        return self._side_slot.video_path

    @property
    def side_video_path(self) -> str | None:
        return self._side_slot.video_path

    @property
    def front_video_path(self) -> str | None:
        return self._front_slot.video_path

    @property
    def back_video_path(self) -> str | None:
        return self._back_slot.video_path

    def get_video_paths(self) -> dict:
        """Return all uploaded video paths."""
        return {
            "side": self._side_slot.video_path,
            "front": self._front_slot.video_path,
            "back": self._back_slot.video_path,
            "facing": self._facing,
        }

    # ------------------------------------------------------------------ Slots

    def _update_analyze_button(self) -> None:
        self._btn_analyze.setEnabled(self._side_slot.is_filled)

    def _on_analyze(self) -> None:
        if not self._side_slot.is_filled:
            QMessageBox.warning(
                self, "Missing Video",
                "A side-view video is required before analysis can begin."
            )
            return
        self.videos_ready.emit(self.get_video_paths())
        # Also emit the old signal for backward compat
        if self._side_slot.video_path:
            self.video_ready.emit(self._side_slot.video_path)
