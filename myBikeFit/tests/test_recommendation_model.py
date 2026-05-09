from __future__ import annotations

import pytest
from models.recommendation_model import Recommendation, Severity


def test_severity_enum_values():
    assert Severity.OPTIMAL.value == "optimal"
    assert Severity.MINOR.value == "minor"
    assert Severity.MODERATE.value == "moderate"
    assert Severity.CRITICAL.value == "critical"


def test_recommendation_construction():
    rec = Recommendation(
        component="saddle_height", severity=Severity.MINOR,
        current_value="142.3°", ideal_range="135–150°",
        adjustment="Raise saddle by 3 mm",
        explanation="Knee extension is slightly low.",
    )
    assert rec.component == "saddle_height"
    assert rec.severity == Severity.MINOR


def test_recommendation_serialization_roundtrip():
    rec = Recommendation(
        component="back_angle", severity=Severity.CRITICAL,
        current_value="65°", ideal_range="35–45°",
        adjustment="Raise handlebars",
        explanation="Back is too low.",
    )
    d = rec.to_dict()
    restored = Recommendation.from_dict(d)
    assert restored.component == rec.component
    assert restored.severity == Severity.CRITICAL
    assert restored.adjustment == rec.adjustment


def test_severity_color_mapping():
    """Minden súlyossági szinthez tartozzon szín."""
    for sev in [Severity.OPTIMAL, Severity.MINOR, Severity.MODERATE, Severity.CRITICAL]:
        assert sev.color.startswith("#")
        assert len(sev.color) == 7