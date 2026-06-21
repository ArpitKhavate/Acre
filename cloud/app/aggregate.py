"""Health-score rollups for the map (PRD section 9.2, cloud side).

No inference here. The device already computed a per-plant `health_score`; the
cloud just averages recent scans per zone and farm-wide so the map has a single
color per zone, and records the factor breakdown so the UI can explain "why".
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models

# Window of recent scans that count toward the current map color.
ROLLUP_WINDOW = timedelta(hours=24)


def _window_start():
    return datetime.now(timezone.utc) - ROLLUP_WINDOW


def recompute_scores(db: Session, farm_id: str) -> dict:
    """Recompute per-zone + farm-wide scores from recent detections."""
    since = _window_start()
    zones = db.query(models.Zone).filter(models.Zone.farm_id == farm_id).all()

    zone_scores = {}
    for zone in zones:
        rows = (
            db.query(models.Detection)
            .filter(
                models.Detection.zone_id == zone.id,
                models.Detection.captured_at >= since,
            )
            .all()
        )
        if not rows:
            continue
        scored = [r.health_score for r in rows if r.health_score is not None]
        avg = sum(scored) / len(scored) if scored else 100.0
        factors = {
            "scans": len(rows),
            "disease": sum(1 for r in rows if r.type == "disease"),
            "pest": sum(1 for r in rows if r.type == "pest"),
            "weed": sum(1 for r in rows if r.type == "weed"),
            "red_leds": sum(1 for r in rows if r.led_state == "RED"),
        }
        zone_scores[zone.id] = (round(avg, 1), factors)
        _upsert_score(db, farm_id, zone.id, avg, factors)

    if zone_scores:
        farm_avg = sum(s for s, _ in zone_scores.values()) / len(zone_scores)
    else:
        farm_avg = 100.0
    _upsert_score(db, farm_id, None, farm_avg, {"zones_scored": len(zone_scores)})
    db.commit()
    return {"farm_score": round(farm_avg, 1), "zones": zone_scores}


def _upsert_score(db: Session, farm_id, zone_id, score, factors):
    db.add(models.FarmHealthScore(
        id=str(uuid.uuid4()),
        farm_id=farm_id,
        zone_id=zone_id,
        score=round(score, 1),
        factors=factors,
    ))


def latest_zone_scores(db: Session, farm_id: str) -> dict:
    """Most recent score per zone (for the map)."""
    rows = (
        db.query(models.FarmHealthScore)
        .filter(models.FarmHealthScore.farm_id == farm_id)
        .order_by(models.FarmHealthScore.computed_at.desc())
        .all()
    )
    out = {}
    for r in rows:
        key = r.zone_id or "__farm__"
        if key not in out:
            out[key] = {"score": r.score, "factors": r.factors,
                        "computed_at": r.computed_at}
    return out
