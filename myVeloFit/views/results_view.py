"""Results view — fit score dashboard and recommendations."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from views.widgets.angle_gauge import AngleGauge
from models.analysis_model import FitScore
from models.recommendation_model import Recommendation


class ResultsView(QWidget):
    """Dashboard showing fit score, per-area breakdown, and recommendations."""

    export_requested = pyqtSignal()
    restart_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        header = QLabel("Fit Results")
        header.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        header.setStyleSheet("color: #cdd6f4; margin-bottom: 8px;")
        layout.addWidget(header)

        # --- Score overview ---
        scores_row = QHBoxLayout()

        self._overall_gauge = AngleGauge("Overall Score", 0, 100)
        self._overall_gauge.setMinimumSize(160, 180)
        scores_row.addWidget(self._overall_gauge)

        self._gauge_knee = AngleGauge("Knee", 0, 100)
        self._gauge_hip = AngleGauge("Hip", 0, 100)
        self._gauge_back = AngleGauge("Back", 0, 100)
        self._gauge_ankle = AngleGauge("Ankle", 0, 100)
        self._gauge_reach = AngleGauge("Reach", 0, 100)

        for g in [self._gauge_knee, self._gauge_hip, self._gauge_back,
                  self._gauge_ankle, self._gauge_reach]:
            scores_row.addWidget(g)

        layout.addLayout(scores_row)

        # --- Category label ---
        self._category_label = QLabel("")
        self._category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._category_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._category_label.setStyleSheet("margin: 8px 0;")
        layout.addWidget(self._category_label)

        # --- Recommendations ---
        rec_header = QLabel("Recommendations")
        rec_header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        rec_header.setStyleSheet("color: #cdd6f4; margin-top: 12px;")
        layout.addWidget(rec_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._rec_container = QWidget()
        self._rec_layout = QVBoxLayout(self._rec_container)
        self._rec_layout.setContentsMargins(0, 0, 0, 0)
        self._rec_layout.setSpacing(8)
        scroll.setWidget(self._rec_container)
        layout.addWidget(scroll, stretch=1)

        # --- Action buttons ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_export = QPushButton("📄  Export PDF")
        btn_export.setFixedSize(160, 40)
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #45475a; color: #cdd6f4;
                font-weight: bold; font-size: 14px; border-radius: 8px;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        btn_export.clicked.connect(self.export_requested.emit)
        btn_row.addWidget(btn_export)

        btn_restart = QPushButton("🔄  Start Over")
        btn_restart.setFixedSize(160, 40)
        btn_restart.setStyleSheet("""
            QPushButton {
                background-color: #7aa2f7; color: #1e1e2e;
                font-weight: bold; font-size: 14px; border-radius: 8px;
            }
            QPushButton:hover { background-color: #89b4fa; }
        """)
        btn_restart.clicked.connect(self.restart_requested.emit)
        btn_row.addWidget(btn_restart)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------ API

    def set_scores(self, scores: FitScore) -> None:
        # Re-purpose the AngleGauge to show 0–100 scores
        self._overall_gauge.set_value(scores.overall)
        self._gauge_knee.set_value(scores.knee_score)
        self._gauge_hip.set_value(scores.hip_score)
        self._gauge_back.set_value(scores.back_score)
        self._gauge_ankle.set_value(scores.ankle_score)
        self._gauge_reach.set_value(scores.reach_score)

        self._category_label.setText(scores.category.upper())
        self._category_label.setStyleSheet(
            f"color: {scores.category_color}; font-size: 18px; font-weight: bold; margin: 8px 0;"
        )

    def set_recommendations(self, recommendations: list[Recommendation]) -> None:
        # Clear existing cards
        while self._rec_layout.count():
            item = self._rec_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for rec in recommendations:
            card = self._create_card(rec)
            self._rec_layout.addWidget(card)

        self._rec_layout.addStretch()

    def _create_card(self, rec: Recommendation) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #313244;
                border-left: 4px solid {rec.severity.color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)

        # Header
        header_row = QHBoxLayout()
        icon = QLabel(rec.severity.icon)
        icon.setFont(QFont("Segoe UI", 16))
        header_row.addWidget(icon)

        name = QLabel(rec.display_name)
        name.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        name.setStyleSheet("color: #cdd6f4;")
        header_row.addWidget(name)
        header_row.addStretch()

        severity_lbl = QLabel(rec.severity.value.upper())
        severity_lbl.setStyleSheet(
            f"color: {rec.severity.color}; font-weight: bold; font-size: 11px;"
        )
        header_row.addWidget(severity_lbl)
        layout.addLayout(header_row)

        # Adjustment
        adj = QLabel(f"⚙️  {rec.adjustment}")
        adj.setStyleSheet("color: #cdd6f4; font-size: 13px; margin-top: 4px;")
        adj.setWordWrap(True)
        layout.addWidget(adj)

        # Current vs Ideal
        detail = QLabel(f"Current: {rec.current_value}  •  Ideal: {rec.ideal_range}")
        detail.setStyleSheet("color: #a6adc8; font-size: 12px;")
        layout.addWidget(detail)

        # Explanation
        expl = QLabel(rec.explanation)
        expl.setStyleSheet("color: #6c7086; font-size: 11px; margin-top: 4px;")
        expl.setWordWrap(True)
        layout.addWidget(expl)

        return card
