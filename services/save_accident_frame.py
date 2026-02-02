import os
import time
import cv2 as cv
import json

BASE_DIR = "accidents"

def save_accident_frame(frame, machine_name, fire_status=False):
    if frame is None:
        return None

    folder_time = time.strftime("%Y-%m-%d", time.localtime())
    file_time = time.strftime("%H-%M-%S", time.localtime())

    file_path = f"{file_time}.jpg"
    folder_path = os.path.join(BASE_DIR, folder_time)
    os.makedirs(folder_path, exist_ok=True)

    stamped = frame.copy()
    cv.putText(stamped, f"{folder_time} {file_time}", (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    success = cv.imwrite(os.path.join(folder_path, file_path), stamped)
    if not success:
        print("Failed to save frame")
        return None

    json_filename = f"{file_time}.json"
    json_path = os.path.join(folder_path, json_filename)
    
    # FIX: Include fire_status in the saved JSON
    log_data = {
        "machine": machine_name,
        "fire_involved": fire_status
    }
    
    with open(json_path, 'w') as f:
        json.dump(log_data, f)

    return os.path.join(folder_path, file_path)