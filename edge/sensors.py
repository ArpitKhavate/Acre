"""Humiture (temperature + humidity) sensor wired to the Pi (PRD section 6).

This build uses only the humiture sensor (no gas sensor). The reading is an
optional environmental signal: high humidity is a disease-risk flag that feeds
the `sensor_anomaly_count` term of the health score (PRD 9.2). The core
scan -> score -> LED/laser loop runs fine without it. Enable with
ACRE_SENSORS_ENABLED=1.

Backends, in order: a concrete driver hook (fill in for your wiring), else a
synthetic generator so the data path is exercisable on a dev box. `gas_raw` is
kept as None for schema/sync compatibility with the cloud, which still has the
column from earlier builds.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Optional

from . import config

ENABLED = os.environ.get("ACRE_SENSORS_ENABLED", "0") == "1"

# Healthy range; humidity above this counts as an anomaly (PRD 9.2).
HUMIDITY_MAX = float(os.environ.get("ACRE_HUMIDITY_MAX", "85"))


@dataclass
class Reading:
    temperature_c: Optional[float]
    humidity_pct: Optional[float]
    gas_raw: Optional[float] = None  # no gas sensor in this build; kept for sync

    def anomaly_count(self) -> int:
        n = 0
        if self.humidity_pct is not None and self.humidity_pct > HUMIDITY_MAX:
            n += 1
        return n


class Sensors:
    def __init__(self):
        self.backend = "disabled"
        self._hum = None
        if not ENABLED:
            return
        try:
            # Real DHT11 on config.HUMITURE_PIN (single-wire). Falls back to
            # synthetic if no GPIO backend is importable (e.g. on a laptop).
            from .drivers import humiture

            self._hum = humiture.open_sensor(
                config.HUMITURE_PIN, config.HUMITURE_MIN_INTERVAL_S
            )
            self.backend = f"dht11:{self._hum.backend}"
        except Exception as exc:
            print(f"[sensors] humiture driver unavailable ({exc}); using synthetic.")
            self.backend = "synthetic"

    def read(self) -> Reading:
        if self.backend == "disabled":
            return Reading(None, None)
        if self.backend == "synthetic":
            # plausible greenhouse-ish values, occasionally anomalous humidity
            return Reading(
                temperature_c=round(random.uniform(20, 28), 1),
                humidity_pct=round(random.uniform(45, 90), 1),
            )
        value = self._hum.read()
        if value is None:
            return Reading(None, None)           # a missed DHT11 read; skip
        temp, hum = value
        return Reading(temperature_c=temp, humidity_pct=hum)
