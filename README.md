# Vehicle Telemetry Dashboard

Open-source vehicle telemetry software for streaming live engine and chassis data to a browser dashboard when the factory cluster does not show the values you actually want.

## What this is

Older and modified vehicles often leave out the data tuners and enthusiasts care about most: boost pressure, oil temperature, AFR, knock, and other signals that matter once a car is no longer stock. This project is an attempt to build a practical telemetry layer on top of that gap instead of relying on a limited factory display or a closed proprietary system. The current version is software-first and runs on simulated telemetry so the backend, logging, and dashboard pipeline can be built and tested before hardware is wired in. It is open-source by design, with the long-term goal of making the same core telemetry workflow adaptable to more than one vehicle platform.

## Current Status

- Phase 1 complete: simulated telemetry pipeline, WebSocket streaming, browser dashboard, SQLite session logging, alert system, and placeholder hardware source modules
- Phase 2 planned and partially in progress: ESP32 firmware, CAN bus integration, and real-vehicle validation on a tuned BMW F30
- Phase 3 planned: a vehicle profile system so the same core hardware and software stack can adapt to different car platforms

## Why I built this

I built this because I own a tuned BMW and a turbo Subaru, and the factory infotainment in older or lightly upgraded cars rarely shows the data I actually care about. I wanted a way to surface things like real boost, oil temperature, and knock activity without replacing the whole dash or buying into a closed ecosystem.

## Architecture

```text
Vehicle data source
    |
    v
Python backend
    |
    +--> SQLite logging
    |
    v
WebSocket
    |
    v
Browser dashboard
```

WebSockets are used because telemetry is continuous and server-driven, so pushing frames is simpler and more responsive than polling from the browser. The backend keeps a source abstraction layer so the dashboard and logger can stay stable whether the input is simulated data now or real hardware later. Simulation came first so the data model, alerting, and session logging could be built before debugging serial, CAN, or vehicle-specific integration issues.

## Tech Stack

- Python with asyncio and websockets for the backend
- SQLite for session logging
- HTML, CSS, and vanilla JavaScript for the dashboard
- Planned hardware layer: ESP32, CAN transceiver, and BLE

## Project Structure

```text
vehicle-telemetry/
├── backend/    # Python backend, telemetry pipeline, source layer, logging
├── dashboard/  # Static browser dashboard
├── data/       # Runtime data directory for local logs and SQLite database
└── docs/       # Architecture and hardware roadmap notes
```

## Run It Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r backend/requirements.txt
python3 backend/server.py
```

In a second terminal:

```bash
cd /path/to/vehicle-telemetry
source .venv/bin/activate
python3 -m http.server 8000
```

Then open localhost:8000/dashboard/.

## Roadmap

- [docs/architecture.md](docs/architecture.md): current software architecture and data flow from source layer to dashboard and SQLite logging
- [docs/hardware-roadmap.md](docs/hardware-roadmap.md): phased plan for moving from simulation to ESP32, CAN, and real-vehicle telemetry input

## Status Disclaimer

Hardware integration is not implemented yet. Placeholder source modules exist for future ESP32, OBD-II, and CAN inputs, but the simulator is the only active telemetry source in the project today.
