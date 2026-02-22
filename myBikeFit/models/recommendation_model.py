"""Recommendation model — actionable bike-fit adjustments."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum


class Severity(Enum):
    OPTIMAL = "optimal"
    MINOR = "minor"
    MODERATE = "moderate"
    CRITICAL = "critical"

    @property
    def color(self) -> str:
        return {
            "optimal": "#22c55e",
            "minor": "#84cc16",
            "moderate": "#eab308",
            "critical": "#ef4444",
        }[self.value]

    @property
    def icon(self) -> str:
        return {
            "optimal": "✅",
            "minor": "🟡",
            "moderate": "🟠",
            "critical": "🔴",
        }[self.value]


@dataclass
class Recommendation:
    """A single bike-fit adjustment recommendation."""

    component: str          # e.g. "saddle_height", "saddle_setback", "stem"
    severity: Severity
    current_value: str      # Human-readable current measurement / angle
    ideal_range: str        # Human-readable ideal range
    adjustment: str         # e.g. "Raise saddle by 8-12 mm"
    explanation: str        # Why this matters for comfort / performance / injury

    @property
    def display_name(self) -> str:
        return self.component.replace("_", " ").title()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Recommendation:
        data = dict(data)
        data["severity"] = Severity(data["severity"])
        return cls(**data)
