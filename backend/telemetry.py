import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from alerts import evaluate_alerts
from config import get_source
from data_source import TelemetrySourceManager
from filters import ema_filter

SENSOR_LIMITS: Dict[str, Tuple[float, float]] = {
    "rpm": (0.0, 9000.0),
    "speed": (0.0, 200.0),
    "coolant": (-40.0, 200.0),
    "oil": (-40.0, 200.0),
    "boost": (-30.0, 40.0),
    "voltage": (0.0, 16.0),
}

DEFAULT_SENSOR_VALUES: Dict[str, float] = {
    "rpm": 0.0,
    "speed": 0.0,
    "coolant": 0.0,
    "oil": 0.0,
    "boost": 0.0,
    "voltage": 13.8,
}

UNITS: Dict[str, str] = {
    "rpm": "rpm",
    "speed": "mph",
    "coolant": "C",
    "coolant_temp": "C",
    "oil": "C",
    "oil_temp": "C",
    "boost": "psi",
    "voltage": "V",
}


@dataclass
class TelemetryFrame:
    timestamp: str
    source: str
    mode: str
    rpm: float
    speed: float
    coolant_temp: float
    oil_temp: float
    boost: float
    voltage: float
    alerts: Dict[str, bool] = field(default_factory=dict)
    status: str = "ok"
    age_s: float = 0.0
    units: Dict[str, str] = field(default_factory=lambda: dict(UNITS))

    def to_dict(self) -> Dict[str, Any]:
        """
        Export both the cleaner backend field names and the legacy keys the
        current dashboard already expects.
        """
        return {
            "timestamp": self.timestamp,
            "ts": self.timestamp,
            "source": self.source,
            "mode": self.mode,
            "status": self.status,
            "age_s": self.age_s,
            "rpm": self.rpm,
            "speed": self.speed,
            "coolant_temp": self.coolant_temp,
            "coolant": self.coolant_temp,
            "oil_temp": self.oil_temp,
            "oil": self.oil_temp,
            "boost": self.boost,
            "voltage": self.voltage,
            "alerts": dict(self.alerts),
            "units": dict(self.units),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: Any, lo: float, hi: float) -> Optional[float]:
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return max(lo, min(hi, parsed))


class TelemetryProcessor:
    """
    Converts raw source payloads into the stable frame shape used by the dashboard.
    """

    def __init__(self, source_manager: Optional[TelemetrySourceManager] = None, smoothing_alpha: float = 0.25) -> None:
        self._source_manager = source_manager or TelemetrySourceManager()
        self._smoothing_alpha = smoothing_alpha
        self._prev_values = {key: None for key in SENSOR_LIMITS}

    def _normalize_sensor(self, key: str, raw: Any) -> float:
        lo, hi = SENSOR_LIMITS[key]
        clamped = _clamp(raw, lo, hi)

        if clamped is None:
            previous = self._prev_values.get(key)
            if previous is not None:
                return previous
            return DEFAULT_SENSOR_VALUES[key]

        previous = self._prev_values.get(key)
        smoothed = ema_filter(previous, clamped, alpha=self._smoothing_alpha)
        self._prev_values[key] = smoothed
        return smoothed

    def build_frame(self) -> TelemetryFrame:
        raw = self._source_manager.read() or {}
        normalized = {key: self._normalize_sensor(key, raw.get(key)) for key in SENSOR_LIMITS}

        alert_payload = {
            "rpm": normalized["rpm"],
            "speed": normalized["speed"],
            "coolant_temp": normalized["coolant"],
            "oil_temp": normalized["oil"],
            "boost": normalized["boost"],
            "voltage": normalized["voltage"],
        }

        return TelemetryFrame(
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=raw.get("source", get_source()),
            mode=raw.get("source", get_source()),
            status=raw.get("status", "ok"),
            age_s=_safe_float(raw.get("age_s")) or 0.0,
            rpm=normalized["rpm"],
            speed=normalized["speed"],
            coolant_temp=normalized["coolant"],
            oil_temp=normalized["oil"],
            boost=normalized["boost"],
            voltage=normalized["voltage"],
            alerts=evaluate_alerts(alert_payload),
        )


class TelemetryService:
    def __init__(self, processor: Optional[TelemetryProcessor] = None) -> None:
        self._processor = processor or TelemetryProcessor()
        self._latest_frame: Optional[TelemetryFrame] = None

    def next_frame(self) -> TelemetryFrame:
        frame = self._processor.build_frame()
        self._latest_frame = frame
        return frame

    def latest_frame(self) -> Optional[TelemetryFrame]:
        if self._latest_frame is None:
            return None
        return self._latest_frame
