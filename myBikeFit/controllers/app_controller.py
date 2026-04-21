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

    PAGE_WELCOME = 0
    PAGE_RIDER = 1
    PAGE_BIKE = 2
    PAGE_VIDEO = 3
    PAGE_ANALYSIS = 4
    PAGE_RESULTS = 5

    def __init__(self, window: MainWindow):
        self._window = window

        self._rider = RiderMeasurements()
        self._bike = BikeGeometry()
        self._pose_sequence: PoseSequence | None = None

        self._rider_ctrl = RiderController(window.rider_view, self._rider)
        self._bike_ctrl = BikeController(window.bike_view, self._bike)
        self._video_ctrl = VideoController(window.video_view)
        self._pose_ctrl = PoseController(window.analysis_view)
        self._analysis_ctrl = AnalysisController(window.results_view)

        self._rider_ctrl.set_on_valid(self._on_rider_valid)
        self._bike_ctrl.set_on_valid(self._on_bike_valid)
        self._video_ctrl.set_on_valid(self._on_video_valid)
        self._pose_ctrl.set_on_complete(self._on_pose_complete)
        self._analysis_ctrl.set_on_complete(self._on_analysis_complete)

        window.new_session_requested.connect(self._new_session)
        window.save_session_requested.connect(self._save)
        window.load_session_requested.connect(self._load)
        window.export_pdf_requested.connect(self._export_pdf)
        window.welcome_view.start_requested.connect(self._new_session)
        window.results_view.restart_requested.connect(self._new_session)
        window.results_view.export_requested.connect(self._export_pdf)

        self._update_analysis_ranges()

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
        self._update_analysis_ranges()
        
        side = self._window.video_view.facing_side
        self._window.analysis_view.facing_side = side
        self._window.navigate_to(self.PAGE_ANALYSIS)
        self._pose_ctrl.start_analysis(path)

    def _on_pose_complete(self, sequence: PoseSequence) -> None:
        self._pose_sequence = sequence
        side = self._window.video_view.facing_side
        valid_count = len(sequence.get_valid_frames(side))
        self._window.set_status(
            f"Pose detection complete — {valid_count} valid frames"
        )
        v_path = getattr(self._window.video_view, "video_path", "")
        self._analysis_ctrl.analyze(sequence, self._rider, self._bike, side=side, video_path=v_path)

    def _on_analysis_complete(self, fit_score, recommendations) -> None:
        self._window.set_status(
            f"Analysis complete — overall score: {fit_score.overall:.0f} ({fit_score.category})"
        )
        self._window.navigate_to(self.PAGE_RESULTS)

        try:
            video_path = getattr(self._window.video_view, "video_path", None)
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
            pass

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
            video_path = getattr(self._window.video_view, "video_path", None)
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

            
            if "fit_score" in data and "recommendations" in data:
                self._update_analysis_ranges()
                self._window.results_view.set_scores(data["fit_score"])
                self._window.results_view.set_recommendations(data["recommendations"])
                self._analysis_ctrl._fit_score = data["fit_score"]
                self._analysis_ctrl._recommendations = data["recommendations"]
                if "cycling_angles" in data:
                    self._analysis_ctrl._angles = data["cycling_angles"]

                video_path = data.get("video_path", "")
                facing_side = data.get("facing_side", "left")
                self._window.analysis_view.facing_side = facing_side
                if video_path:
                    try:
                        self._window.analysis_view.player.load_video(video_path)
                    except Exception:
                        pass

                self._window.set_status(f"Session loaded with results: {path}")
                self._window.navigate_to(self.PAGE_RESULTS)
            else:
                self._window.set_status(f"Session loaded: {path}")
                self._window.navigate_to(self.PAGE_RIDER)
        except Exception as e:
            QMessageBox.critical(self._window, "Load Error", str(e))

    def _export_pdf(self) -> None:
        """Export the current session analysis as a PDF report."""
        if not getattr(self._analysis_ctrl, "fit_score", None):
            QMessageBox.warning(self._window, "Export PDF", "No analysis results to export.")
            return

        date_str = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"myBikeFit_Report_{date_str}.pdf"

        path, _ = QFileDialog.getSaveFileName(
            self._window, "Export PDF Report", default_name, "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            from services.pdf_export_service import PDFReportGenerator
            generator = PDFReportGenerator()
            generator.generate_report(
                filepath=path,
                rider=self._rider,
                bike=self._bike,
                scores=self._analysis_ctrl.fit_score,
                angles=self._analysis_ctrl.angles,
                recommendations=self._analysis_ctrl.recommendations
            )
            QMessageBox.information(self._window, "Export PDF", f"PDF report successfully saved to:\n{path}")
            self._window.set_status(f"Exported PDF down to {path}")
        except Exception as e:
            QMessageBox.critical(self._window, "Export Error", f"Failed to generate PDF:\n{str(e)}")
