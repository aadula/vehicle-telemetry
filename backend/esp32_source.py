# backend/esp32_source.py

"""
ESP32 wireless telemetry data source.

Two modes:
  - If UDP JSON packets are received on port 9999, use those.
  - If nothing has arrived yet, fall back to smooth synthetic data.

This way you can run the project NOW with fake data,
and when the ESP32 starts sending JSON later, it will
automatically switch to real readings.
"""

import json
import math
import socket
import time

ESP32_UDP_PORT = 9999

_start_time = time.time()
_udp_socket = None
_last_data = None


def _init_udp_socket():
    global _udp_socket
    if _udp_socket is not None:
        return

    _udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    _udp_socket.bind(("0.0.0.0", ESP32_UDP_PORT))
    _udp_socket.settimeout(0.0)  # non-blocking


def _synthetic_data():
    t = time.time() - _start_time

    rpm = 900 + 2500 * abs(math.sin(t * 0.4))
    speed = 0 + 80 * abs(math.sin(t * 0.2))
    coolant = 88 + 12 * abs(math.sin(t * 0.12))
    oil = 95 + 18 * abs(math.sin(t * 0.09))
    boost = -7 + 22 * abs(math.sin(t * 0.6))
    voltage = 13.8 + 0.3 * math.sin(t * 0.25)

    return {
        "rpm": rpm,
        "speed": speed,
        "coolant": coolant,
        "oil": oil,
        "boost": boost,
        "voltage": voltage,
    }


def read_esp32_data():
    """
    Try to read one UDP JSON packet from ESP32.

    Expected JSON format:

        {
          "rpm": 2500,
          "speed": 45.2,
          "coolant": 92.5,
          "oil": 100.1,
          "boost": 10.3,
          "voltage": 13.9
        }

    If no packet is available, or parsing fails,
    return the last known data or synthetic data.
    """
    global _last_data

    _init_udp_socket()

    try:
        data, addr = _udp_socket.recvfrom(4096)
        payload = json.loads(data.decode("utf-8"))

        _last_data = {
            "rpm": float(payload.get("rpm", 0.0)),
            "speed": float(payload.get("speed", 0.0)),
            "coolant": float(payload.get("coolant", 0.0)),
            "oil": float(payload.get("oil", 0.0)),
            "boost": float(payload.get("boost", 0.0)),
            "voltage": float(payload.get("voltage", 0.0)),
        }

    except BlockingIOError:
        # no data available this cycle
        pass
    except Exception:
        # parsing or other error: keep last_data
        pass

    if _last_data is None:
        _last_data = _synthetic_data()

    return _last_data
