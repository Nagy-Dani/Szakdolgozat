"""myVeloFit application configuration."""
from __future__ import annotations

APP_NAME = "myVeloFit"
APP_VERSION = "1.0.0"

# Units
DEFAULT_UNITS = "metric"  # "metric" | "imperial"

# Video constraints
VIDEO_MAX_DURATION_SEC = 120
VIDEO_MIN_DURATION_SEC = 5

# MediaPipe Pose settings
POSE_MODEL_COMPLEXITY = 2        # 0 (lite), 1 (full), 2 (heavy)
POSE_MIN_DETECTION_CONFIDENCE = 0.5
POSE_MIN_TRACKING_CONFIDENCE = 0.5

# Frame sampling — process every Nth frame for performance
FRAME_SAMPLE_RATE = 2

# Smoothing window for angle readings
ANGLE_SMOOTHING_WINDOW = 5

# Pedal stroke detection — minimum complete cycles required
MIN_PEDAL_CYCLES = 3

# Persistence
AUTOSAVE_DIR = "~/.myvelofit/sessions"

# UI
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800
SIDEBAR_WIDTH = 200
