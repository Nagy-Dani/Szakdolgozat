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
    knee_val = angles.knee_extension_min  # BDC = minimum knee flexion = maximum extension
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

    # --- Ankle Angle ---
    r = ranges["ankle_angle"]
    ankle_val = (angles.ankle_angle_min + angles.ankle_angle_max) / 2
    ankle_score = _score_single(ankle_val, r["min"], r["max"])
    dev = 0 if r["min"] <= ankle_val <= r["max"] else (
        r["min"] - ankle_val if ankle_val < r["min"] else ankle_val - r["max"]
    )
    sev = _severity_from_deviation(dev, r["max"] - r["min"])
    if ankle_val < r["min"]:
        adj = "Reduce toe pointing — check cleat position and saddle height"
    elif ankle_val > r["max"]:
        adj = "Check cleat position — foot may be too far forward on pedal"
    else:
        adj = "Ankle movement is within normal range"
    recommendations.append(Recommendation(
        component="cleat_position",
        severity=sev,
        current_value=f"{ankle_val:.1f}°",
        ideal_range=f"{r['min']}–{r['max']}°",
        adjustment=adj,
        explanation=(
            "Ankle angle through the pedal stroke reveals cleat positioning and "
            "ankling technique. Excessive toe pointing wastes energy."
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
    weights = {k: v["weight"] for k, v in ranges.items()}
    total_weight = sum(weights.values())
    overall = (
        knee_score * weights.get("knee_extension", 30)
        + hip_score * weights.get("hip_angle", 20)
        + back_score * weights.get("back_angle", 15)
        + ankle_score * weights.get("ankle_angle", 10)
        + reach_score * weights.get("elbow_angle", 5)
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
