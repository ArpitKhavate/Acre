"""Seed the cloud DB: farm, zones, UC IPM treatments, and synthetic history.

The synthetic history keeps the demo map/report from looking empty on a fresh
table (PRD section 12). Run once after starting against an empty DB:

    python -m cloud.seed
"""
from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cloud.app import models
from cloud.app.db import SessionLocal, init_db

ZONES_JSON = Path(__file__).parent.parent / "edge" / "config" / "zones.json"

# Minimal UC IPM-sourced treatment table (PRD section 11). Expand via Claude Code
# scraping UC IPM for your chosen crops.
TREATMENTS = [
    ("tomato_early_blight_treat", "Tomato___Early_blight", "Chlorothalonil",
     "Copper fungicide + remove lower leaves", "Improve airflow; avoid overhead watering", "UC IPM"),
    ("tomato_late_blight_treat", "Tomato___Late_blight", "Mancozeb",
     "Copper fungicide", "Remove and destroy infected plants promptly", "UC IPM"),
    ("potato_late_blight_treat", "Potato___Late_blight", "Mancozeb",
     "Copper fungicide", "Destroy infected foliage; hill soil over tubers", "UC IPM"),
    ("pepper_bell_bacterial_spot_treat", "Pepper_bell___Bacterial_spot", "Copper + mancozeb",
     "Copper spray", "Use disease-free seed; avoid working plants when wet", "UC IPM"),
    ("weed_treat", "weed", "Glyphosate (spot)", "Hand-pull / hoe",
     "Spot-treat only; mulch to suppress regrowth", "UC IPM"),
    ("aphids_treat", "aphids", "Insecticidal soap", "Neem oil / ladybugs",
     "Spray undersides of leaves; repeat weekly", "UC IPM"),
    ("whitefly_treat", "whitefly", "Pyrethrin", "Yellow sticky traps + neem",
     "Treat early morning; monitor with traps", "UC IPM"),
    ("thrips_treat", "thrips", "Spinosad", "Neem oil / predatory mites",
     "Remove weeds nearby that host thrips", "UC IPM"),
    ("spider_mites_treat", "spider_mites", "Abamectin", "Insecticidal soap / spray water",
     "Increase humidity; avoid drought stress", "UC IPM"),
    ("powdery_treat", "Powdery", "Sulfur or potassium bicarbonate fungicide",
     "Neem oil / milk spray (1:9 with water)", "Improve airflow; avoid overhead watering", "UC IPM"),
    ("rust_treat", "Rust", "Chlorothalonil or myclobutanil",
     "Copper fungicide; remove infected leaves promptly", "Destroy infected foliage", "UC IPM"),
]

DEMO_DETECTIONS = [  # (class_name, type, crop, base_score, treatment_id)
    ("Tomato___healthy", "healthy", "tomato", 96, None),
    ("Tomato___Early_blight", "disease", "tomato", 45, "tomato_early_blight_treat"),
    ("Potato___Late_blight", "disease", "potato", 38, "potato_late_blight_treat"),
    ("Pepper_bell___healthy", "healthy", "pepper", 92, None),
    ("weed", "weed", None, 58, "weed_treat"),
    ("aphids", "pest", "tomato", 52, "aphids_treat"),
]


def seed():
    init_db()
    db = SessionLocal()
    data = json.loads(ZONES_JSON.read_text())
    farm_id = data["farm_id"]

    if not db.get(models.Farm, farm_id):
        db.add(models.Farm(id=farm_id, name="Acre Demo Farm"))

    for z in data["zones"]:
        if not db.get(models.Zone, z["zone_id"]):
            db.add(models.Zone(
                id=z["zone_id"], farm_id=farm_id, marker_id=z["marker_id"],
                map_x=z["map_x"], map_y=z["map_y"], crop_type=z["crop_type"],
            ))

    if not db.get(models.Device, "acre-01"):
        db.add(models.Device(id="acre-01", farm_id=farm_id))

    for t in TREATMENTS:
        if not db.get(models.Treatment, t[0]):
            db.add(models.Treatment(
                id=t[0], class_name=t[1], pesticide_name=t[2],
                organic_alternative=t[3], application_notes=t[4], source=t[5],
            ))
    db.commit()

    # Synthetic history: a few scans per zone over the last 24h.
    zones = data["zones"]
    now = datetime.now(timezone.utc)
    created = 0
    for hours_ago in range(0, 24, 4):
        for z in zones:
            cls, typ, crop, base, tid = random.choice(DEMO_DETECTIONS)
            score = max(0, min(100, base + random.randint(-8, 8)))
            db.add(models.Detection(
                id=str(uuid.uuid4()),
                device_id="acre-01",
                zone_id=z["zone_id"],
                captured_at=now - timedelta(hours=hours_ago, minutes=random.randint(0, 59)),
                type=typ,
                class_name=cls,
                crop_type=crop or z["crop_type"],
                confidence=round(random.uniform(0.7, 0.95), 2),
                health_score=score,
                led_state="GREEN" if score >= 70 else "RED",
                bbox={"x": 100, "y": 80, "w": 60, "h": 70},
                treatment_id=tid,
            ))
            created += 1
    db.commit()
    db.close()
    print(f"Seeded farm '{farm_id}', {len(zones)} zones, {len(TREATMENTS)} treatments, "
          f"{created} synthetic detections.")


if __name__ == "__main__":
    seed()
