import json
import threading
import time
from typing import Callable, Optional

import serial


def start_esp32_serial(
    port: str,
    baud: int,
    on_message: Callable[[dict], None],
    stop_event: threading.Event,
    *,
    timeout: float = 1.0,
) -> threading.Thread:
    """
    Opens the ESP32 serial port and streams newline-delimited JSON objects.
    Calls on_message(parsed_dict) for each valid JSON line.
    Runs in a background thread; stop via stop_event.set().
    """

    def worker():
        ser: Optional[serial.Serial] = None
        while not stop_event.is_set():
            try:
                ser = serial.Serial(port, baud, timeout=timeout)
                # give ESP32 a moment; also avoids some first-line garbage
                time.sleep(0.2)

                while not stop_event.is_set():
                    raw = ser.readline()
                    if not raw:
                        continue

                    line = raw.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    # Ignore ESP32 boot spam that is not JSON
                    if not line.startswith("{"):
                        continue

                    try:
                        msg = json.loads(line)
                        on_message(msg)
                    except json.JSONDecodeError:
                        # If a line is partial or corrupted, just skip it
                        continue

            except serial.SerialException as e:
                # Port busy/disconnected; retry after a short delay
                print(f"[ESP32] SerialException: {e} (retrying...)")
                time.sleep(0.5)

            except PermissionError as e:
                print(f"[ESP32] PermissionError: {e} (COM port in use?)")
                time.sleep(0.8)

            finally:
                try:
                    if ser and ser.is_open:
                        ser.close()
                except Exception:
                    pass

        print("[ESP32] Stopped serial thread.")

    t = threading.Thread(target=worker, name="esp32_serial", daemon=True)
    t.start()
    return t
