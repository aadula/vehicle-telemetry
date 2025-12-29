# backend/config.py
import os

# Default source if nothing is set in the environment
_default_source = os.getenv("SOURCE", "sim").lower()

def get_source() -> str:
    # If user sets $env:SOURCE it will be used; otherwise fallback.
    return os.getenv("SOURCE", _default_source).lower()

def set_source(value: str):
    # Optional: lets you switch source in-process later if you want.
    global _default_source
    _default_source = (value or "sim").lower()
