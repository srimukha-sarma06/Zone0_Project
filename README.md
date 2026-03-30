# 🛡️ Zone-0: The Active Safety Interlock

**An Edge AI industrial safety system that doesn't just watch—it acts.**

> **Submitted for: Qualcomm "AI for All" Hackathon 2026**
> *Deployed on: Arduino UNO Q / Modulino Edge Hardware*

## 📖 Overview
Industrial accidents often occur because operators have blind spots or suffer medical emergencies while alone. Traditional safety cameras are **passive**—they record the accident but don't stop it.

**Zone-0** is an **Active Interlock System**. It uses quantized Computer Vision (YOLOv8) running locally on the edge to monitor hazardous zones. If a human enters a danger zone, a worker faints, or fire is confirmed, the system **physically cuts power** to the heavy machinery in milliseconds, preventing injury before it happens.

## ⚡ Key Features
* **👁️ Quantized Edge AI:** Runs a custom YOLOv8n (ONNX) model locally to detect humans, PPE violations, and fire in real-time.
* **🛑 Active Hardware Interlock:** Physically halts machinery (Baler, Hydraulic Press) via GPIO relays the instant a threat is detected.
* **🔥 Dual-Verify Fire System:** Eliminates false alarms by combining **AI Vision** with **Modulino Thermal Sensors**. Fire is only confirmed if the camera sees flames **AND** the temperature exceeds 50°C.
* **🚑 Fall Detection:** Uses heuristic analysis (bounding box aspect ratios) to detect if a worker has fainted within a monitored zone.
* **📊 Low-Latency Dashboard:** A flicker-free Streamlit interface showing live video, CPU/RAM stats, and sensor data.

## 🚀 Performance Optimizations
To achieve consistent **5-10 FPS** on embedded hardware, we implemented aggressive optimizations:

1.  **Model Quantization (ONNX):** We utilize `onnxruntime` instead of PyTorch. The YOLOv8 models were exported to `.onnx` format, reducing memory footprint by 40% while maintaining accuracy.
2.  **Intelligent Frame Skipping:** The AI inference engine processes every **3rd frame** (`AI_SKIP_FRAMES = 3`). This frees up CPU cycles for the video stream rendering and serial communication, ensuring the UI remains responsive.
3.  **Manual Garbage Collection:** Embedded Python environments can struggle with automatic memory management. We force a `gc.collect()` every **60 frames** to prevent "RAM Creep" and ensure 24/7 stability.

## 🛠️ Software Architecture

The system uses a split-architecture approach:

* **Linux Side (Python 3.13):**
    * `accident_logic.py`: The AI Brain. Handles ONNX inference and zone overlap logic.
    * `threading_file.py`: The Controller. Manages the video loop, reads Modulino sensors via Serial, and sends command strings (`"M1"`, `"M2"`, etc).
    * `app.py`: The Dashboard. Renders the UI using Base64 encoding for smooth video.
* **Microcontroller Side (C++):**
    * `Modulino_Zone0.ino`: Firmware that handles pin toggling, reads the thermal sensor, and manages the safety latch logic.

## 📦 Installation & Setup

### 1. Prerequisites
* Python 3.13 (running on the Linux side of the board).
* Dependencies: `opencv-python`, `streamlit`, `onnxruntime`, `psutil`, `pyserial`.

### 2. Deployment Steps
1.  **Clone the Repo:**
    ```bash
    git clone [https://github.com/srimukha-sarma06/Zone0-Active-Safety-Interlock.git](https://github.com/YourUsername/Zone0-Active-Safety-Interlock.git)
    cd Zone0-Active-Safety-Interlock
    ```
2.  **Upload Firmware:** Flash `Modulino_Zone0.ino` to the Arduino side using the Arduino IDE.
3.  **Install Requirements:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Production Auto-Start (Systemd)
To ensure the system starts automatically on boot and recovers from crashes, we use a custom systemd service.

1.  Copy the provided service file:
    ```bash
    sudo cp zone0.service /etc/systemd/system/
    ```
2.  Enable the service:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable zone0.service
    ```
3.  Start the system:
    ```bash
    sudo systemctl start zone0.service
    ```

## 🕹️ Usage Guide
1.  **Start:** The system boots with machines in the "ON" (Safe) state.
2.  **Monitor:** Access the dashboard at `http://<BOARD_IP>:8501`.
3.  **Trigger:**
    * **Zone Breach:** Walk into a defined zone → Machine Stops (`M1`/`M2` sent).
    * **Fire:** Light a flame + Heat sensor > 50°C → All Machines Stop (`fire` sent).
4.  **Reset:** Press physical **Button 1** or **Button 2** on the board to re-enable the machines.

## 📄 License
This project is licensed under the **Mozilla Public License 2.0**. See the `LICENSE.txt` file for details.

## 👥 Team
**Event:** Qualcomm AI for All Hackathon 2026
**Team:** CodeNotWorkin
