#!/usr/bin/env python3
"""Humiture (temp + humidity) read test, via edge/sensors.py.

Forces the sensor on and prints one reading plus its anomaly count. With no
real driver wired, this falls back to synthetic values so the data path is
still exercisable.

    python3 scripts/qnx_humiture_test.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("ACRE_SENSORS_ENABLED", "1")

from edge import sensors  # noqa: E402


def main() -> None:
    unit = sensors.Sensors()
    print("sensors backend:", unit.backend)
    reading = unit.read()
    print(f"  temperature_c = {reading.temperature_c}")
    print(f"  humidity_pct  = {reading.humidity_pct}")
    print(f"  anomalies     = {reading.anomaly_count()} "
          f"(humidity > {sensors.HUMIDITY_MAX} counts as one)")


if __name__ == "__main__":
    main()
