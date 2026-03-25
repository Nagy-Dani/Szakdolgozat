"""Analysis results — cycling angles and fit scores."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class CyclingAngles:
    """Key angles measured during the pedal stroke."""

    knee_extension_min: float = 0.0   # At bottom dead centre (ideal ≈ 140-150°)
    knee_extension_max: float = 0.0   # At top dead centre
    knee_flexion_max: float = 0.0     # Maximum knee bend at TDC (ideal ≈ 65-75°)
    hip_angle_min: float = 0.0        # Torso–thigh angle at TDC (ideal ≈ 40-55° road)
    hip_angle_max: float = 0.0        # Torso–thigh angle at BDC
    back_angle: float = 0.0           # Torso relative to horizontal (ideal ≈ 35-45° road)
    ankle_angle_min: float = 0.0      # Minimum ankle through stroke
    ankle_angle_max: float = 0.0      # Maximum ankle through stroke
    ankle_angle_at_3: float = 0.0     # Ankle at 3 o'clock (power phase, ideal 85-95°)
    foot_ground_at_12: float = 0.0    # Foot-to-ground at TDC (ideal 15-35°)
    foot_ground_at_3: float = 0.0     # Foot-to-ground at 3 o'clock (ideal 0-12°)
    foot_ground_at_6: float = 0.0     # Foot-to-ground at BDC (ideal 5-20°)
    ankle_total_range: float = 0.0    # Max-min ankle angle (coordination indicator)
    shoulder_angle: float = 0.0       # Upper arm to torso
    elbow_angle: float = 0.0          # Elbow bend (ideal ≈ 150-165°)
    
    # Front / Back metrics
    knee_tracking_left: float = 0.0   # Lateral deviation of left knee
    knee_tracking_right: float = 0.0  # Lateral deviation of right knee
    hip_sway: float = 0.0             # Lateral hip sway from center

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CyclingAngles:
        # Filter to only known fields to handle schema evolution
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class FitScore:
    """Overall and per-area fit scores (0–100)."""

    overall: float = 0.0
    knee_score: float = 0.0
    hip_score: float = 0.0
    back_score: float = 0.0
    ankle_score: float = 0.0
    reach_score: float = 0.0
    geometry_score: float = 0.0
    stability_score: float = 0.0

    @property
    def category(self) -> str:
        if self.overall >= 90:
            return "excellent"
        if self.overall >= 75:
            return "good"
        if self.overall >= 55:
            return "fair"
        return "poor"

    @property
    def category_color(self) -> str:
        return {
            "excellent": "#22c55e",
            "good": "#84cc16",
            "fair": "#eab308",
            "poor": "#ef4444",
        }.get(self.category, "#888888")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["category"] = self.category
        return d

    @classmethod
    def from_dict(cls, data: dict) -> FitScore:
        data = dict(data)
        data.pop("category", None)  # computed property, not a constructor arg
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})
