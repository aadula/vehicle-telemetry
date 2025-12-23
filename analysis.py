import sqlite3
from datetime import datetime
import statistics

DB_PATH = "telemetry.db"

# thresholds (tune later)
COOLANT_HIGH = 110.0      # °C
OIL_HIGH = 125.0          # °C
VOLTAGE_LOW = 12.0        # V
MISFIRE_DROP = 800.0      # rpm sudden drop
MISFIRE_SPEED_MIN = 5.0   # mph (car is moving)

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


# ---------- DB helpers ----------

def run_query(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def load_samples():
    """
    Load all samples ordered by time.
    Returns a list of dicts.
    """
    rows = run_query(
        """
        SELECT ts_utc, source, rpm, speed, coolant, oil, boost, voltage
        FROM samples
        ORDER BY id ASC
        """
    )
    samples = []
    for ts, source, rpm, speed, coolant, oil, boost, voltage in rows:
        samples.append(
            {
                "ts": ts,
                "source": source,
                "rpm": float(rpm or 0.0),
                "speed": float(speed or 0.0),
                "coolant": float(coolant or 0.0),
                "oil": float(oil or 0.0),
                "boost": float(boost or 0.0),
                "voltage": float(voltage or 0.0),
            }
        )
    return samples


# ---------- Basic stats ----------

def show_last_frames(n=10):
    rows = run_query(
        """
        SELECT ts_utc, source, rpm, speed, coolant, oil, boost, voltage
        FROM samples
        ORDER BY id DESC
        LIMIT ?
        """,
        (n,),
    )
    print(f"\n--- Last {n} Frames ---")
    for r in rows:
        print(r)


def show_max_and_average():
    print("\n--- Max / Average Values ---")
    max_rpm = run_query("SELECT MAX(rpm) FROM samples")[0][0]
    max_coolant = run_query("SELECT MAX(coolant) FROM samples")[0][0]
    max_oil = run_query("SELECT MAX(oil) FROM samples")[0][0]
    max_boost = run_query("SELECT MAX(boost) FROM samples")[0][0]
    min_voltage = run_query("SELECT MIN(voltage) FROM samples")[0][0]
    avg_voltage = run_query("SELECT AVG(voltage) FROM samples")[0][0]

    print(f"Max RPM:         {max_rpm:.1f}")
    print(f"Max Coolant °C:  {max_coolant:.1f}")
    print(f"Max Oil °C:      {max_oil:.1f}")
    print(f"Max Boost psi:   {max_boost:.1f}")
    print(f"Min Voltage V:   {min_voltage:.2f}")
    print(f"Avg Voltage V:   {avg_voltage:.2f}")


# ---------- 0–60 detection ----------

def find_zero_to_sixty_runs(samples):
    print("\n--- 0–60 Runs (from stored samples) ---")

    runs = []
    start_time = None

    for s in samples:
        speed = s["speed"]
        ts = datetime.fromisoformat(s["ts"])

        if speed < 1:
            start_time = None
            continue

        if start_time is None and 1 <= speed < 5:
            start_time = ts

        if start_time and speed >= 60:
            dt = (ts - start_time).total_seconds()
            runs.append(dt)
            start_time = None

    if not runs:
        print("No 0–60 runs detected.")
        return

    for i, t in enumerate(runs, 1):
        print(f"Run {i}: {t:.2f} seconds")

    print(f"\nFastest 0–60: {min(runs):.2f} seconds")


# ---------- Anomaly detection ----------

def detect_anomalies(samples):
    print("\n--- Anomaly Detection ---")

    temp_spikes = []
    voltage_dips = []
    misfire_like = []

    prev = None

    for s in samples:
        ts = s["ts"]

        # temperature spikes
        if s["coolant"] >= COOLANT_HIGH:
            temp_spikes.append((ts, "coolant", s["coolant"]))
        if s["oil"] >= OIL_HIGH:
            temp_spikes.append((ts, "oil", s["oil"]))

        # voltage dips
        if s["voltage"] <= VOLTAGE_LOW:
            voltage_dips.append((ts, s["voltage"]))

        # misfire-like RPM drops while moving
        if prev is not None:
            rpm_drop = prev["rpm"] - s["rpm"]
            if rpm_drop >= MISFIRE_DROP and s["speed"] >= MISFIRE_SPEED_MIN:
                misfire_like.append(
                    (ts, prev["rpm"], s["rpm"], s["speed"])
                )

        prev = s

    if temp_spikes:
        print(f"Temperature spikes (>{COOLANT_HIGH}°C coolant or >{OIL_HIGH}°C oil):")
        for ts, which, value in temp_spikes[:20]:
            print(f"  {ts}  {which}: {value:.1f}")
        if len(temp_spikes) > 20:
            print(f"  ... and {len(temp_spikes) - 20} more")
    else:
        print("No temperature spikes detected.")

    if voltage_dips:
        print(f"\nVoltage dips (<={VOLTAGE_LOW}V):")
        for ts, value in voltage_dips[:20]:
            print(f"  {ts}  voltage: {value:.2f}")
        if len(voltage_dips) > 20:
            print(f"  ... and {len(voltage_dips) - 20} more")
    else:
        print("\nNo significant voltage dips detected.")

    if misfire_like:
        print(f"\nMisfire-like RPM drops (>{MISFIRE_DROP} rpm while moving):")
        for ts, rpm_before, rpm_after, speed in misfire_like[:20]:
            print(
                f"  {ts}  rpm: {rpm_before:.0f} -> {rpm_after:.0f}  speed: {speed:.1f} mph"
            )
        if len(misfire_like) > 20:
            print(f"  ... and {len(misfire_like) - 20} more")
    else:
        print("\nNo misfire-like RPM events detected.")


# ---------- Heat soak, idle & voltage stability ----------

def analyze_heat_soak(samples):
    print("\n--- Heat Soak Analysis ---")
    if not samples:
        print("No samples.")
        return

    first = samples[0]
    last = samples[-1]

    dt = (
        datetime.fromisoformat(last["ts"])
        - datetime.fromisoformat(first["ts"])
    ).total_seconds()

    d_coolant = last["coolant"] - first["coolant"]
    d_oil = last["oil"] - first["oil"]

    print(f"Session duration: {dt:.1f} s")
    print(f"Coolant change:   {d_coolant:+.1f} °C")
    print(f"Oil change:       {d_oil:+.1f} °C")


def analyze_idle_stability(samples):
    print("\n--- Idle Stability (speed < 1 mph) ---")
    idle_rpms = [s["rpm"] for s in samples if s["speed"] < 1.0]

    if len(idle_rpms) < 10:
        print("Not enough idle data.")
        return

    mean_rpm = statistics.mean(idle_rpms)
    std_rpm = statistics.pstdev(idle_rpms)

    print(f"Idle RPM mean: {mean_rpm:.1f}")
    print(f"Idle RPM std:  {std_rpm:.1f}  (lower = smoother idle)")


def analyze_voltage_stability(samples):
    print("\n--- Voltage Stability ---")
    volts = [s["voltage"] for s in samples]

    if len(volts) < 10:
        print("Not enough voltage data.")
        return

    mean_v = statistics.mean(volts)
    std_v = statistics.pstdev(volts)

    print(f"Mean voltage: {mean_v:.2f} V")
    print(f"Voltage std:  {std_v:.3f} V  (lower = more stable)")


# ---------- Plots ----------

def plot_time_series(samples):
    if plt is None:
        print("\n[Plots disabled] Install matplotlib to see graphs:")
        print("  python -m pip install matplotlib")
        return

    if not samples:
        print("\nNo samples to plot.")
        return

    times = [datetime.fromisoformat(s["ts"]) for s in samples]
    t0 = times[0]
    t_rel = [(t - t0).total_seconds() for t in times]

    rpm = [s["rpm"] for s in samples]
    coolant = [s["coolant"] for s in samples]
    voltage = [s["voltage"] for s in samples]

    plt.figure()
    plt.plot(t_rel, rpm)
    plt.xlabel("Time (s)")
    plt.ylabel("RPM")
    plt.title("RPM vs Time")

    plt.figure()
    plt.plot(t_rel, coolant)
    plt.xlabel("Time (s)")
    plt.ylabel("Coolant (°C)")
    plt.title("Coolant Temperature vs Time")

    plt.figure()
    plt.plot(t_rel, voltage)
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.title("Voltage vs Time")

    plt.show()


# ---------- Main ----------

def main():
    show_last_frames(10)
    show_max_and_average()

    samples = load_samples()
    print(f"\nTotal samples loaded: {len(samples)}")

    find_zero_to_sixty_runs(samples)
    detect_anomalies(samples)
    analyze_heat_soak(samples)
    analyze_idle_stability(samples)
    analyze_voltage_stability(samples)

    plot_time_series(samples)


if __name__ == "__main__":
    main()
