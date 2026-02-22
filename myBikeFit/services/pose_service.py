"""MediaPipe Pose wrapper service."""

from __future__ import annotations

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from models.pose_model import BodyLandmark, PoseFrame
from config import (
    POSE_MODEL_COMPLEXITY,
    POSE_MIN_DETECTION_CONFIDENCE,
    POSE_MIN_TRACKING_CONFIDENCE,
)

# MediaPipe landmark name mapping (index → name) for cycling-relevant points
_LANDMARK_NAMES = {
    0: "nose",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
    29: "left_heel",
    30: "right_heel",
    31: "left_foot_index",
    32: "right_foot_index",
}

# Connections for drawing the skeleton manually
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
    """Wraps MediaPipe Pose for frame-by-frame detection."""

    def __init__(self):
        base_options = mp_python.BaseOptions(model_asset_path='assets/models/pose_landmarker_heavy.task')
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=POSE_MIN_DETECTION_CONFIDENCE,
            min_pose_presence_confidence=POSE_MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=POSE_MIN_TRACKING_CONFIDENCE,
        )
        self._detector = vision.PoseLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1
        self._last_result = None

    def detect(
        self, frame: np.ndarray, frame_number: int = 0, timestamp_ms: float = 0.0
    ) -> PoseFrame | None:
        """Run pose detection on a single BGR frame.

        Returns a PoseFrame with all detected cycling-relevant landmarks,
        or None if no pose was detected.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        # mediapipe tasks API strictly requires strictly increasing timestamps
        ts = int(timestamp_ms) if timestamp_ms > 0 else frame_number
        if ts <= self._last_timestamp_ms:
            ts = self._last_timestamp_ms + 1
        self._last_timestamp_ms = ts

        result = self._detector.detect_for_video(mp_image, ts)
        self._last_result = result

        if not result.pose_landmarks:
            return None

        landmarks: dict[str, BodyLandmark] = {}
        person_landmarks = result.pose_landmarks[0]
        for idx, name in _LANDMARK_NAMES.items():
            lm = person_landmarks[idx]
            landmarks[name] = BodyLandmark(
                name=name,
                x=lm.x,
                y=lm.y,
                z=lm.z,
                visibility=lm.visibility,
            )

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
        
        landmarks_to_use = pose_frame.landmarks if pose_frame else None
            
        if not landmarks_to_use and self._last_result and self._last_result.pose_landmarks:
            landmarks_to_use = {}
            person_landmarks = self._last_result.pose_landmarks[0]
            for idx, name in _LANDMARK_NAMES.items():
                lm = person_landmarks[idx]
                landmarks_to_use[name] = BodyLandmark(name=name, x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility)

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
        if hasattr(self, '_detector') and self._detector:
            self._detector.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
