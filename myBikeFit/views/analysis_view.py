"""Analysis view — pose overlay and live angle readouts."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGroupBox, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal

from views.widgets.angle_gauge import AngleGauge
from views.widgets.video_player import VideoPlayer
from views.help_dialog import show_page_help


class AnalysisView(QWidget):
    """Shows the video with skeleton overlay and real-time angle gauges."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._facing = "left"
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        header = QLabel("Pose Analysis")
        header.setObjectName("pageHeader")
        help_btn = QPushButton("?")
        help_btn.setObjectName("helpBtn")
        help_btn.setFixedSize(28, 28)
        help_btn.setToolTip("Help")
        help_btn.clicked.connect(lambda: show_page_help("analysis", self))
        header_row = QHBoxLayout()
        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(help_btn)
        layout.addLayout(header_row)

        self._progress_label = QLabel("Waiting for video…")
        self._progress_label.setObjectName("pageSubtitle")
        layout.addWidget(self._progress_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(9)
        layout.addWidget(self._progress)

        content = QHBoxLayout()

        self._player = VideoPlayer()
        content.addWidget(self._player, stretch=3)

        gauges_group = QGroupBox("Live Angles")
        gauges_layout = QVBoxLayout(gauges_group)

        self._gauge_knee_ext = AngleGauge("Knee Extension", 65, 148)
        self._gauge_hip = AngleGauge("Hip Angle", 44, 110)
        self._gauge_back = AngleGauge("Back Angle", 28, 45)
        self._gauge_ankle = AngleGauge("Ankle Angle", 95, 135)
        self._gauge_elbow = AngleGauge("Elbow Angle", 150, 165)

        for g in [self._gauge_knee_ext, self._gauge_hip, self._gauge_back,
                  self._gauge_ankle, self._gauge_elbow]:
            gauges_layout.addWidget(g)

        gauges_layout.addStretch()
        content.addWidget(gauges_group, stretch=1)

        layout.addLayout(content, stretch=1)

    @property
    def facing_side(self) -> str:
        """Return 'left' or 'right' — set by AppController from the video page."""
        return self._facing

    @facing_side.setter
    def facing_side(self, side: str) -> None:
        self._facing = side

    @property
    def player(self) -> VideoPlayer:
        return self._player

    def set_progress(self, value: int, text: str = "") -> None:
        self._progress.setValue(value)
        if text:
            self._progress_label.setText(text)

    def update_gauges(
        self,
        knee_ext: float = 0,
        hip: float = 0,
        back: float = 0,
        ankle: float = 0,
        elbow: float = 0,
    ) -> None:
        self._gauge_knee_ext.set_value(knee_ext)
        self._gauge_hip.set_value(hip)
        self._gauge_back.set_value(back)
        self._gauge_ankle.set_value(ankle)
        self._gauge_elbow.set_value(elbow)

    def set_ideal_ranges(self, ranges: dict) -> None:
        """Update gauge ranges from angle_ranges config for a riding style."""
        if "knee_extension" in ranges:
            r = ranges["knee_extension"]
            self._gauge_knee_ext.set_range(r["min"], r["max"])
        if "hip_angle" in ranges:
            r = ranges["hip_angle"]
            self._gauge_hip.set_range(r["min"], r["max"])
        if "back_angle" in ranges:
            r = ranges["back_angle"]
            self._gauge_back.set_range(r["min"], r["max"])
        if "ankle_angle" in ranges:
            r = ranges["ankle_angle"]
            self._gauge_ankle.set_range(r["min"], r["max"])
        if "elbow_angle" in ranges:
            r = ranges["elbow_angle"]
            self._gauge_elbow.set_range(r["min"], r["max"])
