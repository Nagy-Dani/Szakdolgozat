"""Bike geometry input view."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QMessageBox,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from views.widgets.measurement_input import MeasurementInput


class BikeInputView(QWidget):
    """Form for entering bike geometry measurements."""

    bike_data_submitted = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        header = QLabel("Bike Geometry")
        header.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        header.setStyleSheet("color: #cdd6f4; margin-bottom: 8px;")
        layout.addWidget(header)

        subtitle = QLabel(
            "Enter your bike measurements. Leave at 0 if unknown — "
            "the analysis will still work using video-based estimates."
        )
        subtitle.setStyleSheet("color: #a6adc8; margin-bottom: 16px; font-size: 13px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # --- Measurements ---
        group = QGroupBox("Frame & Fit")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        glayout = QVBoxLayout(group)

        self._frame_size = MeasurementInput("Frame Size", "cm", 40, 70, default=0)
        self._saddle_height = MeasurementInput("Saddle Height", "cm", 55, 90, default=0)
        self._saddle_setback = MeasurementInput("Saddle Setback", "cm", -5, 15, default=0)
        self._reach = MeasurementInput("Handlebar Reach", "cm", 30, 70, default=0)
        self._drop = MeasurementInput("Handlebar Drop", "cm", -5, 20, default=0)
        self._crank_length = MeasurementInput("Crank Length", "mm", 140, 185, default=172.5)
        self._stem_length = MeasurementInput("Stem Length", "mm", 50, 150, default=100)
        self._stem_angle = MeasurementInput("Stem Angle", "°", -20, 20, default=-6)

        for w in [self._frame_size, self._saddle_height, self._saddle_setback,
                  self._reach, self._drop, self._crank_length,
                  self._stem_length, self._stem_angle]:
            glayout.addWidget(w)

        layout.addWidget(group)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_skip = QPushButton("Skip  →")
        self._btn_skip.setFixedSize(120, 40)
        self._btn_skip.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        self._btn_skip.clicked.connect(lambda: self.bike_data_submitted.emit({}))
        btn_row.addWidget(self._btn_skip)

        self._btn_next = QPushButton("Next  →")
        self._btn_next.setFixedSize(120, 40)
        self._btn_next.setStyleSheet("""
            QPushButton {
                background-color: #7aa2f7;
                color: #1e1e2e;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #89b4fa; }
        """)
        self._btn_next.clicked.connect(self._on_submit)
        btn_row.addWidget(self._btn_next)
        layout.addLayout(btn_row)

        layout.addStretch()

    def get_data(self) -> dict:
        return {
            "frame_size_cm": self._frame_size.value,
            "saddle_height_cm": self._saddle_height.value,
            "saddle_setback_cm": self._saddle_setback.value,
            "handlebar_reach_cm": self._reach.value,
            "handlebar_drop_cm": self._drop.value,
            "crank_length_mm": self._crank_length.value,
            "stem_length_mm": self._stem_length.value,
            "stem_angle_deg": self._stem_angle.value,
        }

    def set_data(self, data: dict) -> None:
        self._frame_size.value = data.get("frame_size_cm", 0)
        self._saddle_height.value = data.get("saddle_height_cm", 0)
        self._saddle_setback.value = data.get("saddle_setback_cm", 0)
        self._reach.value = data.get("handlebar_reach_cm", 0)
        self._drop.value = data.get("handlebar_drop_cm", 0)
        self._crank_length.value = data.get("crank_length_mm", 172.5)
        self._stem_length.value = data.get("stem_length_mm", 100)
        self._stem_angle.value = data.get("stem_angle_deg", -6)

    def show_errors(self, errors: list[str]) -> None:
        QMessageBox.warning(self, "Validation Errors", "\n".join(errors))

    def _on_submit(self) -> None:
        self.bike_data_submitted.emit(self.get_data())
