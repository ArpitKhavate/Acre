"""Optional environmental sensors wired to the Pi (PRD section 6, optional add-on).

Humiture (temp + humidity) and gas, read via Pi I2C/analog. This is a flagged
QNX-driver risk and is NOT on the critical path: the scan -> score -> LED loop
runs fine without it. Enable with ACRE_SENSORS_ENABLED=1.

Backends, in order: a concrete driver hook (fill in for your wiring), else a
synthetic generator so the data path is exercisable on a dev box. The optional
`sensor_anomaly_count` term in health_score consumes these readings.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass

ENABLED = os.environ.get("ACRE_SENSORS_ENABLED", "0") == "1"

# Healthy ranges; readings outside count as anomalies (PRD 9.2).
HUMIDITY_MAX = float(os.environ.get("ACRE_HUMIDITY_MAX", "85"))
GAS_MAX = float(os.environ.get("ACRE_GAS_MAX", "600"))


@dataclass
class Reading:
    temperature_c: float | None
    humidity_pct: float | None
    gas_raw: float | None

    def anomaly_count(self) -> int:
        n = 0
        if self.humidity_pct is not None and self.humidity_pct > HUMIDITY_MAX:
            n += 1
        if self.gas_raw is not None and self.gas_raw > GAS_MAX:
            n += 1
        return n


class Sensors:
    def __init__(self):
        self.backend = "disabled"
        if not ENABLED:
            return
        try:
            # Driver hook: wire a DHT/AHT humiture sensor + an MQ-series gas
            # sensor through the AD/DC converter on Pi I2C, and read here.
            # from .drivers.humiture import read_humiture
            # from .drivers.gas import read_gas
            raise ImportError
        except Exception:
            self.backend = "synthetic"

    def read(self) -> Reading:
        if self.backend == "disabled":
            return Reading(None, None, None)
        # synthetic: plausible greenhouse-ish values, occasionally anomalous
        return Reading(
            temperature_c=round(random.uniform(20, 28), 1),
            humidity_pct=round(random.uniform(45, 90), 1),
            gas_raw=round(random.uniform(300, 650), 0),
        )
