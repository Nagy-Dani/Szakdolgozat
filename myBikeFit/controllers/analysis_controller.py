"""Analysis controller — orchestrates angle calculation and recommendations."""

from __future__ import annotations

from models.pose_model import PoseSequence
from models.rider_model import RiderMeasurements
from models.bike_model import BikeGeometry
from models.analysis_model import CyclingAngles, FitScore
from models.recommendation_model import Recommendation
from services.angle_calculator import compute_frame_angles, aggregate_angles
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
        sequence: PoseSequence,
        rider: RiderMeasurements,
        bike: BikeGeometry | None = None,
        side: str = "left",
        video_path: str = ""
    ) -> None:
        """Run the full analysis pipeline and push results to the view."""

        frame_angles: list[dict[str, float]] = []
        for pose_frame in sequence.get_valid_frames(side):
            angles = compute_frame_angles(pose_frame, side=side)
            if angles:
                frame_angles.append(angles)

        if not frame_angles:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self._view, "Analysis Failed",
                "Could not compute angles — ensure the video shows a clear side view "
                "with your full body visible while pedaling."
            )
            return

        self._angles = aggregate_angles(frame_angles)

        if video_path:
            import os
            from services.com_calculator import generate_com_overlay
            output_dir = "sessions"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "com_overlay.jpg")
            com_data = generate_com_overlay(sequence, video_path, side, output_path)
            if com_data:
                self._angles.com_bb_offset = com_data.get("offset_percent", 0.0)
                self._angles.com_image_path = com_data.get("image_path", "")

        self._fit_score, self._recommendations = evaluate_fit(
            self._angles,
            rider=rider,
            bike=bike,
        )

        self._view.set_scores(self._fit_score)
        self._view.set_recommendations(self._recommendations)

        if self._on_complete_callback:
            self._on_complete_callback(self._fit_score, self._recommendations)

    _on_complete_callback = None

    def set_on_complete(self, callback) -> None:
        self._on_complete_callback = callback
