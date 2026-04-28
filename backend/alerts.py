from typing import Any, Dict, List

COOLANT_HIGH = 105.0
OIL_HIGH = 115.0
VOLTAGE_LOW = 12.2
BOOST_HIGH = 18.0
RPM_HIGH = 6500.0

ALERT_RULES = [
    {
        "key": "coolant_high",
        "field": "coolant_temp",
        "threshold": COOLANT_HIGH,
        "comparison": "gt",
        "message": "Overheating warning",
        "level": "danger",
    },
    {
        "key": "oil_high",
        "field": "oil_temp",
        "threshold": OIL_HIGH,
        "comparison": "gt",
        "message": "Oil temperature warning",
        "level": "danger",
    },
    {
        "key": "voltage_low",
        "field": "voltage",
        "threshold": VOLTAGE_LOW,
        "comparison": "lt",
        "message": "Low voltage warning",
        "level": "warn",
    },
    {
        "key": "boost_high",
        "field": "boost",
        "threshold": BOOST_HIGH,
        "comparison": "gt",
        "message": "Overboost warning",
        "level": "danger",
    },
    {
        "key": "rpm_high",
        "field": "rpm",
        "threshold": RPM_HIGH,
        "comparison": "gt",
        "message": "High RPM warning",
        "level": "warn",
    },
]


def _read_value(sample: Dict[str, Any], field: str) -> float:
    fallback_fields = {
        "coolant_temp": "coolant",
        "oil_temp": "oil",
    }
    raw = sample.get(field, sample.get(fallback_fields.get(field, ""), 0.0))
    try:
        return float(raw or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _is_active(value: float, comparison: str, threshold: float) -> bool:
    if comparison == "lt":
        return value < threshold
    return value > threshold


def evaluate_alerts(sample: Dict[str, Any]) -> Dict[str, Any]:
    flags: Dict[str, bool] = {}
    active: List[Dict[str, Any]] = []
    messages: List[str] = []

    for rule in ALERT_RULES:
        value = _read_value(sample, rule["field"])
        triggered = _is_active(value, rule["comparison"], rule["threshold"])
        flags[rule["key"]] = triggered

        if not triggered:
            continue

        active.append(
            {
                "key": rule["key"],
                "message": rule["message"],
                "level": rule["level"],
                "field": rule["field"],
                "value": value,
                "threshold": rule["threshold"],
            }
        )
        messages.append(rule["message"])

    return {
        **flags,
        "has_alerts": bool(active),
        "messages": messages,
        "active": active,
    }
