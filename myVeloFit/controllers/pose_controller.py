"""Pose controller — runs MediaPipe pose detection in a background thread."""

from __future__ import annotations

import cv2
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal, QObject

from models.pose_model import PoseFrame, PoseSequence
from services.pose_service import PoseDetector
from services.video_service import load_video
from config import FRAME_SAMPLE_RATE


class PoseWorker(QObject):
    """Worker that runs pose detection on a video in a background thread."""

    progress = pyqtSignal(int, str)            # percent, message
    frame_processed = pyqtSignal(int, object, object)  # frame_num, PoseFrame, annotated_frame
    finished = pyqtSignal(object)              # PoseSequence
    error = pyqtSignal(str)

    def __init__(self, video_path: str, sample_rate: int = FRAME_SAMPLE_RATE):
        super().__init__()
        self._video_path = video_path
        self._sample_rate = sample_rate
        self._running = True

    def run(self) -> None:
        try:
            cap = load_video(self._video_path)
        except FileNotFoundError as e:
            self.error.emit(str(e))
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        sequence = PoseSequence(fps=fps, total_frames=total, video_width=width, video_height=height)
        detector = PoseDetector()

        idx = 0
        while self._running:
            ret, frame = cap.read()
            if not ret:
                break

            if idx % self._sample_rate == 0:
                timestamp = (idx / fps) * 1000
                pose_frame = detector.detect(frame, frame_number=idx, timestamp_ms=timestamp)
                if pose_frame:
                    sequence.add_frame(pose_frame)
                    annotated = detector.draw_skeleton(frame)
                    self.frame_processed.emit(idx, pose_frame, annotated)

                pct = int((idx / max(total, 1)) * 100)
                self.progress.emit(pct, f"Processing frame {idx}/{total}")

            idx += 1

        cap.release()
        detector.close()
        self.progress.emit(100, "Analysis complete")
        self.finished.emit(sequence)

    def stop(self) -> None:
        self._running = False


class PoseController:
    """Manages pose detection lifecycle."""

    def __init__(self, analysis_view):
        self._view = analysis_view
        self._thread: QThread | None = None
        self._worker: PoseWorker | None = None

    def start_analysis(self, video_path: str) -> None:
        """Begin pose detection in a background thread."""
        self.stop()

        self._thread = QThread()
        self._worker = PoseWorker(video_path)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.frame_processed.connect(self._on_frame)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)

        self._thread.start()

    def stop(self) -> None:
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)

    def _on_progress(self, pct: int, msg: str) -> None:
        self._view.set_progress(pct, msg)

    def _on_frame(self, frame_num: int, pose_frame: PoseFrame, annotated) -> None:
        # Update the analysis view's video player with the annotated frame
        self._view.player.set_overlay(annotated)

    def _on_finished(self, sequence: PoseSequence) -> None:
        if self._on_complete_callback:
            self._on_complete_callback(sequence)

    def _on_error(self, msg: str) -> None:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self._view, "Pose Detection Error", msg)

    _on_complete_callback = None

    def set_on_complete(self, callback) -> None:
        self._on_complete_callback = callback
