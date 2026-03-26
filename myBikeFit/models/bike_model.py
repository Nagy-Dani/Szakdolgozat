"""Bike geometry model."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class BikeGeometry:
    """Core bike geometry measurements for fit analysis."""

    frame_size_cm: float = 0.0        # Seat tube length (center-to-top)
    saddle_height_cm: float = 0.0     # Center of BB to top of saddle
    saddle_setback_cm: float = 0.0    # Horizontal offset behind BB center
    handlebar_reach_cm: float = 0.0   # Saddle nose to handlebar center
    handlebar_drop_cm: float = 0.0    # Vertical drop saddle → handlebar (+ = drop)
    crank_length_mm: float = 172.5    # Crank arm length
    stem_length_mm: float = 100.0     # Stem length
    stem_angle_deg: float = -6.0      # Stem angle (negative = drop)

    # ---------- validation ----------

    _RANGES = {
        "frame_size_cm": (40.0, 70.0),
        "saddle_height_cm": (55.0, 90.0),
        "saddle_setback_cm": (-5.0, 15.0),
        "handlebar_reach_cm": (30.0, 70.0),
        "handlebar_drop_cm": (-5.0, 20.0),
        "crank_length_mm": (140.0, 185.0),
        "stem_length_mm": (50.0, 150.0),
        "stem_angle_deg": (-20.0, 20.0),
    }

    def validate(self) -> list[str]:
        errors: list[str] = []
        for fname, (lo, hi) in self._RANGES.items():
            val = getattr(self, fname)
            if val != 0.0 and not (lo <= val <= hi):
                errors.append(
                    f"{fname}: {val} outside valid range [{lo}, {hi}]"
                )
        return errors

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ---------- serialization ----------

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> BikeGeometry:
        return cls(**data)
