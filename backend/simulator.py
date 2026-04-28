import math
import random
import time
from typing import Dict


class Simulator:
    def __init__(self) -> None:
        self._start_time = time.time()
        self._last_time = self._start_time
        self._state = {
            "speed": 0.0,
            "coolant": 75.0,
            "oil": 70.0,
            "voltage": 13.9,
            "rpm": 800.0,
            "boost": -5.0,
            "last_misfire_ts": 0.0,
            "last_voltage_dip_ts": 0.0,
        }

    def _drive_cycle(self, elapsed_s: float) -> float:
        throttle = 0.5 + 0.5 * math.sin(elapsed_s / 10.0)
        throttle *= 0.6 + 0.4 * (0.5 + 0.5 * math.sin(elapsed_s / 30.0))
        throttle += random.uniform(-0.05, 0.05)
        return max(0.0, min(1.0, throttle))

    def read(self) -> Dict[str, float]:
        now = time.time()
        elapsed_s = now - self._start_time
        dt = max(0.01, now - self._last_time)
        self._last_time = now

        throttle = self._drive_cycle(elapsed_s)

        accel = 6.0 * throttle - 0.03 * self._state["speed"]
        self._state["speed"] += accel * dt
        self._state["speed"] = max(0.0, min(130.0, self._state["speed"]))

        gear_ratio = 120.0
        target_rpm = 800.0 + self._state["speed"] * gear_ratio * (0.3 + 0.7 * throttle)
        self._state["rpm"] += (target_rpm - self._state["rpm"]) * min(1.0, dt * 2.0)
        self._state["rpm"] += random.uniform(-40.0, 40.0)
        self._state["rpm"] = max(700.0, min(6800.0, self._state["rpm"]))

        coolant_target = 85.0 + 20.0 * throttle
        oil_target = 90.0 + 25.0 * throttle
        self._state["coolant"] += (coolant_target - self._state["coolant"]) * dt * 0.1
        self._state["oil"] += (oil_target - self._state["oil"]) * dt * 0.07
        self._state["coolant"] += random.uniform(-0.1, 0.1)
        self._state["oil"] += random.uniform(-0.1, 0.1)
        self._state["coolant"] = max(70.0, min(120.0, self._state["coolant"]))
        self._state["oil"] = max(70.0, min(135.0, self._state["oil"]))

        if random.random() < 0.0005:
            self._state["coolant"] += 10.0
            self._state["oil"] += 8.0

        base_boost = -8.0 + 0.004 * max(0.0, self._state["rpm"] - 1200.0) * throttle
        self._state["boost"] = base_boost + random.uniform(-1.0, 1.0)
        self._state["boost"] = max(-10.0, min(20.0, self._state["boost"]))

        self._state["voltage"] += (13.85 - self._state["voltage"]) * dt * 0.5
        self._state["voltage"] += random.uniform(-0.03, 0.03)
        if now - self._state["last_voltage_dip_ts"] > 20.0 and random.random() < 0.01:
            self._state["voltage"] -= random.uniform(1.0, 1.7)
            self._state["last_voltage_dip_ts"] = now
        self._state["voltage"] = max(11.0, min(14.5, self._state["voltage"]))

        if (
            self._state["speed"] > 20.0
            and throttle > 0.4
            and now - self._state["last_misfire_ts"] > 15.0
            and random.random() < 0.01
        ):
            self._state["rpm"] -= random.uniform(900.0, 1400.0)
            self._state["last_misfire_ts"] = now

        self._state["rpm"] = max(700.0, min(6800.0, self._state["rpm"]))

        return {
            "rpm": self._state["rpm"],
            "speed": self._state["speed"],
            "coolant": self._state["coolant"],
            "oil": self._state["oil"],
            "boost": self._state["boost"],
            "voltage": self._state["voltage"],
        }


_DEFAULT_SIMULATOR = Simulator()


def simulate_sensor_data() -> Dict[str, float]:
    """Compatibility wrapper used by the rest of the backend today."""
    return _DEFAULT_SIMULATOR.read()
