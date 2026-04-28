from typing import Any, Dict

from simulator import simulate_sensor_data

TelemetryPayload = Dict[str, Any]


class SimulatedTelemetrySource:
    """Active source used by the app until real hardware is wired in."""

    name = "sim"

    def read(self) -> TelemetryPayload:
        payload = dict(simulate_sensor_data())
        payload["source"] = self.name
        payload["status"] = "ok"
        payload["age_s"] = 0.0
        return payload
