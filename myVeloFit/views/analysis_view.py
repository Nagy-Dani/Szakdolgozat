"""Analysis view — pose overlay and live angle readouts."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from views.widgets.angle_gauge import AngleGauge
from views.widgets.video_player import VideoPlayer


class AnalysisView(QWidget):
    """Shows the video with skeleton overlay and real-time angle gauges."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        header = QLabel("Pose Analysis")
        header.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        header.setStyleSheet("color: #cdd6f4; margin-bottom: 8px;")
        layout.addWidget(header)

        # --- Progress ---
        self._progress_label = QLabel("Waiting for video…")
        self._progress_label.setStyleSheet("color: #a6adc8; font-size: 13px;")
        layout.addWidget(self._progress_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(8)
        self._progress.setStyleSheet("""
            QProgressBar {
                background-color: #313244;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #7aa2f7;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self._progress)

        # --- Main content: video + gauges ---
        content = QHBoxLayout()

        # Video
        self._player = VideoPlayer()
        content.addWidget(self._player, stretch=3)

        # Angle gauges sidebar
        gauges_group = QGroupBox("Live Angles")
        gauges_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        gauges_layout = QVBoxLayout(gauges_group)

        self._gauge_knee_ext = AngleGauge("Knee Extension", 140, 150)
        self._gauge_hip = AngleGauge("Hip Angle", 40, 55)
        self._gauge_back = AngleGauge("Back Angle", 35, 45)
        self._gauge_ankle = AngleGauge("Ankle Angle", 90, 120)
        self._gauge_elbow = AngleGauge("Elbow Angle", 150, 165)

        for g in [self._gauge_knee_ext, self._gauge_hip, self._gauge_back,
                  self._gauge_ankle, self._gauge_elbow]:
            gauges_layout.addWidget(g)

        gauges_layout.addStretch()
        content.addWidget(gauges_group, stretch=1)

        layout.addLayout(content, stretch=1)

    # ------------------------------------------------------------------ API

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
