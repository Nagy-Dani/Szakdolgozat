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
    """Angle at the ankle (knee-ankle-toe). Ideal ≈ 75-105°."""
    return _angle_3p(_lm_xy(knee), _lm_xy(ankle), _lm_xy(toe))


def calculate_foot_ground_angle(heel: BodyLandmark, toe: BodyLandmark) -> float:
    """Angle of the foot (heel→toe) relative to horizontal.

    Positive = toe-down. In image coords Y increases downward,
    so toe below heel means toe.y > heel.y → positive angle.
    """
    dx = toe.x - heel.x
    dy = toe.y - heel.y  # positive when toe is lower (toe-down)
    return math.degrees(math.atan2(dy, abs(dx) + 1e-8))


def calculate_elbow_angle(shoulder: BodyLandmark, elbow: BodyLandmark, wrist: BodyLandmark) -> float:
    """Angle at the elbow (shoulder-elbow-wrist). Ideal ≈ 150-165°."""
    return _angle_3p(_lm_xy(shoulder), _lm_xy(elbow), _lm_xy(wrist))


def calculate_shoulder_angle(hip: BodyLandmark, shoulder: BodyLandmark, elbow: BodyLandmark) -> float:
    """Angle at the shoulder (hip-shoulder-elbow)."""
    return _angle_3p(_lm_xy(hip), _lm_xy(shoulder), _lm_xy(elbow))


# ──────────────────────────────────────────── Frame-level calculation


def compute_frame_angles(pose: PoseFrame, side: str = "left") -> dict[str, float] | None:
    """Compute all cycling angles for a single PoseFrame.

    Args:
        pose: The detected pose frame.
        side: Which body side to use — "left" or "right".

    Returns None if required landmarks are missing.
    """
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


# ──────────────────────────────────────────── Helper: bilateral geometry


