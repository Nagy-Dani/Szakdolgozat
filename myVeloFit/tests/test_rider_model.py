"""Tests for rider model."""
from __future__ import annotations

import pytest
from models.rider_model import RiderMeasurements, Flexibility, RidingStyle


def test_valid_rider():
    rider = RiderMeasurements(
        height_cm=180, weight_kg=75, inseam_cm=85,
        foot_size_eu=43, arm_length_cm=62, torso_length_cm=52,
        shoulder_width_cm=44,
    )
    assert rider.is_valid
    assert rider.validate() == []


def test_invalid_height():
    rider = RiderMeasurements(height_cm=50)  # too short
    errors = rider.validate()
    assert any("height_cm" in e for e in errors)


def test_estimated_saddle_height():
    rider = RiderMeasurements(inseam_cm=85)
    assert rider.estimated_saddle_height == pytest.approx(75.1, rel=0.01)


def test_serialization_roundtrip():
    rider = RiderMeasurements(
        height_cm=175, weight_kg=70, inseam_cm=82,
        foot_size_eu=42, arm_length_cm=60, torso_length_cm=50,
        shoulder_width_cm=40, flexibility=Flexibility.HIGH,
        riding_style=RidingStyle.MTB, name="Alice",
    )
    d = rider.to_dict()
    restored = RiderMeasurements.from_dict(d)
    assert restored.height_cm == rider.height_cm
    assert restored.flexibility == Flexibility.HIGH
    assert restored.riding_style == RidingStyle.MTB
    assert restored.name == "Alice"
