"""Tests for angle calculator."""
from __future__ import annotations

import pytest
from models.pose_model import BodyLandmark
from services.angle_calculator import (
    calculate_knee_extension,
    calculate_hip_angle,
    calculate_back_angle,
    _angle_3p,
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
    shoulder = _lm(0.3, 0.2, "left_shoulder")
    hip = _lm(0.35, 0.4, "left_hip")
    angle = calculate_back_angle(shoulder, hip)
    assert 0 <= angle <= 90
