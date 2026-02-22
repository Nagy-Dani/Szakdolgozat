"""Rider input view — body measurements form."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from views.widgets.measurement_input import MeasurementInput
from models.rider_model import Flexibility, RidingStyle


class RiderInputView(QWidget):
    """Form for entering rider body measurements."""

    rider_data_submitted = pyqtSignal(dict)  # Emits all rider data as dict

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        # Header
        header = QLabel("Rider Measurements")
        header.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        header.setStyleSheet("color: #cdd6f4; margin-bottom: 8px;")
        layout.addWidget(header)

        subtitle = QLabel("Enter your body measurements to enable accurate bike-fit analysis.")
        subtitle.setStyleSheet("color: #a6adc8; margin-bottom: 16px; font-size: 13px;")
        layout.addWidget(subtitle)

        # --- Name ---
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name (optional):"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Your name")
        self._name_input.setMaximumWidth(300)
        name_row.addWidget(self._name_input)
        name_row.addStretch()
        layout.addLayout(name_row)

        # --- Body measurements group ---
        body_group = QGroupBox("Body Measurements")
        body_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        body_layout = QVBoxLayout(body_group)

        self._height = MeasurementInput("Height", "cm", 100, 250, default=175)
        self._weight = MeasurementInput("Weight", "kg", 30, 200, default=75)
        self._inseam = MeasurementInput("Inseam (inner leg)", "cm", 50, 120, default=82)
        self._foot_size = MeasurementInput("Foot Size", "EU", 30, 55, decimals=0, default=43)
        self._arm_length = MeasurementInput("Arm Length", "cm", 40, 90, default=60)
        self._torso_length = MeasurementInput("Torso Length", "cm", 30, 80, default=50)
        self._shoulder_width = MeasurementInput("Shoulder Width", "cm", 25, 60, default=42)

        for w in [self._height, self._weight, self._inseam, self._foot_size,
                  self._arm_length, self._torso_length, self._shoulder_width]:
            body_layout.addWidget(w)

        layout.addWidget(body_group)

        # --- Profile group ---
        profile_group = QGroupBox("Riding Profile")
        profile_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        profile_layout = QFormLayout(profile_group)

        self._flexibility = QComboBox()
        self._flexibility.addItems([f.value.title() for f in Flexibility])
        self._flexibility.setCurrentIndex(1)  # Medium
        profile_layout.addRow("Flexibility:", self._flexibility)

        self._riding_style = QComboBox()
        self._riding_style.addItems([s.value.title() for s in RidingStyle])
        self._riding_style.setCurrentIndex(0)  # Road
        profile_layout.addRow("Riding Style:", self._riding_style)

        layout.addWidget(profile_group)

        # --- Next button ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_next = QPushButton("Next  →")
        self._btn_next.setFixedSize(140, 40)
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

    # ------------------------------------------------------------------ API

    def get_data(self) -> dict:
        return {
            "name": self._name_input.text().strip() or None,
            "height_cm": self._height.value,
            "weight_kg": self._weight.value,
            "inseam_cm": self._inseam.value,
            "foot_size_eu": self._foot_size.value,
            "arm_length_cm": self._arm_length.value,
            "torso_length_cm": self._torso_length.value,
            "shoulder_width_cm": self._shoulder_width.value,
            "flexibility": self._flexibility.currentText().lower(),
            "riding_style": self._riding_style.currentText().lower(),
        }

    def set_data(self, data: dict) -> None:
        """Populate form from a data dict (e.g. loaded session)."""
        if data.get("name"):
            self._name_input.setText(data["name"])
        self._height.value = data.get("height_cm", 175)
        self._weight.value = data.get("weight_kg", 75)
        self._inseam.value = data.get("inseam_cm", 82)
        self._foot_size.value = data.get("foot_size_eu", 43)
        self._arm_length.value = data.get("arm_length_cm", 60)
        self._torso_length.value = data.get("torso_length_cm", 50)
        self._shoulder_width.value = data.get("shoulder_width_cm", 42)

    def show_errors(self, errors: list[str]) -> None:
        QMessageBox.warning(self, "Validation Errors", "\n".join(errors))

    # ------------------------------------------------------------------ Slots

    def _on_submit(self) -> None:
        self.rider_data_submitted.emit(self.get_data())
