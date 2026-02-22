"""Bike controller — validates bike geometry input."""

from __future__ import annotations

from models.bike_model import BikeGeometry


class BikeController:
    """Connects BikeInputView signals to the BikeGeometry model."""

    def __init__(self, view, model: BikeGeometry | None = None):
        self._view = view
        self._model = model or BikeGeometry()
        self._view.bike_data_submitted.connect(self._on_data_submitted)

    @property
    def model(self) -> BikeGeometry:
        return self._model

    def _on_data_submitted(self, data: dict) -> None:
        if not data:
            # User skipped — keep defaults
            if self._on_valid_callback:
                self._on_valid_callback(self._model)
            return

        try:
            self._model = BikeGeometry(**data)
        except (ValueError, TypeError) as e:
            self._view.show_errors([str(e)])
            return

        errors = self._model.validate()
        if errors:
            self._view.show_errors(errors)
            return

        if self._on_valid_callback:
            self._on_valid_callback(self._model)

    _on_valid_callback = None

    def set_on_valid(self, callback) -> None:
        self._on_valid_callback = callback

    def load(self, model: BikeGeometry) -> None:
        self._model = model
        self._view.set_data(model.to_dict())

    def suggest_saddle_height(self, inseam_cm: float) -> float:
        """Auto-suggest saddle height using LeMond formula."""
        return round(inseam_cm * 0.883, 1)
