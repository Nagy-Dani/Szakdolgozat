"""Tests for analysis model."""
from __future__ import annotations

from models.analysis_model import FitScore


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
