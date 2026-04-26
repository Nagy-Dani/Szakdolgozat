from __future__ import annotations

import pytest
from models.pose_model import BodyLandmark, PoseFrame, PoseSequence


def _make_complete_frame(side="left", visibility=1.0):
    """Helper: build a PoseFrame with all required landmarks for one side."""
    names = [
        f"{side}_shoulder", f"{side}_elbow", f"{side}_wrist",
        f"{side}_hip", f"{side}_knee", f"{side}_ankle",
        f"{side}_heel", f"{side}_foot_index",
    ]
    landmarks = {n: BodyLandmark(name=n, x=0.5, y=0.5, z=0, visibility=visibility) for n in names}
    return PoseFrame(frame_number=0, timestamp_ms=0, landmarks=landmarks)


def test_body_landmark_construction():
    lm = BodyLandmark(name="left_knee", x=0.5, y=0.7, z=-0.1, visibility=0.95)
    assert lm.name == "left_knee"
    assert lm.x == 0.5
    assert lm.visibility == 0.95


def test_pose_frame_is_complete_returns_true():
    """Ha minden szükséges landmark látható, az is_complete True."""
    frame = _make_complete_frame(side="left", visibility=0.9)
    assert frame.is_complete("left") is True


def test_pose_frame_is_complete_low_visibility():
    """Alacsony visibility esetén nem teljes a frame."""
    frame = _make_complete_frame(side="left", visibility=0.3)
    assert frame.is_complete("left") is False


def test_pose_frame_is_complete_missing_landmark():
    """Hiányzó testpont esetén nem teljes."""
    frame = _make_complete_frame(side="left")
    del frame.landmarks["left_knee"]
    assert frame.is_complete("left") is False


def test_pose_sequence_duration():
    """A duration_sec property a total_frames / fps értékét adja vissza."""
    seq = PoseSequence(fps=30.0, total_frames=900,
                       video_width=1920, video_height=1080)
    assert seq.duration_sec == pytest.approx(30.0)


def test_pose_sequence_get_valid_frames_filters_incomplete():
    """A get_valid_frames csak a teljes képkockákat adja vissza."""
    seq = PoseSequence(fps=30.0, total_frames=2,
                       video_width=1920, video_height=1080)
    seq.frames = [
        _make_complete_frame(side="left", visibility=0.9),
        _make_complete_frame(side="left", visibility=0.2),
    ]
    valid = seq.get_valid_frames("left")
    assert len(valid) == 1