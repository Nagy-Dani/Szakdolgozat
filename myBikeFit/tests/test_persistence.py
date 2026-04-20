"""Tests for persistence_service — full session save/load roundtrip."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from models.rider_model import RiderMeasurements, Flexibility, RidingStyle
from models.bike_model import BikeGeometry
from models.analysis_model import CyclingAngles, FitScore
from models.recommendation_model import Recommendation, Severity
from services.persistence_service import save_session, load_session


def _sample_rider() -> RiderMeasurements:
    return RiderMeasurements(
        height_cm=180.0, weight_kg=75.0, inseam_cm=85.0,
        foot_size_eu=43.0, arm_length_cm=62.0, torso_length_cm=52.0,
        shoulder_width_cm=44.0, flexibility=Flexibility.MEDIUM,
        riding_style=RidingStyle.ROAD, name="TestRider",
    )


def _sample_bike() -> BikeGeometry:
    return BikeGeometry(
        frame_size_cm=56.0, saddle_height_cm=75.0, saddle_setback_cm=5.0,
        handlebar_reach_cm=45.0, handlebar_drop_cm=8.0,
    )


def _sample_angles() -> CyclingAngles:
    return CyclingAngles(
        knee_extension_min=140.0, knee_extension_max=155.0,
        knee_flexion_max=72.0, hip_angle_min=48.0, hip_angle_max=65.0,
        back_angle=40.0, ankle_angle_min=88.0, ankle_angle_max=105.0,
        ankle_angle_at_3=92.0, foot_ground_at_12=25.0,
        foot_ground_at_3=6.0, foot_ground_at_6=14.0,
        ankle_total_range=17.0, shoulder_angle=42.0, elbow_angle=158.0,
    )


def _sample_score() -> FitScore:
    return FitScore(overall=82.0, knee_score=90.0, hip_score=78.0,
                    back_score=85.0, ankle_score=70.0, reach_score=75.0)


def _sample_recs() -> list[Recommendation]:
    return [
        Recommendation(
            component="saddle_height", severity=Severity.MINOR,
            current_value="140.0°", ideal_range="65–148°",
            adjustment="Saddle height is well set",
            explanation="Knee extension determines saddle height.",
        ),
        Recommendation(
            component="handlebar_position", severity=Severity.MODERATE,
            current_value="40.0°", ideal_range="35–45°",
            adjustment="Raise handlebars",
            explanation="Back angle affects comfort.",
        ),
    ]


def test_full_roundtrip():
    """Save a complete session and load it back — all fields must survive."""
    rider = _sample_rider()
    bike = _sample_bike()
    angles = _sample_angles()
    score = _sample_score()
    recs = _sample_recs()

    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "test_session.json")

        save_session(
            rider=rider, bike=bike, fit_score=score,
            cycling_angles=angles, recommendations=recs,
            facing_side="right", video_path="/some/video.mp4",
            path=path,
        )

        # Verify JSON is valid and has v2.0 schema
        with open(path) as f:
            raw = json.load(f)
        assert raw["version"] == "2.0"
        assert raw["facing_side"] == "right"
        assert raw["video_path"] == "/some/video.mp4"
        assert "cycling_angles" in raw
        assert "recommendations" in raw
        assert len(raw["recommendations"]) == 2

        # Load and verify
        data = load_session(path)

        assert data["rider"].name == "TestRider"
        assert data["rider"].riding_style == RidingStyle.ROAD
        assert data["bike"].frame_size_cm == 56.0
        assert data["facing_side"] == "right"
        assert data["video_path"] == "/some/video.mp4"

        loaded_angles = data["cycling_angles"]
        assert loaded_angles.knee_extension_min == 140.0
        assert loaded_angles.ankle_angle_at_3 == 92.0
        assert loaded_angles.foot_ground_at_12 == 25.0

        loaded_score = data["fit_score"]
        assert loaded_score.overall == 82.0
        assert loaded_score.category == "good"

        loaded_recs = data["recommendations"]
        assert len(loaded_recs) == 2
        assert loaded_recs[0].severity == Severity.MINOR
        assert loaded_recs[1].component == "handlebar_position"


def test_minimal_save_load():
    """Save only rider+bike (no analysis yet) and load — should still work."""
    rider = _sample_rider()
    bike = _sample_bike()

    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "minimal.json")
        save_session(rider=rider, bike=bike, path=path)

        data = load_session(path)
        assert data["rider"].height_cm == 180.0
        assert data["bike"].saddle_height_cm == 75.0
        assert "fit_score" not in data
        assert "cycling_angles" not in data
        assert "recommendations" not in data
        assert data["facing_side"] == "left"  # default


def test_cycling_angles_from_dict():
    angles = _sample_angles()
    d = angles.to_dict()
    restored = CyclingAngles.from_dict(d)
    assert restored.knee_extension_min == angles.knee_extension_min
    assert restored.ankle_angle_at_3 == angles.ankle_angle_at_3


def test_fit_score_from_dict():
    score = _sample_score()
    d = score.to_dict()
    assert "category" in d
    restored = FitScore.from_dict(d)
    assert restored.overall == score.overall
    assert restored.category == "good"
