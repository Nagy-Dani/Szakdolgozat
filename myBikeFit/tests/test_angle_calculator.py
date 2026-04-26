from __future__ import annotations

import pytest
from models.pose_model import BodyLandmark
from services.angle_calculator import (
    calculate_knee_extension,
    calculate_hip_angle,
    calculate_back_angle,
    calculate_ankle_angle,
    calculate_elbow_angle,
    aggregate_angles,
    _angle_3p,
    _angle_to_horizontal,
)


def _lm(x, y, name="test"):
    return BodyLandmark(name=name, x=x, y=y, z=0, visibility=1.0)


def test_angle_straight_line():
    """Three collinear points should give 180°."""
    angle = _angle_3p((0, 0), (1, 0), (2, 0))
    assert angle == pytest.approx(180.0, abs=0.1)


def test_angle_right_angle():
    """90° angle."""
    angle = _angle_3p((0, 1), (0, 0), (1, 0))
    assert angle == pytest.approx(90.0, abs=0.1)


def test_knee_extension():
    hip = _lm(0.3, 0.4, "left_hip")
    knee = _lm(0.35, 0.6, "left_knee")
    ankle = _lm(0.33, 0.8, "left_ankle")
    angle = calculate_knee_extension(hip, knee, ankle)
    assert 0 < angle < 180


def test_hip_angle():
    shoulder = _lm(0.3, 0.2, "left_shoulder")
    hip = _lm(0.35, 0.4, "left_hip")
    knee = _lm(0.38, 0.6, "left_knee")
    angle = calculate_hip_angle(shoulder, hip, knee)
    assert 0 < angle < 180


def test_back_angle():
    shoulder = _lm(0.35, 0.2, "left_shoulder")
    hip = _lm(0.35, 0.4, "left_hip")
    angle = calculate_back_angle(shoulder, hip)
    assert 0 <= angle <= 90
    
def _lm(x, y, name="test"):
    return BodyLandmark(name=name, x=x, y=y, z=0, visibility=1.0)


def test_angle_3p_acute():
    """45°-os szöget kell visszaadnia."""
    angle = _angle_3p((1, 1), (0, 0), (1, 0))
    assert angle == pytest.approx(45.0, abs=0.1)


def test_angle_3p_zero_vector_safe():
    """Egybeeső pontok esetén ne dobjon hibát (regularizáció)."""
    angle = _angle_3p((0, 0), (0, 0), (1, 0))
    assert 0 <= angle <= 180


def test_angle_to_horizontal_horizontal_line():
    """Vízszintes egyenesnek 0°-os szögnek kell lennie."""
    angle = _angle_to_horizontal((0, 0), (1, 0))
    assert angle == pytest.approx(0.0, abs=0.1)


def test_angle_to_horizontal_vertical_line():
    """Függőleges egyenesnek 90°-os szögnek kell lennie."""
    angle = _angle_to_horizontal((0, 0), (0, 1))
    assert angle == pytest.approx(90.0, abs=0.1)


def test_angle_to_horizontal_returns_acute():
    """Tompaszöget hegyesszögbe kell konvertálnia."""
    angle = _angle_to_horizontal((0, 0), (-1, 1))
    assert 0 <= angle <= 90


def test_calculate_elbow_angle_in_range():
    shoulder = _lm(0.3, 0.3, "left_shoulder")
    elbow = _lm(0.4, 0.4, "left_elbow")
    wrist = _lm(0.5, 0.5, "left_wrist")
    angle = calculate_elbow_angle(shoulder, elbow, wrist)
    assert 0 < angle <= 180


def test_calculate_ankle_angle_in_range():
    knee = _lm(0.35, 0.5, "left_knee")
    ankle = _lm(0.33, 0.8, "left_ankle")
    toe = _lm(0.4, 0.85, "left_foot_index")
    angle = calculate_ankle_angle(knee, ankle, toe)
    assert 0 < angle <= 180


def test_aggregate_angles_with_empty_input():
    """Üres bemenet esetén CyclingAngles default értékekkel."""
    result = aggregate_angles({})
    assert result.knee_extension_min == 0
    assert result.knee_extension_max == 0
