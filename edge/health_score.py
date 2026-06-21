"""Per-plant health score (PRD section 9.2), computed on-device.

score = 100
      - min(40, weed_pressure        * 40)
      - min(30, disease_severity     * 30)
      - min(20, pest_pressure        * 20)
      - min(10, sensor_anomaly_count *  2)   # optional

LED = GREEN if score >= HEALTH_THRESHOLD else RED.

This is what decides the spray-substitute LED color. The same numbers sync to
the cloud, which only rolls them up into the map (no cloud inference).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import config
from .detect import PlantResult


@dataclass
class ScoreResult:
    score: float
    led_state: str            # "GREEN" | "RED"
    type: str                 # primary finding: healthy|disease|pest|weed
    class_name: str
    crop_type: Optional[str]
    confidence: float
    factors: dict


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def compute(result: PlantResult, sensor_anomaly_count: int = 0,
            threshold: float | None = None) -> ScoreResult:
    thr = config.HEALTH_THRESHOLD if threshold is None else threshold

    weed_pressure = 1.0 if result.weed_boxes else 0.0
    disease_severity = 0.0 if result.is_healthy else result.disease_conf
    pest_pressure = result.pest_conf if result.pest_class else 0.0

    weed_pen = min(40.0, weed_pressure * 40.0)
    disease_pen = min(30.0, disease_severity * 30.0)
    pest_pen = min(20.0, pest_pressure * 20.0)
    sensor_pen = min(10.0, sensor_anomaly_count * 2.0)

    score = _clamp(100.0 - weed_pen - disease_pen - pest_pen - sensor_pen, 0.0, 100.0)
    led_state = "GREEN" if score >= thr else "RED"

    # Pick the primary finding for logging / treatment lookup.
    if not result.is_healthy and disease_severity > 0:
        ftype, fclass, fconf = "disease", result.disease_class, result.disease_conf
    elif result.pest_class:
        ftype, fclass, fconf = "pest", result.pest_class, result.pest_conf
    elif result.weed_boxes:
        top = max(result.weed_boxes, key=lambda b: b.conf)
        ftype, fclass, fconf = "weed", top.cls_name, top.conf
    else:
        ftype, fclass, fconf = "healthy", (result.crop_type or "plant"), 1.0

    return ScoreResult(
        score=round(score, 1),
        led_state=led_state,
        type=ftype,
        class_name=fclass or "unknown",
        crop_type=result.crop_type,
        confidence=round(float(fconf), 3),
        factors={
            "weed_penalty": round(weed_pen, 1),
            "disease_penalty": round(disease_pen, 1),
            "pest_penalty": round(pest_pen, 1),
            "sensor_penalty": round(sensor_pen, 1),
            "threshold": thr,
        },
    )
