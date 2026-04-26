from __future__ import annotations

from models.analysis_model import FitScore, CyclingAngles


def test_fit_score_categories():
    assert FitScore(overall=95).category == "excellent"
    assert FitScore(overall=80).category == "good"
    assert FitScore(overall=60).category == "fair"
    assert FitScore(overall=30).category == "poor"


def test_fit_score_serialization():
    score = FitScore(overall=85, knee_score=90, hip_score=80,
                     back_score=85, ankle_score=88, reach_score=75)
    d = score.to_dict()
    assert d["category"] == "good"
    assert d["overall"] == 85
    
def test_fit_score_clamping():
    """A FitScore overall értéke negatív vagy 100 feletti is lehet bemenet, de a
    category property korrekt kategóriát ad."""
    assert FitScore(overall=120).category == "excellent"
    assert FitScore(overall=-10).category == "poor"


def test_fit_score_category_color_present():
    """Minden kategóriához tartozzon érvényes hex színkód."""
    for value in [95, 80, 60, 30]:
        score = FitScore(overall=value)
        assert score.category_color.startswith("#")


def test_cycling_angles_default_is_zero():
    """Új CyclingAngles() minden mezője default 0."""
    a = CyclingAngles()
    assert a.knee_extension_min == 0
    assert a.shoulder_angle == 0
