# myVeloFit — Recreate Prompt & Specification

## Overview

**myVeloFit** is a desktop application built with **Python 3.11+** and **PyQt6** that helps cyclists optimize their bike fit. The application follows the **MVC (Model-View-Controller)** architecture pattern strictly.

The user provides body measurements (height, weight, inseam, foot size, arm length, torso length, shoulder width), then records or uploads a **side-view video** of themselves pedaling on the bike. The app uses **computer vision** (MediaPipe Pose) to detect body landmarks, calculates key cycling angles (knee extension, hip angle, back angle, ankle angle), compares them to biomechanical best-practice ranges, and provides **actionable bike-fit recommendations** (raise/lower saddle, move saddle forward/back, adjust stem length/angle, etc.).

---

## Architecture: MVC

```
myVeloFit/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Project readme
├── assets/                          # Icons, images, stylesheets
│   ├── icons/
│   ├── images/
│   └── styles/
│       └── app.qss                  # Qt stylesheet
├── models/                          # MODEL layer — data & business logic
│   ├── __init__.py
│   ├── rider_model.py               # Rider body measurements
│   ├── bike_model.py                # Bike geometry data
│   ├── pose_model.py                # Pose landmark data structures
│   ├── analysis_model.py            # Angle calculations & fit scoring
│   └── recommendation_model.py      # Fit recommendations engine
├── views/                           # VIEW layer — PyQt6 UI
│   ├── __init__.py
│   ├── main_window.py               # Main window with navigation
│   ├── rider_input_view.py          # Body measurements input form
│   ├── bike_input_view.py           # Bike geometry input form
│   ├── video_capture_view.py        # Video upload / webcam capture
│   ├── analysis_view.py             # Pose overlay & angle display
│   ├── results_view.py              # Recommendations dashboard
│   └── widgets/                     # Reusable custom widgets
│       ├── __init__.py
│       ├── measurement_input.py     # Labeled input with unit selector
│       ├── angle_gauge.py           # Visual gauge for angle ranges
│       └── video_player.py          # Video playback with overlay
├── controllers/                     # CONTROLLER layer — logic glue
│   ├── __init__.py
│   ├── app_controller.py            # Top-level app orchestration
│   ├── rider_controller.py          # Rider input validation & persistence
│   ├── bike_controller.py           # Bike input validation & persistence
│   ├── video_controller.py          # Video loading, frame extraction
│   ├── pose_controller.py           # MediaPipe pose estimation pipeline
│   └── analysis_controller.py       # Run analysis, generate recommendations
├── services/                        # Shared services / utilities
│   ├── __init__.py
│   ├── video_service.py             # OpenCV video I/O helpers
│   ├── pose_service.py              # MediaPipe wrapper
│   ├── angle_calculator.py          # Geometric angle math
│   ├── fit_rules_engine.py          # Rule-based recommendation logic
│   └── persistence_service.py       # Save/load sessions (JSON)
├── tests/                           # Unit & integration tests
│   ├── __init__.py
│   ├── test_rider_model.py
│   ├── test_analysis_model.py
│   ├── test_angle_calculator.py
│   └── test_fit_rules_engine.py
└── config/
    ├── __init__.py
    ├── settings.py                  # App-wide settings / constants
    └── angle_ranges.json            # Ideal angle ranges reference data
```

---

## Detailed Component Specifications

### 1. MODELS

#### `rider_model.py`
```python
@dataclass
class RiderMeasurements:
    height_cm: float              # Total body height
    weight_kg: float              # Body weight
    inseam_cm: float              # Inner leg measurement (floor to crotch)
    foot_size_eu: float           # EU shoe size
    arm_length_cm: float          # Shoulder to wrist
    torso_length_cm: float        # Hip to shoulder
    shoulder_width_cm: float      # Shoulder-to-shoulder
    flexibility: str              # "low" | "medium" | "high"
    riding_style: str             # "road" | "tt" | "mtb" | "gravel" | "commute"
```
- Validation: all numeric fields > 0, flexibility and riding_style from enums.
- Method `to_dict()` / `from_dict()` for serialization.

