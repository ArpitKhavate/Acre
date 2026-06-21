"""Seed the LOCAL device DB with demo detections so the on-device report has
content to show during a test — even before the camera/model are running on QNX.

This writes the same `detections` rows the scan loop would, spread over the last
few hours, with a clear mix of healthy zones, a disease, a pest, and a weed so
`python3 -m edge.report` produces a meaningful report.

    python3 -m edge.seed_demo            # add demo rows
    python3 -m edge.seed_demo --reset    # wipe local detections first
"""
from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

from . import config, local_db

# zone_id -> (class_name, type, crop, base_health, treatment_id)
DEMO_BY_ZONE = {
    "Z1": ("Tomato___healthy", "healthy", "tomato", 95, None),
    "Z2": ("Potato___Late_blight", "disease", "potato", 38, "potato_late_blight_treat"),
    "Z3": ("Pepper_bell___healthy", "healthy", "pepper", 92, None),
    "Z4": ("aphids", "pest", "tomato", 52, "aphids_treat"),
    "Z5": ("Potato___healthy", "healthy", "potato", 90, None),
    "Z6": ("weed", "weed", "pepper", 58, "weed_treat"),
}
_DEFAULT = ("Tomato___healthy", "healthy", "tomato", 94, None)


def _insert(conn, zone_id, captured_at, cls, typ, crop, score, tid):
    conn.execute(
        """INSERT INTO detections
           (uuid, zone_id, captured_at, type, class_name, crop_type, confidence,
            health_score, led_state, bbox_x, bbox_y, bbox_w, bbox_h,
            treatment_id, image_path, synced)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
        (str(uuid.uuid4()), zone_id, captured_at, typ, cls, crop,
         round(random.uniform(0.78, 0.95), 2), score,
         "GREEN" if score >= config.HEALTH_THRESHOLD else "RED",
         120, 80, 60, 70, tid, None),
    )


def seed(reset: bool = False) -> int:
    zones = json.loads(config.ZONES_CONFIG.read_text())["zones"]
    conn = local_db.connect()
    if reset:
        conn.execute("DELETE FROM detections")
        conn.commit()

    now = datetime.now(timezone.utc)
    created = 0
    for hours_ago in (3, 2, 1, 0):
        for z in zones:
            zid = z["zone_id"]
            cls, typ, crop, base, tid = DEMO_BY_ZONE.get(zid, _DEFAULT)
            score = max(0, min(100, base + random.randint(-6, 6)))
            ts = (now - timedelta(hours=hours_ago,
                                  minutes=random.randint(0, 59))).isoformat()
            _insert(conn, zid, ts, cls, typ, crop, score, tid)
            created += 1
    conn.commit()
    conn.close()
    print(f"Seeded {created} demo detections across {len(zones)} zones "
          f"into {config.DB_PATH}")
    return created


def main():
    ap = argparse.ArgumentParser(description="Seed local demo detections")
    ap.add_argument("--reset", action="store_true",
                    help="delete existing local detections first")
    args = ap.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
