from typing import Any, Dict

TelemetryPayload = Dict[str, Any]


class ObdTelemetrySource:
    """
    Placeholder for future OBD-II telemetry input.

    TODO: add an adapter-backed OBD-II reader that maps live diagnostic values
    into the shared telemetry frame.
    """

    name = "obd"

    def read(self) -> TelemetryPayload:
        raise NotImplementedError("OBD-II telemetry input is planned but not implemented yet.")
