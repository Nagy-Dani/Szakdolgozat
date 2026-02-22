"""Geometric angle calculations for cycling biomechanics."""

from __future__ import annotations

import math

import numpy as np

from models.pose_model import BodyLandmark, PoseFrame
from models.analysis_model import CyclingAngles


def _angle_3p(p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> float:
    """Calculate the angle at p2 formed by the line segments p1-p2 and p3-p2.

    Returns the angle in degrees (0–180).
    """
    v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
    v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def _angle_to_horizontal(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Angle of the line p1→p2 relative to the horizontal (in degrees)."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return abs(math.degrees(math.atan2(dy, dx)))


def _lm_xy(lm: BodyLandmark) -> tuple[float, float]:
    return (lm.x, lm.y)


# ──────────────────────────────────────────── Per-landmark calculations


def calculate_knee_extension(hip: BodyLandmark, knee: BodyLandmark, ankle: BodyLandmark) -> float:
    """Angle at the knee (hip-knee-ankle). Ideal at BDC ≈ 140-150°."""
    return _angle_3p(_lm_xy(hip), _lm_xy(knee), _lm_xy(ankle))


def calculate_hip_angle(shoulder: BodyLandmark, hip: BodyLandmark, knee: BodyLandmark) -> float:
    """Angle at the hip (shoulder-hip-knee). Ideal ≈ 40-55° (road)."""
    return _angle_3p(_lm_xy(shoulder), _lm_xy(hip), _lm_xy(knee))


def calculate_back_angle(shoulder: BodyLandmark, hip: BodyLandmark) -> float:
    """Angle of the torso (shoulder→hip) relative to horizontal. Ideal ≈ 35-45° road."""
    return _angle_to_horizontal(_lm_xy(hip), _lm_xy(shoulder))


def calculate_ankle_angle(knee: BodyLandmark, ankle: BodyLandmark, toe: BodyLandmark) -> float:
    """Angle at the ankle (knee-ankle-toe). Ideal ≈ 90-120°."""
    return _angle_3p(_lm_xy(knee), _lm_xy(ankle), _lm_xy(toe))


def calculate_elbow_angle(shoulder: BodyLandmark, elbow: BodyLandmark, wrist: BodyLandmark) -> float:
    """Angle at the elbow (shoulder-elbow-wrist). Ideal ≈ 150-165°."""
    return _angle_3p(_lm_xy(shoulder), _lm_xy(elbow), _lm_xy(wrist))


def calculate_shoulder_angle(hip: BodyLandmark, shoulder: BodyLandmark, elbow: BodyLandmark) -> float:
    """Angle at the shoulder (hip-shoulder-elbow)."""
    return _angle_3p(_lm_xy(hip), _lm_xy(shoulder), _lm_xy(elbow))


# ──────────────────────────────────────────── Frame-level calculation


def compute_frame_angles(pose: PoseFrame) -> dict[str, float] | None:
    """Compute all cycling angles for a single PoseFrame.

    Returns None if required landmarks are missing.
    """
    get = pose.get
    hip = get("left_hip")
    knee = get("left_knee")
    ankle = get("left_ankle")
    shoulder = get("left_shoulder")
    elbow = get("left_elbow")
    wrist = get("left_wrist")
    toe = get("left_foot_index")

    if not all([hip, knee, ankle, shoulder, elbow, wrist, toe]):
        return None

    return {
        "knee_extension": calculate_knee_extension(hip, knee, ankle),
        "hip_angle": calculate_hip_angle(shoulder, hip, knee),
        "back_angle": calculate_back_angle(shoulder, hip),
        "ankle_angle": calculate_ankle_angle(knee, ankle, toe),
        "elbow_angle": calculate_elbow_angle(shoulder, elbow, wrist),
        "shoulder_angle": calculate_shoulder_angle(hip, shoulder, elbow),
    }


# ──────────────────────────────────────────── Aggregation over cycles


def aggregate_angles(frames_angles: list[dict[str, float]]) -> CyclingAngles:
    """Aggregate per-frame angle dicts into a single CyclingAngles summary.

    Uses min/max/mean across the pedal stroke for each angle.
    """
    if not frames_angles:
        return CyclingAngles()

    keys = frames_angles[0].keys()
    arrays = {k: [f[k] for f in frames_angles] for k in keys}

    return CyclingAngles(
        knee_extension_min=float(np.min(arrays["knee_extension"])),
        knee_extension_max=float(np.max(arrays["knee_extension"])),
        knee_flexion_max=180.0 - float(np.min(arrays["knee_extension"])),
        hip_angle_min=float(np.min(arrays["hip_angle"])),
        hip_angle_max=float(np.max(arrays["hip_angle"])),
        back_angle=float(np.mean(arrays["back_angle"])),
        ankle_angle_min=float(np.min(arrays["ankle_angle"])),
        ankle_angle_max=float(np.max(arrays["ankle_angle"])),
        shoulder_angle=float(np.mean(arrays["shoulder_angle"])),
        elbow_angle=float(np.mean(arrays["elbow_angle"])),
    )
