"""Video controller — handles video loading and frame management."""

from __future__ import annotations

from services.video_service import get_video_info, load_video, VideoInfo
from config import VIDEO_MIN_DURATION_SEC, VIDEO_MAX_DURATION_SEC


class VideoController:
    """Connects VideoCaptureView to video services."""

    def __init__(self, view):
        self._view = view
        self._video_info: VideoInfo | None = None
        self._view.video_ready.connect(self._on_video_ready)

    @property
    def video_info(self) -> VideoInfo | None:
        return self._video_info

    def _on_video_ready(self, path: str) -> None:
        info = get_video_info(path)
        if info is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self._view, "Error", f"Cannot read video: {path}")
            return

        # Duration check
        if info.duration_sec < VIDEO_MIN_DURATION_SEC:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self._view, "Video Too Short",
                f"Video is only {info.duration_sec:.1f}s. "
                f"Minimum is {VIDEO_MIN_DURATION_SEC}s for reliable analysis."
            )
            return

        if info.duration_sec > VIDEO_MAX_DURATION_SEC:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self._view, "Video Too Long",
                f"Video is {info.duration_sec:.1f}s. "
                f"Only the first {VIDEO_MAX_DURATION_SEC}s will be analyzed."
            )

        self._video_info = info

        if self._on_valid_callback:
            self._on_valid_callback(path, info)

    _on_valid_callback = None

    def set_on_valid(self, callback) -> None:
        self._on_valid_callback = callback
