"""Tests for fit rules engine."""
from __future__ import annotations

import pytest
from models.analysis_model import CyclingAngles
from services.fit_rules_engine import evaluate_fit


def test_perfect_road_fit():
    """Angles within ideal road ranges should score highly."""
    angles = CyclingAngles(
        knee_extension_min=135,
        knee_extension_max=140,
        knee_flexion_max=70,
        hip_angle_min=50,
        hip_angle_max=65,
        back_angle=40,
        ankle_angle_min=82,
        ankle_angle_max=100,
        ankle_angle_at_3=90,
        foot_ground_at_12=25,
        foot_ground_at_3=6,
        foot_ground_at_6=12,
        ankle_total_range=18,
        shoulder_angle=45,
        elbow_angle=158,
    )
    score, recs = evaluate_fit(angles, "road")
    assert score.overall >= 85
    assert score.category in ("excellent", "good")


def test_poor_knee_extension():
    """Very low knee extension should generate a critical recommendation."""
    angles = CyclingAngles(
        knee_extension_min=20,
        knee_extension_max=30,  # <=35 degrees below the new 65 min to trigger critical/moderate
        knee_flexion_max=80,
        hip_angle_min=48,
        hip_angle_max=65,
        back_angle=40,
        ankle_angle_min=85,
        ankle_angle_max=100,
        ankle_angle_at_3=90,
        foot_ground_at_12=25,
        foot_ground_at_3=6,
        foot_ground_at_6=12,
        ankle_total_range=15,
        shoulder_angle=45,
        elbow_angle=158,
    )
    score, recs = evaluate_fit(angles, "road")
    saddle_rec = next(r for r in recs if r.component == "saddle_height")
    assert saddle_rec.severity.value != "optimal"
    assert "Raise" in saddle_rec.adjustment


def test_different_styles_return_results():
    """All riding styles should produce valid results."""
    angles = CyclingAngles(
        knee_extension_min=140, knee_extension_max=150,
        knee_flexion_max=70, hip_angle_min=48, hip_angle_max=65,
        back_angle=40, ankle_angle_min=85, ankle_angle_max=100,
        ankle_angle_at_3=90, foot_ground_at_12=25,
        foot_ground_at_3=6, foot_ground_at_6=12,
        ankle_total_range=15, shoulder_angle=45, elbow_angle=158,
    )
    for style in ["road", "mtb", "tt", "gravel", "commute"]:
        score, recs = evaluate_fit(angles, style)
        assert 0 <= score.overall <= 100
        assert len(recs) >= 3
