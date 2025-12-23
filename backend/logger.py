import os
import sqlite3
from datetime import datetime

# telemetry.db will live in the project root:
# vehicle-telemetry/telemetry.db
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "telemetry.db")


def _get_connection():
    """Open a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def init_log():
    """
    Initialize the SQLite database and create tables if they don't exist.
    Call this once at startup (server.py already does this).
    """
    conn = _get_connection()
    cur = conn.cursor()

    # Main samples table: one row per telemetry frame
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS samples (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc    TEXT NOT NULL,
            source    TEXT,
            rpm       REAL,
            speed     REAL,
            coolant   REAL,
            oil       REAL,
            boost     REAL,
            voltage   REAL
        );
        """
    )

    # Optional index for faster querying by time
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_samples_ts
        ON samples (ts_utc);
        """
    )

    conn.commit()
    conn.close()


def append_log(data: dict):
    """
    Append one telemetry frame into the SQLite database.

    `data` is expected to be a dict like:
      {
        "source": "sim" | "can" | "esp32",
        "rpm": float,
        "speed": float,
        "coolant": float,
        "oil": float,
        "boost": float,
        "voltage": float,
        ...
      }
    Extra keys are ignored.
    """
    conn = _get_connection()
    cur = conn.cursor()

    ts = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO samples (
            ts_utc,
            source,
            rpm,
            speed,
            coolant,
            oil,
            boost,
            voltage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            ts,
            data.get("source"),
            float(data.get("rpm", 0.0)),
            float(data.get("speed", 0.0)),
            float(data.get("coolant", 0.0)),
            float(data.get("oil", 0.0)),
            float(data.get("boost", 0.0)),
            float(data.get("voltage", 0.0)),
        ),
    )

    conn.commit()
    conn.close()
