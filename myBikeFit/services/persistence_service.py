"""Session persistence — save and load analysis sessions as JSON."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from models.rider_model import RiderMeasurements
from models.bike_model import BikeGeometry
from models.analysis_model import CyclingAngles, FitScore
from models.recommendation_model import Recommendation


def save_session(
    rider: RiderMeasurements,
    bike: BikeGeometry,
    fit_score: FitScore | None = None,
    cycling_angles: CyclingAngles | None = None,
    recommendations: list[Recommendation] | None = None,
    facing_side: str = "left",
    video_path: str | None = None,
    path: str | None = None,
) -> str:
    """Save the current session to a JSON file.
    Returns the path of the saved file.
    """
    if path is None:
        save_dir = Path(__file__).resolve().parent.parent / "sessions"
        save_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = rider.name or "session"
        path = str(save_dir / f"{name}_{timestamp}.json")

    data: dict = {
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "facing_side": facing_side,
        "video_path": video_path,
        "rider": rider.to_dict(),
        "bike": bike.to_dict(),
    }

    if cycling_angles is not None:
        data["cycling_angles"] = cycling_angles.to_dict()

    if fit_score is not None:
        data["fit_score"] = fit_score.to_dict()

    if recommendations:
        data["recommendations"] = [r.to_dict() for r in recommendations]

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return path


def load_session(path: str) -> dict:
    """Load a session from a JSON file.
    Returns a dict with keys: 'rider', 'bike', and optionally
    'fit_score', 'cycling_angles', 'recommendations', 'facing_side', 'video_path'.
    """
    with open(path) as f:
        data = json.load(f)

    result: dict = {}
    result["rider"] = RiderMeasurements.from_dict(data["rider"])
    result["bike"] = BikeGeometry.from_dict(data["bike"])

    result["facing_side"] = data.get("facing_side", "left")
    result["video_path"] = data.get("video_path")

    if "cycling_angles" in data:
        result["cycling_angles"] = CyclingAngles.from_dict(data["cycling_angles"])

    if "fit_score" in data:
        result["fit_score"] = FitScore.from_dict(data["fit_score"])

    if "recommendations" in data:
        result["recommendations"] = [
            Recommendation.from_dict(r) for r in data["recommendations"]
        ]

    return result
