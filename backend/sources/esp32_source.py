from typing import Any, Dict

TelemetryPayload = Dict[str, Any]


class Esp32TelemetrySource:
    """
    Placeholder for future ESP32-backed telemetry input.

    TODO: connect serial or wireless ESP32 payloads to the backend source layer
    once real hardware is available for testing.
    """

    name = "esp32"

    def read(self) -> TelemetryPayload:
        raise NotImplementedError("ESP32 telemetry input is planned but not implemented yet.")
