"""
backend/data_source.py

Central switch for where telemetry comes from:
- sim   -> simulated driving
- can   -> USB2CAN (real car)
- esp32 -> ESP32 serial stream

Always returns a dict that includes:
  source, status, age_s, rpm, speed, coolant, oil, boost, voltage
"""

from typing import Dict, Any

from config import get_source
from simulate import simulate_sensor_data
from sources.esp32_state import start_reader_once, get_latest, seconds_since_update

# Try to import CAN source
try:
    from can_source import init_can, read_can_sensors
except ImportError:
    init_can = None
    read_can_sensors = None

_can_initialized = False


def _wrap(source: str, status: str, age_s: float, payload: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    out["source"] = source
    out["status"] = status
    out["age_s"] = float(age_s)
    return out


def get_sensor_data() -> Dict[str, Any]:
    global _can_initialized

    src = (get_source() or "sim").lower()

    if src == "sim":
        return _wrap("sim", "ok", 0.0, simulate_sensor_data())

    if src == "can":
        if init_can is None or read_can_sensors is None:
            return _wrap("can", "unavailable", 0.0, simulate_sensor_data())

        if not _can_initialized:
            try:
                init_can()
                _can_initialized = True
            except Exception:
                return _wrap("can", "init_failed", 0.0, simulate_sensor_data())

        try:
            data = read_can_sensors()
            return _wrap("can", "ok", 0.0, data)
        except Exception:
            return _wrap("can", "read_error", 0.0, simulate_sensor_data())

    if src == "esp32":
        start_reader_once()

        age = seconds_since_update()
        latest = get_latest()

        # If fresh, use it
        if latest and age < 2.0:
            return _wrap("esp32", "ok", age, latest)

        # If we had something but it's stale
        if latest and age >= 2.0:
            return _wrap("esp32", "stale", age, latest)

        # Never received anything yet
        return _wrap("esp32", "waiting", age, simulate_sensor_data())

    # default fallback
    return _wrap(src, "unknown_source", 0.0, simulate_sensor_data())
