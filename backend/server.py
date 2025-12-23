import asyncio
import json
import websockets
import traceback
from datetime import datetime

from config import SOURCE
from data_source import get_sensor_data
from filters import ema_filter
from logger import init_log, append_log

HOST = "0.0.0.0"   # listen on all network interfaces
PORT = 8765


prev_values = {
    "rpm": None,
    "speed": None,
    "coolant": None,
    "oil": None,
    "boost": None,
    "voltage": None,
}

ERROR_LOG = "backend_error.log"


def log_error(e: Exception):
    """Write errors to a log file instead of killing the server."""
    with open(ERROR_LOG, "a") as f:
        f.write(f"[{datetime.utcnow().isoformat()}] {repr(e)}\n")
        f.write(traceback.format_exc() + "\n\n")


async def handler(websocket):
    """Send smoothed telemetry data in a loop to one connected client."""
    global prev_values

    while True:
        try:
            raw = get_sensor_data()

            smoothed = {}
            for key, new_val in raw.items():
                prev = prev_values.get(key)
                smoothed_val = ema_filter(prev, new_val, alpha=0.25)
                smoothed[key] = smoothed_val
                prev_values[key] = smoothed_val

            # include source for the UI
            smoothed["source"] = SOURCE

            # log and send
            append_log(smoothed)
            await websocket.send(json.dumps(smoothed))
            await asyncio.sleep(0.05)  # ~20 Hz

        except Exception as e:
            # Log the error and keep the loop running
            log_error(e)
            await asyncio.sleep(0.5)


async def main():
    init_log()
    async with websockets.serve(handler, HOST, PORT):
        print(f"WebSocket server running at ws://{HOST}:{PORT} (SOURCE={SOURCE})")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
