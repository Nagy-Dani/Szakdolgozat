"""Rule-based fit recommendation engine."""

from __future__ import annotations

import json
from pathlib import Path

from models.analysis_model import CyclingAngles, FitScore
from models.recommendation_model import Recommendation, Severity


def _load_ranges() -> dict:
    path = Path(__file__).resolve().parent.parent / "config" / "angle_ranges.json"
    with open(path) as f:
        return json.load(f)


def _severity_from_deviation(deviation: float, range_width: float) -> Severity:
    """Map absolute deviation to severity."""
    ratio = deviation / max(range_width, 1)
    if ratio <= 0:
        return Severity.OPTIMAL
    if ratio <= 0.5:
        return Severity.MINOR
    if ratio <= 1.0:
        return Severity.MODERATE
    return Severity.CRITICAL


def _score_single(value: float, ideal_min: float, ideal_max: float) -> float:
    """Score a single value against an ideal range (0–100)."""
    if ideal_min <= value <= ideal_max:
        return 100.0
    if value < ideal_min:
        deviation = ideal_min - value
    else:
        deviation = value - ideal_max
    range_width = ideal_max - ideal_min
    penalty = (deviation / max(range_width, 1)) * 40
    return max(0.0, 100.0 - penalty)


# ──────────────────────────────────────────── Main API


