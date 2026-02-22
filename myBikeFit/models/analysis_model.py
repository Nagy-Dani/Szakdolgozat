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
    shoulder_angle: float = 0.0       # Upper arm to torso
    elbow_angle: float = 0.0          # Elbow bend (ideal ≈ 150-165°)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FitScore:
    """Overall and per-area fit scores (0–100)."""

    overall: float = 0.0
    knee_score: float = 0.0
    hip_score: float = 0.0
    back_score: float = 0.0
    ankle_score: float = 0.0
    reach_score: float = 0.0

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
