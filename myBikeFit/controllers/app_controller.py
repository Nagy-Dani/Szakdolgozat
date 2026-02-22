"""App controller — top-level orchestrator for the entire application."""

from __future__ import annotations

import json

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from views.main_window import MainWindow
from models.rider_model import RiderMeasurements
from models.bike_model import BikeGeometry
from models.pose_model import PoseSequence
from controllers.rider_controller import RiderController
from controllers.bike_controller import BikeController
from controllers.video_controller import VideoController
from controllers.pose_controller import PoseController
from controllers.analysis_controller import AnalysisController
from services.persistence_service import save_session, load_session


class AppController:
    """Creates all sub-controllers, connects the navigation flow."""

    # Page indices
    PAGE_RIDER = 0
    PAGE_BIKE = 1
    PAGE_VIDEO = 2
    PAGE_ANALYSIS = 3
    PAGE_RESULTS = 4

    def __init__(self, window: MainWindow):
        self._window = window

        # Models
        self._rider = RiderMeasurements()
        self._bike = BikeGeometry()
        self._pose_sequence: PoseSequence | None = None

        # Sub-controllers
        self._rider_ctrl = RiderController(window.rider_view, self._rider)
        self._bike_ctrl = BikeController(window.bike_view, self._bike)
        self._video_ctrl = VideoController(window.video_view)
        self._pose_ctrl = PoseController(window.analysis_view)
        self._analysis_ctrl = AnalysisController(window.results_view)

        # Wire navigation
        self._rider_ctrl.set_on_valid(self._on_rider_valid)
        self._bike_ctrl.set_on_valid(self._on_bike_valid)
        self._video_ctrl.set_on_valid(self._on_video_valid)
        self._pose_ctrl.set_on_complete(self._on_pose_complete)
        self._analysis_ctrl.set_on_complete(self._on_analysis_complete)

        # Menu actions
        window.new_session_requested.connect(self._new_session)
        window.save_session_requested.connect(self._save)
        window.load_session_requested.connect(self._load)
        window.export_pdf_requested.connect(self._export_pdf)
        window.results_view.restart_requested.connect(self._new_session)
        window.results_view.export_requested.connect(self._export_pdf)

        # Load angle ranges for analysis view based on riding style
        self._update_analysis_ranges()

    # ------------------------------------------------------------------ Flow

    def _on_rider_valid(self, rider: RiderMeasurements) -> None:
        self._rider = rider
        self._window.set_status(
            f"Rider: {rider.name or 'unnamed'} — "
            f"estimated saddle height: {rider.estimated_saddle_height} cm"
        )
        self._update_analysis_ranges()
        self._window.navigate_to(self.PAGE_BIKE)

    def _on_bike_valid(self, bike: BikeGeometry) -> None:
        self._bike = bike
        self._window.set_status("Bike geometry saved")
        self._window.navigate_to(self.PAGE_VIDEO)

    def _on_video_valid(self, path: str, info) -> None:
        self._window.set_status(
            f"Video loaded: {info.width}×{info.height}, "
            f"{info.fps:.0f} fps, {info.duration_sec:.1f}s"
        )
        self._window.navigate_to(self.PAGE_ANALYSIS)
        # Start pose detection
        self._pose_ctrl.start_analysis(path)

    def _on_pose_complete(self, sequence: PoseSequence) -> None:
        self._pose_sequence = sequence
        self._window.set_status(
            f"Pose detection complete — {len(sequence.valid_frames)} valid frames"
        )
        # Run analysis
        self._analysis_ctrl.analyze(sequence, self._rider, self._bike)

    def _on_analysis_complete(self, fit_score, recommendations) -> None:
        self._window.set_status(
            f"Analysis complete — overall score: {fit_score.overall:.0f} ({fit_score.category})"
        )
        self._window.navigate_to(self.PAGE_RESULTS)

    # ------------------------------------------------------------------ Actions

    def _update_analysis_ranges(self) -> None:
        """Load ideal angle ranges for the current riding style."""
        from pathlib import Path
        path = Path(__file__).resolve().parent.parent / "config" / "angle_ranges.json"
        try:
            with open(path) as f:
                all_ranges = json.load(f)
            style = self._rider.riding_style.value
            ranges = all_ranges.get(style, all_ranges["road"])
            self._window.analysis_view.set_ideal_ranges(ranges)
        except Exception:
            pass

    def _new_session(self) -> None:
        self._rider = RiderMeasurements()
        self._bike = BikeGeometry()
        self._pose_sequence = None
        self._pose_ctrl.stop()
        self._window.navigate_to(self.PAGE_RIDER)
        self._window.set_status("New session started")

    def _save(self) -> None:
        try:
            path = save_session(
                self._rider,
                self._bike,
                self._analysis_ctrl.fit_score,
            )
            self._window.set_status(f"Session saved: {path}")
        except Exception as e:
            QMessageBox.critical(self._window, "Save Error", str(e))

    def _load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self._window, "Open Session", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            data = load_session(path)
            self._rider = data["rider"]
            self._bike = data["bike"]
            self._rider_ctrl.load(self._rider)
            self._bike_ctrl.load(self._bike)
            self._window.set_status(f"Session loaded: {path}")
            self._window.navigate_to(self.PAGE_RIDER)
        except Exception as e:
            QMessageBox.critical(self._window, "Load Error", str(e))

    def _export_pdf(self) -> None:
        # Placeholder — PDF export not yet implemented in MVP
        QMessageBox.information(
            self._window, "Export PDF",
            "PDF export is planned for a future release."
        )
