"""
Source selection for raw telemetry input.

Only the simulator is active right now. Hardware source modules exist as
placeholders so the project structure is ready for future work, but they do
not pretend to provide live telemetry yet.
"""

from typing import Any, Dict, Optional

from config import get_source
from sources.can_source import CanTelemetrySource
from sources.esp32_source import Esp32TelemetrySource
from sources.obd_source import ObdTelemetrySource
from sources.simulated_source import SimulatedTelemetrySource

TelemetryPayload = Dict[str, Any]
ACTIVE_SOURCE_NAME = "sim"


class TelemetrySourceManager:
    def __init__(self) -> None:
        self._simulated = SimulatedTelemetrySource()
        self._planned_sources = {
            "esp32": Esp32TelemetrySource(),
            "can": CanTelemetrySource(),
            "obd": ObdTelemetrySource(),
        }

    def _planned_fallback(self, requested_source: str, status_suffix: str = "planned") -> TelemetryPayload:
        payload = self._simulated.read()
        payload["status"] = f"{requested_source}_{status_suffix}"
        payload["requested_source"] = requested_source
        return payload

    def read(self, requested_source: Optional[str] = None) -> TelemetryPayload:
        source_name = (requested_source or get_source() or ACTIVE_SOURCE_NAME).lower()

        if source_name == ACTIVE_SOURCE_NAME:
            return self._simulated.read()

        if source_name in self._planned_sources:
            return self._planned_fallback(source_name)

        return self._planned_fallback(source_name, status_suffix="unknown_source")


_DEFAULT_MANAGER = TelemetrySourceManager()


def get_sensor_data() -> TelemetryPayload:
    """Backwards-compatible helper for callers that expect a module function."""
    return _DEFAULT_MANAGER.read()
