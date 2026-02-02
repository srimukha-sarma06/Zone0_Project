import cv2 as cv
import numpy as np
from onnx_model import YOLOv8_ONNX  # <--- NEW IMPORT
import json
import time
import gc

# AI Configuration
AI_SKIP_FRAMES = 3       
FIRE_CHECK_INTERVAL = 10 

# ID Configuration (Make sure these match your ONNX model training)
PERSON_ID = 5  # Check if 'Person' is actually ID 0 or 5 in your specific ONNX model
VIOLATION_IDS = {
    2: "No Hardhat",
    4: "No Vest"
}

# --- LOAD MODELS WITH ONNX RUNTIME ---
print("Loading ONNX Models...")
try:
    model_ppe = YOLOv8_ONNX("models/PPE_Yolov8n.onnx")
    print("PPE Model Loaded.")
except Exception as e:
    print(f"Error loading PPE Model: {e}")
    model_ppe = None

try:
    model_fire = YOLOv8_ONNX("models/Fire_Smoke.onnx")
    print("Fire Model Loaded.")
except Exception as e:
    print(f"Error loading Fire Model: {e}")
    model_fire = None
# -------------------------------------

try:
    with open('config.json', 'r') as f:
        ACCIDENT_CONFIG = json.load(f)
except:
    ACCIDENT_CONFIG = {"machines": []}

prev_time = time.time()
frame_counter = 0

last_persons = []
last_violations = []
last_fire_coords = []
last_fire_status = False

def is_inside(inner_box, outer_box):
    ix1, iy1, ix2, iy2 = inner_box
    ox1, oy1, ox2, oy2 = outer_box
    c_x = (ix1 + ix2) / 2
    c_y = (iy1 + iy2) / 2
    return (ox1 < c_x < ox2) and (oy1 < c_y < oy2)

fall_counter = 0        
FALL_PERSISTENCE = 25    

def overlap(frame):
    global prev_time, frame_counter, fall_counter
    global last_persons, last_violations, last_fire_coords, last_fire_status
    
    machines = ACCIDENT_CONFIG.get('machines', [])
    h_img, w_img = frame.shape[:2]
    
    zone_breached = False
    breached_machine_name = None
    fire_involved = False
    faint_detected = False
    active_warnings = set() 
    
    frame_counter += 1
    if frame_counter % 60 == 0: gc.collect() 

    run_ai = (frame_counter % AI_SKIP_FRAMES == 0)
    
    if run_ai:
        last_persons = []
        last_violations = []

        # --- PPE DETECTION (ONNX) ---
        if model_ppe:
            # predict() now takes the frame directly
            detections = model_ppe.predict(frame, conf=0.4) 
            
            for d in detections:
                cls_id = d['class_id']
                coords = d['box'] # Format is [x1, y1, x2, y2]
                
                if cls_id == PERSON_ID: 
                    last_persons.append(coords)
                elif cls_id in VIOLATION_IDS: 
                    last_violations.append((cls_id, coords))

        # --- FIRE DETECTION (ONNX) ---
        if model_fire and (frame_counter % FIRE_CHECK_INTERVAL == 0):
            last_fire_coords = []
            last_fire_status = False
            
            fire_detections = model_fire.predict(frame, conf=0.5)
            
            for d in fire_detections:
                last_fire_status = True
                last_fire_coords.append(d['box'])

    curr_time = time.time()
    prev_time = curr_time

    # --- DRAW MACHINES ---
    for machine in machines:
        z = machine['zone']
        z_px = [int(z[0]*w_img), int(z[1]*h_img), int(z[2]*w_img), int(z[3]*h_img)]
        cv.rectangle(frame, (z_px[0], z_px[1]), (z_px[2], z_px[3]), (255, 0, 0), 2)
        cv.putText(frame, machine['name'], (z_px[0], z_px[1]-10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # --- DRAW FIRE ---
    if last_fire_status:
        fire_involved = True
        zone_breached = True
        breached_machine_name = "CRITICAL: FIRE"
        for fc in last_fire_coords:
            cv.rectangle(frame, (fc[0], fc[1]), (fc[2], fc[3]), (0, 0, 255), 3)
            cv.putText(frame, "FIRE", (fc[0], fc[1]-10), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # --- DRAW PERSONS & CHECK FALLS ---
    is_fall_detected_this_frame = False 

    for p_box in last_persons:
        px1, py1, px2, py2 = p_box
        status_color = (0, 255, 0)
        
        # Fall Logic
        p_w = px2 - px1
        p_h = py2 - py1
        
        ratio_condition = p_w > (p_h * 1.3) 
        size_condition = p_w > (w_img * 0.1) 
        not_giant_condition = (p_w * p_h) < (w_img * h_img * 0.7)
        not_bottom_edge = py2 < (h_img * 0.95)

        if ratio_condition and size_condition and not_giant_condition and not_bottom_edge:
            is_fall_detected_this_frame = True
            status_color = (0, 0, 255) 
        
        # Violation Checks
        current_person_violations = []
        for v_id, v_box in last_violations:
            if is_inside(v_box, p_box):
                violation_name = VIOLATION_IDS[v_id]
                current_person_violations.append(violation_name)
                vx1, vy1, vx2, vy2 = v_box
                cv.rectangle(frame, (vx1, vy1), (vx2, vy2), (0, 0, 255), 2)
                cv.putText(frame, violation_name, (vx1, vy1-10), cv.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (0,0,255), 1)

        if current_person_violations:
            status_color = (0, 165, 255)
            active_warnings.update(current_person_violations)

        # Zone Breach Checks
        for machine in machines:
            z = machine['zone']
            mz = [int(z[0]*w_img), int(z[1]*h_img), int(z[2]*w_img), int(z[3]*h_img)]
            inter_x1 = max(mz[0], px1); inter_y1 = max(mz[1], py1)
            inter_x2 = min(mz[2], px2); inter_y2 = min(mz[3], py2)
            
            if max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1) > 0:
                zone_breached = True
                if not fire_involved and "MAN DOWN" not in str(breached_machine_name):
                    breached_machine_name = machine['name']
                status_color = (0, 0, 255)

        cv.rectangle(frame, (px1, py1), (px2, py2), status_color, 2)
        cv.putText(frame,"Person", (px1, py1-10), cv.FONT_HERSHEY_COMPLEX_SMALL, 0.8, status_color, 1)

    if is_fall_detected_this_frame:
        fall_counter += 1
    else:
        fall_counter = max(0, fall_counter - 1)

    if fall_counter > FALL_PERSISTENCE:
        faint_detected = True
        zone_breached = True
        breached_machine_name = "MEDICAL: MAN DOWN"

    if zone_breached:
        cv.putText(frame, "STOP MACHINE", (50, h_img - 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    warning_msg = ", ".join(active_warnings) if active_warnings else None
    
    return zone_breached, frame, breached_machine_name, warning_msg, fire_involved, faint_detected
