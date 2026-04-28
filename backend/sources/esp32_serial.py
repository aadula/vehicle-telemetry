# backend/sources/esp32_serial.py
import os
import time
import json
import serial
from serial.tools import list_ports

DEFAULT_BAUD = int(os.getenv("ESP32_BAUD", "115200"))
PORT_OVERRIDE = os.getenv("ESP32_PORT")

KEYWORDS = [
    "CP210", "Silicon Labs",
    "CH340", "CH341",
    "USB Serial", "USB to UART",
    "FTDI",
]

KNOWN_VIDPID = {
    (0x10C4, 0xEA60),  # Silicon Labs CP210x
}

def autodetect_port():
    if PORT_OVERRIDE:
        return PORT_OVERRIDE

    ports = list(list_ports.comports())
    if not ports:
        return None

    for p in ports:
        if p.vid is not None and p.pid is not None and (p.vid, p.pid) in KNOWN_VIDPID:
            return p.device

    for p in ports:
        desc = (p.description or "")
        manu = (p.manufacturer or "")
        text = f"{desc} {manu}".lower()
        if any(k.lower() in text for k in KEYWORDS):
            return p.device

    if len(ports) == 1:
        return ports[0].device

    return None

def open_serial_with_retry(baud=DEFAULT_BAUD, timeout=1, retry_delay=1.0):
    while True:
        port = autodetect_port()
        if not port:
            print("[ESP32] No matching serial port yet. Plug ESP32 in... retrying")
            time.sleep(retry_delay)
            continue

        try:
            print(f"[ESP32] Opening {port} @ {baud}")
            ser = serial.Serial(port, baudrate=baud, timeout=timeout)

            time.sleep(0.3)
            try:
                ser.reset_input_buffer()
            except Exception:
                pass

            return ser

        except PermissionError:
            print(f"[ESP32] {port} is busy (Access denied). Close Serial Monitor / other scripts. Retrying...")
            time.sleep(1.5)

        except Exception as e:
            print(f"[ESP32] Failed to open {port}: {e}")
            time.sleep(retry_delay)

def esp32_stream_forever(on_message, baud=DEFAULT_BAUD):
    while True:
        ser = None
        try:
            ser = open_serial_with_retry(baud=baud, timeout=1, retry_delay=1.0)
            print(f"[ESP32] Connected on {ser.port} @ {baud}")

            while True:
                try:
                    raw = ser.readline()
                except Exception as e:
                    raise RuntimeError(f"Serial read failed: {e}")

                if not raw:
                    continue

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                if not line.startswith("{"):
                    continue

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                on_message(msg)

        except Exception as e:
            print(f"[ESP32] Disconnected / error: {e}. Reconnecting in 1s...")
            time.sleep(1.0)

        finally:
            try:
                if ser:
                    ser.close()
            except Exception:
                pass
