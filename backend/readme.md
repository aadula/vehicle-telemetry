# Real-Time Vehicle Telemetry Gauge System

A simple real-time vehicle telemetry dashboard that streams simulated sensor data from a Python backend to a JavaScript frontend using WebSockets.

The dashboard displays:

- RPM  
- Speed  
- Coolant temperature  
- Oil temperature  
- Boost pressure  
- Battery voltage  

with basic smoothing, visual alerts, and data logging.

---

## Features

- **Real-time data stream (≈20 Hz)** from Python to the browser via WebSockets  
- **Simulated telemetry** (RPM, speed, temps, boost, voltage) in `simulate.py`  
- **Exponential Moving Average (EMA) smoothing** in `filters.py`  
- **Visual alerts** (red text) for:
  - Overheating coolant  
  - High oil temperature  
  - High boost  
  - Low voltage (tunable thresholds in `app.js`)  
- **CSV logging** of all readings with timestamps for later analysis (`data_log.csv`)  
- Modular structure that can be extended to real OBD-II / CAN data later

---

## Tech Stack

**Backend**

- Python 3  
- `websockets` library  
- Simple EMA filtering  
- CSV logging

**Frontend**

- HTML + CSS  
- Vanilla JavaScript  
- WebSocket client for live updates

---

## Project Structure

```text
vehicle-telemetry/
├── backend/
│   ├── simulate.py      # Generates simulated sensor data
│   ├── server.py        # WebSocket server streaming data to clients
│   ├── filters.py       # Exponential moving average filter
│   ├── logger.py        # CSV logging of telemetry
│
├── dashboard/
│   ├── index.html       # Telemetry dashboard UI
│   ├── style.css        # Basic styling for cards / layout
│   └── app.js           # WebSocket client + UI updates + alerts
│
└── data_log.csv         # Created at runtime: logged telemetry data
