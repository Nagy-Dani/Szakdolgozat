"""Tests for fit rules engine."""
from __future__ import annotations

import pytest
from models.analysis_model import CyclingAngles
from models.rider_model import RiderMeasurements, RidingStyle
from models.bike_model import BikeGeometry
from services.fit_rules_engine import evaluate_fit


@pytest.fixture
def default_rider():
    return RiderMeasurements(name="Test Rider", riding_style=RidingStyle.ROAD)


@pytest.fixture
def default_bike():
    return BikeGeometry()


def test_perfect_road_fit(default_rider, default_bike):
    """Angles within ideal road ranges should score highly."""
    angles = CyclingAngles(
        knee_extension_min=135, knee_extension_max=140, knee_flexion_max=70,
        hip_angle_min=50, hip_angle_max=65, back_angle=40,
        ankle_angle_min=82, ankle_angle_max=100, ankle_angle_at_3=90,
        foot_ground_at_12=25, foot_ground_at_3=6, foot_ground_at_6=12,
        ankle_total_range=18, shoulder_angle=45, elbow_angle=158,
    )
    score, recs = evaluate_fit(angles, default_rider, default_bike)
    assert score.overall >= 85
    assert score.category in ("excellent", "good")


def test_poor_knee_extension(default_rider, default_bike):
    """Very low knee extension should generate a critical recommendation."""
    angles = CyclingAngles(
        knee_extension_min=20, knee_extension_max=30, knee_flexion_max=80,
        hip_angle_min=48, hip_angle_max=65, back_angle=40,
        ankle_angle_min=85, ankle_angle_max=100, ankle_angle_at_3=90,
        foot_ground_at_12=25, foot_ground_at_3=6, foot_ground_at_6=12,
        ankle_total_range=15, shoulder_angle=45, elbow_angle=158,
    )
    score, recs = evaluate_fit(angles, default_rider, default_bike)
    saddle_rec = next(r for r in recs if r.component == "saddle_height")
    assert saddle_rec.severity.value != "optimal"
    assert "Raise" in saddle_rec.adjustment


def test_different_styles_return_results(default_rider, default_bike):
    """All riding styles should produce valid results."""
    angles = CyclingAngles(
        knee_extension_min=140, knee_extension_max=150, knee_flexion_max=70,
        hip_angle_min=48, hip_angle_max=65, back_angle=40,
        ankle_angle_min=85, ankle_angle_max=100, ankle_angle_at_3=90,
        foot_ground_at_12=25, foot_ground_at_3=6, foot_ground_at_6=12,
        ankle_total_range=15, shoulder_angle=45, elbow_angle=158,
    )
    for style in ["road", "mtb", "tt", "gravel", "commute"]:
        # Update rider style dynamically
        from enum import Enum
        class TempStyle(Enum): ROAD="road"; MTB="mtb"; TT="tt"; GRAVEL="gravel"; COMMUTE="commute"
        for s in TempStyle:
            if s.value == style:
                default_rider.riding_style = s
                break
        
        score, recs = evaluate_fit(angles, default_rider, default_bike)
        assert 0 <= score.overall <= 100
        assert len(recs) >= 3


def test_geometric_recommendations_triggered():
    """If body measurements are provided, geometric recs should be generated.
    Ideal is 80 * 0.883 = 70.6 (Too high)
    Ideal is 80 * 0.66 = 52.8 (Too big)
    Ideal is (80*1.25)+65 = 165.0 (Too long)
    Ideal is (365+(0.85*58))/10 = 41.43 (Too long)
    """
    angles = CyclingAngles()
    rider = RiderMeasurements(inseam_cm=80.0, torso_length_cm=50.0, arm_length_cm=60.0)
    bike = BikeGeometry(
        saddle_height_cm=75.0,  
        frame_size_cm=58.0,     
        crank_length_mm=175.0,  
        handlebar_reach_cm=70.0 
    )
    score, recs = evaluate_fit(angles, rider, bike)

    assert score.geometry_score > 0.0
    
    comps = [r.component for r in recs]
    assert "saddle_height_geometric" in comps
    assert "frame_size" in comps
    assert "crank_length" in comps
    assert "overall_reach" in comps

    saddle_geom = next(r for r in recs if r.component == "saddle_height_geometric")
    assert "high" in saddle_geom.adjustment

    crank = next(r for r in recs if r.component == "crank_length")
    assert "long" in crank.adjustment


def test_geometric_recommendations_skipped_if_missing():
    """If body measurements are zeros (default), skip geometric checks."""
    angles = CyclingAngles()
    rider = RiderMeasurements()
    bike = BikeGeometry()   
    
    score, recs = evaluate_fit(angles, rider, bike)
    comps = [r.component for r in recs]
    
    assert score.geometry_score == 0.0
    
    assert "saddle_height_geometric" not in comps
    assert "frame_size" not in comps
    assert "crank_length" not in comps
    assert "overall_reach" not in comps
