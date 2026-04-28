# Vehicle Telemetry Architecture

## 1. Current Architecture

The current system is a small real-time telemetry pipeline:

```text
Browser Dashboard
    ↓
WebSocket connection
    ↓
Python backend server
    ↓
Telemetry source layer
    ↓
Simulator now, hardware later
    ↓
SQLite logging
```

Main components:

- `dashboard/`: static HTML, CSS, and JavaScript frontend
- `backend/server.py`: WebSocket server and frame broadcast loop
- `backend/telemetry.py`: frame normalization, smoothing, and alert attachment
- `backend/data_source.py`: source selection layer
- `backend/sources/simulated_source.py`: current active telemetry source
- `backend/sources/esp32_source.py`, `backend/sources/can_source.py`, `backend/sources/obd_source.py`: planned placeholders for future hardware input
- `backend/database.py`: SQLite persistence in `data/telemetry.db`

## 2. Data Flow

1. The browser opens a WebSocket connection to the Python backend.
2. The backend reads raw telemetry from the source layer.
3. The source layer currently returns simulator data from `backend/sources/simulated_source.py`.
4. The backend normalizes the frame, applies smoothing, and adds alerts.
5. The frame is written to SQLite.
6. The same frame is sent to connected dashboard clients.
7. The dashboard renders live values and warnings from that payload.

## 3. Why WebSockets Are Used

WebSockets are used because telemetry is continuous, low-latency, and server-driven. The backend can push new frames as soon as they are available instead of waiting for the browser to poll repeatedly. That keeps the dashboard simpler and better matches real-time streaming behavior.

## 4. Why Simulation Comes Before Hardware

Simulation allows the software path to be built first:

- backend frame format
- dashboard rendering
- logging
- alerts
- replay and analysis workflows

This reduces debugging complexity. When hardware is introduced later, the main change should be the input source, not the rest of the system.

## 5. Future ESP32 / CAN / OBD-II Fit

Future hardware support is expected to plug into the existing source layer in `backend/data_source.py`.

- `ESP32`: provide serial-fed sensor payloads to the backend
- `CAN`: decode frames from a compatible CAN interface
- `OBD-II`: query diagnostic values and map them into the same telemetry frame

The design goal is to keep one stable output schema for the dashboard and logger, regardless of whether the input comes from the simulator, ESP32, CAN, or OBD-II.

At the moment, the hardware source files are placeholders only. They exist to define the intended structure, not to imply that live hardware telemetry is already working.

## 6. Current Limitations

- Simulator data is the only complete source in active use
- ESP32, CAN, and OBD-II source modules are placeholders and do not provide live data yet
- Session logging is local only
- Derived dashboard metrics are still estimation-based, not hardware-verified
