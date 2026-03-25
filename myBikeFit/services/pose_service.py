"""RTMPose wrapper service (via rtmlib)."""

from __future__ import annotations

import cv2
import numpy as np
from rtmlib import BodyWithFeet

from models.pose_model import BodyLandmark, PoseFrame
from config import (
    POSE_BACKEND,
    POSE_DEVICE,
    POSE_MIN_DETECTION_CONFIDENCE,
)

# Halpe26 keypoint index → our internal landmark name.
# Only the cycling-relevant subset is kept; the rest are ignored.
_LANDMARK_NAMES: dict[int, str] = {
    0:  "nose",
    5:  "left_shoulder",
    6:  "right_shoulder",
    7:  "left_elbow",
    8:  "right_elbow",
    9:  "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip",
    13: "left_knee",
    14: "right_knee",
    15: "left_ankle",
    16: "right_ankle",
    20: "left_foot_index",   # left big toe
    21: "right_foot_index",  # right big toe
    24: "left_heel",
    25: "right_heel",
}

# Connections for drawing the skeleton
_CONNECTIONS = [
    ("nose", "left_shoulder"), ("nose", "right_shoulder"),
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"), ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"), ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"), ("right_knee", "right_ankle"),
    ("left_ankle", "left_heel"), ("right_ankle", "right_heel"),
    ("left_heel", "left_foot_index"), ("right_heel", "right_foot_index"),
    ("left_ankle", "left_foot_index"), ("right_ankle", "right_foot_index"),
]


class PoseDetector:
    """Wraps RTMPose (via rtmlib) for frame-by-frame detection."""

    def __init__(self):
        self._body = BodyWithFeet(
            mode='balanced',
            backend=POSE_BACKEND,
            device=POSE_DEVICE,
        )
        self._last_landmarks: dict[str, BodyLandmark] | None = None

    def detect(
        self, frame: np.ndarray, frame_number: int = 0, timestamp_ms: float = 0.0
    ) -> PoseFrame | None:
        """Run pose detection on a single BGR frame.

        Returns a PoseFrame with all detected cycling-relevant landmarks,
        or None if no pose was detected.
        """
        h, w = frame.shape[:2]

        # rtmlib returns (keypoints, scores) — arrays of shape (N, K, 2) and (N, K)
        keypoints, scores = self._body(frame)

        if keypoints is None or len(keypoints) == 0:
            return None

        # Use only the first detected person
        person_kps = keypoints[0]   # shape (K, 2) — pixel coords
        person_scores = scores[0]   # shape (K,)

        landmarks: dict[str, BodyLandmark] = {}
        for idx, name in _LANDMARK_NAMES.items():
            if idx >= len(person_kps):
                continue
            kp = person_kps[idx]
            score = float(person_scores[idx])

            # Normalize pixel coordinates to [0, 1] range
            landmarks[name] = BodyLandmark(
                name=name,
                x=float(kp[0]) / w,
                y=float(kp[1]) / h,
                z=0.0,  # RTMPose 2D models don't provide depth
                visibility=score,
            )

        if not landmarks:
            return None

        self._last_landmarks = landmarks

        return PoseFrame(
            frame_number=frame_number,
            timestamp_ms=timestamp_ms,
            landmarks=landmarks,
        )

    def draw_skeleton(
        self, frame: np.ndarray, pose_frame: PoseFrame | None = None
    ) -> np.ndarray:
        """Draw the pose skeleton on a frame manually."""
        annotated = frame.copy()

        landmarks_to_use = pose_frame.landmarks if pose_frame else self._last_landmarks

        if not landmarks_to_use:
            return annotated

        h, w = frame.shape[:2]

        # Draw connections
        for name1, name2 in _CONNECTIONS:
            if name1 in landmarks_to_use and name2 in landmarks_to_use:
                pt1 = landmarks_to_use[name1]
                pt2 = landmarks_to_use[name2]
                if pt1.visibility > 0.5 and pt2.visibility > 0.5:
                    x1, y1 = int(pt1.x * w), int(pt1.y * h)
                    x2, y2 = int(pt2.x * w), int(pt2.y * h)
                    cv2.line(annotated, (x1, y1), (x2, y2), (255, 255, 0), 2)

        # Draw keypoints
        for name, lm in landmarks_to_use.items():
            if lm.visibility > 0.5:
                x, y = int(lm.x * w), int(lm.y * h)
                cv2.circle(annotated, (x, y), 4, (0, 255, 0), -1)

        return annotated

    def close(self) -> None:
        # rtmlib doesn't require explicit cleanup, but keep the interface
        self._body = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