#### `bike_model.py`
```python
@dataclass
class BikeGeometry:
    frame_size_cm: float          # Seat tube length
    saddle_height_cm: float       # Center of BB to top of saddle
    saddle_setback_cm: float      # Horizontal offset behind BB
    handlebar_reach_cm: float     # Saddle nose to handlebar center
    handlebar_drop_cm: float      # Saddle top to handlebar top (negative = drop)
    crank_length_mm: float        # Crank arm length
    stem_length_mm: float         # Stem length
    stem_angle_deg: float         # Stem angle
```

#### `pose_model.py`
```python
@dataclass
class BodyLandmark:
    name: str
    x: float          # Normalized 0-1
    y: float          # Normalized 0-1
    z: float          # Depth
    visibility: float  # Confidence 0-1

@dataclass
class PoseFrame:
    frame_number: int
    timestamp_ms: float
    landmarks: dict[str, BodyLandmark]   # e.g. "left_hip", "left_knee", ...

@dataclass
class PoseSequence:
    frames: list[PoseFrame]
    fps: float
    total_frames: int
```

#### `analysis_model.py`
```python
@dataclass
class CyclingAngles:
    knee_extension_min: float      # At bottom of pedal stroke (ideal: 140-150°)
    knee_extension_max: float      # At top of pedal stroke
    knee_flexion_max: float        # Max knee bend at top (ideal: 65-75°)
    hip_angle_min: float           # Torso-thigh angle (ideal: 40-55° road)
    back_angle: float              # Torso relative to horizontal (ideal: 35-45° road)
    ankle_angle_range: tuple       # Min/max ankle through stroke (ideal: 90-120°)
    shoulder_angle: float          # Upper arm to torso
    elbow_angle: float             # Elbow bend (ideal: 150-165°)

@dataclass
class FitScore:
    overall: float                 # 0-100
    knee_score: float
    hip_score: float
    back_score: float
    ankle_score: float
    reach_score: float
    category: str                  # "excellent" | "good" | "fair" | "poor"
```

#### `recommendation_model.py`
```python
@dataclass
class Recommendation:
    component: str          # "saddle_height" | "saddle_setback" | "stem" | ...
    severity: str           # "critical" | "moderate" | "minor" | "optimal"
    current_value: str
    ideal_range: str
    adjustment: str         # e.g. "Raise saddle by 8-12mm"
    explanation: str        # Why this matters
```

---

### 2. VIEWS (PyQt6)

#### `main_window.py`
- `QMainWindow` with a `QStackedWidget` for page navigation.
- Left sidebar `QListWidget` or `QToolBar` with navigation: 
  **Rider → Bike → Video → Analysis → Results**
- Progress indicator showing current step.
- Menu bar: File (New Session, Open, Save, Export PDF), Help (About).

#### `rider_input_view.py`
- `QWidget` form with labeled `QDoubleSpinBox` fields for each measurement.
- Unit toggle (metric / imperial) affecting all fields.
- `QComboBox` for flexibility level and riding style.
- Profile image placeholder (optional).
- "Next" button emits `rider_data_submitted` signal.

#### `bike_input_view.py`
- Similar form for bike geometry.
- Bike diagram SVG showing where each measurement is taken.
- Optional: preset dropdown for common bike sizes.
- "Next" button emits `bike_data_submitted` signal.

#### `video_capture_view.py`
- Two tabs: **Upload File** (drag-and-drop or file dialog) and **Record** (webcam).
- Video preview with `QLabel` rendering frames via `QPixmap`.
- Playback controls: play/pause, scrub slider, frame-by-frame step.
- Guidelines overlay showing ideal camera position (side view, full body visible).
- "Analyze" button emits `video_ready` signal.

#### `analysis_view.py`
- Live or frame-by-frame playback with **pose skeleton overlay** drawn on frames.
- Side panel showing real-time angle values with color coding:
  - 🟢 Green = within ideal range
  - 🟡 Yellow = slightly off
  - 🔴 Red = needs adjustment
- Progress bar during analysis.
- Angle history chart (`QChart` / `matplotlib`) showing angles through pedal stroke.

#### `results_view.py`
- **Fit Score** displayed as a large circular gauge (0-100).
- Per-area scores in smaller gauges (knee, hip, back, ankle, reach).
- List of `Recommendation` cards, sorted by severity.
- Each card: icon, component name, adjustment text, explanation toggle.
- "Export Report" button → generates PDF with all data, screenshots, recommendations.
- "Start Over" button to reset.

