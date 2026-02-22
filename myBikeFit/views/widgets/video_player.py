"""VideoPlayer widget — OpenCV frame rendering in a QLabel with threading."""

from __future__ import annotations

import cv2
import numpy as np

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap


class VideoPlayer(QWidget):
    """Widget that displays video frames with play/pause and scrubbing."""

    frame_changed = pyqtSignal(int, np.ndarray)  # frame_number, frame_data

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._cap: cv2.VideoCapture | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._playing = False
        self._current_frame = 0
        self._total_frames = 0
        self._fps = 30.0
        self._overlay_frame: np.ndarray | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Video display
        self._display = QLabel()
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setMinimumSize(640, 480)
        self._display.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        layout.addWidget(self._display)

        # Controls
        controls = QHBoxLayout()
        self._btn_play = QPushButton("▶")
        self._btn_play.setFixedWidth(40)
        self._btn_play.clicked.connect(self.toggle_play)
        controls.addWidget(self._btn_play)

        self._btn_prev = QPushButton("◀")
        self._btn_prev.setFixedWidth(40)
        self._btn_prev.clicked.connect(self.prev_frame)
        controls.addWidget(self._btn_prev)

        self._btn_next = QPushButton("▶|")
        self._btn_next.setFixedWidth(40)
        self._btn_next.clicked.connect(self.next_frame_step)
        controls.addWidget(self._btn_next)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.sliderMoved.connect(self.seek)
        controls.addWidget(self._slider)

        self._lbl_time = QLabel("0 / 0")
        controls.addWidget(self._lbl_time)

        layout.addLayout(controls)

    # --- Public API ---

    def load_video(self, path: str) -> bool:
        self.stop()
        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            return False
        self._total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._current_frame = 0
        self._slider.setRange(0, max(0, self._total_frames - 1))
        self._show_frame(0)
        return True

    def set_overlay(self, frame: np.ndarray) -> None:
        """Set a frame with skeleton overlay to display instead of raw."""
        self._overlay_frame = frame
        self._render(frame)

    def toggle_play(self) -> None:
        if self._playing:
            self.pause()
        else:
            self.play()

    def play(self) -> None:
        if self._cap is None:
            return
        self._playing = True
        self._btn_play.setText("⏸")
        self._timer.start(int(1000 / self._fps))

    def pause(self) -> None:
        self._playing = False
        self._btn_play.setText("▶")
        self._timer.stop()

    def stop(self) -> None:
        self.pause()
        if self._cap:
            self._cap.release()
            self._cap = None

    def seek(self, frame_number: int) -> None:
        self._show_frame(frame_number)

    def next_frame_step(self) -> None:
        self._show_frame(self._current_frame + 1)

    def prev_frame(self) -> None:
        self._show_frame(max(0, self._current_frame - 1))

    # --- Internal ---

    def _next_frame(self) -> None:
        if self._current_frame >= self._total_frames - 1:
            self.pause()
            return
        self._show_frame(self._current_frame + 1)

    def _show_frame(self, frame_number: int) -> None:
        if self._cap is None:
            return
        frame_number = max(0, min(frame_number, self._total_frames - 1))
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self._cap.read()
        if not ret:
            return
        self._current_frame = frame_number
        self._slider.blockSignals(True)
        self._slider.setValue(frame_number)
        self._slider.blockSignals(False)
        self._lbl_time.setText(f"{frame_number} / {self._total_frames}")
        self._render(frame)
        self.frame_changed.emit(frame_number, frame)

    def _render(self, frame: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img).scaled(
            self._display.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._display.setPixmap(pixmap)

    def closeEvent(self, event):  # noqa: N802
        self.stop()
        super().closeEvent(event)
