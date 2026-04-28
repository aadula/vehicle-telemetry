# Product Roadmap

## Purpose

The project currently exists as a software-first telemetry system built around simulated vehicle data. That is intentional: it allows the backend, dashboard, alerting, and logging layers to mature before they depend on real hardware access.

This roadmap describes a realistic path from the current portfolio-grade prototype to a more complete telemetry product.

## Phase 1: Portfolio / Simulation Version

### Goals

- Build a stable end-to-end telemetry pipeline
- Demonstrate the product concept without requiring vehicle hardware
- Keep the codebase organized enough for future hardware integration

### Scope

- Simulated telemetry data
- WebSocket backend
- Live browser dashboard
- Basic alerts
- SQLite session logging
- Clean GitHub documentation

### Deliverables

- A Python backend that emits telemetry frames at a steady cadence
- A browser dashboard that renders live values and connection state
- A basic alert system for threshold-based warnings
- Local SQLite logging for session playback and analysis
- Project documentation that explains architecture, roadmap, and local setup

### Exit Criteria

- The system can run repeatable demo sessions using simulated data
- Telemetry frames are stored locally and can be analyzed after a run
- The repository is clean enough to serve as a public portfolio project

## Phase 2: Hardware Input Prototype

### Goals

- Replace the simulator with an external hardware source
- Validate the backend’s ability to ingest real-time device data
- Handle malformed or incomplete readings without breaking the live dashboard

### Scope

- ESP32 or other microcontroller input
- Serial communication to the Python backend
- Basic sensor validation
- Stable data format
- Safety checks for bad or missing data

### Deliverables

- A microcontroller payload format that maps cleanly into the existing telemetry schema
- A serial input path in the backend with reconnect handling
- Validation for out-of-range, missing, or partially populated sensor values
- Source state reporting for waiting, stale, disconnected, and degraded conditions

### Exit Criteria

- The backend can continuously ingest hardware-fed telemetry over serial
- Bad packets do not crash the server or corrupt the session stream
- The dashboard does not need structural changes when switching from simulation to hardware input

## Phase 3: Vehicle Data Integration

### Goals

- Connect to actual vehicle diagnostics and bus data
- Start with a small reliable signal set before expanding coverage
- Make the system resilient to real-world data quality issues

### Scope

- OBD-II support
- CAN bus support
- Live RPM, speed, coolant temperature, and voltage
- Noisy signal handling
- Fallback mode if hardware disconnects

### Deliverables

- One or more real vehicle input paths through OBD-II and/or CAN
- Mapping of live RPM, speed, coolant temperature, and voltage into the shared telemetry frame
- Filtering or fallback logic for noisy, delayed, or missing signals
- Source failover behavior so the UI remains usable when live hardware becomes unavailable

### Exit Criteria

- Core live vehicle metrics can be read and displayed in real time
- Disconnects and signal dropouts do not take down the dashboard
- Hardware-fed frames remain compatible with logging, alerts, and replay

## Phase 4: Product Dashboard

### Goals

- Expand the dashboard from a live demo surface into a more useful operator tool
- Improve usability across different vehicles and users
- Add post-session features that support review and diagnosis

### Scope

- Session replay
- Driver or operator profiles
- Vehicle profiles
- Maintenance flags
- Anomaly detection
- Exportable logs
- Mobile and tablet-friendly interface

### Deliverables

- Replay controls backed by saved session logs
- Profile support for multiple drivers or multiple vehicle configurations
- Maintenance-oriented flags tied to thresholds or session summaries
- Anomaly detection for overheating, voltage drops, unusual sensor patterns, or data loss
- Export tools for logs in a portable format
- Responsive dashboard layouts for tablets and laptop-sized displays

### Exit Criteria

- Sessions can be reviewed after capture with meaningful state context
- Different drivers or vehicles can reuse the same dashboard with configuration changes rather than code changes
- The dashboard remains practical on portable screens

## Phase 5: Advanced Product Features

### Goals

- Explore features that move the system beyond a single-device telemetry viewer
- Add capabilities that support scaling, long-term maintenance, and broader productization

### Scope

- Predictive maintenance
- Cloud sync
- Fleet or multi-vehicle support
- GPS route overlay
- AI-assisted diagnostics
- Hardware enclosure concept
- Mobile app companion

### Deliverables

- Maintenance models or heuristics based on historical session trends
- Optional cloud sync for session storage and cross-device access
- Support for organizing data from more than one vehicle
- GPS-linked route context for recorded telemetry sessions
- Diagnostic assistance that summarizes suspicious patterns without replacing raw telemetry visibility
- A first-pass enclosure concept for hardware deployment
- A mobile companion app concept for monitoring or reviewing sessions

### Exit Criteria

- Advanced features are built on top of a stable core telemetry product rather than compensating for missing fundamentals
- Multi-vehicle or cloud features do not break the local-first operating mode
- Product complexity remains manageable relative to actual hardware and user needs

## Recommended Implementation Order

1. Keep Phase 1 stable and well-documented
2. Prove one microcontroller input path in Phase 2
3. Add one reliable live vehicle integration path in Phase 3
4. Improve review, configuration, and usability in Phase 4
5. Treat Phase 5 as optional expansion once the product core is dependable

## Constraints and Assumptions

- Hardware access may be intermittent, so simulation remains an important development tool
- The telemetry frame schema should stay stable as new sources are added
- Local logging and offline operation should remain available even if cloud features are introduced later
- Early product work should prioritize correctness, resilience, and debuggability over feature count
