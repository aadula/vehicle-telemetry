import asyncio
import json
import traceback
from datetime import datetime
import os

import websockets

from config import get_source
from data_source import get_sensor_data
from filters import ema_filter
from logger import init_log, append_log

HOST = "0.0.0.0"
PORT = 8765

ERROR_LOG = "backend_error.log"
MAX_ERROR_LOG_BYTES = 2_000_000  # ~2MB

SENSOR_KEYS = ["rpm", "speed", "coolant", "oil", "boost", "voltage"]
prev_values = {k: None for k in SENSOR_KEYS}


def rotate_error_log():
    try:
        if os.path.exists(ERROR_LOG) and os.path.getsize(ERROR_LOG) > MAX_ERROR_LOG_BYTES:
            # keep one backup
            if os.path.exists(ERROR_LOG + ".1"):
                os.remove(ERROR_LOG + ".1")
            os.rename(ERROR_LOG, ERROR_LOG + ".1")
    except Exception:
        pass


def log_error(e: Exception):
    rotate_error_log()
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.utcnow().isoformat()}] {repr(e)}\n")
        f.write(traceback.format_exc() + "\n\n")


def clamp(x, lo, hi):
    if x is None:
        return None
    try:
        x = float(x)
    except Exception:
        return None
    return max(lo, min(hi, x))


async def handler(websocket):
    global prev_values

    while True:
        try:
            raw = get_sensor_data() or {}

            out = {}

            # Always pass metadata through
            out["source"] = raw.get("source", get_source())
            out["status"] = raw.get("status", "ok")
            out["age_s"] = float(raw.get("age_s", 0.0))

            # Clamp inputs
            clamped = {
                "rpm": clamp(raw.get("rpm"), 0, 9000),
                "speed": clamp(raw.get("speed"), 0, 200),
                "coolant": clamp(raw.get("coolant"), -40, 200),
                "oil": clamp(raw.get("oil"), -40, 200),
                "boost": clamp(raw.get("boost"), -30, 40),
                "voltage": clamp(raw.get("voltage"), 0, 16),
            }

            # Smooth only sensor keys
            for key in SENSOR_KEYS:
                new_val = clamped.get(key)
                prev = prev_values.get(key)
                smoothed_val = ema_filter(prev, new_val, alpha=0.25)
                out[key] = smoothed_val
                prev_values[key] = smoothed_val

            out["ts"] = datetime.utcnow().isoformat() + "Z"
            out["units"] = {
                "rpm": "rpm",
                "speed": "mph",
                "coolant": "C",
                "oil": "C",
                "boost": "psi",
                "voltage": "V",
            }

            append_log(out)
            await websocket.send(json.dumps(out))
            await asyncio.sleep(0.05)

        except Exception as e:
            log_error(e)
            await asyncio.sleep(0.5)


async def main():
    init_log()
    async with websockets.serve(handler, HOST, PORT):
        print(f"WebSocket server running at ws://{HOST}:{PORT} (SOURCE={get_source()})")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
