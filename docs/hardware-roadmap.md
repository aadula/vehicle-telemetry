# Hardware Roadmap

## Purpose

The project currently runs on simulated telemetry so the software stack can be built and tested without depending on a vehicle or hardware setup. The long-term goal is to replace simulated inputs with real telemetry sources while keeping the same backend-to-dashboard data flow.

This roadmap is intended as an engineering development plan for moving from simulation to hardware-backed telemetry in manageable stages.

## Phase 1: Software Simulation

### Goals

- Establish a stable backend service for telemetry streaming
- Build a browser dashboard that can render live values reliably
- Define a consistent telemetry frame format
- Save sessions locally for later analysis

### Scope

- Python WebSocket server
- Browser dashboard
- Simulated telemetry generation
- SQLite logging

### Deliverables

- A backend that emits telemetry frames at a predictable rate
- A dashboard that can consume and display those frames in real time
- A local SQLite database for session logs
- Basic alert handling and source status reporting

### Exit Criteria

- The simulator can run for extended sessions without crashing
- The dashboard remains compatible with the backend telemetry schema
- Telemetry frames are saved locally and can be reviewed after a run

## Phase 2: Microcontroller Input

### Goals

- Replace simulated input with microcontroller-fed sensor data
- Prove that the backend can ingest real external data without major architectural changes
- Add basic safeguards around malformed or stale readings

### Scope

- ESP32 reads sensor data
- Serial communication from ESP32 to the Python backend
- Basic validation and safety checks

### Deliverables

- ESP32-side code that publishes telemetry in a stable format
- A Python serial reader that can reconnect cleanly after disconnects
- Field validation for missing, invalid, or out-of-range sensor values
- Source status handling for waiting, stale, and disconnected conditions

### Engineering Notes

- The first target should be simple and reliable transport, not full sensor coverage
- Payload structure should match the existing backend schema as closely as possible
- Logging raw incoming frames during development will make debugging easier

### Exit Criteria

- The backend can receive ESP32 data continuously over serial
- Invalid packets do not crash the server
- The dashboard can switch between simulated and ESP32 input without UI changes

## Phase 3: OBD-II / CAN Integration

### Goals

- Connect the system to real vehicle diagnostics
- Read a small set of high-value live signals before expanding coverage
- Make the backend tolerant of real-world bus noise and incomplete data

### Scope

- Connect to real vehicle diagnostics
- Parse live RPM, speed, coolant temperature, and voltage
- Handle noisy or missing data

### Deliverables

- A working OBD-II or CAN input path for at least the core telemetry fields
- Decode logic for the initial supported signals
- Fallback behavior when frames are delayed, incomplete, or unavailable
- Clear source-state reporting so the dashboard can indicate degraded input quality

### Engineering Notes

- Start with a small supported signal list before attempting broader vehicle coverage
- Vehicle-specific CAN decoding may require capture, labeling, and verification work
- OBD-II polling rates and CAN frame timing should be measured and documented

### Exit Criteria

- The system can ingest live vehicle data from a real diagnostics path
- Core signals are mapped consistently into the existing telemetry frame
- Missing or noisy data is handled without breaking the dashboard or logger

## Phase 4: Product-Level Dashboard

### Goals

- Make the telemetry software more useful for real sessions and review
- Improve operator visibility during live runs and after-the-fact analysis
- Prepare the UI for practical use on larger mobile devices and tablets

### Scope

- Session replay
- Anomaly detection
- Mobile and tablet UI
- Alerts and diagnostics

### Deliverables

- Replay tools for reviewing recorded sessions
- Basic anomaly detection for temperature, voltage, and sensor dropouts
- Responsive UI improvements for tablets and laptop-mounted displays
- Diagnostic and alert views that summarize active issues clearly

### Engineering Notes

- Product-level polish should come after the live data path is dependable
- Alerting should stay explainable and threshold-driven before adding more complex heuristics
- Mobile and tablet layouts should prioritize readability over visual density

### Exit Criteria

- Recorded sessions can be reviewed in a useful way
- Alerts and diagnostic summaries are consistent with backend telemetry state
- The dashboard remains usable on laptop and tablet-sized screens

## Recommended Order of Work

1. Keep the simulator and current software flow stable
2. Finalize one reliable ESP32 input path
3. Add basic validation and fault handling around external data
4. Integrate one real diagnostics source through OBD-II or CAN
5. Improve replay, diagnostics, and UI once live data is dependable

## Constraints

- Avoid expanding hardware scope too early
- Keep the telemetry frame format stable as new inputs are added
- Prefer incremental validation with one data source at a time
- Treat disconnects, stale data, and malformed packets as normal operating conditions that must be handled safely
