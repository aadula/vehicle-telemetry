from typing import Any, Dict

TelemetryPayload = Dict[str, Any]


class CanTelemetrySource:
    """
    Placeholder for future CAN-backed telemetry input.

    TODO: connect a supported CAN interface, decode a small stable signal set,
    and normalize those values into the shared telemetry frame.
    """

    name = "can"

    def read(self) -> TelemetryPayload:
        raise NotImplementedError("CAN telemetry input is planned but not implemented yet.")
