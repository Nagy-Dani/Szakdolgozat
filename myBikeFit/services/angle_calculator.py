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
    """Angle of the line p1→p2 relative to the horizontal (in degrees).
    Always returns a value in 0–90° (the acute angle between the line
    and the horizontal axis), regardless of the direction of the line.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = abs(math.degrees(math.atan2(dy, dx)))
    if angle > 90:
        angle = 180 - angle
    return angle


def _lm_xy(lm: BodyLandmark) -> tuple[float, float]:
    return (lm.x, lm.y)

def calculate_knee_extension(hip: BodyLandmark, knee: BodyLandmark, ankle: BodyLandmark) -> float:
    """Angle at the knee"""
    return _angle_3p(_lm_xy(hip), _lm_xy(knee), _lm_xy(ankle))

def calculate_hip_angle(shoulder: BodyLandmark, hip: BodyLandmark, knee: BodyLandmark) -> float:
    """Angle at the hip"""
    return _angle_3p(_lm_xy(shoulder), _lm_xy(hip), _lm_xy(knee))

def calculate_back_angle(shoulder: BodyLandmark, hip: BodyLandmark) -> float:
    """Angle of the torso (shoulder→hip) relative to horizontal"""
    return _angle_to_horizontal(_lm_xy(hip), _lm_xy(shoulder))

def calculate_ankle_angle(knee: BodyLandmark, ankle: BodyLandmark, toe: BodyLandmark) -> float:
    """Angle at the ankle"""
    return _angle_3p(_lm_xy(knee), _lm_xy(ankle), _lm_xy(toe))

def calculate_foot_ground_angle(heel: BodyLandmark, toe: BodyLandmark) -> float:
    """Angle of the foot (heel→toe) relative to horizontal.
    Positive = toe-down. In image coords Y increases downward,
    so toe below heel means toe.y > heel.y -> positive angle.
    """
    dx = toe.x - heel.x
    dy = toe.y - heel.y
    return math.degrees(math.atan2(dy, abs(dx) + 1e-8))

def calculate_elbow_angle(shoulder: BodyLandmark, elbow: BodyLandmark, wrist: BodyLandmark) -> float:
    """Angle at the elbow"""
    return _angle_3p(_lm_xy(shoulder), _lm_xy(elbow), _lm_xy(wrist))

def calculate_shoulder_angle(hip: BodyLandmark, shoulder: BodyLandmark, elbow: BodyLandmark) -> float:
    """Angle at the shoulder"""
    return _angle_3p(_lm_xy(hip), _lm_xy(shoulder), _lm_xy(elbow))


def compute_frame_angles(pose: PoseFrame, side: str = "left") -> dict[str, float] | None:
    """Compute all cycling angles for a single PoseFrame."""
    get = pose.get
    hip = get(f"{side}_hip")
    knee = get(f"{side}_knee")
    ankle = get(f"{side}_ankle")
    shoulder = get(f"{side}_shoulder")
    elbow = get(f"{side}_elbow")
    wrist = get(f"{side}_wrist")
    toe = get(f"{side}_foot_index")
    heel = get(f"{side}_heel")

    if not all([hip, knee, ankle, shoulder, elbow, wrist, toe, heel]):
        return None

    return {
        "knee_extension": calculate_knee_extension(hip, knee, ankle),
        "hip_angle": calculate_hip_angle(shoulder, hip, knee),
        "back_angle": calculate_back_angle(shoulder, hip),
        "ankle_angle": calculate_ankle_angle(knee, ankle, toe),
        "foot_ground_angle": calculate_foot_ground_angle(heel, toe),
        "elbow_angle": calculate_elbow_angle(shoulder, elbow, wrist),
        "shoulder_angle": calculate_shoulder_angle(hip, shoulder, elbow),
    }


def _find_pedal_positions(knee_angles: list[float]) -> dict[str, int]:
    """Identify frame indices for key pedal positions using knee angle.
    - TDC (12 o'clock): maximum knee flexion = minimum knee angle
    - BDC (6 o'clock): maximum knee extension = maximum knee angle
    - 3 o'clock: midpoint frame between TDC and BDC (descending)
    """
    tdc_idx = int(np.argmin(knee_angles))
    bdc_idx = int(np.argmax(knee_angles))

    if tdc_idx < bdc_idx:
        three_idx = (tdc_idx + bdc_idx) // 2
    else:
        mid = (tdc_idx + bdc_idx + len(knee_angles)) // 2
        three_idx = mid % len(knee_angles)

    return {"tdc": tdc_idx, "bdc": bdc_idx, "three": three_idx}


def aggregate_angles(frames_angles: list[dict[str, float]]) -> CyclingAngles:
    """Aggregate per-frame angle dicts into a single CyclingAngles summary.
    Uses min/max/mean across the pedal stroke for each angle,
    and extracts position-specific ankle/foot measurements.
    """
    if not frames_angles:
        return CyclingAngles()

    keys = frames_angles[0].keys()
    arrays = {k: [f[k] for f in frames_angles] for k in keys}

    positions = _find_pedal_positions(arrays["knee_extension"])

    ankle_at_3 = arrays["ankle_angle"][positions["three"]]
    foot_ground_at_12 = arrays["foot_ground_angle"][positions["tdc"]]
    foot_ground_at_3 = arrays["foot_ground_angle"][positions["three"]]
    foot_ground_at_6 = arrays["foot_ground_angle"][positions["bdc"]]
    ankle_total_range = float(np.max(arrays["ankle_angle"]) - np.min(arrays["ankle_angle"]))

    return CyclingAngles(
        knee_extension_min=float(np.min(arrays["knee_extension"])),
        knee_extension_max=float(np.max(arrays["knee_extension"])),
        knee_flexion_max=180.0 - float(np.min(arrays["knee_extension"])),
        hip_angle_min=float(np.min(arrays["hip_angle"])),
        hip_angle_max=float(np.max(arrays["hip_angle"])),
        back_angle=float(np.mean(arrays["back_angle"])),
        ankle_angle_min=float(np.min(arrays["ankle_angle"])),
        ankle_angle_max=float(np.max(arrays["ankle_angle"])),
        ankle_angle_at_3=float(ankle_at_3),
        foot_ground_at_12=float(foot_ground_at_12),
        foot_ground_at_3=float(foot_ground_at_3),
        foot_ground_at_6=float(foot_ground_at_6),
        ankle_total_range=float(ankle_total_range),
        shoulder_angle=float(np.mean(arrays["shoulder_angle"])),
        elbow_angle=float(np.mean(arrays["elbow_angle"])),
    )
