"""Analysis results — cycling angles and fit scores."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class CyclingAngles:
    """Key angles measured during the pedal stroke."""

    knee_extension_min: float = 0.0   
    knee_extension_max: float = 0.0   
    knee_flexion_max: float = 0.0     
    hip_angle_min: float = 0.0        
    hip_angle_max: float = 0.0        
    back_angle: float = 0.0           
    ankle_angle_min: float = 0.0      
    ankle_angle_max: float = 0.0      
    ankle_angle_at_3: float = 0.0     
    foot_ground_at_12: float = 0.0    
    foot_ground_at_3: float = 0.0     
    foot_ground_at_6: float = 0.0     
    ankle_total_range: float = 0.0    
    shoulder_angle: float = 0.0       
    elbow_angle: float = 0.0          
    
    com_bb_offset: float = 0.0        
    com_image_path: str = ""          

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CyclingAngles:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class FitScore:
    """Overall and per-area fit scores (0–100)."""

    overall: float = 0.0
    knee_score: float = 0.0
    hip_score: float = 0.0
    back_score: float = 0.0
    ankle_score: float = 0.0
    reach_score: float = 0.0
    geometry_score: float = 0.0

    @property
    def category(self) -> str:
        if self.overall >= 90:
            return "excellent"
        if self.overall >= 75:
            return "good"
        if self.overall >= 55:
            return "fair"
        return "poor"

    @property
    def category_color(self) -> str:
        return {
            "excellent": "#22c55e",
            "good": "#84cc16",
            "fair": "#eab308",
            "poor": "#ef4444",
        }.get(self.category, "#888888")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["category"] = self.category
        return d

    @classmethod
    def from_dict(cls, data: dict) -> FitScore:
        data = dict(data)
        data.pop("category", None)
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})
