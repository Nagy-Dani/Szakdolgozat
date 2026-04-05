"""Rider input view — body measurements form."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from views.widgets.measurement_input import MeasurementInput
from views.help_dialog import show_page_help
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

        header = QLabel("Rider Measurements")
        header.setObjectName("pageHeader")
        help_btn = QPushButton("?")
        help_btn.setObjectName("helpBtn")
        help_btn.setFixedSize(28, 28)
        help_btn.setToolTip("Help")
        help_btn.clicked.connect(lambda: show_page_help("rider", self))
        header_row = QHBoxLayout()
        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(help_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("Enter your body measurements to enable accurate bike-fit analysis.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name (optional):"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Your name")
        self._name_input.setMaximumWidth(300)
        name_row.addWidget(self._name_input)
        name_row.addStretch()
        layout.addLayout(name_row)

        body_group = QGroupBox("Body Measurements")
        body_layout = QVBoxLayout(body_group)

        self._height = MeasurementInput("Height", "cm", 100, 250, default=180)
        self._weight = MeasurementInput("Weight", "kg", 30, 200, default=65)
        self._inseam = MeasurementInput("Inseam (inner leg)", "cm", 50, 120, default=83)
        self._foot_size = MeasurementInput("Foot Size", "EU", 30, 55, decimals=0, default=41)
        self._arm_length = MeasurementInput("Arm Length", "cm", 40, 90, default=60)
        self._torso_length = MeasurementInput("Torso Length", "cm", 30, 80, default=52)
        self._shoulder_width = MeasurementInput("Shoulder Width", "cm", 25, 60, default=38)

        for w in [self._height, self._weight, self._inseam, self._foot_size,
                  self._arm_length, self._torso_length, self._shoulder_width]:
            body_layout.addWidget(w)

        layout.addWidget(body_group)

        profile_group = QGroupBox("Riding Profile")
        profile_layout = QFormLayout(profile_group)

        self._flexibility = QComboBox()
        self._flexibility.addItems([f.value.title() for f in Flexibility])
        self._flexibility.setCurrentIndex(1)
        profile_layout.addRow("Flexibility:", self._flexibility)

        self._riding_style = QComboBox()
        self._riding_style.addItems([s.value.title() for s in RidingStyle])
        self._riding_style.setCurrentIndex(0)
        profile_layout.addRow("Riding Style:", self._riding_style)

        layout.addWidget(profile_group)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_next = QPushButton("Next  →")
        self._btn_next.setFixedSize(140, 40)
        self._btn_next.setProperty("class", "primary")
        self._btn_next.clicked.connect(self._on_submit)
        btn_row.addWidget(self._btn_next)
        layout.addLayout(btn_row)

        layout.addStretch()

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
        self._height.value = data.get("height_cm", 180)
        self._weight.value = data.get("weight_kg", 65)
        self._inseam.value = data.get("inseam_cm", 83)
        self._foot_size.value = data.get("foot_size_eu", 41)
        self._arm_length.value = data.get("arm_length_cm", 60)
        self._torso_length.value = data.get("torso_length_cm", 52)
        self._shoulder_width.value = data.get("shoulder_width_cm", 38)

    def show_errors(self, errors: list[str]) -> None:
        QMessageBox.warning(self, "Validation Errors", "\n".join(errors))

    def _on_submit(self) -> None:
        """Handle Next button click — emit signal with rider data."""
        self.rider_data_submitted.emit(self.get_data())
