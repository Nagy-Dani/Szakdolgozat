"""Center of Mass (CoM) and Bottom Bracket (BB) estimation service."""

from __future__ import annotations

import cv2
import math
from models.pose_model import PoseSequence

def generate_com_overlay(
    sequence: PoseSequence,
    video_path: str,
    side: str,
    output_path: str
) -> dict:
    """
    Calculates the CoM and BB, draws them on the 3 o'clock power phase frame,
    and returns a dictionary of the metrics.
    """
    valid_frames = sequence.get_valid_frames(side)
    if not valid_frames:
        return {}

    ankle_xs, ankle_ys = [], []
    for f in valid_frames:
        ank = f.landmarks.get(f"{side}_ankle")
        if ank and ank.visibility > 0.5:
            ankle_xs.append(ank.x)
            ankle_ys.append(ank.y)
    
    if not ankle_xs:
        return {}
        
    bb_x = (min(ankle_xs) + max(ankle_xs)) / 2.0
    bb_y = (min(ankle_ys) + max(ankle_ys)) / 2.0
    bb_r_x = (max(ankle_xs) - min(ankle_xs)) / 2.0
    bb_r_y = (max(ankle_ys) - min(ankle_ys)) / 2.0

    power_frame = None
    if side == "left":
        power_frame = max(
            valid_frames, 
            key=lambda f: f.landmarks[f"{side}_foot_index"].x if f"{side}_foot_index" in f.landmarks else 0
        )
    else:
        power_frame = min(
            valid_frames, 
            key=lambda f: f.landmarks[f"{side}_foot_index"].x if f"{side}_foot_index" in f.landmarks else 1
        )

    lm = power_frame.landmarks
    def get_pt(name):
        pt = lm.get(f"{side}_{name}")
        return (pt.x, pt.y) if pt and pt.visibility > 0.5 else None

    shoulder = get_pt("shoulder")
    hip = get_pt("hip")
    knee = get_pt("knee")
    ankle = get_pt("ankle")
    wrist = get_pt("wrist")
    
    if not all([shoulder, hip, knee, ankle]):
        return {}
        
    def mid(p1, p2): return ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)

    trunk_com = mid(shoulder, hip)
    thigh_com = mid(hip, knee)
    shank_com = mid(knee, ankle)
    arm_com = mid(shoulder, wrist) if wrist else shoulder
    
    w_trunk, w_thigh, w_shank, w_arm = 0.55, 0.28, 0.09, 0.08
    com_x = trunk_com[0]*w_trunk + thigh_com[0]*w_thigh + shank_com[0]*w_shank + arm_com[0]*w_arm
    com_y = trunk_com[1]*w_trunk + thigh_com[1]*w_thigh + shank_com[1]*w_shank + arm_com[1]*w_arm

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, power_frame.frame_number)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return {}

    h, w = frame.shape[:2]
    
    bb_px = (int(bb_x * w), int(bb_y * h))
    com_px = (int(com_x * w), int(com_y * h))
    
    cv2.ellipse(frame, bb_px, (int(bb_r_x*w), int(bb_r_y*h)), 0, 0, 360, (255, 0, 255), 3)
    
    cv2.drawMarker(frame, bb_px, (255, 0, 255), markerType=cv2.MARKER_CROSS, markerSize=20, thickness=3)
    cv2.line(frame, (bb_px[0], bb_px[1]-max(300, int(0.4*h))), (bb_px[0], bb_px[1]+50), (255, 0, 255), 2)
    
    cv2.circle(frame, com_px, 10, (0, 255, 0), -1)
    cv2.line(frame, (com_px[0], 0), (com_px[0], h), (0, 255, 0), 2)
    
    dist_px = com_px[0] - bb_px[0]
    direction = "BEHIND" if ((dist_px < 0 and side == "left") or (dist_px > 0 and side == "right")) else "IN FRONT"
    
    cv2.putText(
        frame, 
        f"CoM {direction} of BB", 
        (com_px[0] + 15, com_px[1]), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        1.5, (0, 255, 0), 3
    )

    cv2.imwrite(output_path, frame)
    
    offset_percent = (bb_x - com_x) if side == "left" else (com_x - bb_x)
    
    return {
        "com_x": com_x,
        "bb_x": bb_x,
        "offset_percent": offset_percent,
        "image_path": output_path
    }
