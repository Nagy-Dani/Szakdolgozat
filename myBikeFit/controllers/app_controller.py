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

    # Page indices (must match MainWindow.PAGES order)
    PAGE_RIDER = 0
    PAGE_BIKE = 1
    PAGE_VIDEO = 2
    PAGE_SIDE_ANALYSIS = 3
    PAGE_FRONT_ANALYSIS = 4
    PAGE_BACK_ANALYSIS = 5
    PAGE_RESULTS = 6

    # Keep backward-compatible aliases
    PAGE_ANALYSIS = PAGE_SIDE_ANALYSIS

    def __init__(self, window: MainWindow):
        self._window = window

        # Models
        self._rider = RiderMeasurements()
        self._bike = BikeGeometry()
        self._pose_sequences: dict[str, PoseSequence | None] = {
            "side": None, "front": None, "back": None,
        }

        # Uploaded video paths (populated when user clicks Analyze)
        self._video_paths: dict[str, str | None] = {
            "side": None, "front": None, "back": None,
        }

        # Sub-controllers — rider, bike, video (single instance)
        self._rider_ctrl = RiderController(window.rider_view, self._rider)
        self._bike_ctrl = BikeController(window.bike_view, self._bike)
        self._video_ctrl = VideoController(window.video_view)

        # One PoseController per analysis view
        self._pose_ctrls: dict[str, PoseController] = {
            "side":  PoseController(window.side_analysis_view),
            "front": PoseController(window.front_analysis_view),
            "back":  PoseController(window.back_analysis_view),
        }

        # Single analysis controller (aggregates results from all views)
        self._analysis_ctrl = AnalysisController(window.results_view)

        # The analysis pipeline: list of view types to process sequentially
        self._analysis_queue: list[str] = []

        # Wire navigation
        self._rider_ctrl.set_on_valid(self._on_rider_valid)
        self._bike_ctrl.set_on_valid(self._on_bike_valid)

        # Connect the new multi-video signal
        window.video_view.videos_ready.connect(self._on_videos_ready)

        # Wire pose completion for each view
        for view_type, ctrl in self._pose_ctrls.items():
            ctrl.set_on_complete(
                lambda seq, vt=view_type: self._on_pose_complete(vt, seq)
            )

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

    def _on_videos_ready(self, paths: dict) -> None:
        """Handle the multi-video upload signal."""
        self._video_paths["side"] = paths.get("side")
        self._video_paths["front"] = paths.get("front")
        self._video_paths["back"] = paths.get("back")

        facing = paths.get("facing", "left")

        # Copy facing side to all analysis views
        self._window.side_analysis_view.facing_side = facing
        self._window.front_analysis_view.facing_side = facing
        self._window.back_analysis_view.facing_side = facing

        # Reload ranges from config
        self._update_analysis_ranges()

        # Build the analysis queue based on which videos were uploaded
        self._analysis_queue = []
        for vt in ("side", "front", "back"):
            if self._video_paths[vt]:
                self._analysis_queue.append(vt)

        self._window.set_status(
            f"Videos loaded: {', '.join(self._analysis_queue)} — starting analysis"
        )

        # Start with the first view in the queue
        self._start_next_analysis()

    def _start_next_analysis(self) -> None:
        """Navigate to the next analysis page and start pose detection."""
        if not self._analysis_queue:
            # All views done — run final scoring
            side = self._window.video_view.facing_side
            if self._pose_sequences.get("side"):
                self._analysis_ctrl.analyze(
                    self._pose_sequences,
                    self._rider,
                    self._bike,
                    side=side,
                )
            else:
                self._window.navigate_to(self.PAGE_RESULTS)
            return

        current_view_type = self._analysis_queue.pop(0)
        path = self._video_paths[current_view_type]

        page_map = {
            "side":  self.PAGE_SIDE_ANALYSIS,
            "front": self.PAGE_FRONT_ANALYSIS,
            "back":  self.PAGE_BACK_ANALYSIS,
        }
        self._window.navigate_to(page_map[current_view_type])
        self._pose_ctrls[current_view_type].start_analysis(path)

    def _on_pose_complete(self, view_type: str, sequence: PoseSequence) -> None:
        self._pose_sequences[view_type] = sequence
        # For front/back views, use the view_type as the 'side' for validation;
        # for side views, use the actual left/right facing side.
        if view_type in ("front", "back"):
            validation_side = view_type
        else:
            validation_side = self._window.video_view.facing_side
        valid_count = len(sequence.get_valid_frames(validation_side))
        self._window.set_status(
            f"{view_type.title()} pose detection complete — {valid_count} valid frames"
        )
        # Move on to the next view in the queue (or finish)
        self._start_next_analysis()

    def _on_analysis_complete(self, fit_score, recommendations) -> None:
        self._window.set_status(
            f"Analysis complete — overall score: {fit_score.overall:.0f} ({fit_score.category})"
        )
        self._window.navigate_to(self.PAGE_RESULTS)

        # Auto-save full session after analysis
        try:
            video_path = self._video_paths.get("side")
            facing_side = getattr(self._window.video_view, "facing_side", "left")
            path = save_session(
                rider=self._rider,
                bike=self._bike,
                fit_score=fit_score,
                cycling_angles=self._analysis_ctrl.angles,
                recommendations=recommendations,
                facing_side=facing_side,
                video_path=video_path,
            )
            self._window.set_status(
                f"Analysis complete — score: {fit_score.overall:.0f} "
                f"({fit_score.category}) — saved to {path}"
            )
        except Exception:
            pass  # Don't block the UI on save failure

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
            # Update all three analysis views
            self._window.side_analysis_view.set_ideal_ranges(ranges)
            self._window.front_analysis_view.set_ideal_ranges(ranges)
            self._window.back_analysis_view.set_ideal_ranges(ranges)
        except Exception:
            pass

    def _new_session(self) -> None:
        self._rider = RiderMeasurements()
        self._bike = BikeGeometry()
        self._pose_sequences = {"side": None, "front": None, "back": None}
        self._video_paths = {"side": None, "front": None, "back": None}
        self._analysis_queue.clear()
        for ctrl in self._pose_ctrls.values():
            ctrl.stop()
        self._window.navigate_to(self.PAGE_RIDER)
        self._window.set_status("New session started")

    def _save(self) -> None:
        try:
            video_path = self._video_paths.get("side")
            facing_side = getattr(self._window.video_view, "facing_side", "left")
            path = save_session(
                rider=self._rider,
                bike=self._bike,
                fit_score=self._analysis_ctrl.fit_score,
                cycling_angles=self._analysis_ctrl.angles,
                recommendations=self._analysis_ctrl.recommendations,
                facing_side=facing_side,
                video_path=video_path,
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

            # Restore results if the session contains analysis data
            if "fit_score" in data and "recommendations" in data:
                self._update_analysis_ranges()
                self._window.results_view.set_scores(data["fit_score"])
                self._window.results_view.set_recommendations(data["recommendations"])
                self._window.set_status(f"Session loaded with results: {path}")
                self._window.navigate_to(self.PAGE_RESULTS)
            else:
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
