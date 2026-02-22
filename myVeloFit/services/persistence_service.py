"""Session persistence — save and load analysis sessions as JSON."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from models.rider_model import RiderMeasurements
from models.bike_model import BikeGeometry
from models.analysis_model import FitScore


def save_session(
    rider: RiderMeasurements,
    bike: BikeGeometry,
    fit_score: FitScore | None = None,
    path: str | None = None,
) -> str:
    """Save the current session to a JSON file.

    Returns the path of the saved file.
    """
    if path is None:
        save_dir = Path.home() / ".myvelofit" / "sessions"
        save_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = rider.name or "session"
        path = str(save_dir / f"{name}_{timestamp}.json")

    data = {
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "rider": rider.to_dict(),
        "bike": bike.to_dict(),
    }
    if fit_score:
        data["fit_score"] = fit_score.to_dict()

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return path


def load_session(path: str) -> dict:
    """Load a session from a JSON file.

    Returns a dict with keys: 'rider', 'bike', 'fit_score' (optional).
    """
    with open(path) as f:
        data = json.load(f)

    result: dict = {}
    result["rider"] = RiderMeasurements.from_dict(data["rider"])
    result["bike"] = BikeGeometry.from_dict(data["bike"])

    if "fit_score" in data:
        d = data["fit_score"]
        d.pop("category", None)
        result["fit_score"] = FitScore(**d)

    return result
