"""Analysis view — pose overlay and live angle readouts.

Supports three view types: 'side', 'front', and 'back'.
Each view type loads a different set of AngleGauge widgets.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from views.widgets.angle_gauge import AngleGauge
from views.widgets.video_player import VideoPlayer


# Gauge definitions per view type: list of (key, label, default_min, default_max)
_GAUGE_DEFS: dict[str, list[tuple[str, str, float, float]]] = {
    "side": [
        ("knee_extension", "Knee Extension", 140, 150),
        ("hip_angle",      "Hip Angle",      40,  55),
        ("back_angle",     "Back Angle",     35,  45),
        ("ankle_angle",    "Ankle Angle",    90,  120),
        ("elbow_angle",    "Elbow Angle",    150, 165),
    ],
    "front": [
        ("knee_tracking_left",   "Knee Tracking (L)",  0, 10),
        ("knee_tracking_right",  "Knee Tracking (R)",  0, 10),
    ],
    "back": [
        ("hip_sway",             "Hip Sway",           0,  8),
    ],
}

_VIEW_TITLES: dict[str, str] = {
    "side":  "Side-View Analysis",
    "front": "Front-View Analysis",
    "back":  "Back-View Analysis",
}


class AnalysisView(QWidget):
    """Shows the video with skeleton overlay and real-time angle gauges.

    Parameters
    ----------
    view_type : str
        One of 'side', 'front', 'back'.  Determines which gauges are shown.
    """

    def __init__(self, view_type: str = "side", parent: QWidget | None = None):
        super().__init__(parent)
        self._view_type = view_type
        self._facing = "left"
        self._gauges: dict[str, AngleGauge] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        header = QLabel(_VIEW_TITLES.get(self._view_type, "Pose Analysis"))
        header.setObjectName("pageHeader")
        layout.addWidget(header)

        # --- Progress ---
        self._progress_label = QLabel("Waiting for video…")
        self._progress_label.setObjectName("pageSubtitle")
        layout.addWidget(self._progress_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(8)
        layout.addWidget(self._progress)

        # --- Main content: video + gauges ---
        content = QHBoxLayout()

        # Video
        self._player = VideoPlayer()
        content.addWidget(self._player, stretch=3)

        # Angle gauges sidebar — built dynamically from _GAUGE_DEFS
        gauges_group = QGroupBox("Live Angles")
        gauges_layout = QVBoxLayout(gauges_group)

        defs = _GAUGE_DEFS.get(self._view_type, _GAUGE_DEFS["side"])
        for key, label, lo, hi in defs:
            gauge = AngleGauge(label, lo, hi)
            self._gauges[key] = gauge
            gauges_layout.addWidget(gauge)

        gauges_layout.addStretch()
        content.addWidget(gauges_group, stretch=1)

        layout.addLayout(content, stretch=1)

    # ------------------------------------------------------------------ API

    @property
    def view_type(self) -> str:
        return self._view_type

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

    def update_gauges(self, **values: float) -> None:
        """Update gauge values by key name.

        Works for any view type — pass keyword arguments matching
        the gauge keys defined in _GAUGE_DEFS.

        For backward compatibility the side view also accepts the old
        positional-style keyword arguments.
        """
        for key, val in values.items():
            if key in self._gauges:
                self._gauges[key].set_value(val)

    # Legacy positional helper (side view only)
    def update_side_gauges(
        self,
        knee_ext: float = 0,
        hip: float = 0,
        back: float = 0,
        ankle: float = 0,
        elbow: float = 0,
    ) -> None:
        self.update_gauges(
            knee_extension=knee_ext,
            hip_angle=hip,
            back_angle=back,
            ankle_angle=ankle,
            elbow_angle=elbow,
        )

    def set_ideal_ranges(self, ranges: dict) -> None:
        """Update gauge ranges from angle_ranges config for a riding style."""
        for key, gauge in self._gauges.items():
            if key in ranges:
                r = ranges[key]
                gauge.set_range(r["min"], r["max"])
