"""Pose landmark data structures."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BodyLandmark:
    """Single body landmark detected by MediaPipe."""

    name: str
    x: float  # Normalized 0–1 (left of image → right)
    y: float  # Normalized 0–1 (top of image → bottom)
    z: float  # Depth estimate
    visibility: float  # Confidence 0–1


@dataclass
class PoseFrame:
    """All landmarks detected in a single video frame."""

    frame_number: int
    timestamp_ms: float
    landmarks: dict[str, BodyLandmark] = field(default_factory=dict)

    def get(self, name: str) -> BodyLandmark | None:
        return self.landmarks.get(name)

    @property
    def is_complete(self) -> bool:
        """Check that the key cycling landmarks are visible."""
        required = [
            "left_hip", "left_knee", "left_ankle",
            "left_shoulder", "left_elbow", "left_wrist",
            "left_heel", "left_foot_index",
        ]
        return all(
            name in self.landmarks and self.landmarks[name].visibility > 0.5
            for name in required
        )


@dataclass
class PoseSequence:
    """Ordered sequence of pose frames extracted from a video."""

    frames: list[PoseFrame] = field(default_factory=list)
    fps: float = 30.0
    total_frames: int = 0
    video_width: int = 0
    video_height: int = 0

    def add_frame(self, frame: PoseFrame) -> None:
        self.frames.append(frame)

    @property
    def duration_sec(self) -> float:
        return self.total_frames / self.fps if self.fps > 0 else 0.0

    @property
    def valid_frames(self) -> list[PoseFrame]:
        return [f for f in self.frames if f.is_complete]
