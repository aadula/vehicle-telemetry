# backend/sources/esp32_state.py
import threading
import time
from typing import Dict, Any, Optional

from sources.esp32_serial import esp32_stream_forever

_lock = threading.Lock()
_latest: Optional[Dict[str, Any]] = None
_last_update_mono: float = 0.0
_started = False


def _on_message(msg: Dict[str, Any]):
    global _latest, _last_update_mono
    with _lock:
        _latest = msg
        _last_update_mono = time.monotonic()


def start_reader_once():
    """Start the ESP32 reader in a background thread (only once)."""
    global _started
    if _started:
        return
    _started = True

    t = threading.Thread(
        target=esp32_stream_forever,
        args=(_on_message,),
        daemon=True
    )
    t.start()


def get_latest() -> Optional[Dict[str, Any]]:
    """Return latest ESP32 JSON dict (or None if not received yet)."""
    with _lock:
        return dict(_latest) if _latest else None


def seconds_since_update() -> float:
    """Seconds since last ESP32 message. Big number if never received."""
    with _lock:
        if _last_update_mono <= 0:
            return 1e9
        return time.monotonic() - _last_update_mono
