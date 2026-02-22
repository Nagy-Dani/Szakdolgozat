"""MeasurementInput — labeled numeric input with unit display."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QDoubleSpinBox,
)
from PyQt6.QtCore import pyqtSignal


class MeasurementInput(QWidget):
    """A labeled numeric field with unit suffix.

    Example usage::

        inp = MeasurementInput("Height", "cm", min_val=100, max_val=250)
        inp.value_changed.connect(lambda v: print(v))
    """

    value_changed = pyqtSignal(float)

    def __init__(
        self,
        label: str,
        unit: str = "cm",
        min_val: float = 0.0,
        max_val: float = 999.0,
        decimals: int = 1,
        default: float = 0.0,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self._label = QLabel(label)
        self._label.setMinimumWidth(140)
        layout.addWidget(self._label)

        self._spin = QDoubleSpinBox()
        self._spin.setRange(min_val, max_val)
        self._spin.setDecimals(decimals)
        self._spin.setValue(default)
        self._spin.setSuffix(f"  {unit}")
        self._spin.setMinimumWidth(140)
        self._spin.valueChanged.connect(self.value_changed.emit)
        layout.addWidget(self._spin)

        layout.addStretch()

    # --- public API ---

    @property
    def value(self) -> float:
        return self._spin.value()

    @value.setter
    def value(self, v: float) -> None:
        self._spin.setValue(v)

    def set_unit(self, unit: str) -> None:
        self._spin.setSuffix(f"  {unit}")
