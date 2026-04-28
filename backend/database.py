import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "telemetry.db")


def _get_connection() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=5.0)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_payload(data: Any) -> Dict[str, Any]:
    if hasattr(data, "to_dict") and callable(data.to_dict):
        return data.to_dict()
    if isinstance(data, dict):
        return data
    return dict(data)


def _as_json(value: Any) -> str:
    try:
        return json.dumps(value if value is not None else {})
    except (TypeError, ValueError):
        return "{}"


def init_log() -> None:
    """Create the SQLite schema used for telemetry logs."""
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp      TEXT NOT NULL,
                rpm            REAL,
                speed          REAL,
                coolant_temp   REAL,
                oil_temp       REAL,
                boost          REAL,
                voltage        REAL,
                source         TEXT,
                alerts         TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
            ON telemetry (timestamp);
            """
        )


def append_log(data: Dict[str, Any]) -> None:
    """Persist one telemetry frame. Extra keys are ignored."""
    payload = _as_payload(data)
    ts = payload.get("timestamp") or payload.get("ts") or (datetime.utcnow().isoformat() + "Z")

    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO telemetry (
                timestamp,
                rpm,
                speed,
                coolant_temp,
                oil_temp,
                boost,
                voltage,
                source,
                alerts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                ts,
                _as_float(payload.get("rpm")),
                _as_float(payload.get("speed")),
                _as_float(payload.get("coolant_temp", payload.get("coolant"))),
                _as_float(payload.get("oil_temp", payload.get("oil"))),
                _as_float(payload.get("boost")),
                _as_float(payload.get("voltage")),
                payload.get("source"),
                _as_json(payload.get("alerts")),
            ),
        )
