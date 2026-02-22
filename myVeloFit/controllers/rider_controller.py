"""Rider controller — validates rider input and manages rider model."""

from __future__ import annotations

from models.rider_model import RiderMeasurements, Flexibility, RidingStyle


class RiderController:
    """Connects RiderInputView signals to the RiderMeasurements model."""

    def __init__(self, view, model: RiderMeasurements | None = None):
        self._view = view
        self._model = model or RiderMeasurements()
        self._view.rider_data_submitted.connect(self._on_data_submitted)

    @property
    def model(self) -> RiderMeasurements:
        return self._model

    def _on_data_submitted(self, data: dict) -> None:
        """Validate and update the model from the view's form data."""
        try:
            self._model = RiderMeasurements(
                height_cm=data["height_cm"],
                weight_kg=data["weight_kg"],
                inseam_cm=data["inseam_cm"],
                foot_size_eu=data["foot_size_eu"],
                arm_length_cm=data["arm_length_cm"],
                torso_length_cm=data["torso_length_cm"],
                shoulder_width_cm=data["shoulder_width_cm"],
                flexibility=Flexibility(data.get("flexibility", "medium")),
                riding_style=RidingStyle(data.get("riding_style", "road")),
                name=data.get("name"),
            )
        except (ValueError, KeyError) as e:
            self._view.show_errors([str(e)])
            return

        errors = self._model.validate()
        if errors:
            self._view.show_errors(errors)
            return

        # Valid — notify the app controller to move to the next page
        if self._on_valid_callback:
            self._on_valid_callback(self._model)

    _on_valid_callback = None

    def set_on_valid(self, callback) -> None:
        """Register a callback for when valid rider data is submitted."""
        self._on_valid_callback = callback

    def load(self, model: RiderMeasurements) -> None:
        """Load an existing model into the view."""
        self._model = model
        self._view.set_data(model.to_dict())