def _midpoint(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def _knee_tracking_angle(
    hip: BodyLandmark, knee: BodyLandmark, ankle: BodyLandmark,
) -> float:
    """Lateral deviation of the knee from the hip-ankle vertical line (degrees).

    In a front/back view the hip and ankle should form a roughly vertical line.
    The knee may deviate inward (valgus) or outward (varus).
    Returns the absolute deviation angle so 0° = perfect tracking.
    """
    # Vectors in 2-D image space (x = lateral, y = vertical)
    hip_ankle = np.array([ankle.x - hip.x, ankle.y - hip.y])
    hip_knee = np.array([knee.x - hip.x, knee.y - hip.y])
    # Project hip_knee onto hip_ankle direction
    ha_len = np.linalg.norm(hip_ankle) + 1e-8
    proj_len = np.dot(hip_knee, hip_ankle) / ha_len
    proj = (hip_ankle / ha_len) * proj_len
    deviation = hip_knee - proj
    dev_angle = float(np.degrees(np.arctan2(np.linalg.norm(deviation), abs(proj_len) + 1e-8)))
    return abs(dev_angle)


# ──────────────────────────────────────────── Front-view calculations

# MediaPipe is less reliable from front/back views — use a lower threshold.
_FRONT_BACK_VIS_THRESHOLD = 0.3


def compute_front_angles(pose: PoseFrame) -> dict[str, float] | None:
    """Compute front-view metrics — knee tracking only.

    Requires both left and right hip, knee, ankle landmarks.
    Returns None if required landmarks are missing.
    """
    get = pose.get
    l_hip, r_hip = get("left_hip"), get("right_hip")
    l_knee, r_knee = get("left_knee"), get("right_knee")
    l_ankle, r_ankle = get("left_ankle"), get("right_ankle")

    required = [l_hip, r_hip, l_knee, r_knee, l_ankle, r_ankle]
    if not all(lm and lm.visibility > _FRONT_BACK_VIS_THRESHOLD for lm in required):
        return None

    return {
        "knee_tracking_left": _knee_tracking_angle(l_hip, l_knee, l_ankle),
        "knee_tracking_right": _knee_tracking_angle(r_hip, r_knee, r_ankle),
    }


# ──────────────────────────────────────────── Back-view calculations


def compute_back_angles(pose: PoseFrame) -> dict[str, float] | None:
    """Compute back-view metrics — hip lateral sway.

    Measures how far the hip midpoint deviates laterally from the
    shoulder midpoint (a proxy for the body's center line).
    0° = perfectly centered, larger = more sway.

    Only requires hips and shoulders — avoids lower-body landmarks
    that MediaPipe struggles with from behind.
    """
    get = pose.get
    l_hip, r_hip = get("left_hip"), get("right_hip")
    l_shoulder, r_shoulder = get("left_shoulder"), get("right_shoulder")

    required = [l_hip, r_hip, l_shoulder, r_shoulder]
    if not all(lm and lm.visibility > _FRONT_BACK_VIS_THRESHOLD for lm in required):
        return None

    # Center references
    shoulder_mid = _midpoint(_lm_xy(l_shoulder), _lm_xy(r_shoulder))
    hip_mid = _midpoint(_lm_xy(l_hip), _lm_xy(r_hip))

    # Lateral offset as an angle (degrees)
    dx = abs(hip_mid[0] - shoulder_mid[0])
    dy = abs(hip_mid[1] - shoulder_mid[1]) + 1e-8
    hip_sway = float(np.degrees(np.arctan2(dx, dy)))

    return {"hip_sway": hip_sway}


# ──────────────────────────────────────────── Dispatcher


def compute_angles_for_view(
    pose: PoseFrame, view_type: str, side: str = "left",
) -> dict[str, float] | None:
    """Dispatch to the right angle-calculation function based on view type."""
    if view_type == "front":
        return compute_front_angles(pose)
    if view_type == "back":
        return compute_back_angles(pose)
    return compute_frame_angles(pose, side=side)


# ──────────────────────────────────────────── Aggregation over cycles


def _find_pedal_positions(knee_angles: list[float]) -> dict[str, int]:
    """Identify frame indices for key pedal positions using knee angle.

    - TDC (12 o'clock): maximum knee flexion = minimum knee angle
    - BDC (6 o'clock): maximum knee extension = maximum knee angle
    - 3 o'clock: midpoint frame between TDC and BDC (descending)
    """
    tdc_idx = int(np.argmin(knee_angles))
    bdc_idx = int(np.argmax(knee_angles))

    # 3 o'clock is roughly halfway between TDC and BDC
    if tdc_idx < bdc_idx:
        three_idx = (tdc_idx + bdc_idx) // 2
    else:
        # TDC is after BDC in this sequence — wrap around
        mid = (tdc_idx + bdc_idx + len(knee_angles)) // 2
        three_idx = mid % len(knee_angles)

    return {"tdc": tdc_idx, "bdc": bdc_idx, "three": three_idx}


def aggregate_angles(
    side_frames: list[dict[str, float]],
    front_frames: list[dict[str, float]] | None = None,
    back_frames: list[dict[str, float]] | None = None,
) -> CyclingAngles:
    """Aggregate per-frame angle dicts into a single CyclingAngles summary.

    Uses min/max/mean across the pedal stroke for each angle,
    and extracts position-specific ankle/foot measurements.
    """
    if not side_frames:
        return CyclingAngles()

    keys = side_frames[0].keys()
    arrays = {k: [f[k] for f in side_frames] for k in keys}

    # Detect pedal positions from knee angles
    positions = _find_pedal_positions(arrays["knee_extension"])

    # Position-specific ankle and foot-ground angles
    ankle_at_3 = arrays["ankle_angle"][positions["three"]]
    foot_ground_at_12 = arrays["foot_ground_angle"][positions["tdc"]]
    foot_ground_at_3 = arrays["foot_ground_angle"][positions["three"]]
    foot_ground_at_6 = arrays["foot_ground_angle"][positions["bdc"]]
    ankle_total_range = float(np.max(arrays["ankle_angle"]) - np.min(arrays["ankle_angle"]))

    angles_summary = CyclingAngles(
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
    
    # ──────────────────────────────────────────── Front/Back Aggregation
    
    if front_frames:
        f_keys = front_frames[0].keys()
        f_arrays = {k: [f[k] for f in front_frames] for k in f_keys}
        if "knee_tracking_left" in f_arrays:
            angles_summary.knee_tracking_left = float(np.mean(f_arrays["knee_tracking_left"]))
        if "knee_tracking_right" in f_arrays:
            angles_summary.knee_tracking_right = float(np.mean(f_arrays["knee_tracking_right"]))
            
    if back_frames:
        b_keys = back_frames[0].keys()
        b_arrays = {k: [f[k] for f in back_frames] for k in b_keys}
        if "hip_sway" in b_arrays:
            angles_summary.hip_sway = float(np.mean(b_arrays["hip_sway"]))
            
    return angles_summary
