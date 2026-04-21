"""Rule-based fit recommendation engine."""

from __future__ import annotations

import json
from pathlib import Path

from models.analysis_model import CyclingAngles, FitScore
from models.recommendation_model import Recommendation, Severity
from models.rider_model import RiderMeasurements, Flexibility
from models.bike_model import BikeGeometry


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


_FLEXIBILITY_OFFSETS: dict[Flexibility, dict[str, int]] = {
    Flexibility.LOW:    {"hip_angle": +6, "back_angle": +6, "knee_flexion_max": +4},
    Flexibility.MEDIUM: {"hip_angle":  0, "back_angle":  0, "knee_flexion_max":  0},
    Flexibility.HIGH:   {"hip_angle": -6, "back_angle": -6, "knee_flexion_max": -4},
}


def _apply_flexibility_offsets(ranges: dict, flexibility: Flexibility) -> dict:
    """Shift ideal windows for flexibility-sensitive angles without mutating the original."""
    offsets = _FLEXIBILITY_OFFSETS.get(flexibility, {})
    if not offsets:
        return ranges
    result = {k: dict(v) for k, v in ranges.items()}
    for angle, delta in offsets.items():
        if angle in result:
            result[angle]["min"] += delta
            result[angle]["max"] += delta
    return result


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

def evaluate_fit(
    angles: CyclingAngles,
    rider: RiderMeasurements,
    bike: BikeGeometry,
) -> tuple[FitScore, list[Recommendation]]:
    """Evaluate cycling angles and geometric measurements against ideal ranges.
    Returns (FitScore, list[Recommendation]).
    """
    all_ranges = _load_ranges()
    riding_style = rider.riding_style.value if rider else "road"
    ranges = all_ranges.get(riding_style, all_ranges["road"])
    if rider:
        ranges = _apply_flexibility_offsets(ranges, rider.flexibility)

    recommendations: list[Recommendation] = []

    r = ranges["knee_extension"]
    knee_val = angles.knee_extension_max
    knee_score = _score_single(knee_val, r["min"], r["max"])
    dev = 0 if r["min"] <= knee_val <= r["max"] else (
        r["min"] - knee_val if knee_val < r["min"] else knee_val - r["max"]
    )
    sev = _severity_from_deviation(dev, r["max"] - r["min"])
    adj = ""
    if knee_val < r["min"]:
        mm = round(dev * 1.5, 0)
        adj = f"Raise saddle by approximately {mm:.0f} mm"
    elif knee_val > r["max"]:
        mm = round(dev * 1.5, 0)
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

    r = ranges["hip_angle"]
    hip_val = angles.hip_angle_min
    hip_score = _score_single(hip_val, r["min"], r["max"])
    dev = 0 if r["min"] <= hip_val <= r["max"] else (
        r["min"] - hip_val if hip_val < r["min"] else hip_val - r["max"]
    )
    sev = _severity_from_deviation(dev, r["max"] - r["min"])
    if hip_val < r["min"]:
        adj = f"Move saddle forward or raise handlebars to open hip angle"
    elif hip_val > r["max"]:
        adj = f"Move saddle backward or lower handlebars to close hip angle"
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

    r_ank = ranges.get("ankle_angle_at_3", {"min": 100, "max": 120})
    ankle_at_3 = angles.ankle_angle_at_3
    ankle_score = _score_single(ankle_at_3, r_ank["min"], r_ank["max"])
    dev = 0 if r_ank["min"] <= ankle_at_3 <= r_ank["max"] else (
        r_ank["min"] - ankle_at_3 if ankle_at_3 < r_ank["min"] else ankle_at_3 - r_ank["max"]
    )
    sev = _severity_from_deviation(dev, r_ank["max"] - r_ank["min"])
    if ankle_at_3 < r_ank["min"]:
        adj = "Ankle too dorsiflexed at power phase — check cleat position (may be too far back)"
    elif ankle_at_3 > r_ank["max"]:
        adj = "Excessive toe pointing at power phase — check cleat position (may be too far forward)"
    else:
        adj = "Ankle position at power phase is ideal"
    recommendations.append(Recommendation(
        component="ankle_power_phase",
        severity=sev,
        current_value=f"{ankle_at_3:.1f}°",
        ideal_range=f"{r_ank['min']}–{r_ank['max']}°",
        adjustment=adj,
        explanation=(
            "At 3 o'clock (power phase), the ankle should be slightly pointed down. "
            "This is the most powerful foot posture for the down-stroke."
        ),
    ))

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
            "At 12 o'clock, a moderate toe-down posture (15-35) eases the foot "
            "through the top of the stroke. Too flat may indicate joint restrictions."
        ),
    ))

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
    
    has_measurements = (
        rider and bike and
        rider.inseam_cm > 0 and
        bike.saddle_height_cm > 0
    )

    if has_measurements:
        geom_scores: list[float] = []

        ideal_saddle = rider.inseam_cm * 0.883
        actual_saddle = bike.saddle_height_cm
        diff = abs(actual_saddle - ideal_saddle)
        geom_scores.append(_score_single(actual_saddle, ideal_saddle - 1.0, ideal_saddle + 1.0))
        
        if diff <= 1.0:
            sev, adj = Severity.OPTIMAL, "Saddle height perfectly matches your inseam"
        elif diff <= 2.5:
            sev, adj = Severity.MINOR, (
                f"Saddle is slightly {'high' if actual_saddle > ideal_saddle else 'low'} "
                f"for your inseam (ideal ≈ {ideal_saddle:.1f} cm)"
            )
        else:
            sev, adj = Severity.MODERATE, (
                f"Saddle is significantly {'high' if actual_saddle > ideal_saddle else 'low'} "
                f"for your inseam (ideal ≈ {ideal_saddle:.1f} cm)"
            )
        recommendations.append(Recommendation(
            component="saddle_height_geometric",
            severity=sev,
            current_value=f"{actual_saddle:.1f} cm",
            ideal_range=f"{ideal_saddle - 1.0:.1f}–{ideal_saddle + 1.0:.1f} cm",
            adjustment=adj,
            explanation=(
                "Based on the LeMond formula, ideal saddle height is 88.3% of your inseam. "
                "This serves as a starting point before fine-tuning via knee angle."
            ),
        ))

        if bike.frame_size_cm > 0:
            mult = 0.574 if riding_style == "mtb" else 0.66
            ideal_frame = rider.inseam_cm * mult
            actual_frame = bike.frame_size_cm
            f_diff = abs(actual_frame - ideal_frame)
            geom_scores.append(_score_single(actual_frame, ideal_frame - 2.0, ideal_frame + 2.0))
            
            if f_diff <= 2.0:
                sev, adj = Severity.OPTIMAL, "Frame size is ideal for your leg length"
            elif f_diff <= 4.0:
                sev, adj = Severity.MINOR, (
                    f"Frame is slightly {'large' if actual_frame > ideal_frame else 'small'} "
                    f"for your leg length (ideal ≈ {ideal_frame:.1f} cm)"
                )
            else:
                sev, adj = Severity.MODERATE, (
                    f"Frame is significantly {'large' if actual_frame > ideal_frame else 'small'} "
                    f"for your leg length (ideal ≈ {ideal_frame:.1f} cm)"
                )
            recommendations.append(Recommendation(
                component="frame_size",
                severity=sev,
                current_value=f"{actual_frame:.1f} cm",
                ideal_range=f"{ideal_frame - 2.0:.1f}–{ideal_frame + 2.0:.1f} cm",
                adjustment=adj,
                explanation="Frame size dictates standover height and overall bike proportion relative to your legs.",
            ))

        if bike.crank_length_mm > 0:
            ideal_crank = (rider.inseam_cm * 1.25) + 65.0
            actual_crank = bike.crank_length_mm
            c_diff = abs(actual_crank - ideal_crank)
            geom_scores.append(_score_single(actual_crank, ideal_crank - 2.5, ideal_crank + 2.5))
            
            if c_diff <= 2.5:
                sev, adj = Severity.OPTIMAL, "Crank length perfectly matches your leg proportions"
            elif c_diff <= 5.0:
                sev, adj = Severity.MINOR, (
                    f"Cranks are slightly {'long' if actual_crank > ideal_crank else 'short'} "
                    f"(ideal ≈ {ideal_crank:.1f} mm)"
                )
            else:
                sev, adj = Severity.MODERATE, (
                    f"Cranks are significantly {'long' if actual_crank > ideal_crank else 'short'} "
                    f"(ideal ≈ {ideal_crank:.1f} mm)"
                )
            recommendations.append(Recommendation(
                component="crank_length",
                severity=sev,
                current_value=f"{actual_crank:.1f} mm",
                ideal_range=f"{ideal_crank - 2.5:.1f}–{ideal_crank + 2.5:.1f} mm",
                adjustment=adj,
                explanation="Proper crank length prevents excessive knee flexion at the top of the pedal stroke.",
            ))

        if bike.handlebar_reach_cm > 0 and bike.frame_size_cm > 0:
            ideal_reach = (365.0 + (0.85 * bike.frame_size_cm)) / 10.0
            actual_reach = bike.handlebar_reach_cm
            r_diff = abs(actual_reach - ideal_reach)
            geom_scores.append(_score_single(actual_reach, ideal_reach - 2.0, ideal_reach + 2.0))
            
            if r_diff <= 2.0:
                sev, adj = Severity.OPTIMAL, "Reach matches your frame size perfectly"
            elif r_diff <= 4.0:
                sev, adj = Severity.MINOR, (
                    f"Reach is slightly {'long' if actual_reach > ideal_reach else 'short'} "
                    f"(ideal ≈ {ideal_reach:.1f} cm)"
                )
            else:
                sev, adj = Severity.MODERATE, (
                    f"Reach is significantly {'long' if actual_reach > ideal_reach else 'short'} "
                    f"(ideal ≈ {ideal_reach:.1f} cm)"
                )
            recommendations.append(Recommendation(
                component="overall_reach",
                severity=sev,
                current_value=f"{actual_reach:.1f} cm",
                ideal_range=f"{ideal_reach - 2.0:.1f}–{ideal_reach + 2.0:.1f} cm",
                adjustment=adj,
                explanation="Ideal reach balances your extension based on the frame size to prevent back/neck strain.",
            ))

    geometry_score = 0.0
    w_geom = 0

    if has_measurements and 'geom_scores' in locals() and geom_scores:
        geometry_score = sum(geom_scores) / len(geom_scores)
        w_geom = ranges.get("geometry", {}).get("weight", 20)
        
    w_knee = ranges.get("knee_extension", {}).get("weight", 30)
    w_hip = ranges.get("hip_angle", {}).get("weight", 20)
    w_back = ranges.get("back_angle", {}).get("weight", 15)
    w_ankle = ranges.get("ankle_angle", {}).get("weight", 10)
    w_elbow = ranges.get("elbow_angle", {}).get("weight", 5)
    total_weight = w_knee + w_hip + w_back + w_ankle + w_elbow + w_geom

    overall = (
        knee_score * w_knee
        + hip_score * w_hip
        + back_score * w_back
        + ankle_score * w_ankle
        + reach_score * w_elbow
        + geometry_score * w_geom
    ) / total_weight

    fit_score = FitScore(
        overall=round(overall, 1),
        knee_score=round(knee_score, 1),
        hip_score=round(hip_score, 1),
        back_score=round(back_score, 1),
        ankle_score=round(ankle_score, 1),
        reach_score=round(reach_score, 1),
        geometry_score=round(geometry_score, 1),
    )

    severity_order = {Severity.CRITICAL: 0, Severity.MODERATE: 1, Severity.MINOR: 2, Severity.OPTIMAL: 3}
    recommendations.sort(key=lambda r: severity_order.get(r.severity, 99))

    return fit_score, recommendations
