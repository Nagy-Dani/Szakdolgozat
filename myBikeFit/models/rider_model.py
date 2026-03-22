"""Rider body measurements model."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Flexibility(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RidingStyle(Enum):
    ROAD = "road"
    TT = "tt"
    MTB = "mtb"
    GRAVEL = "gravel"
    COMMUTE = "commute"


@dataclass
class RiderMeasurements:
    """All body measurements needed for bike-fit analysis."""

    height_cm: float = 0.0
    weight_kg: float = 0.0
    inseam_cm: float = 0.0
    foot_size_eu: float = 0.0
    arm_length_cm: float = 0.0
    torso_length_cm: float = 0.0
    shoulder_width_cm: float = 0.0
    flexibility: Flexibility = Flexibility.MEDIUM
    riding_style: RidingStyle = RidingStyle.ROAD
    name: Optional[str] = None

    # ---------- validation ----------

    _RANGES: dict = field(default_factory=lambda: {
        "height_cm": (100.0, 250.0),
        "weight_kg": (30.0, 200.0),
        "inseam_cm": (50.0, 120.0),
        "foot_size_eu": (30.0, 55.0),
        "arm_length_cm": (40.0, 90.0),
        "torso_length_cm": (30.0, 80.0),
        "shoulder_width_cm": (25.0, 60.0),
    }, repr=False)

    def validate(self) -> list[str]:
        """Return a list of validation error messages (empty = valid)."""
        errors: list[str] = []
        for field_name, (lo, hi) in self._RANGES.items():
            value = getattr(self, field_name)
            if not (lo <= value <= hi):
                errors.append(
                    f"{field_name}: {value} is outside the valid range [{lo}, {hi}]"
                )
        return errors

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ---------- derived helpers ----------

    @property
    def estimated_saddle_height(self) -> float:
        """Quick LeMond formula: saddle height ≈ inseam × 0.883."""
        return round(self.inseam_cm * 0.883, 1)

    # ---------- serialization ----------

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("_RANGES", None)
        d["flexibility"] = self.flexibility.value
        d["riding_style"] = self.riding_style.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> RiderMeasurements:
        data = dict(data)  # copy
        data.pop("_RANGES", None)
        data["flexibility"] = Flexibility(data.get("flexibility", "medium"))
        data["riding_style"] = RidingStyle(data.get("riding_style", "road"))
        return cls(**data)
