import math
import random
import time

_start_time = time.time()
_last_time = _start_time

_state = {
    "speed": 0.0,        # mph
    "coolant": 75.0,     # °C
    "oil": 70.0,         # °C
    "voltage": 13.9,     # V
    "rpm": 800.0,        # rpm
    "boost": -5.0,       # psi
    "last_misfire_ts": 0.0,
    "last_voltage_dip_ts": 0.0,
}


def _drive_cycle(t):
    """
    Synthetic 'driver' profile: how hard we're on the throttle [0..1].
    Uses a mix of sin waves so you get pulls, cruising, and off-throttle.
    """
    # base waveform between 0 and 1
    throttle = 0.5 + 0.5 * math.sin(t / 10.0)
    # add slower modulation
    throttle *= (0.6 + 0.4 * (0.5 + 0.5 * math.sin(t / 30.0)))
    # small random wiggle
    throttle += random.uniform(-0.05, 0.05)
    return max(0.0, min(1.0, throttle))


def simulate_sensor_data():
    """
    More realistic simulator that mimics a street drive:
      - speed ramps up/down with 'throttle'
      - rpm follows speed + throttle
      - coolant/oil warm up over time
      - boost responds to rpm + throttle
      - occasional misfire-like rpm drops
      - occasional voltage dips
    """
    global _last_time, _state

    now = time.time()
    t = now - _start_time
    dt = max(0.01, now - _last_time)
    _last_time = now

    throttle = _drive_cycle(t)

    # ----- Speed dynamics -----
    # Very simple physics: accel ~ throttle - drag
    accel = 6.0 * throttle - 0.03 * _state["speed"]  # mph per second
    _state["speed"] += accel * dt
    _state["speed"] = max(0.0, min(130.0, _state["speed"]))

    # ----- RPM dynamics -----
    # crude gear-ish relation: rpm depends on speed and throttle
    # idle around 750–900, pulls up to ~6500
    gear_ratio = 120.0  # rpm per mph in current "gear"
    target_rpm = 800.0 + _state["speed"] * gear_ratio * (0.3 + 0.7 * throttle)
    # smooth toward target
    _state["rpm"] += (target_rpm - _state["rpm"]) * min(1.0, dt * 2.0)
    # small noise
    _state["rpm"] += random.uniform(-40.0, 40.0)
    _state["rpm"] = max(700.0, min(6800.0, _state["rpm"]))

    # ----- Coolant & oil warm-up / heat soak -----
    # Aim for 90–105°C coolant, 95–120°C oil
    coolant_target = 85.0 + 20.0 * throttle  # harder driving = hotter
    oil_target = 90.0 + 25.0 * throttle

    # warm-up / cool-down rates
    _state["coolant"] += (coolant_target - _state["coolant"]) * dt * 0.1
    _state["oil"] += (oil_target - _state["oil"]) * dt * 0.07

    # small noise
    _state["coolant"] += random.uniform(-0.1, 0.1)
    _state["oil"] += random.uniform(-0.1, 0.1)

    # clamp ranges
    _state["coolant"] = max(70.0, min(120.0, _state["coolant"]))
    _state["oil"] = max(70.0, min(135.0, _state["oil"]))

    # Occasionally simulate a heat spike
    if random.random() < 0.0005:
        _state["coolant"] += 10.0
        _state["oil"] += 8.0

    # ----- Boost -----
    # negative at idle, positive on throttle with rpm
    load = throttle
    base_boost = -8.0 + 0.004 * max(0.0, _state["rpm"] - 1200.0) * load
    _state["boost"] = base_boost + random.uniform(-1.0, 1.0)
    _state["boost"] = max(-10.0, min(20.0, _state["boost"]))

    # ----- Voltage -----
    # Base around 13.8–14.1, tiny noise
    _state["voltage"] += (13.85 - _state["voltage"]) * dt * 0.5
    _state["voltage"] += random.uniform(-0.03, 0.03)

    # occasional voltage dips (alt/battery sag, big load)
    if now - _state["last_voltage_dip_ts"] > 20.0 and random.random() < 0.01:
        _state["voltage"] -= random.uniform(1.0, 1.7)
        _state["last_voltage_dip_ts"] = now

    _state["voltage"] = max(11.0, min(14.5, _state["voltage"]))

    # ----- Misfire-like events -----
    # large drop in rpm while car is moving and on throttle
    if (
        _state["speed"] > 20.0
        and throttle > 0.4
        and now - _state["last_misfire_ts"] > 15.0
        and random.random() < 0.01
    ):
        _state["rpm"] -= random.uniform(900.0, 1400.0)
        _state["last_misfire_ts"] = now

    _state["rpm"] = max(700.0, min(6800.0, _state["rpm"]))

    return {
        "rpm": _state["rpm"],
        "speed": _state["speed"],
        "coolant": _state["coolant"],
        "oil": _state["oil"],
        "boost": _state["boost"],
        "voltage": _state["voltage"],
    }
