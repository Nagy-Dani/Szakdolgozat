"""AngleGauge — custom painted arc gauge for angle values."""
from __future__ import annotations

import math

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QConicalGradient


class AngleGauge(QWidget):
    """A circular arc gauge that shows a current angle value against ideal range.

    Green zone = ideal, yellow = slightly off, red = far off.
    """

    def __init__(
        self,
        label: str = "",
        ideal_min: float = 0.0,
        ideal_max: float = 180.0,
        value: float = 0.0,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._label = label
        self._ideal_min = ideal_min
        self._ideal_max = ideal_max
        self._value = value
        self.setMinimumSize(120, 140)

    # --- public API ---

    def set_value(self, value: float) -> None:
        self._value = value
        self.update()

    def set_range(self, ideal_min: float, ideal_max: float) -> None:
        self._ideal_min = ideal_min
        self._ideal_max = ideal_max
        self.update()

    @property
    def severity_color(self) -> QColor:
        if self._ideal_min <= self._value <= self._ideal_max:
            return QColor("#22c55e")  # green
        margin = (self._ideal_max - self._ideal_min) * 0.5
        if (self._ideal_min - margin) <= self._value <= (self._ideal_max + margin):
            return QColor("#eab308")  # yellow
        return QColor("#ef4444")      # red

    # --- painting ---

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height() - 24  # leave room for label
        size = min(w, h)
        margin = 10
        rect = QRectF(
            (w - size) / 2 + margin,
            margin,
            size - 2 * margin,
            size - 2 * margin,
        )

        # Background arc (gray)
        pen = QPen(QColor("#333333"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 210 * 16, -240 * 16)

        # Value arc
        color = self.severity_color
        pen.setColor(color)
        painter.setPen(pen)
        frac = max(0.0, min(1.0, self._value / 180.0))
        span = int(-240 * frac * 16)
        painter.drawArc(rect, 210 * 16, span)

        # Value text
        painter.setPen(QColor("white"))
        font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._value:.0f}°")

        # Label
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        label_rect = QRectF(0, h + 4, w, 20)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignHCenter, self._label)

        painter.end()
