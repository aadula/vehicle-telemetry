import os

DEFAULT_SOURCE = "sim"
SUPPORTED_SOURCES = {"sim", "can", "esp32", "obd"}

_default_source = os.getenv("SOURCE", DEFAULT_SOURCE).lower()


def normalize_source(value: str) -> str:
    normalized = (value or DEFAULT_SOURCE).lower()
    if normalized in SUPPORTED_SOURCES:
        return normalized
    return normalized

def get_source() -> str:
    return normalize_source(os.getenv("SOURCE", _default_source))


def set_source(value: str) -> None:
    global _default_source
    _default_source = normalize_source(value)
