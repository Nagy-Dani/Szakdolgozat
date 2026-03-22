"""Video I/O helpers using OpenCV."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class VideoInfo:
    path: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration_sec: float
    codec: str


def get_video_info(path: str) -> VideoInfo | None:
    """Read basic metadata from a video file."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None
    info = VideoInfo(
        path=path,
        width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        fps=cap.get(cv2.CAP_PROP_FPS) or 30.0,
        frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        duration_sec=0.0,
        codec=_fourcc_to_str(int(cap.get(cv2.CAP_PROP_FOURCC))),
    )
    info.duration_sec = info.frame_count / info.fps if info.fps > 0 else 0.0
    cap.release()
    return info


def load_video(path: str) -> cv2.VideoCapture:
    """Open a video file and return the VideoCapture object."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {path}")
    return cap


def extract_frames(
    cap: cv2.VideoCapture,
    sample_rate: int = 1,
    max_frames: int | None = None,
) -> list[np.ndarray]:
    """Extract frames from a VideoCapture, taking every `sample_rate`-th frame."""
    frames: list[np.ndarray] = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % sample_rate == 0:
            frames.append(frame)
            if max_frames and len(frames) >= max_frames:
                break
        idx += 1
    return frames


def save_frame(frame: np.ndarray, path: str) -> None:
    """Save a single frame as an image file."""
    cv2.imwrite(path, frame)


def _fourcc_to_str(fourcc: int) -> str:
    return "".join(chr((fourcc >> (8 * i)) & 0xFF) for i in range(4))
