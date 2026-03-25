"""PDF export service for generating analysis reports."""

from __future__ import annotations

import datetime

from fpdf import FPDF

from models.analysis_model import FitScore, CyclingAngles
from models.recommendation_model import Recommendation
from models.rider_model import RiderMeasurements
from models.bike_model import BikeGeometry


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class PDFReportGenerator(FPDF):
    """Generates a professional PDF report from the fit session data."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def _clean_text(self, text: str) -> str:
        """Replace common unicode chars that Helvetica (WinAnsi) doesn't support."""
        if not text:
            return ""
        return (str(text)
                .replace("—", "-")
                .replace("–", "-")
                .replace("•", "-")
                .replace("’", "'")
                .replace("‘", "'")
                .replace("“", '"')
                .replace("”", '"')
                .replace("°", " deg")
                .replace("⚙️", "*")
                .replace("🟢", "")
                .replace("🟡", "")
                .replace("🟠", "")
                .replace("🔴", ""))

    def cell(self, w=0, h=0, text="", *args, **kwargs):
        super().cell(w, h, self._clean_text(text), *args, **kwargs)

    def multi_cell(self, w, h, text="", *args, **kwargs):
        super().multi_cell(w, h, self._clean_text(text), *args, **kwargs)

    def generate_report(
        self,
        filepath: str,
        rider: RiderMeasurements,
        bike: BikeGeometry,
        scores: FitScore,
        angles: CyclingAngles,
        recommendations: list[Recommendation]
    ) -> None:
        """Construct the PDF and save to disk."""
        self.add_page()
        self._draw_header(rider)
        self.ln(10)
        
        self._draw_scores(scores)
        self.ln(10)
        
        self._draw_angles(angles)
        self.ln(10)
        
        self._draw_recommendations(recommendations)
        
        self.output(filepath)

    def _header_section(self, title: str):
        self.set_font("helvetica", 'B', 14)
        self.set_text_color(51, 65, 85)  # slate-700
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT", border="B")
        self.ln(4)

    def _draw_header(self, rider: RiderMeasurements) -> None:
        self.set_font("helvetica", 'B', 24)
        self.set_text_color(15, 23, 42)  # slate-900
        self.cell(0, 12, "myBikeFit Analysis Report", new_x="LMARGIN", new_y="NEXT", align="C")
        
        self.set_font("helvetica", '', 10)
        self.set_text_color(100, 116, 139)  # slate-500
        date_str = datetime.datetime.now().strftime("%B %d, %Y - %H:%M")
        self.cell(0, 6, f"Generated on {date_str}", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(6)

        self._header_section("Rider Details")
        self.set_font("helvetica", '', 11)
        self.set_text_color(71, 85, 105) # slate-600
        
        col1 = f"Name: {rider.name or 'N/A'}\nHeight: {rider.height_cm} cm\nWeight: {rider.weight_kg} kg"
        col2 = f"Style: {rider.riding_style.name.title()}\nInseam: {rider.inseam_cm} cm\nFlexibility: {rider.flexibility.name.title()}"
        
        # Save X, Y
        startX = self.get_x()
        startY = self.get_y()
        self.multi_cell(90, 6, col1, new_x="RIGHT", new_y="TOP")
        self.set_xy(startX + 95, startY)
        self.multi_cell(90, 6, col2, new_x="LMARGIN", new_y="NEXT")

    def _draw_scores(self, scores: FitScore) -> None:
        self._header_section("Fit Scores")
        
        # Overall Score Block
        r, g, b = _hex_to_rgb(scores.category_color)
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", 'B', 16)
        
        overall_text = f"OVERALL SCORE: {scores.overall:.0f} / 100 ({scores.category.upper()})"
        self.cell(0, 12, overall_text, border=0, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
        self.ln(4)

        # Draw component scores 3 per row
        components = [
            ("Knee", scores.knee_score),
            ("Hip", scores.hip_score),
            ("Back", scores.back_score),
            ("Ankle", scores.ankle_score),
            ("Reach", scores.reach_score),
        ]
        if scores.geometry_score > 0:
            components.append(("Sizing", scores.geometry_score))
            
        columns = 3
        col_width = (self.w - 30) / columns
        
        self.set_font("helvetica", 'B', 11)
        self.set_text_color(71, 85, 105)
        
        for i, (name, score) in enumerate(components):
            # Pick color based on score
            if score >= 90: color = (34, 197, 94)    # green
            elif score >= 75: color = (132, 204, 22) # lime
            elif score >= 55: color = (234, 179, 8)  # yellow
            else: color = (239, 68, 68)              # red
            
            self.set_fill_color(*color)
            self.set_text_color(255, 255, 255)
            
            box_text = f"{name}: {score:.0f}"
            self.cell(col_width - 4, 10, box_text, new_x="RIGHT", new_y="TOP", align="C", fill=True)
            self.cell(4, 10, "", new_x="RIGHT", new_y="TOP") # padding
            
            if (i + 1) % columns == 0:
                self.ln(12)
                
        if len(components) % columns != 0:
            self.ln(12)

    def _draw_angles(self, angles: CyclingAngles) -> None:
        self._header_section("Detailed Measurements")
        
        self.set_font("helvetica", '', 10)
        self.set_text_color(51, 65, 85)
        
        data = [
            ("Max Knee Extension (BDC)", f"{angles.knee_extension_min:.1f} deg"),
            ("Max Knee Flexion (TDC)", f"{angles.knee_flexion_max:.1f} deg"),
            ("Min Hip Angle (TDC)", f"{angles.hip_angle_min:.1f} deg"),
            ("Max Hip Angle (BDC)", f"{angles.hip_angle_max:.1f} deg"),
            ("Back Angle", f"{angles.back_angle:.1f} deg"),
            ("Shoulder Angle", f"{angles.shoulder_angle:.1f} deg"),
            ("Elbow Angle", f"{angles.elbow_angle:.1f} deg"),
            ("Ankle Range", f"{angles.ankle_total_range:.1f} deg"),
        ]
        
        # 2 columns
        col_w = (self.w - 30) / 2
        for i in range(0, len(data), 2):
            left_lbl, left_val = data[i]
            self.cell(col_w * 0.7, 6, left_lbl, border=1)
            self.cell(col_w * 0.3, 6, left_val, border=1, align="R")
            
            if i + 1 < len(data):
                right_lbl, right_val = data[i+1]
                self.cell(4, 6, "", border=0) # gap
                self.cell(col_w * 0.7, 6, right_lbl, border=1)
                self.cell(col_w * 0.3, 6, right_val, border=1, align="R", new_x="LMARGIN", new_y="NEXT")
            else:
                self.ln(6)

    def _draw_recommendations(self, recommendations: list[Recommendation]) -> None:
        self._header_section("Actionable Recommendations")
        
        if not recommendations:
            self.set_font("helvetica", 'I', 11)
            self.set_text_color(100, 116, 139)
            self.cell(0, 10, "No recommendations. Your fit is optimal!", new_x="LMARGIN", new_y="NEXT")
            return

        for rec in recommendations:
            # Severity color
            r, g, b = _hex_to_rgb(rec.severity.color)
            self.set_fill_color(r, g, b)
            self.cell(4, 18, "", fill=True) # left border accent
            self.cell(2, 18, "") # spacer
            
            startX = self.get_x()
            startY = self.get_y()
            
            self.set_font("helvetica", 'B', 11)
            self.set_text_color(51, 65, 85)
            self.cell(0, 6, f"{rec.display_name} ({rec.severity.value.upper()})", new_x="LMARGIN", new_y="NEXT")
            
            self.set_x(startX)
            self.set_font("helvetica", '', 10)
            self.set_text_color(15, 23, 42)
            self.multi_cell(0, 5, rec.adjustment, new_x="LMARGIN", new_y="NEXT")
            
            self.set_x(startX)
            self.set_font("helvetica", 'I', 9)
            self.set_text_color(100, 116, 139)
            self.multi_cell(0, 5, rec.explanation, new_x="LMARGIN", new_y="NEXT")
            
            self.ln(6)
