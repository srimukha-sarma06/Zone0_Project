import threading 
import time
import cv2 as cv
import gc
import serial
from services.save_accident_frame import save_accident_frame
from accident_logic import overlap

# --- CONFIGURATION ---
TEMP_THRESHOLD = 50.0  # Fire confirmed if Temp > 50°C
cooldown_time = 10

# --- SERIAL SETUP ---
ser = None
# Try internal ports used by Monitor/Serial bridge
possible_ports = ['/dev/ttyS0', '/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyMSM0', '/dev/ttyS1']

for port in possible_ports:
    try:
        # Note: Baud rate must match Arduino "Monitor.begin(115200)"
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"✅ CONNECTED TO MODULINO: {port}")
        break
    except:
        continue

if ser is None:
    print("⚠️ MODULINO NOT FOUND (Simulation Mode)")

time.sleep(2)

def video_live(state):
    # --- CAMERA SETUP ---
    cap = None
    for i in [0, 1, 2]:
        try:
            temp = cv.VideoCapture(i, cv.CAP_V4L2) 
            if not temp.isOpened(): temp = cv.VideoCapture(i) 
            if temp.isOpened():
                ret, _ = temp.read()
                if ret: cap = temp; break
                temp.release()
        except: pass
        
    if not cap:
        print("❌ CRITICAL: No camera found")
        return

    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    
    last_trigger_time = 0
    
    # Initialize temp in state if not present
    if not hasattr(state, 'current_temp'):
        state.current_temp = 0.0

    while True:
        if not threading.main_thread().is_alive(): break

        # 1. READ TEMPERATURE FROM ARDUINO
        # Expecting format: "T:45.5"
        if ser and ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("T:"):
                    # Parse "T:45.5" -> 45.5
                    temp_str = line.split(":")[1]
                    state.current_temp = float(temp_str)
            except Exception:
                pass

        cap.grab()  
        ret, frame = cap.read()
        if not ret: continue
        
        # 2. RUN AI LOGIC
        is_overlap, annotated_frame, machine, ppe_warning, fire_involved_ai, fall_detected = overlap(frame)
        
        # 3. SEND COMMANDS TO ARDUINO
        # Important: Commands must end with \n because Arduino uses readStringUntil('\n')
        if ser:
            try:
                # PRIORITY 1: FIRE (AI + TEMP CHECK)
                # We send "fire" to Arduino, and Arduino checks the temp locally
                if fire_involved_ai:
                     ser.write(b"fire\n")
                     # We also update Python state for the UI
                     if state.current_temp > TEMP_THRESHOLD:
                         state.fire_involved = True
                         print("Fire Detected!!")
                     else:
                         state.fire_involved = False # AI sees fire, but temp is low (False Alarm)

                # PRIORITY 2: ZONE BREACH
                elif machine:
                    if "Baler" in machine:
                        ser.write(b"M1\n") # Matches if (cmd == "M1")
                        print("Baler Overlap")
                    if "Hydraulic" in machine:
                        ser.write(b"M2\n") # Matches if (cmd == "M2")
                        print("Hydraulic Press Overlap")
                
            except Exception as e:
                print(f"Serial Write Error: {e}")

        # Update rest of state
        state.machine_overlap = machine      
        state.missing_ppe = ppe_warning      
        state.latest_frame = annotated_frame 
        state.faint = fall_detected

        # 4. SAVE INCIDENT
        # Only save if it's a real threat (Machine breach OR Confirmed Fire)
        real_fire = (fire_involved_ai and state.current_temp > TEMP_THRESHOLD)
        
        if is_overlap or real_fire:
            now = time.time()
            if now - last_trigger_time > cooldown_time:
                trigger_type = "Fire" if real_fire else machine
                threading.Thread(target=save_accident_frame, 
                                 args=(annotated_frame.copy(), trigger_type, real_fire)).start()
                last_trigger_time = now
        
        time.sleep(0.1)
    
    cap.release()