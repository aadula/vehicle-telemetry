"""
data_source.py

Central switch for where telemetry comes from:
- sim   -> simulated driving
- can   -> USB2CAN (real car)
- esp32 -> future wireless board
"""

from typing import Dict, Any

from config import SOURCE
from simulate import simulate_sensor_data

# Try to import CAN source
try:
  from can_source import init_can, read_can_sensors
except ImportError:
  init_can = None
  read_can_sensors = None

_can_initialized = False


def get_sensor_data() -> Dict[str, Any]:
    """
    Route to the correct data source based on SOURCE in config.py
    Returns a dict with keys:
      rpm, speed, coolant, oil, boost, voltage
    """
    global _can_initialized

    src = (SOURCE or "").lower()

    if src == "sim":
        return simulate_sensor_data()

    elif src == "can":
        if init_can is None or read_can_sensors is None:
            # Fallback if python-can not installed or module missing
            print("[DATA] CAN requested but can_source not available, falling back to sim.")
            return simulate_sensor_data()

        if not _can_initialized:
            try:
                init_can()
                _can_initialized = True
            except Exception as e:
                print(f"[DATA] Failed to init CAN: {e}")
                print("[DATA] Falling back to sim mode.")
                return simulate_sensor_data()

        try:
            return read_can_sensors()
        except Exception as e:
            print(f"[DATA] Error reading from CAN: {e}")
            return simulate_sensor_data()

    elif src == "esp32":
        # placeholder for future: we can add an ESP32 source later
        # For now, just reuse sim
        return simulate_sensor_data()

    # default fallback
    return simulate_sensor_data()
