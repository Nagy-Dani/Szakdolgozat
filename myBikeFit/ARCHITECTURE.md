# myBikeFit — Complete Architectural Documentation

> **Generated from the full design & implementation chat session.**  
> This document explains every file, every function, how they connect,  
> and the exact user-flow and data-flow through the entire application.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure (File Tree)](#3-project-structure-file-tree)
4. [Architecture: MVC Pattern](#4-architecture-mvc-pattern)
5. [Startup Sequence](#5-startup-sequence)
6. [User Flow (Step by Step)](#6-user-flow-step-by-step)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [Layer 1 — Models (Data & Validation)](#8-layer-1--models-data--validation)
9. [Layer 2 — Views (PyQt6 UI)](#9-layer-2--views-pyqt6-ui)
10. [Layer 3 — Controllers (Logic Glue)](#10-layer-3--controllers-logic-glue)
11. [Layer 4 — Services (Business Logic & I/O)](#11-layer-4--services-business-logic--io)
12. [Configuration](#12-configuration)
13. [Signal & Slot Wiring Map](#13-signal--slot-wiring-map)
14. [Threading Model](#14-threading-model)
15. [Scoring & Recommendation Algorithm](#15-scoring--recommendation-algorithm)
16. [Session Persistence](#16-session-persistence)
17. [Tests](#17-tests)
18. [How to Run](#18-how-to-run)
19. [Future Enhancements](#19-future-enhancements)

---

## 1. Project Overview

**myBikeFit** is a desktop bike-fitting application. The user enters body measurements (height, weight, inseam, foot size, arm length, etc.), uploads a **side-view video** of themselves pedaling, and the app:

1. Detects body pose using **MediaPipe Pose** (computer vision).
2. Calculates key **cycling angles** (knee extension, hip angle, back angle, ankle angle, elbow angle).
3. Compares those angles against **biomechanical ideal ranges** (which vary by riding style — road, MTB, TT, gravel, commute).
4. Produces an **overall fit score (0–100)** with per-area breakdowns.
5. Generates **actionable recommendations** ("Raise saddle by ~12mm", "Consider a shorter stem", etc.).

---

## 2. Technology Stack

| Component | Technology | Why |
|---|---|---|
| UI Framework | **PyQt6** | Cross-platform native desktop UI |
| Video I/O | **OpenCV (cv2)** | Industry-standard video processing |
| Pose Detection | **MediaPipe Pose** | Real-time body landmark detection |
| Math | **NumPy** | Vector math for angle calculations |
| Persistence | **JSON (stdlib)** | Simple, human-readable session files |
| Styling | **QSS (Qt Stylesheet)** | Catppuccin Mocha dark theme |
| Testing | **pytest** | Unit testing for models and services |

---

## 3. Project Structure (File Tree)

```
myBikeFit/
├── main.py                              ← Application entry point
├── requirements.txt                     ← Python dependencies
├── README.md                            ← Quick-start guide
├── PROMPT.md                            ← Original recreation prompt/spec
│
├── assets/
│   └── styles/
│       └── app.qss                      ← Dark theme stylesheet
│
├── config/
│   ├── __init__.py                      ← App constants (settings.py equivalent)
│   └── angle_ranges.json               ← Ideal angle ranges per riding style
│
├── models/                              ← MODEL layer
│   ├── __init__.py
│   ├── rider_model.py                   ← RiderMeasurements dataclass
│   ├── bike_model.py                    ← BikeGeometry dataclass
│   ├── pose_model.py                    ← BodyLandmark, PoseFrame, PoseSequence
│   ├── analysis_model.py               ← CyclingAngles, FitScore
│   └── recommendation_model.py         ← Recommendation, Severity
│
├── views/                               ← VIEW layer
│   ├── __init__.py
│   ├── main_window.py                   ← QMainWindow + sidebar + QStackedWidget
│   ├── rider_input_view.py              ← Body measurements form
│   ├── bike_input_view.py               ← Bike geometry form
│   ├── video_capture_view.py            ← Video upload + preview
│   ├── analysis_view.py                 ← Pose overlay + live gauges
│   ├── results_view.py                  ← Score dashboard + recommendation cards
│   └── widgets/                         ← Reusable custom widgets
│       ├── __init__.py
│       ├── measurement_input.py         ← Labeled QDoubleSpinBox + unit
│       ├── angle_gauge.py               ← Custom painted arc gauge
│       └── video_player.py              ← OpenCV frame renderer + playback controls
│
├── controllers/                         ← CONTROLLER layer
│   ├── __init__.py
│   ├── app_controller.py                ← Top-level orchestrator
│   ├── rider_controller.py              ← Rider input validation
│   ├── bike_controller.py               ← Bike input validation
│   ├── video_controller.py              ← Video loading + validation
│   ├── pose_controller.py               ← MediaPipe in QThread
│   └── analysis_controller.py           ← Angle computation + recommendations
│
├── services/                            ← Shared business logic
│   ├── __init__.py
│   ├── video_service.py                 ← OpenCV video helpers
│   ├── pose_service.py                  ← MediaPipe wrapper
│   ├── angle_calculator.py              ← Geometric angle math
│   ├── fit_rules_engine.py              ← Rule-based scoring + recommendations
│   └── persistence_service.py           ← JSON save/load
│
└── tests/                               ← Unit tests
    ├── __init__.py
    ├── test_rider_model.py
    ├── test_analysis_model.py
    ├── test_angle_calculator.py
    └── test_fit_rules_engine.py
```

---

## 4. Architecture: MVC Pattern

The application strictly separates concerns into three layers:

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                │
│                    (clicks, types, uploads)                  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────┐        ┌──────────────────────────┐
│      VIEWS           │        │     CONTROLLERS          │
│  (PyQt6 Widgets)     │◄──────►│  (Logic Glue)            │
│                      │signals │                          │
│  • MainWindow        │& slots │  • AppController         │
│  • RiderInputView    │        │  • RiderController       │
│  • BikeInputView     │        │  • BikeController        │
│  • VideoCaptureView  │        │  • VideoController       │
│  • AnalysisView      │        │  • PoseController        │
│  • ResultsView       │        │  • AnalysisController    │
└──────────────────────┘        └─────────┬────────────────┘
                                          │
                                          │ reads/writes
                                          ▼
                                ┌──────────────────────────┐
                                │      MODELS              │
                                │  (Dataclasses)           │
                                │                          │
                                │  • RiderMeasurements     │
                                │  • BikeGeometry          │
                                │  • PoseSequence          │
                                │  • CyclingAngles         │
                                │  • FitScore              │
                                │  • Recommendation        │
                                └─────────┬────────────────┘
                                          │
                                          │ uses
                                          ▼
                                ┌──────────────────────────┐
                                │      SERVICES            │
                                │  (Business Logic)        │
                                │                          │
                                │  • video_service         │
                                │  • pose_service          │
                                │  • angle_calculator      │
                                │  • fit_rules_engine      │
                                │  • persistence_service   │
                                └──────────────────────────┘
```

### Key Rule

> **Views never import Controllers.** Controllers connect to View signals during initialization. Views only emit signals; Controllers listen and act.

---

## 5. Startup Sequence

```
main.py
  │
  ├── QApplication created
  ├── Global font set ("Segoe UI", 11)
  ├── app.qss stylesheet loaded and applied
  │
  ├── MainWindow() created
  │   ├── Creates RiderInputView     (index 0 in QStackedWidget)
  │   ├── Creates BikeInputView      (index 1)
  │   ├── Creates VideoCaptureView   (index 2)
  │   ├── Creates AnalysisView       (index 3)
  │   ├── Creates ResultsView        (index 4)
  │   ├── Builds sidebar QListWidget with 5 page labels
  │   ├── Sets up File menu (New, Open, Save, Export PDF)
  │   └── Sets up status bar
  │
  ├── AppController(window) created
  │   ├── Creates empty RiderMeasurements model
  │   ├── Creates empty BikeGeometry model
  │   ├── Creates RiderController(rider_view, rider_model)
  │   │     └── Connects rider_view.rider_data_submitted → _on_data_submitted
  │   ├── Creates BikeController(bike_view, bike_model)
  │   │     └── Connects bike_view.bike_data_submitted → _on_data_submitted
  │   ├── Creates VideoController(video_view)
  │   │     └── Connects video_view.video_ready → _on_video_ready
  │   ├── Creates PoseController(analysis_view)
  │   ├── Creates AnalysisController(results_view)
  │   │
  │   ├── Wires callbacks:
  │   │     rider_ctrl.on_valid    → app._on_rider_valid
  │   │     bike_ctrl.on_valid     → app._on_bike_valid
  │   │     video_ctrl.on_valid    → app._on_video_valid
  │   │     pose_ctrl.on_complete  → app._on_pose_complete
  │   │     analysis_ctrl.on_complete → app._on_analysis_complete
  │   │
  │   ├── Wires menu signals:
  │   │     window.new_session_requested  → app._new_session
  │   │     window.save_session_requested → app._save
  │   │     window.load_session_requested → app._load
  │   │     window.export_pdf_requested   → app._export_pdf
  │   │     results_view.restart_requested → app._new_session
  │   │     results_view.export_requested  → app._export_pdf
  │   │
  │   └── Loads angle_ranges.json for current riding style → analysis_view gauges
  │
  ├── window.show()
  └── app.exec() ← Qt event loop starts
```

---

## 6. User Flow (Step by Step)

```
╔═══════════════════════════════════════════════════════════════════╗
║  STEP 1: RIDER                                                   ║
║  ┌────────────────────────────────────────────────────────┐       ║
║  │  Enter: name, height, weight, inseam, foot size,      │       ║
║  │         arm length, torso length, shoulder width       │       ║
║  │  Select: flexibility (low/med/high)                    │       ║
║  │  Select: riding style (road/tt/mtb/gravel/commute)    │       ║
║  │  Click: [Next →]                                       │       ║
║  └─────────────────────────────┬──────────────────────────┘       ║
║                                │ rider_data_submitted signal      ║
║                                ▼                                  ║
║  RiderController validates → RiderMeasurements model created      ║
║  AppController._on_rider_valid() → navigate to BIKE page          ║
╠═══════════════════════════════════════════════════════════════════╣
║  STEP 2: BIKE                                                     ║
║  ┌────────────────────────────────────────────────────────┐       ║
║  │  Enter: frame size, saddle height, setback, reach,     │       ║
║  │         drop, crank length, stem length, stem angle    │       ║
║  │  Click: [Next →] or [Skip →]                           │       ║
║  └─────────────────────────────┬──────────────────────────┘       ║
║                                │ bike_data_submitted signal       ║
║                                ▼                                  ║
║  BikeController validates → BikeGeometry model created            ║
║  AppController._on_bike_valid() → navigate to VIDEO page          ║
╠═══════════════════════════════════════════════════════════════════╣
║  STEP 3: VIDEO                                                    ║
║  ┌────────────────────────────────────────────────────────┐       ║
║  │  Click: [Upload Video] → file dialog opens             │       ║
║  │  Video preview loads in VideoPlayer widget              │       ║
║  │  Can: play/pause, scrub, step frame-by-frame           │       ║
║  │  Click: [Analyze →]                                     │       ║
║  └─────────────────────────────┬──────────────────────────┘       ║
║                                │ video_ready signal (file path)   ║
║                                ▼                                  ║
║  VideoController validates duration (5–120s)                      ║
║  AppController._on_video_valid() → navigate to ANALYSIS page      ║
║                               + starts PoseController             ║
╠═══════════════════════════════════════════════════════════════════╣
║  STEP 4: ANALYSIS (automatic — user watches)                      ║
║  ┌────────────────────────────────────────────────────────┐       ║
║  │  Progress bar filling as frames are processed          │       ║
║  │  Video shows skeleton overlay (green bones)            │       ║
║  │  Side gauges update in real-time:                      │       ║
║  │    🟢 Knee Extension  🟢 Hip Angle  🟡 Back Angle     │       ║
║  │    🟢 Ankle Angle     🔴 Elbow Angle                  │       ║
║  └─────────────────────────────┬──────────────────────────┘       ║
║                                │ PoseWorker.finished signal       ║
║                                ▼                                  ║
║  PoseController → PoseSequence complete                           ║
║  AppController._on_pose_complete() → runs AnalysisController      ║
║  AnalysisController.analyze() → computes angles → FitScore        ║
║  → generates Recommendations → pushes to ResultsView              ║
║  AppController._on_analysis_complete() → navigate to RESULTS page ║
╠═══════════════════════════════════════════════════════════════════╣
║  STEP 5: RESULTS                                                  ║
║  ┌────────────────────────────────────────────────────────┐       ║
║  │  Overall Score: 78/100  [GOOD]                         │       ║
║  │  Per-area: Knee 90 | Hip 75 | Back 80 | Ankle 65 |    │       ║
║  │                                         Reach 70      │       ║
║  │                                                        │       ║
║  │  Recommendation Cards (sorted by severity):            │       ║
║  │  🔴 CRITICAL: Saddle Height                            │       ║
║  │     "Raise saddle by approximately 12mm"               │       ║
║  │  🟠 MODERATE: Handlebar Position                       │       ║
║  │     "Lower handlebars or use a longer stem"            │       ║
║  │  🟡 MINOR: Cleat Position                              │       ║
║  │     "Reduce toe pointing — check cleat position"       │       ║
║  │  ✅ OPTIMAL: Stem Length                                │       ║
║  │     "Reach and elbow bend are comfortable"             │       ║
║  │                                                        │       ║
║  │  [📄 Export PDF]    [🔄 Start Over]                    │       ║
║  └────────────────────────────────────────────────────────┘       ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 7. Data Flow Diagrams

### 7.1 Main Data Pipeline

```
User Input               Computer Vision              Math                  Rules Engine
──────────               ───────────────              ────                  ────────────

RiderMeasurements ──┐
                    │
BikeGeometry ───────┤
                    │
Video File ─────────┤
       │            │
       ▼            │
  ┌──────────┐      │
  │ OpenCV   │      │
  │ Frames   │      │
  └────┬─────┘      │
       │            │
       ▼            │
  ┌──────────┐      │
  │MediaPipe │      │
  │ Pose     │      │
  └────┬─────┘      │
       │            │
       ▼            │
  PoseSequence      │
  [PoseFrame]       │
  [BodyLandmark]    │
       │            │
       ▼            │
  ┌──────────────┐  │
  │ angle_       │  │
  │ calculator   │  │    ┌────────────────┐     ┌──────────────┐
  │              │──┼───►│ CyclingAngles  │────►│ fit_rules_   │
  │ per-frame    │  │    │ (aggregated)   │     │ engine       │
  │ angles       │  │    └────────────────┘     │              │
  └──────────────┘  │                           │ + riding     │
                    │                           │   style      │◄── angle_ranges.json
                    │                           │ + ideal      │
                    │                           │   ranges     │
                    │                           └──────┬───────┘
                    │                                  │
                    │                      ┌───────────┴──────────┐
                    │                      │                      │
                    │                      ▼                      ▼
                    │               ┌──────────┐          ┌──────────────┐
                    │               │ FitScore │          │ list of      │
                    │               │ (0–100)  │          │ Recommendation│
                    │               └──────────┘          └──────────────┘
                    │                      │                      │
                    │                      ▼                      ▼
                    │               ┌──────────────────────────────┐
                    └──────────────►│        ResultsView           │
                                    │  gauges + recommendation     │
                                    │  cards                       │
                                    └──────────────────────────────┘
```

### 7.2 Signal Flow Between Components

```
┌──────────────┐  rider_data_submitted(dict)  ┌──────────────────┐  callback  ┌────────────────┐
│RiderInputView├─────────────────────────────►│ RiderController  ├──────────►│ AppController  │
└──────────────┘                              └──────────────────┘           │                │
                                                                             │  navigate_to   │
┌──────────────┐  bike_data_submitted(dict)   ┌──────────────────┐  callback │  (PAGE_BIKE)   │
│BikeInputView ├─────────────────────────────►│ BikeController   ├──────────►│                │
└──────────────┘                              └──────────────────┘           │  navigate_to   │
                                                                             │  (PAGE_VIDEO)  │
┌──────────────┐  video_ready(str)            ┌──────────────────┐  callback │                │
│VideoCaptureV ├─────────────────────────────►│ VideoController  ├──────────►│  navigate_to   │
└──────────────┘                              └──────────────────┘           │  (PAGE_ANALYSIS│
                                                                             │  + start pose) │
┌──────────────┐  progress(int,str)           ┌──────────────────┐  callback │                │
│PoseWorker    ├─────────────────────────────►│ PoseController   ├──────────►│  run analysis  │
│ (QThread)    │  frame_processed(...)        │                  │           │                │
│              │  finished(PoseSequence)      │                  │           │                │
└──────────────┘                              └──────────────────┘           │                │
                                                                             │                │
┌──────────────┐  set_scores()                ┌──────────────────┐  callback │  navigate_to   │
│ResultsView   │◄─────────────────────────────┤AnalysisController├──────────►│  (PAGE_RESULTS)│
│              │  set_recommendations()       └──────────────────┘           └────────────────┘
│              │
│              ├──restart_requested────────────────────────────────────────►AppController._new_session
│              └──export_requested─────────────────────────────────────────►AppController._export_pdf
```

---

## 8. Layer 1 — Models (Data & Validation)

### 8.1 `models/rider_model.py`

| Component | Description |
|---|---|
| **`Flexibility`** (Enum) | `LOW`, `MEDIUM`, `HIGH` — rider's body flexibility level |
| **`RidingStyle`** (Enum) | `ROAD`, `TT`, `MTB`, `GRAVEL`, `COMMUTE` — determines ideal angle ranges |
| **`RiderMeasurements`** (@dataclass) | Central rider data container |

**Fields:**

| Field | Type | Range | Purpose |
|---|---|---|---|
| `height_cm` | float | 100–250 | Total body height |
| `weight_kg` | float | 30–200 | Body weight |
| `inseam_cm` | float | 50–120 | Floor to crotch (key for saddle height) |
| `foot_size_eu` | float | 30–55 | EU shoe size |
| `arm_length_cm` | float | 40–90 | Shoulder to wrist |
| `torso_length_cm` | float | 30–80 | Hip to shoulder |
| `shoulder_width_cm` | float | 25–60 | Shoulder-to-shoulder |
| `flexibility` | Flexibility | enum | Affects ideal angle ranges |
| `riding_style` | RidingStyle | enum | Selects which angle_ranges profile to use |
| `name` | Optional[str] | — | Optional display name |

**Methods:**

| Method | Returns | Description |
|---|---|---|
| `validate()` | `list[str]` | Checks all numeric fields against `_RANGES`. Returns error messages. |
| `is_valid` (property) | `bool` | `True` if `validate()` returns empty list |
| `estimated_saddle_height` (property) | `float` | LeMond formula: `inseam × 0.883` |
| `to_dict()` | `dict` | Serializes to dict (enums → strings) |
| `from_dict(data)` (classmethod) | `RiderMeasurements` | Deserializes from dict |

---

### 8.2 `models/bike_model.py`

| Component | Description |
|---|---|
| **`BikeGeometry`** (@dataclass) | Bike frame & component measurements |

**Fields:**

| Field | Type | Default | Purpose |
|---|---|---|---|
| `frame_size_cm` | float | 0.0 | Seat tube length |
| `saddle_height_cm` | float | 0.0 | BB center to saddle top |
| `saddle_setback_cm` | float | 0.0 | Horizontal offset behind BB |
| `handlebar_reach_cm` | float | 0.0 | Saddle to handlebar |
| `handlebar_drop_cm` | float | 0.0 | Vertical drop |
| `crank_length_mm` | float | 172.5 | Crank arm length |
| `stem_length_mm` | float | 100.0 | Stem length |
| `stem_angle_deg` | float | -6.0 | Stem angle (negative = drop) |

**Methods:** `validate()`, `is_valid`, `to_dict()`, `from_dict()` — same pattern as RiderMeasurements. Note: fields at `0.0` skip validation (user may not know them).

---

### 8.3 `models/pose_model.py`

| Component | Description |
|---|---|
| **`BodyLandmark`** (@dataclass) | Single joint point from MediaPipe |
| **`PoseFrame`** (@dataclass) | All landmarks for one video frame |
| **`PoseSequence`** (@dataclass) | Ordered collection of PoseFrames |

**BodyLandmark fields:** `name`, `x` (0–1), `y` (0–1), `z` (depth), `visibility` (0–1 confidence).

**PoseFrame methods:**

| Method | Returns | Description |
|---|---|---|
| `get(name)` | `BodyLandmark \| None` | Lookup landmark by name (e.g., "left_knee") |
| `is_complete` (property) | `bool` | `True` if all 8 cycling-critical left-side landmarks have visibility > 0.5 |

Required landmarks for `is_complete`: `left_hip`, `left_knee`, `left_ankle`, `left_shoulder`, `left_elbow`, `left_wrist`, `left_heel`, `left_foot_index`.

**PoseSequence methods:**

| Method | Returns | Description |
|---|---|---|
| `add_frame(frame)` | None | Appends a PoseFrame |
| `duration_sec` (property) | `float` | total_frames / fps |
| `valid_frames` (property) | `list[PoseFrame]` | Filters to only `is_complete` frames |

---

### 8.4 `models/analysis_model.py`

| Component | Description |
|---|---|
| **`CyclingAngles`** (@dataclass) | Aggregated angles across the pedal stroke |
| **`FitScore`** (@dataclass) | Per-area and overall scores |

**CyclingAngles fields:**

| Field | Ideal (Road) | Meaning |
|---|---|---|
| `knee_extension_min` | 140–150° | At bottom dead centre (BDC) |
| `knee_extension_max` | — | At top dead centre (TDC) |
| `knee_flexion_max` | 65–75° | Max knee bend at TDC |
| `hip_angle_min` | 40–55° | Torso-thigh angle at TDC |
| `back_angle` | 35–45° | Torso vs horizontal (mean) |
| `ankle_angle_min/max` | 90–120° | Through pedal stroke |
| `elbow_angle` | 150–165° | Elbow bend (mean) |

**FitScore fields & properties:**

| Field | Type | Description |
|---|---|---|
| `overall` | float | Weighted average 0–100 |
| `knee_score` | float | 0–100 |
| `hip_score` | float | 0–100 |
| `back_score` | float | 0–100 |
| `ankle_score` | float | 0–100 |
| `reach_score` | float | 0–100 |
| `category` (property) | str | "excellent" (≥90), "good" (≥75), "fair" (≥55), "poor" (<55) |
| `category_color` (property) | str | Hex color for the category |

---

### 8.5 `models/recommendation_model.py`

| Component | Description |
|---|---|
| **`Severity`** (Enum) | `OPTIMAL`, `MINOR`, `MODERATE`, `CRITICAL` — each has `.color` and `.icon` |
| **`Recommendation`** (@dataclass) | Single actionable bike-fit adjustment |

**Recommendation fields:**

| Field | Example |
|---|---|
| `component` | `"saddle_height"` |
| `severity` | `Severity.CRITICAL` |
| `current_value` | `"128.5°"` |
| `ideal_range` | `"140–150°"` |
| `adjustment` | `"Raise saddle by approximately 29 mm"` |
| `explanation` | `"Knee extension at the bottom..."` |
| `display_name` (property) | `"Saddle Height"` (auto-formatted) |

---

## 9. Layer 2 — Views (PyQt6 UI)

### 9.1 `views/main_window.py` — `MainWindow(QMainWindow)`

The **top-level window**. Contains:

- **Menu bar**: File (New `Ctrl+N`, Open `Ctrl+O`, Save `Ctrl+S`, Export PDF) + Help (About)
- **Sidebar** (200px wide): `QListWidget` with 5 page entries (👤 Rider, 🚲 Bike, 🎥 Video, 📐 Analysis, 📊 Results)
- **Content area**: `QStackedWidget` holding all 5 page views
- **Status bar**: Shows context messages

**Signals emitted:**

| Signal | Trigger |
|---|---|
| `page_changed(int)` | User clicks sidebar item |
| `new_session_requested()` | File → New Session |
| `save_session_requested()` | File → Save Session |
| `load_session_requested()` | File → Open Session |
| `export_pdf_requested()` | File → Export PDF |

**Key methods:**

| Method | Description |
|---|---|
| `navigate_to(index)` | Programmatically switch to page 0–4 |
| `set_status(message)` | Update status bar text |

---

### 9.2 `views/rider_input_view.py` — `RiderInputView(QWidget)`

Form with 7 `MeasurementInput` widgets, 2 `QComboBox` dropdowns, and a `QLineEdit` for name.

**Signal:** `rider_data_submitted(dict)` — emitted when user clicks "Next →".

**Methods:**

| Method | Description |
|---|---|
| `get_data()` → `dict` | Reads all form values into a flat dict |
| `set_data(dict)` | Populates form from dict (for session loading) |
| `show_errors(list[str])` | Shows `QMessageBox.warning` with validation errors |

---

### 9.3 `views/bike_input_view.py` — `BikeInputView(QWidget)`

Same pattern as RiderInputView. Has "Skip →" button that emits an empty dict (all defaults kept).

**Signal:** `bike_data_submitted(dict)`

---

### 9.4 `views/video_capture_view.py` — `VideoCaptureView(QWidget)`

- Tips panel with filming guidelines
- Embedded `VideoPlayer` widget
- "Upload Video" button → `QFileDialog`
- "Analyze →" button (disabled until video loaded)

**Signal:** `video_ready(str)` — emits the file path of the selected video.

**Properties:** `video_path`, `player`

---

### 9.5 `views/analysis_view.py` — `AnalysisView(QWidget)`

Split layout:
- **Left (75%)**: `VideoPlayer` showing skeleton-overlaid frames
- **Right (25%)**: 5 `AngleGauge` widgets (Knee Extension, Hip, Back, Ankle, Elbow)
- **Top**: Progress bar + progress label

**Methods:**

| Method | Description |
|---|---|
| `set_progress(value, text)` | Updates progress bar (0–100) and label |
| `update_gauges(knee, hip, back, ankle, elbow)` | Sets gauge values |
| `set_ideal_ranges(dict)` | Updates green/yellow/red zones on gauges per riding style |

---

### 9.6 `views/results_view.py` — `ResultsView(QWidget)`

- 6 `AngleGauge` widgets repurposed as 0–100 score gauges (overall + 5 areas)
- Category label ("EXCELLENT", "GOOD", "FAIR", "POOR") with color
- Scrollable list of `Recommendation` cards (colored severity border, icon, adjustment text, explanation)
- "Export PDF" and "Start Over" buttons

**Signals:** `export_requested()`, `restart_requested()`

**Methods:**

| Method | Description |
|---|---|
| `set_scores(FitScore)` | Populates all score gauges + category label |
| `set_recommendations(list[Recommendation])` | Clears and rebuilds recommendation cards |

---

### 9.7 Custom Widgets

#### `widgets/measurement_input.py` — `MeasurementInput(QWidget)`

A horizontal row: `QLabel` (field name, 140px) + `QDoubleSpinBox` (with unit suffix) + stretch.

| API | Description |
|---|---|
| `value` (property, getter/setter) | Get/set the numeric value |
| `value_changed` (signal) | Emitted when value changes |
| `set_unit(str)` | Change the unit suffix |

#### `widgets/angle_gauge.py` — `AngleGauge(QWidget)`

Custom-painted circular arc gauge. Shows a value on a 0–180° arc with color zones:
- 🟢 Green: value within `[ideal_min, ideal_max]`
- 🟡 Yellow: value within ±50% of range width
- 🔴 Red: value far outside range

| API | Description |
|---|---|
| `set_value(float)` | Update displayed value + repaint |
| `set_range(ideal_min, ideal_max)` | Update green zone boundaries |
| `severity_color` (property) | Current color based on value vs range |

#### `widgets/video_player.py` — `VideoPlayer(QWidget)`

Renders OpenCV frames via `QPixmap` in a `QLabel`. Includes play/pause, prev/next frame, scrub slider.

| API | Description |
|---|---|
| `load_video(path)` → `bool` | Open video with OpenCV |
| `set_overlay(frame)` | Display an annotated frame (e.g., with skeleton) |
| `toggle_play()` / `play()` / `pause()` / `stop()` | Playback controls |
| `seek(frame_number)` | Jump to specific frame |
| `frame_changed` (signal) | Emits `(frame_number, np.ndarray)` |

---

## 10. Layer 3 — Controllers (Logic Glue)

### 10.1 `controllers/app_controller.py` — `AppController`

**The brain of the application.** Created once at startup. Owns all sub-controllers and manages the navigation state machine.

```
__init__(window: MainWindow)
```

Creates all sub-controllers, wires all callbacks and menu signals.

**Navigation flow methods (private):**

| Method | Triggered By | Action |
|---|---|---|
| `_on_rider_valid(rider)` | RiderController callback | Store rider model, update status bar, navigate → BIKE |
| `_on_bike_valid(bike)` | BikeController callback | Store bike model, navigate → VIDEO |
| `_on_video_valid(path, info)` | VideoController callback | Navigate → ANALYSIS, start `PoseController` |
| `_on_pose_complete(sequence)` | PoseController callback | Run `AnalysisController.analyze()` |
| `_on_analysis_complete(score, recs)` | AnalysisController callback | Navigate → RESULTS |

**Action methods (private):**

| Method | Triggered By | Action |
|---|---|---|
| `_new_session()` | Menu or "Start Over" | Reset all models, navigate → RIDER |
| `_save()` | Menu Ctrl+S | Call `persistence_service.save_session()` |
| `_load()` | Menu Ctrl+O | File dialog → `persistence_service.load_session()` → populate views |
| `_export_pdf()` | Menu or button | Placeholder (future) |
| `_update_analysis_ranges()` | On rider change | Load `angle_ranges.json` for riding style → update gauge ranges |

---

### 10.2 `controllers/rider_controller.py` — `RiderController`

```
__init__(view: RiderInputView, model: RiderMeasurements)
```

Connects `view.rider_data_submitted` → `_on_data_submitted`.

| Method | Description |
|---|---|
| `_on_data_submitted(dict)` | Creates `RiderMeasurements` from dict, validates, shows errors or calls `_on_valid_callback` |
| `set_on_valid(callback)` | Register callback for valid data |
| `load(model)` | Populate view from existing model |

---

### 10.3 `controllers/bike_controller.py` — `BikeController`

Same pattern. Additionally has `suggest_saddle_height(inseam) → float` (LeMond formula). Empty dict input = skip (keep defaults).

---

### 10.4 `controllers/video_controller.py` — `VideoController`

```
__init__(view: VideoCaptureView)
```

Connects `view.video_ready` → `_on_video_ready`.

| Method | Description |
|---|---|
| `_on_video_ready(path)` | Calls `video_service.get_video_info()`, validates duration (5–120s), warns user, calls `_on_valid_callback(path, info)` |

---

### 10.5 `controllers/pose_controller.py` — `PoseController` + `PoseWorker`

**Two classes working together:**

**`PoseWorker(QObject)`** — runs in a `QThread`:

| Signal | Emits | When |
|---|---|---|
| `progress(int, str)` | percentage + message | Every sampled frame |
| `frame_processed(int, PoseFrame, ndarray)` | frame data + annotated image | After each pose detection |
| `finished(PoseSequence)` | complete sequence | When all frames processed |
| `error(str)` | error message | On failure |

**`PoseWorker.run()` algorithm:**
1. Open video with OpenCV
2. Read metadata (fps, total frames, dimensions)
3. Create empty `PoseSequence`
4. Create `PoseDetector` (MediaPipe wrapper)
5. Loop through frames (taking every `FRAME_SAMPLE_RATE`-th frame):
   - Run `detector.detect(frame)` → `PoseFrame`
   - If detected: add to sequence, draw skeleton, emit `frame_processed`
   - Emit `progress` with percentage
6. Release video, close detector
7. Emit `finished(sequence)`

**`PoseController`** — manages the worker lifecycle:

| Method | Description |
|---|---|
| `start_analysis(video_path)` | Creates QThread + PoseWorker, wires signals, starts thread |
| `stop()` | Stops worker, quits thread |
| `set_on_complete(callback)` | Register callback for when sequence is ready |

---

### 10.6 `controllers/analysis_controller.py` — `AnalysisController`

```
__init__(results_view: ResultsView)
```

**`analyze(sequence, rider, bike)` algorithm:**

```
1. For each valid PoseFrame in sequence:
   └── compute_frame_angles(pose_frame) → dict of 6 angle values
       (knee_extension, hip_angle, back_angle, ankle_angle, elbow_angle, shoulder_angle)

2. aggregate_angles(all_frame_dicts) → CyclingAngles
   └── Min/max/mean per angle across all frames

3. evaluate_fit(cycling_angles, riding_style) → (FitScore, list[Recommendation])
   └── Compares each angle against ideal ranges from angle_ranges.json
   └── Computes weighted overall score
   └── Generates adjustment text per component

4. Push to ResultsView:
   └── results_view.set_scores(fit_score)
   └── results_view.set_recommendations(recommendations)

5. Call _on_complete_callback(fit_score, recommendations)
```

---

## 11. Layer 4 — Services (Business Logic & I/O)

### 11.1 `services/video_service.py`

| Function | Signature | Description |
|---|---|---|
| `get_video_info(path)` | `→ VideoInfo \| None` | Reads metadata (width, height, fps, frame count, codec) without loading all frames |
| `load_video(path)` | `→ cv2.VideoCapture` | Opens video, raises `FileNotFoundError` if fails |
| `extract_frames(cap, sample_rate, max_frames)` | `→ list[ndarray]` | Reads frames at given sample rate |
| `save_frame(frame, path)` | `→ None` | Writes single frame as image file |

**`VideoInfo`** dataclass: `path`, `width`, `height`, `fps`, `frame_count`, `duration_sec`, `codec`.

---

### 11.2 `services/pose_service.py` — `PoseDetector`

Wraps `mediapipe.solutions.pose`.

**Landmark mapping** (17 cycling-relevant points):
```
 0 → nose
11 → left_shoulder    12 → right_shoulder
13 → left_elbow       14 → right_elbow
15 → left_wrist       16 → right_wrist
23 → left_hip         24 → right_hip
25 → left_knee        26 → right_knee
27 → left_ankle       28 → right_ankle
29 → left_heel        30 → right_heel
31 → left_foot_index  32 → right_foot_index
```

| Method | Signature | Description |
|---|---|---|
| `detect(frame, frame_number, timestamp_ms)` | `→ PoseFrame \| None` | Run MediaPipe on BGR frame → PoseFrame with BodyLandmarks |
| `draw_skeleton(frame)` | `→ ndarray` | Draw green skeleton overlay on a copy of the frame |
| `close()` | `→ None` | Release MediaPipe resources |

---

### 11.3 `services/angle_calculator.py`

**Core geometry functions:**

| Function | Points | Formula | Ideal (Road) |
|---|---|---|---|
| `calculate_knee_extension(hip, knee, ankle)` | Angle at **knee** | 3-point angle | 140–150° at BDC |
| `calculate_hip_angle(shoulder, hip, knee)` | Angle at **hip** | 3-point angle | 40–55° |
| `calculate_back_angle(shoulder, hip)` | **Torso** vs horizontal | `atan2(dy, dx)` | 35–45° |
| `calculate_ankle_angle(knee, ankle, toe)` | Angle at **ankle** | 3-point angle | 90–120° |
| `calculate_elbow_angle(shoulder, elbow, wrist)` | Angle at **elbow** | 3-point angle | 150–165° |
| `calculate_shoulder_angle(hip, shoulder, elbow)` | Angle at **shoulder** | 3-point angle | — |

**Internal helpers:**

| Function | Description |
|---|---|
| `_angle_3p(p1, p2, p3)` | Angle at p2 using dot product / arccos. Returns 0–180°. |
| `_angle_to_horizontal(p1, p2)` | Absolute angle of the line p1→p2 vs horizontal |
| `_lm_xy(landmark)` | Extract `(x, y)` tuple from BodyLandmark |

**Aggregation functions:**

| Function | Description |
|---|---|
| `compute_frame_angles(PoseFrame)` | Calls all 6 angle functions for one frame → `dict[str, float]` or `None` |
| `aggregate_angles(list[dict])` | Min/max/mean across all frames → `CyclingAngles` dataclass |

---

### 11.4 `services/fit_rules_engine.py`

The **recommendation brain**. Takes `CyclingAngles` + riding style → `FitScore` + `list[Recommendation]`.

**Internal helpers:**

| Function | Description |
|---|---|
| `_load_ranges()` | Reads `config/angle_ranges.json` |
| `_severity_from_deviation(dev, range_width)` | Maps deviation ratio → Severity enum: 0→OPTIMAL, ≤0.5→MINOR, ≤1.0→MODERATE, >1.0→CRITICAL |
| `_score_single(value, min, max)` | Scores a single value: 100 if in range, else `100 - (deviation/range_width × 40)` clamped to 0 |

**Main function:**

```python
evaluate_fit(angles: CyclingAngles, riding_style: str) → (FitScore, list[Recommendation])
```

**Evaluation for each body area:**

| Area | Angle Used | Component | Adjustment Logic |
|---|---|---|---|
| **Knee** | `knee_extension_min` (at BDC) | `saddle_height` | Low → "Raise saddle by N mm" (N = deviation × 2.5) |
| **Hip** | `hip_angle_min` (at TDC) | `saddle_setback` | Low → "Move saddle back or raise handlebars" |
| **Back** | `back_angle` (mean) | `handlebar_position` | Low → "Raise handlebars or shorter stem" |
| **Ankle** | Average of min+max | `cleat_position` | Low → "Reduce toe pointing" |
| **Elbow** | `elbow_angle` (mean) | `stem_length` | Low → "Stem too long — shorter stem" |

**Overall score formula:**
$$\text{overall} = \frac{\sum_{area} (\text{area\_score} \times \text{weight}_{area})}{\sum \text{weights}}$$

Weights from `angle_ranges.json` (default road): knee=30, hip=20, back=15, ankle=10, elbow=5. Total=80.

---

### 11.5 `services/persistence_service.py`

| Function | Description |
|---|---|
| `save_session(rider, bike, fit_score?, path?)` | Writes JSON to `~/.myvelofit/sessions/<name>_<timestamp>.json` |
| `load_session(path)` | Reads JSON → dict with `RiderMeasurements`, `BikeGeometry`, optional `FitScore` |

**JSON format:**
```json
{
  "version": "1.0",
  "timestamp": "2026-02-17T14:30:00",
  "rider": { "height_cm": 180, "weight_kg": 75, ... },
  "bike": { "frame_size_cm": 56, ... },
  "fit_score": { "overall": 78, "knee_score": 90, ... }
}
```

---

## 12. Configuration

### 12.1 `config/__init__.py` (Settings)

| Constant | Value | Purpose |
|---|---|---|
| `APP_NAME` | `"myBikeFit"` | Window title |
| `APP_VERSION` | `"1.0.0"` | Displayed in title & about |
| `DEFAULT_UNITS` | `"metric"` | Metric/imperial toggle |
| `VIDEO_MAX_DURATION_SEC` | `120` | Max video length |
| `VIDEO_MIN_DURATION_SEC` | `5` | Min video length |
| `POSE_MODEL_COMPLEXITY` | `2` | MediaPipe accuracy (0=lite, 1=full, 2=heavy) |
| `POSE_MIN_DETECTION_CONFIDENCE` | `0.5` | MediaPipe threshold |
| `POSE_MIN_TRACKING_CONFIDENCE` | `0.5` | MediaPipe threshold |
| `FRAME_SAMPLE_RATE` | `2` | Process every Nth frame |
| `ANGLE_SMOOTHING_WINDOW` | `5` | Rolling average window |
| `MIN_PEDAL_CYCLES` | `3` | Minimum cycles for stable analysis |
| `AUTOSAVE_DIR` | `~/.myvelofit/sessions` | Session file location |
| `WINDOW_MIN_WIDTH` | `1200` | Minimum window size |
| `WINDOW_MIN_HEIGHT` | `800` | Minimum window size |
| `SIDEBAR_WIDTH` | `200` | Navigation sidebar width |

### 12.2 `config/angle_ranges.json`

Ideal angle ranges per riding style. Each angle has `min`, `max`, and `weight` for scoring.

| Angle | Road | MTB | TT |
|---|---|---|---|
| knee_extension | 140–150° (w=30) | 135–150° | 142–152° |
| knee_flexion_max | 65–75° (w=20) | 65–80° | 60–72° |
| hip_angle | 40–55° (w=20) | 45–65° | 30–45° |
| back_angle | 35–45° (w=15) | 40–55° | 15–30° |
| ankle_angle | 90–120° (w=10) | 85–120° | 90–115° |
| elbow_angle | 150–165° (w=5) | 145–170° | 85–100° |

Also includes `gravel` and `commute` profiles.

---

## 13. Signal & Slot Wiring Map

Complete map of every PyQt6 signal → slot connection:

```
SIGNAL                                        SLOT / CALLBACK
─────────────────────────────────────────     ──────────────────────────────────────

MainWindow._nav_list.currentRowChanged    →   MainWindow._on_page_selected (switches QStackedWidget)
MainWindow.new_session_requested          →   AppController._new_session
MainWindow.save_session_requested         →   AppController._save
MainWindow.load_session_requested         →   AppController._load
MainWindow.export_pdf_requested           →   AppController._export_pdf

RiderInputView._btn_next.clicked          →   RiderInputView._on_submit
RiderInputView.rider_data_submitted       →   RiderController._on_data_submitted
RiderController._on_valid_callback        →   AppController._on_rider_valid

BikeInputView._btn_next.clicked           →   BikeInputView._on_submit
BikeInputView._btn_skip.clicked           →   lambda: bike_data_submitted.emit({})
BikeInputView.bike_data_submitted         →   BikeController._on_data_submitted
BikeController._on_valid_callback         →   AppController._on_bike_valid

VideoCaptureView._btn_upload.clicked      →   VideoCaptureView._on_upload
VideoCaptureView._btn_analyze.clicked     →   VideoCaptureView._on_analyze
VideoCaptureView.video_ready              →   VideoController._on_video_ready
VideoController._on_valid_callback        →   AppController._on_video_valid

PoseWorker.progress                       →   PoseController._on_progress → AnalysisView.set_progress
PoseWorker.frame_processed                →   PoseController._on_frame → AnalysisView.player.set_overlay
PoseWorker.finished                       →   PoseController._on_finished → PoseController._on_complete_callback
PoseWorker.finished                       →   QThread.quit
PoseWorker.error                          →   PoseController._on_error (QMessageBox)
PoseController._on_complete_callback      →   AppController._on_pose_complete

AnalysisController._on_complete_callback  →   AppController._on_analysis_complete

ResultsView.export_requested              →   AppController._export_pdf
ResultsView.restart_requested             →   AppController._new_session

VideoPlayer._timer.timeout                →   VideoPlayer._next_frame (internal playback)
VideoPlayer._btn_play.clicked             →   VideoPlayer.toggle_play
VideoPlayer._slider.sliderMoved           →   VideoPlayer.seek
VideoPlayer.frame_changed                 →   (available for external use)

MeasurementInput._spin.valueChanged       →   MeasurementInput.value_changed
```

---

## 14. Threading Model

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN THREAD (Qt Event Loop)                                    │
│                                                                 │
│  • All UI rendering                                             │
│  • Signal/slot delivery                                         │
│  • User interaction handling                                    │
│  • Controller logic (instantaneous)                             │
│  • Analysis scoring (fast — no I/O)                             │
│                                                                 │
│  NEVER: OpenCV video reading, MediaPipe inference               │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ signals (thread-safe in Qt)
                          │
┌─────────────────────────────────────────────────────────────────┐
│  WORKER THREAD (QThread)                                        │
│                                                                 │
│  • PoseWorker.run():                                            │
│    - cv2.VideoCapture frame-by-frame reading                    │
│    - MediaPipe Pose inference per frame                         │
│    - Skeleton drawing                                           │
│    - Emits progress/frame_processed/finished signals            │
│                                                                 │
│  Started by:  PoseController.start_analysis()                   │
│  Stopped by:  PoseController.stop() or worker reaches end       │
└─────────────────────────────────────────────────────────────────┘
```

**Why threading matters:** MediaPipe processes each frame in ~20–100ms (model complexity 2). A 30fps, 30-second video = 900 frames. At 50ms/frame that's ~45 seconds of blocking. Without threading, the UI would freeze completely.

---

## 15. Scoring & Recommendation Algorithm

### Step-by-step for each body area:

```
1. Get the measured angle value (from CyclingAngles)
2. Look up ideal range from angle_ranges.json for the current riding_style
3. Calculate deviation:
   - If value is within [min, max] → deviation = 0
   - If value < min → deviation = min - value
   - If value > max → deviation = value - max
4. Calculate score:
   score = 100 - (deviation / range_width) × 40
   score = clamp(score, 0, 100)
5. Determine severity:
   ratio = deviation / range_width
   ratio ≤ 0   → OPTIMAL  (✅ green)
   ratio ≤ 0.5 → MINOR    (🟡 yellow)
   ratio ≤ 1.0 → MODERATE (🟠 orange)
   ratio > 1.0 → CRITICAL (🔴 red)
6. Generate adjustment text (e.g., "Raise saddle by ~Nmm")
7. Create Recommendation object
```

### Overall score:

```
                   Σ (area_score × area_weight)
overall_score = ─────────────────────────────────
                       Σ (area_weights)

Weights (road):  knee=30, hip=20, back=15, ankle=10, elbow=5
```

### Saddle height mm estimation:

```
mm_adjustment ≈ deviation_degrees × 2.5
```

This is a rough approximation: ~2.5mm of saddle height change ≈ 1° of knee extension change.

---

## 16. Session Persistence

### Save path:
```
~/.myvelofit/sessions/{rider_name}_{YYYYMMDD_HHMMSS}.json
```

### JSON structure:
```json
{
  "version": "1.0",
  "timestamp": "2026-02-17T14:30:00.000000",
  "rider": {
    "height_cm": 180.0,
    "weight_kg": 75.0,
    "inseam_cm": 85.0,
    "foot_size_eu": 43.0,
    "arm_length_cm": 62.0,
    "torso_length_cm": 52.0,
    "shoulder_width_cm": 44.0,
    "flexibility": "medium",
    "riding_style": "road",
    "name": "John"
  },
  "bike": {
    "frame_size_cm": 56.0,
    "saddle_height_cm": 75.0,
    "saddle_setback_cm": 5.0,
    "handlebar_reach_cm": 45.0,
    "handlebar_drop_cm": 8.0,
    "crank_length_mm": 172.5,
    "stem_length_mm": 100.0,
    "stem_angle_deg": -6.0
  },
  "fit_score": {
    "overall": 78.3,
    "knee_score": 90.0,
    "hip_score": 75.0,
    "back_score": 80.0,
    "ankle_score": 65.0,
    "reach_score": 70.0,
    "category": "good"
  }
}
```

---

## 17. Tests

### `tests/test_rider_model.py`

| Test | Validates |
|---|---|
| `test_valid_rider` | All fields in range → `is_valid == True` |
| `test_invalid_height` | Height=50 (out of range) → validation error for height_cm |
| `test_estimated_saddle_height` | Inseam=85 → estimated saddle ≈ 75.1cm |
| `test_serialization_roundtrip` | `to_dict()` → `from_dict()` preserves all fields including enums |

### `tests/test_analysis_model.py`

| Test | Validates |
|---|---|
| `test_fit_score_categories` | 95→excellent, 80→good, 60→fair, 30→poor |
| `test_fit_score_serialization` | `to_dict()` includes computed category |

### `tests/test_angle_calculator.py`

| Test | Validates |
|---|---|
| `test_angle_straight_line` | Three collinear points → 180° |
| `test_angle_right_angle` | L-shaped points → 90° |
| `test_knee_extension` | Realistic landmarks → angle between 0–180 |
| `test_hip_angle` | Realistic landmarks → angle between 0–180 |
| `test_back_angle` | Realistic landmarks → angle between 0–90 |

### `tests/test_fit_rules_engine.py`

| Test | Validates |
|---|---|
| `test_perfect_road_fit` | Ideal angles → score ≥ 85, category excellent/good |
| `test_poor_knee_extension` | Knee at 120° → critical/moderate severity, "Raise" in adjustment |
| `test_different_styles_return_results` | All 5 styles produce valid scores + ≥3 recommendations |

---

## 18. How to Run

```bash
cd /home/ndg1bp/ws/myBikeFit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Run tests:
```bash
cd /home/ndg1bp/ws/myBikeFit
pytest tests/ -v
```

---

## 19. Future Enhancements

| Feature | Status | Notes |
|---|---|---|
| PDF report export | Placeholder | Use `fpdf2` or `reportlab` |
| Webcam live recording | Not implemented | Add tab in VideoCaptureView |
| Imperial unit toggle | Not implemented | MeasurementInput.set_unit() + conversion math |
| Pedal stroke cycle detection | Not implemented | Find local minima of knee Y-coordinate |
| Rolling angle smoothing | Config exists | Apply window=5 rolling mean to angle readings |
| Side-view validation | Not implemented | Check landmark Z-value consistency |
| Bike diagram SVG | Not implemented | Add to BikeInputView showing measurement points |
| Multi-rider profiles | Not implemented | List/load profiles from persistence |
| Real-time angle display during analysis | Partial | Gauges exist but not wired to per-frame updates in analysis loop |

---

*This document was generated from the complete chat session that designed and built the myBikeFit application.*