#### Custom Widgets
- `MeasurementInput`: QLabel + QDoubleSpinBox + unit QLabel, with metric/imperial conversion.
- `AngleGauge`: Custom painted widget showing current value on a colored arc (green zone, yellow zone, red zone).
- `VideoPlayer`: Wraps OpenCV frame display in QLabel with threading for smooth playback.

---

### 3. CONTROLLERS

#### `app_controller.py`
- Creates all models, views, controllers.
- Manages navigation flow between views.
- Handles session save/load via `persistence_service`.

#### `rider_controller.py`
- Connects `rider_input_view` signals to `rider_model`.
- Validates input ranges (e.g., height 100-250cm, weight 30-200kg).
- Emits validation errors back to view.

#### `bike_controller.py`
- Same pattern for bike data.
- Auto-suggests values based on rider measurements (e.g., saddle height ≈ inseam × 0.883).

#### `video_controller.py`
- Handles file loading via `video_service`.
- Manages webcam capture (OpenCV `VideoCapture`).
- Extracts frames, validates video (side view check, resolution, duration).
- Feeds frames to `pose_controller`.

#### `pose_controller.py`
- Runs MediaPipe Pose on each frame in a `QThread` worker.
- Emits progress signals.
- Builds `PoseSequence` and passes to `analysis_controller`.

#### `analysis_controller.py`
- Takes `PoseSequence` + `RiderMeasurements` + `BikeGeometry`.
- Uses `angle_calculator` to compute `CyclingAngles` for each frame.
- Identifies pedal stroke cycles (using knee Y-position periodicity).
- Averages angles across cycles.
- Uses `fit_rules_engine` to generate `FitScore` and `list[Recommendation]`.
- Pushes results to `results_view`.

---

### 4. SERVICES

#### `video_service.py`
- `load_video(path) -> VideoCapture` with validation.
- `extract_frames(cap, sample_rate) -> list[np.ndarray]`.
- `save_frame(frame, path)`.
- `get_video_info(path) -> dict` (fps, resolution, duration, codec).

#### `pose_service.py`
- Wraps `mediapipe.solutions.pose`.
- `detect_pose(frame) -> list[BodyLandmark]`.
- `draw_skeleton(frame, landmarks) -> np.ndarray`.
- Configurable: model complexity (0/1/2), min confidence.

#### `angle_calculator.py`
- `calculate_angle(p1, p2, p3) -> float` — angle at p2 formed by p1-p2-p3.
- `calculate_knee_extension(hip, knee, ankle) -> float`.
- `calculate_hip_angle(shoulder, hip, knee) -> float`.
- `calculate_back_angle(shoulder, hip) -> float` — relative to horizontal.
- `calculate_ankle_angle(knee, ankle, toe) -> float`.
- All using 2D projected coordinates.

#### `fit_rules_engine.py`
- Loads ideal angle ranges from `config/angle_ranges.json`.
- Adjusts ranges based on `riding_style` (road vs MTB vs TT).
- For each angle: computes deviation, assigns severity, generates recommendation text.
- Scoring formula: `score = max(0, 100 - Σ(weighted_deviations))`.

#### `persistence_service.py`
- `save_session(rider, bike, results, path)` → JSON file.
- `load_session(path) -> (RiderMeasurements, BikeGeometry, ...)`.
- Auto-save on analysis completion.

---

### 5. CONFIG

#### `angle_ranges.json`
```json
{
  "road": {
    "knee_extension": {"min": 140, "max": 150, "weight": 30},
    "knee_flexion_max": {"min": 65, "max": 75, "weight": 20},
    "hip_angle": {"min": 40, "max": 55, "weight": 20},
    "back_angle": {"min": 35, "max": 45, "weight": 15},
    "ankle_angle": {"min": 90, "max": 120, "weight": 10},
    "elbow_angle": {"min": 150, "max": 165, "weight": 5}
  },
  "mtb": {
    "knee_extension": {"min": 135, "max": 150, "weight": 30},
    "knee_flexion_max": {"min": 65, "max": 80, "weight": 20},
    "hip_angle": {"min": 45, "max": 65, "weight": 20},
    "back_angle": {"min": 40, "max": 55, "weight": 15},
    "ankle_angle": {"min": 85, "max": 120, "weight": 10},
    "elbow_angle": {"min": 145, "max": 170, "weight": 5}
  },
  "tt": {
    "knee_extension": {"min": 142, "max": 152, "weight": 30},
    "knee_flexion_max": {"min": 60, "max": 72, "weight": 20},
    "hip_angle": {"min": 30, "max": 45, "weight": 20},
    "back_angle": {"min": 15, "max": 30, "weight": 15},
    "ankle_angle": {"min": 90, "max": 115, "weight": 10},
    "elbow_angle": {"min": 85, "max": 100, "weight": 5}
  }
}
```

