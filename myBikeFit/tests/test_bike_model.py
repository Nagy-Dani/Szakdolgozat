from __future__ import annotations

import pytest
from models.bike_model import BikeGeometry


def test_default_values():
    """Default crank length is 172.5 mm, stem 100 mm, stem angle -6°."""
    bike = BikeGeometry()
    assert bike.crank_length_mm == 172.5
    assert bike.stem_length_mm == 100
    assert bike.stem_angle_deg == -6


def test_custom_values():
    bike = BikeGeometry(
        frame_size_cm=56.0, saddle_height_cm=75.0, saddle_setback_cm=5.0,
        handlebar_reach_cm=45.0, handlebar_drop_cm=8.0,
        crank_length_mm=175.0,
    )
    assert bike.frame_size_cm == 56.0
    assert bike.crank_length_mm == 175.0


def test_serialization_roundtrip():
    bike = BikeGeometry(frame_size_cm=58.0, saddle_height_cm=76.5)
    d = bike.to_dict()
    restored = BikeGeometry.from_dict(d)
    assert restored.frame_size_cm == 58.0
    assert restored.saddle_height_cm == 76.5


def test_empty_geometry_roundtrip():
    """Default BikeGeometry should also round-trip cleanly."""
    bike = BikeGeometry()
    d = bike.to_dict()
    restored = BikeGeometry.from_dict(d)
    assert restored.crank_length_mm == 172.5


def test_partial_dict_loads_with_defaults():
    """Hiányos szótárból betöltve a hiányzó mezők default értékkel jelenjenek meg."""
    d = {"frame_size_cm": 54.0}
    bike = BikeGeometry.from_dict(d)
    assert bike.frame_size_cm == 54.0
    assert bike.crank_length_mm == 172.5