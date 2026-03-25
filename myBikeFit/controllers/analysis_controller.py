"""Analysis controller — orchestrates angle calculation and recommendations."""

from __future__ import annotations

from models.pose_model import PoseSequence
from models.rider_model import RiderMeasurements
from models.bike_model import BikeGeometry
from models.analysis_model import CyclingAngles, FitScore
from models.recommendation_model import Recommendation
from services.angle_calculator import compute_angles_for_view, aggregate_angles
from services.fit_rules_engine import evaluate_fit


class AnalysisController:
    """Takes pose data + rider/bike info and produces fit results."""

    def __init__(self, results_view):
        self._view = results_view
        self._angles: CyclingAngles | None = None
        self._fit_score: FitScore | None = None
        self._recommendations: list[Recommendation] = []

    @property
    def angles(self) -> CyclingAngles | None:
        return self._angles

    @property
    def fit_score(self) -> FitScore | None:
        return self._fit_score

    @property
    def recommendations(self) -> list[Recommendation]:
        return self._recommendations

    def analyze(
        self,
        sequences: dict[str, PoseSequence],
        rider: RiderMeasurements,
        bike: BikeGeometry | None = None,
        side: str = "left",
    ) -> None:
        """Run the full analysis pipeline and push results to the view."""

        # 1. Compute per-frame angles for each view
        view_frames: dict[str, list[dict[str, float]]] = {
            "side": [], "front": [], "back": []
        }
        
        for view_type, sequence in sequences.items():
            if not sequence:
                continue
            
            # For side view, use the specified facing side. For front/back, use the view_type.
            validation_side = side if view_type == "side" else view_type
                
            for pose_frame in sequence.get_valid_frames(validation_side):
                angles = compute_angles_for_view(pose_frame, view_type=view_type, side=side)
                if angles:
                    view_frames[view_type].append(angles)

        if not view_frames["side"]:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self._view, "Analysis Failed",
                "Could not compute angles — ensure the video shows a clear side view "
                "with your full body visible while pedaling."
            )
            return

        # 2. Aggregate across pedal stroke and views
        self._angles = aggregate_angles(
            side_frames=view_frames["side"],
            front_frames=view_frames["front"] if view_frames["front"] else None,
            back_frames=view_frames["back"] if view_frames["back"] else None,
        )

        # 3. Generate fit score and recommendations
        self._fit_score, self._recommendations = evaluate_fit(
            self._angles,
            rider=rider,
            bike=bike,
        )

        # 4. Push to results view
        self._view.set_scores(self._fit_score)
        self._view.set_recommendations(self._recommendations)

        if self._on_complete_callback:
            self._on_complete_callback(self._fit_score, self._recommendations)

    _on_complete_callback = None

    def set_on_complete(self, callback) -> None:
        self._on_complete_callback = callback
