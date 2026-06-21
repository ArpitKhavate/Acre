"""Poke conversational report (PRD section 4, Interaction Co / Poke track).

Builds a daily/weekly/monthly report from the same backend data the web app
uses and delivers it conversationally via Poke. Reuses the cloud aggregation +
Claude summary so the conversational and visual reports stay consistent.

    python -m cloud.integrations.poke_report --farm demo-farm-1 --period daily
"""
from __future__ import annotations

import argparse
import os

import requests
from sqlalchemy.orm import Session

from cloud.app import aggregate, ai_summary, models
from cloud.app.db import SessionLocal

POKE_API_URL = os.environ.get("POKE_API_URL", "https://poke.com/api/v1/inbound-sms/webhook")


def build_report(db: Session, farm_id: str, period: str) -> dict:
    roll = aggregate.recompute_scores(db, farm_id)
    zone_ids = [z.id for z in db.query(models.Zone)
                .filter(models.Zone.farm_id == farm_id).all()]
    flagged = (db.query(models.Detection)
               .filter(models.Detection.zone_id.in_(zone_ids),
                       models.Detection.type != "healthy").all())
    treatments_needed = sorted({d.class_name for d in flagged})
    worst = sorted(
        ((zid, s) for zid, (s, _) in roll["zones"].items()), key=lambda kv: kv[1]
    )[:3]
    period_data = {
        "farm_score": roll["farm_score"],
        "period": period,
        "worst_zones": [zid for zid, s in worst if s < 80],
        "treatments_needed": treatments_needed,
    }
    period_data["summary"] = ai_summary.generate_summary(period_data)
    return period_data


def deliver(report: dict) -> bool:
    api_key = os.environ.get("POKE_API_KEY")
    if not api_key:
        print("[poke] POKE_API_KEY not set; report built but not sent:\n")
        print(report["summary"])
        return False
    try:
        resp = requests.post(
            POKE_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"message": report["summary"]},
            timeout=10,
        )
        print(f"[poke] delivered ({resp.status_code})")
        return resp.ok
    except Exception as exc:
        print(f"[poke] delivery failed: {exc}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--farm", default="demo-farm-1")
    ap.add_argument("--period", default="daily", choices=["daily", "weekly", "monthly"])
    args = ap.parse_args()
    db = SessionLocal()
    try:
        report = build_report(db, args.farm, args.period)
        deliver(report)
    finally:
        db.close()


if __name__ == "__main__":
    main()