def evaluate_fit(
    angles: CyclingAngles,
    riding_style: str = "road",
) -> tuple[FitScore, list[Recommendation]]:
    """Evaluate cycling angles against ideal ranges and generate recommendations.

    Returns (FitScore, list[Recommendation]).
    """
    all_ranges = _load_ranges()
    ranges = all_ranges.get(riding_style, all_ranges["road"])

    recommendations: list[Recommendation] = []

    # --- Knee Extension (at BDC) ---
    r = ranges["knee_extension"]
    knee_val = angles.knee_extension_max  # BDC = minimum knee flexion = maximum extension
    knee_score = _score_single(knee_val, r["min"], r["max"])
    dev = 0 if r["min"] <= knee_val <= r["max"] else (
        r["min"] - knee_val if knee_val < r["min"] else knee_val - r["max"]
    )
    sev = _severity_from_deviation(dev, r["max"] - r["min"])
    adj = ""
    if knee_val < r["min"]:
        mm = round(dev * 2.5, 0)  # rough mm per degree
        adj = f"Raise saddle by approximately {mm:.0f} mm"
    elif knee_val > r["max"]:
        mm = round(dev * 2.5, 0)
        adj = f"Lower saddle by approximately {mm:.0f} mm"
    else:
        adj = "Saddle height is well set"
    recommendations.append(Recommendation(
        component="saddle_height",
        severity=sev,
        current_value=f"{knee_val:.1f}°",
        ideal_range=f"{r['min']}–{r['max']}°",
        adjustment=adj,
        explanation=(
            "Knee extension at the bottom of the pedal stroke determines saddle height. "
            "Too low causes knee stress; too high reduces power and risks rocking."
        ),
    ))

    # --- Hip Angle ---
    r = ranges["hip_angle"]
    hip_val = angles.hip_angle_min  # At TDC, most closed
    hip_score = _score_single(hip_val, r["min"], r["max"])
    dev = 0 if r["min"] <= hip_val <= r["max"] else (
        r["min"] - hip_val if hip_val < r["min"] else hip_val - r["max"]
    )
    sev = _severity_from_deviation(dev, r["max"] - r["min"])
    if hip_val < r["min"]:
        adj = f"Move saddle back or raise handlebars to open hip angle"
    elif hip_val > r["max"]:
        adj = f"Move saddle forward or lower handlebars to close hip angle"
    else:
        adj = "Hip angle is in a good range"
    recommendations.append(Recommendation(
        component="saddle_setback",
        severity=sev,
        current_value=f"{hip_val:.1f}°",
        ideal_range=f"{r['min']}–{r['max']}°",
        adjustment=adj,
        explanation=(
            "Hip angle affects power output and breathing. "
            "A too-closed hip angle compresses the abdomen and limits breathing capacity."
        ),
    ))

    # --- Back Angle ---
    r = ranges["back_angle"]
    back_val = angles.back_angle
    back_score = _score_single(back_val, r["min"], r["max"])
    dev = 0 if r["min"] <= back_val <= r["max"] else (
        r["min"] - back_val if back_val < r["min"] else back_val - r["max"]
    )
    sev = _severity_from_deviation(dev, r["max"] - r["min"])
    if back_val < r["min"]:
        adj = "Raise handlebars or use a shorter/steeper stem"
    elif back_val > r["max"]:
        adj = "Lower handlebars or use a longer/more negative stem"
    else:
        adj = "Back angle is well positioned"
    recommendations.append(Recommendation(
        component="handlebar_position",
        severity=sev,
        current_value=f"{back_val:.1f}°",
        ideal_range=f"{r['min']}–{r['max']}°",
        adjustment=adj,
        explanation=(
            "Back angle affects aerodynamics and comfort. "
            "Too flat strains the neck and lower back; too upright increases drag."
        ),
    ))

    # --- Ankle Angle at 3 o'clock (Power Phase) ---
    r = ranges["ankle_angle"]
    ankle_at_3 = angles.ankle_angle_at_3
    ankle_score = _score_single(ankle_at_3, 85, 95)  # Tighter range at power phase
    dev = 0 if 85 <= ankle_at_3 <= 95 else (
        85 - ankle_at_3 if ankle_at_3 < 85 else ankle_at_3 - 95
    )
    sev = _severity_from_deviation(dev, 10)
    if ankle_at_3 < 85:
        adj = "Ankle too dorsiflexed at power phase — check cleat position (may be too far back)"
    elif ankle_at_3 > 95:
        adj = "Excessive toe pointing at power phase — check cleat position (may be too far forward)"
    else:
        adj = "Ankle position at power phase is ideal"
    recommendations.append(Recommendation(
        component="ankle_power_phase",
        severity=sev,
        current_value=f"{ankle_at_3:.1f}°",
        ideal_range="85–95°",
        adjustment=adj,
        explanation=(
            "At 3 o'clock (power phase), the ankle should be near neutral (90°). "
            "This is the most powerful foot posture for the down-stroke."
        ),
    ))

    # --- Foot-to-Ground at 12 o'clock (TDC) ---
    r_ft12 = ranges.get("foot_ground_at_12", {"min": 15, "max": 35})
    ft12 = angles.foot_ground_at_12
    dev = 0 if r_ft12["min"] <= ft12 <= r_ft12["max"] else (
        r_ft12["min"] - ft12 if ft12 < r_ft12["min"] else ft12 - r_ft12["max"]
    )
    sev = _severity_from_deviation(dev, r_ft12["max"] - r_ft12["min"])
    if ft12 < r_ft12["min"]:
        adj = (
            "Foot too flat at top of stroke — may indicate hip/knee restriction "
            "or could benefit from shorter cranks"
        )
    elif ft12 > r_ft12["max"]:
        adj = "Excessive toe-down at top of stroke — ankle stability may be compromised"
    else:
        adj = "Foot angle at top of pedal stroke is good"
    recommendations.append(Recommendation(
        component="foot_angle_tdc",
        severity=sev,
        current_value=f"{ft12:.1f}°",
        ideal_range=f"{r_ft12['min']}–{r_ft12['max']}°",
        adjustment=adj,
        explanation=(
            "At 12 o'clock, a moderate toe-down posture (15-35°) eases the foot "
            "through the top of the stroke. Too flat may indicate joint restrictions."
        ),
    ))

    # --- Foot-to-Ground at 3 o'clock ---
    r_ft3 = ranges.get("foot_ground_at_3", {"min": 0, "max": 12})
    ft3 = angles.foot_ground_at_3
    dev = 0 if r_ft3["min"] <= ft3 <= r_ft3["max"] else (
        r_ft3["min"] - ft3 if ft3 < r_ft3["min"] else ft3 - r_ft3["max"]
    )
    sev = _severity_from_deviation(dev, r_ft3["max"] - r_ft3["min"])
    if ft3 < r_ft3["min"]:
        adj = "Heel is too low at power phase — check cleat position"
    elif ft3 > r_ft3["max"]:
        adj = "Too much toe-down at power phase — check cleat position or ankle stability"
    else:
        adj = "Foot angle at power phase is well positioned"
    recommendations.append(Recommendation(
        component="foot_angle_power",
        severity=sev,
        current_value=f"{ft3:.1f}°",
        ideal_range=f"{r_ft3['min']}–{r_ft3['max']}°",
        adjustment=adj,
        explanation=(
            "At 3 o'clock, the foot should be nearly level (0-12° toe-down) "
            "for maximum power transfer through the pedal."
        ),
    ))

    # --- Foot-to-Ground at 6 o'clock (BDC) ---
    r_ft6 = ranges.get("foot_ground_at_6", {"min": 5, "max": 20})
    ft6 = angles.foot_ground_at_6
    dev = 0 if r_ft6["min"] <= ft6 <= r_ft6["max"] else (
        r_ft6["min"] - ft6 if ft6 < r_ft6["min"] else ft6 - r_ft6["max"]
    )
    sev = _severity_from_deviation(dev, r_ft6["max"] - r_ft6["min"])
    if ft6 < r_ft6["min"]:
        adj = "Foot too flat at bottom — may indicate low saddle or poor cleat position"
    elif ft6 > r_ft6["max"]:
        adj = "Too much toe-down at bottom — saddle may be too high or cleat too far forward"
    else:
        adj = "Foot angle at bottom of stroke is normal"
    recommendations.append(Recommendation(
        component="foot_angle_bdc",
        severity=sev,
        current_value=f"{ft6:.1f}°",
        ideal_range=f"{r_ft6['min']}–{r_ft6['max']}°",
        adjustment=adj,
        explanation=(
            "At 6 o'clock, a slight toe-down (5-20°) eases the foot through "
            "the bottom of the stroke for a smooth transition to recovery."
        ),
    ))

    # --- Ankle Coordination ---
    coord_range = angles.ankle_total_range
    if coord_range < 10:
        sev = Severity.MINOR
        adj = "Very little ankle movement — pedal stroke may lack dynamic coordination"
    elif coord_range > 30:
        sev = Severity.MINOR
        adj = "Excessive ankle movement — may indicate unstable foot/ankle mechanics"
    else:
        sev = Severity.OPTIMAL
        adj = "Ankle coordination through the pedal stroke is good"
    recommendations.append(Recommendation(
        component="ankle_coordination",
        severity=sev,
        current_value=f"{coord_range:.1f}°",
        ideal_range="10–30°",
        adjustment=adj,
        explanation=(
            "Total ankle range of motion indicates pedal stroke coordination. "
            "Too little suggests a rigid stroke; too much may indicate instability."
        ),
    ))

    # --- Elbow Angle ---
    r = ranges["elbow_angle"]
    elbow_val = angles.elbow_angle
    reach_score = _score_single(elbow_val, r["min"], r["max"])
    dev = 0 if r["min"] <= elbow_val <= r["max"] else (
        r["min"] - elbow_val if elbow_val < r["min"] else elbow_val - r["max"]
    )
    sev = _severity_from_deviation(dev, r["max"] - r["min"])
    if elbow_val < r["min"]:
        adj = "Stem may be too long — consider a shorter stem"
    elif elbow_val > r["max"]:
        adj = "Stem may be too short — consider a longer stem or more reach"
    else:
        adj = "Reach and elbow bend are comfortable"
    recommendations.append(Recommendation(
        component="stem_length",
        severity=sev,
        current_value=f"{elbow_val:.1f}°",
        ideal_range=f"{r['min']}–{r['max']}°",
        adjustment=adj,
        explanation=(
            "Elbow bend indicates reach. A slight bend absorbs road vibrations "
            "and prevents locking out, which causes numbness and fatigue."
        ),
    ))

    # --- Overall score (weighted) ---
    # Only use weights for the 5 components that are actually scored
    w_knee = ranges.get("knee_extension", {}).get("weight", 30)
    w_hip = ranges.get("hip_angle", {}).get("weight", 20)
    w_back = ranges.get("back_angle", {}).get("weight", 15)
    w_ankle = ranges.get("ankle_angle", {}).get("weight", 10)
    w_elbow = ranges.get("elbow_angle", {}).get("weight", 5)
    total_weight = w_knee + w_hip + w_back + w_ankle + w_elbow

    overall = (
        knee_score * w_knee
        + hip_score * w_hip
        + back_score * w_back
        + ankle_score * w_ankle
        + reach_score * w_elbow
    ) / total_weight

    fit_score = FitScore(
        overall=round(overall, 1),
        knee_score=round(knee_score, 1),
        hip_score=round(hip_score, 1),
        back_score=round(back_score, 1),
        ankle_score=round(ankle_score, 1),
        reach_score=round(reach_score, 1),
    )

    # Sort recommendations by severity (critical first)
    severity_order = {Severity.CRITICAL: 0, Severity.MODERATE: 1, Severity.MINOR: 2, Severity.OPTIMAL: 3}
    recommendations.sort(key=lambda r: severity_order.get(r.severity, 99))

    return fit_score, recommendations
