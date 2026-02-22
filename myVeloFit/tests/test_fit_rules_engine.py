"""Tests for fit rules engine."""
from __future__ import annotations

import pytest
from models.analysis_model import CyclingAngles
from services.fit_rules_engine import evaluate_fit


def test_perfect_road_fit():
    """Angles within ideal road ranges should score highly."""
    angles = CyclingAngles(
        knee_extension_min=145,
        knee_extension_max=160,
        knee_flexion_max=70,
        hip_angle_min=48,
        hip_angle_max=65,
        back_angle=40,
        ankle_angle_min=100,
        ankle_angle_max=110,
        shoulder_angle=45,
        elbow_angle=158,
    )
    score, recs = evaluate_fit(angles, "road")
    assert score.overall >= 85
    assert score.category in ("excellent", "good")


def test_poor_knee_extension():
    """Low knee extension should generate a critical recommendation."""
    angles = CyclingAngles(
        knee_extension_min=120,  # way too low
        knee_extension_max=150,
        knee_flexion_max=60,
        hip_angle_min=48,
        hip_angle_max=65,
        back_angle=40,
        ankle_angle_min=100,
        ankle_angle_max=110,
        shoulder_angle=45,
        elbow_angle=158,
    )
    score, recs = evaluate_fit(angles, "road")
    saddle_rec = next(r for r in recs if r.component == "saddle_height")
    assert saddle_rec.severity.value in ("critical", "moderate")
    assert "Raise" in saddle_rec.adjustment


def test_different_styles_return_results():
    """All riding styles should produce valid results."""
    angles = CyclingAngles(
        knee_extension_min=145, knee_extension_max=160,
        knee_flexion_max=70, hip_angle_min=48, hip_angle_max=65,
        back_angle=40, ankle_angle_min=100, ankle_angle_max=110,
        shoulder_angle=45, elbow_angle=158,
    )
    for style in ["road", "mtb", "tt", "gravel", "commute"]:
        score, recs = evaluate_fit(angles, style)
        assert 0 <= score.overall <= 100
        assert len(recs) >= 3
