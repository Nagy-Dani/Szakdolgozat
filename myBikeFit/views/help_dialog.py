"""Shared help dialog utility for myBikeFit.

Call ``show_page_help(page_key, parent)`` from any view to show a
non-blocking, page-specific help dialog.
Edit ``_HELP_TEXTS`` below to update or translate any help content.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt


# ── Edit help text here ───────────────────────────────────────────────────────
# Each entry: page_key → (dialog_title, body_html)
_HELP_TEXTS: dict[str, tuple[str, str]] = {
    "welcome": (
        "About myBikeFit",
        """
        <p><b>myBikeFit</b> is an AI-powered bike fitting assistant.</p>
        <p>It uses computer vision to analyse a side-view video of you pedalling
        and measures your key cycling angles — knee extension, hip angle, back
        angle, ankle angle and elbow angle.</p>
        <p><b>How to get started:</b></p>
        <ol>
            <li>Click <i>Start New Session</i> to begin.</li>
            <li>Enter your body measurements on the <b>Rider</b> page.</li>
            <li>Enter your bike measurements on the <b>Bike</b> page (optional).</li>
            <li>Upload a side-view pedalling video on the <b>Video</b> page.</li>
            <li>Wait for automatic pose analysis to complete.</li>
            <li>Review your fit score and recommendations on the <b>Results</b> page.</li>
        </ol>
        <p>You can save and reload sessions at any time via the <b>File</b> menu.</p>
        """,
    ),
    "rider": (
        "Help — Rider Measurements",
        """
        <p>Enter your body measurements as accurately as possible.
        These values are used to estimate ideal angle ranges and
        saddle height for your body proportions.</p>
        <ul>
            <li><b>Height</b> — your total standing height in cm.</li>
            <li><b>Weight</b> — your body weight in kg.</li>
            <li><b>Inseam (inner leg)</b> — measure from the floor to your crotch
                while standing barefoot. This is the most important measurement
                for saddle height estimation.</li>
            <li><b>Foot Size</b> — your EU shoe size (e.g. 42).</li>
            <li><b>Arm Length</b> — from the tip of your shoulder to your wrist.</li>
            <li><b>Torso Length</b> — from your hip bone to your shoulder.</li>
            <li><b>Shoulder Width</b> — shoulder to shoulder across your back.</li>
            <li><b>Flexibility</b> — your general flexibility level.
                Higher flexibility allows more aggressive (lower) positions.</li>
            <li><b>Riding Style</b> — determines the ideal angle ranges used
                in scoring (Road, MTB, TT, Gravel, Commute).</li>
        </ul>
        <p>Click <b>Next</b> when done. All fields will be validated before continuing.</p>
        """,
    ),
    "bike": (
        "Help — Bike Geometry",
        """
        <p>Enter your current bike measurements. If you do not know a value,
        leave it at <b>0</b> — the analysis will still work using video-based
        estimates only.</p>
        <ul>
            <li><b>Frame Size</b> — seat tube length in cm (often marked on the frame).</li>
            <li><b>Saddle Height</b> — vertical distance from the centre of the
                bottom bracket to the top of the saddle, in cm.</li>
            <li><b>Saddle Setback</b> — horizontal distance the saddle is behind
                the bottom bracket centre, in cm.</li>
            <li><b>Handlebar Reach</b> — horizontal distance from saddle nose to
                handlebar centre, in cm.</li>
            <li><b>Handlebar Drop</b> — vertical difference between saddle top
                and handlebar top, in cm.</li>
            <li><b>Crank Length</b> — length of the crank arm in mm
                (printed on the crank, typically 170–175 mm).</li>
            <li><b>Stem Length</b> — stem length in mm.</li>
            <li><b>Stem Angle</b> — stem angle in degrees
                (negative = drop, positive = rise).</li>
        </ul>
        <p>You can also click <b>Skip</b> to proceed with default values.</p>
        """,
    ),
    "video": (
        "Help — Video Input",
        """
        <p>Upload a side-view video of yourself riding the bike.
        The video is processed locally — it is never uploaded to the internet.</p>
        <p><b>Requirements:</b></p>
        <ul>
            <li>Duration: between 5 and 120 seconds.</li>
            <li>Format: MP4, AVI, MOV or MKV.</li>
            <li>Camera must capture your <b>full body from the side</b>.</li>
        </ul>
        <p><b>Tips for best results:</b></p>
        <ul>
            <li>Place the camera at <b>hip height</b>, perpendicular to the bike.</li>
            <li>Ensure <b>good lighting</b> — avoid shooting into a window or bright background.</li>
            <li>Wear <b>fitted clothing</b> so joints are clearly visible.</li>
            <li>Pedal at a <b>steady cadence</b> for at least 10 seconds.</li>
            <li>Set the <i>Cyclist facing</i> toggle to match which direction
                you face in the video (left or right).</li>
        </ul>
        <p>After uploading, click <b>Analyze</b> to start pose detection.</p>
        """,
    ),
    "analysis": (
        "Help — Pose Analysis",
        """
        <p>The application is analysing your video using <b>MediaPipe Pose</b>
        (computer vision). This runs entirely on your computer.</p>
        <p><b>What is happening:</b></p>
        <ol>
            <li>Each video frame is processed to detect 17 body landmarks.</li>
            <li>Key cycling angles are calculated for every frame.</li>
            <li>The results are aggregated across the full pedal stroke.</li>
        </ol>
        <p><b>Live gauges</b> (right panel) show representative angle values
        updating in real time:</p>
        <ul>
            <li><b>Knee Extension</b> — angle at the knee at the bottom of the stroke.</li>
            <li><b>Hip Angle</b> — torso-to-thigh angle at the top of the stroke.</li>
            <li><b>Back Angle</b> — torso angle relative to horizontal.</li>
            <li><b>Ankle Angle</b> — ankle position through the stroke.</li>
            <li><b>Elbow Angle</b> — arm bend at the elbow.</li>
        </ul>
        <p>🟢 Green = within ideal range &nbsp; 🟡 Yellow = slightly off &nbsp; 🔴 Red = needs adjustment</p>
        <p>Processing time depends on video length and your computer's speed.
        Please wait until the progress bar reaches 100%.</p>
        """,
    ),
    "results": (
        "Help — Fit Results",
        """
        <p>The results page shows your <b>personalised bike fit assessment</b>.</p>
        <p><b>Score gauges (top row):</b></p>
        <ul>
            <li><b>Overall Score</b> — weighted average of all areas (0–100).</li>
            <li><b>Knee, Hip, Back, Ankle, Reach</b> — score per body area.</li>
            <li><b>Sizing</b> — static geometry check against your body proportions
                (only shown when bike data was entered).</li>
        </ul>
        <p><b>Score categories:</b>
            🟢 Excellent (≥ 90) &nbsp; 🔵 Good (≥ 75) &nbsp;
            🟡 Fair (≥ 55) &nbsp; 🔴 Poor (&lt; 55)
        </p>
        <p><b>Recommendation cards</b> are sorted by severity:</p>
        <ul>
            <li>🔴 <b>Critical</b> — significant adjustment needed.</li>
            <li>🟠 <b>Moderate</b> — worth addressing.</li>
            <li>🟡 <b>Minor</b> — small improvement possible.</li>
            <li>✅ <b>Optimal</b> — this area is well set up.</li>
        </ul>
        <p>Use <b>Export PDF</b> to save a full report, or <b>Start Over</b>
        to begin a new session.</p>
        """,
    ),
}
# ─────────────────────────────────────────────────────────────────────────────


def show_page_help(page_key: str, parent: QWidget) -> None:
    """Open a non-blocking help dialog for the given page key."""
    title, body_html = _HELP_TEXTS.get(
        page_key,
        ("Help", "<p>No help available for this page.</p>"),
    )

    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(480)
    dialog.setMaximumWidth(600)
    dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    root = QVBoxLayout(dialog)
    root.setContentsMargins(24, 20, 24, 20)
    root.setSpacing(16)

    # Scrollable body
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)

    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)

    body = QLabel(body_html)
    body.setObjectName("helpBody")
    body.setWordWrap(True)
    body.setTextFormat(Qt.TextFormat.RichText)
    body.setOpenExternalLinks(False)
    content_layout.addWidget(body)
    content_layout.addStretch()

    scroll.setWidget(content)
    root.addWidget(scroll)

    # Close button
    btn_row = QHBoxLayout()
    btn_row.addStretch()
    close_btn = QPushButton("Close")
    close_btn.setObjectName("helpCloseBtn")
    close_btn.setFixedSize(100, 36)
    close_btn.setProperty("class", "secondary")
    close_btn.clicked.connect(dialog.close)
    btn_row.addWidget(close_btn)
    root.addLayout(btn_row)

    dialog.show()