#### `settings.py`
```python
APP_NAME = "myVeloFit"
APP_VERSION = "1.0.0"
DEFAULT_UNITS = "metric"              # "metric" | "imperial"
VIDEO_MAX_DURATION_SEC = 120
VIDEO_MIN_DURATION_SEC = 5
POSE_MODEL_COMPLEXITY = 2             # 0, 1, or 2
POSE_MIN_DETECTION_CONFIDENCE = 0.5
POSE_MIN_TRACKING_CONFIDENCE = 0.5
FRAME_SAMPLE_RATE = 2                 # Process every Nth frame
AUTOSAVE_DIR = "~/.myvelofit/sessions"
```

---

## Key Technologies

| Component | Technology |
|---|---|
| UI Framework | PyQt6 |
| Video Processing | OpenCV (cv2) |
| Pose Estimation | MediaPipe Pose |
| Angle Math | NumPy |
| Charts | PyQtChart or matplotlib |
| PDF Export | ReportLab or FPDF2 |
| Persistence | JSON (stdlib) |
| Testing | pytest |

---

## User Flow (MVP)

1. **Launch** → Main window with sidebar navigation.
2. **Step 1: Rider** → Enter body measurements → Validate → Next.
3. **Step 2: Bike** → Enter bike geometry (or skip for auto-detect) → Next.
4. **Step 3: Video** → Upload side-view video of pedaling → Preview → "Analyze".
5. **Step 4: Analysis** → Watch pose skeleton overlay with live angle readouts → Wait for completion.
6. **Step 5: Results** → View fit score, per-area breakdown, actionable recommendations → Export PDF.

---

## Implementation Order (MVP phases)

### Phase 1 — Skeleton
- Project scaffolding, `main.py`, `main_window.py` with stacked pages.
- `rider_input_view.py` with all form fields.
- `rider_model.py` and `rider_controller.py`.

### Phase 2 — Video
- `video_capture_view.py` (upload only, no webcam yet).
- `video_service.py` and `video_controller.py`.
- Frame display in UI.

### Phase 3 — Pose Detection
- `pose_service.py` wrapping MediaPipe.
- `pose_controller.py` with QThread worker.
- `analysis_view.py` with skeleton overlay.

### Phase 4 — Analysis & Recommendations
- `angle_calculator.py` with all angle computations.
- `analysis_model.py` and `analysis_controller.py`.
- `fit_rules_engine.py` with `angle_ranges.json`.
- `results_view.py` with scores and recommendation cards.

### Phase 5 — Polish
- Bike input view and model.
- Session save/load.
- PDF export.
- Unit conversion (imperial).
- Styling with `app.qss`.

---

## Critical Implementation Notes

1. **Threading**: All video processing and pose detection MUST run in `QThread` workers. Never block the UI thread with OpenCV or MediaPipe calls.

2. **Coordinate Systems**: MediaPipe returns normalized coordinates (0-1). Convert to pixel coordinates using frame dimensions for drawing. Use normalized coords for angle calculations.

3. **Pedal Stroke Detection**: Identify cycles by finding local minima/maxima of the knee Y-coordinate over time. Average angles across at least 3 complete cycles for stability.

4. **Side View Assumption**: The app assumes a pure side-view camera angle. Add a validation step that checks landmark depths (Z-values) are roughly consistent, warning the user if the camera angle seems off.

5. **Angle Stability**: Use a rolling average (window=5 frames) to smooth noisy angle readings before displaying or scoring.

6. **Saddle Height Formula**: Quick sanity check — `ideal_saddle_height ≈ inseam_cm × 0.883`. Use this as a cross-reference with the vision-based analysis.

7. **Signals & Slots**: All communication between Views and Controllers uses PyQt6 signals/slots. Views never import Controllers directly; Controllers connect to View signals during initialization.
