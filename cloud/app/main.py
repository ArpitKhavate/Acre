"""Acre cloud API (FastAPI) — reporting only, no inference (PRD sections 8.6, 9, 10).

Endpoints:
  POST /api/sync                          idempotent ingest from edge devices
  GET  /api/farms/{farm_id}/map           zones + latest health color for the map
  GET  /api/farms/{farm_id}/treatments    pesticide summary grouped by zone
  POST /api/farms/{farm_id}/report        recompute scores + Claude AI summary
  GET  /api/farms/{farm_id}/report/latest most recent stored report
  GET  /health
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import aggregate, ai_summary, models
from .db import get_db, init_db
from .schemas import SyncRequest, SyncResponse

app = FastAPI(title="Acre Cloud API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "acre-cloud"}


@app.post("/api/sync", response_model=SyncResponse)
def sync(payload: SyncRequest, db: Session = Depends(get_db)):
    """Idempotent upsert by uuid (PRD 8.6). Retried batches never double-count."""
    synced = 0
    dupes = 0

    _ensure_device(db, payload.device_id)

    for d in payload.records.detections:
        if db.get(models.Detection, d.uuid):
            dupes += 1
            continue
        db.add(models.Detection(
            id=d.uuid,
            device_id=payload.device_id,
            zone_id=d.zone_id,
            captured_at=d.captured_at,
            type=d.type,
            class_name=d.class_name,
            crop_type=d.crop_type,
            confidence=d.confidence,
            health_score=d.health_score,
            led_state=d.led_state,
            bbox=d.bbox.model_dump() if d.bbox else None,
            treatment_id=d.treatment_id,
            image_url=d.image_url,
        ))
        synced += 1

    for s in payload.records.sensor_readings:
        if db.get(models.SensorReading, s.uuid):
            dupes += 1
            continue
        db.add(models.SensorReading(
            id=s.uuid,
            device_id=payload.device_id,
            zone_id=s.zone_id,
            captured_at=s.captured_at,
            temperature_c=s.temperature_c,
            humidity_pct=s.humidity_pct,
            gas_raw=s.gas_raw,
        ))
        synced += 1

    dev = db.get(models.Device, payload.device_id)
    if dev:
        dev.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return SyncResponse(synced=synced, duplicates_ignored=dupes)


@app.get("/api/farms/{farm_id}/map")
def farm_map(farm_id: str, db: Session = Depends(get_db)):
    zones = db.query(models.Zone).filter(models.Zone.farm_id == farm_id).all()
    scores = aggregate.latest_zone_scores(db, farm_id)
    out_zones = []
    for z in zones:
        s = scores.get(z.id)
        out_zones.append({
            "zone_id": z.id,
            "crop_type": z.crop_type,
            "map_x": z.map_x,
            "map_y": z.map_y,
            "score": s["score"] if s else None,
            "factors": s["factors"] if s else None,
            "color": _color(s["score"]) if s else "gray",
        })
    farm = scores.get("__farm__")
    return {
        "farm_id": farm_id,
        "farm_score": farm["score"] if farm else None,
        "zones": out_zones,
    }


@app.get("/api/farms/{farm_id}/treatments")
def treatments_summary(farm_id: str, db: Session = Depends(get_db)):
    """Pesticide table grouped by zone (PRD section 10.2)."""
    zone_ids = [z.id for z in db.query(models.Zone)
                .filter(models.Zone.farm_id == farm_id).all()]
    rows = (
        db.query(models.Detection)
        .filter(models.Detection.zone_id.in_(zone_ids),
                models.Detection.type != "healthy")
        .all()
    )
    grouped: dict = {}
    for r in rows:
        key = (r.zone_id, r.class_name)
        g = grouped.setdefault(key, {"zone_id": r.zone_id, "class_name": r.class_name,
                                     "count": 0, "max_conf": 0.0, "treatment_id": r.treatment_id})
        g["count"] += 1
        g["max_conf"] = max(g["max_conf"], r.confidence)

    out = []
    for g in grouped.values():
        t = db.get(models.Treatment, g["treatment_id"]) if g["treatment_id"] else None
        out.append({**g, "treatment": _treatment_dict(t)})
    return {"farm_id": farm_id, "rows": out}


@app.post("/api/farms/{farm_id}/report")
def generate_report(farm_id: str, period: str = "daily", db: Session = Depends(get_db)):
    roll = aggregate.recompute_scores(db, farm_id)
    treatments = treatments_summary(farm_id, db)
    worst = sorted(
        ((zid, s) for zid, (s, _) in roll["zones"].items()),
        key=lambda kv: kv[1],
    )[:3]
    period_data = {
        "farm_score": roll["farm_score"],
        "worst_zones": [zid for zid, _ in worst if _ < 80],
        "treatments_needed": list({r["class_name"] for r in treatments["rows"]}),
        "zone_scores": {zid: s for zid, (s, _) in roll["zones"].items()},
    }
    summary = ai_summary.generate_summary(period_data)

    report = models.Report(
        id=str(uuid.uuid4()),
        farm_id=farm_id,
        period=period,
        health_score=roll["farm_score"],
        ai_summary=summary,
    )
    db.add(report)
    db.commit()
    return {
        "farm_id": farm_id,
        "health_score": roll["farm_score"],
        "ai_summary": summary,
        "period_data": period_data,
    }


@app.get("/api/farms/{farm_id}/report/latest")
def latest_report(farm_id: str, db: Session = Depends(get_db)):
    r = (
        db.query(models.Report)
        .filter(models.Report.farm_id == farm_id)
        .order_by(models.Report.generated_at.desc())
        .first()
    )
    if not r:
        return {"farm_id": farm_id, "report": None}
    return {
        "farm_id": farm_id,
        "report": {
            "period": r.period,
            "health_score": r.health_score,
            "ai_summary": r.ai_summary,
            "generated_at": r.generated_at,
        },
    }


def _ensure_device(db: Session, device_id: str):
    if not db.get(models.Device, device_id):
        db.add(models.Device(id=device_id, farm_id=None))
        db.commit()


def _color(score):
    if score is None:
        return "gray"
    if score >= 80:
        return "green"
    if score >= 50:
        return "amber"
    return "red"


def _treatment_dict(t):
    if not t:
        return None
    return {
        "id": t.id,
        "pesticide_name": t.pesticide_name,
        "organic_alternative": t.organic_alternative,
        "application_notes": t.application_notes,
        "source": t.source,
    }
