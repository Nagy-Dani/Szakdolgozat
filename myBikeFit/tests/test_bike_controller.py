from __future__ import annotations

import pytest
from controllers.bike_controller import BikeController


class _DummyView:
    """Minimális mock view a controller példányosításához."""
    class _Signal:
        def connect(self, _): pass
    bike_data_submitted = _Signal()


@pytest.fixture
def controller():
    return BikeController(_DummyView())


def test_lemond_formula(controller):
    """A LeMond-képletnek inseam * 0.883 értéket kell visszaadnia."""
    result = controller.suggest_saddle_height(85.0)
    assert result == pytest.approx(85.0 * 0.883, abs=0.1)


def test_lemond_formula_zero_inseam(controller):
    """Nulla inseam esetén nulla magasságot ad vissza."""
    assert controller.suggest_saddle_height(0) == 0