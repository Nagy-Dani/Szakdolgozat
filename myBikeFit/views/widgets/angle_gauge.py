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
        score_mode: bool = False,
    ):
        super().__init__(parent)
        self._label = label
        self._ideal_min = ideal_min
        self._ideal_max = ideal_max
        self._value = value
        self._score_mode = score_mode
        self.setMinimumSize(100, 120)

    def set_value(self, value: float) -> None:
        self._value = value
        self.update()

    def set_range(self, ideal_min: float, ideal_max: float) -> None:
        self._ideal_min = ideal_min
        self._ideal_max = ideal_max
        self.update()

    def set_score_mode(self, enabled: bool) -> None:
        self._score_mode = enabled
        self.update()

    @property
    def severity_color(self) -> QColor:
        if self._score_mode:
            if self._value >= 90:
                return QColor("#22c55e")
            if self._value >= 75:
                return QColor("#84cc16")
            if self._value >= 55:
                return QColor("#eab308")
            return QColor("#ef4444")
        if self._ideal_min <= self._value <= self._ideal_max:
            return QColor("#22c55e")
        margin = (self._ideal_max - self._ideal_min) * 0.5
        if (self._ideal_min - margin) <= self._value <= (self._ideal_max + margin):
            return QColor("#eab308")
        return QColor("#ef4444")

    def paintEvent(self, event):
        """Paint the gauge."""

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height() - 24
        size = min(w, h)
        margin = 10
        rect = QRectF(
            (w - size) / 2 + margin,
            margin,
            size - 2 * margin,
            size - 2 * margin,
        )

        pen = QPen(QColor("#333333"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 210 * 16, -240 * 16)

        color = self.severity_color
        pen.setColor(color)
        painter.setPen(pen)
        scale = 100.0 if self._score_mode else 180.0
        frac = max(0.0, min(1.0, self._value / scale))
        span = int(-240 * frac * 16)
        painter.drawArc(rect, 210 * 16, span)

        painter.setPen(QColor("white"))
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        text = f"{self._value:.0f}" if self._score_mode else f"{self._value:.0f}°"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        font = QFont("Arial", 9)
        painter.setFont(font)
        label_rect = QRectF(0, h + 4, w, 20)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignHCenter, self._label)

        range_font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(range_font)
        painter.setPen(QColor("#a6adc8"))
        
        y_pos = rect.bottom() - 10
        min_rect = QRectF(rect.left() - 15, y_pos, 40, 20)
        max_rect = QRectF(rect.right() - 25, y_pos, 40, 20)
        
        painter.drawText(min_rect, Qt.AlignmentFlag.AlignCenter, f"{self._ideal_min:.0f}")
        painter.drawText(max_rect, Qt.AlignmentFlag.AlignCenter, f"{self._ideal_max:.0f}")

        painter.end()
