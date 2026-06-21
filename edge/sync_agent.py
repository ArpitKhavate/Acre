"""Offline-first sync agent (PRD section 8.3).

Wakes on a timer, checks for unsynced rows, batches them, and POSTs to the cloud
backend. No network this cycle -> does nothing, tries again later. Idempotent by
client UUID, so retried batches never double-count. Can run as a thread inside
main.py or standalone (`python -m edge.sync_agent`).
"""
from __future__ import annotations

import time

from . import config, led, local_db


def _bbox(row: dict):
    if row.get("bbox_x") is None:
        return None
    return {"x": row["bbox_x"], "y": row["bbox_y"], "w": row["bbox_w"], "h": row["bbox_h"]}


def build_payload(detections: list[dict], sensors: list[dict]) -> dict:
    return {
        "device_id": config.DEVICE_ID,
        "records": {
            "detections": [
                {
                    "uuid": d["uuid"],
                    "zone_id": d["zone_id"],
                    "captured_at": d["captured_at"],
                    "type": d["type"],
                    "class_name": d["class_name"],
                    "crop_type": d.get("crop_type"),
                    "confidence": d["confidence"],
                    "health_score": d.get("health_score"),
                    "led_state": d.get("led_state"),
                    "bbox": _bbox(d),
                    "treatment_id": d.get("treatment_id"),
                }
                for d in detections
            ],
            "sensor_readings": [
                {
                    "uuid": s["uuid"],
                    "zone_id": s["zone_id"],
                    "captured_at": s["captured_at"],
                    "temperature_c": s.get("temperature_c"),
                    "humidity_pct": s.get("humidity_pct"),
                    "gas_raw": s.get("gas_raw"),
                }
                for s in sensors
            ],
        },
    }


def sync_once(conn) -> tuple[bool, int]:
    """Attempt one sync cycle. Returns (attempted_with_data, records_sent)."""
    import requests

    detections = local_db.unsynced_detections(conn, config.SYNC_BATCH_SIZE)
    sensors = local_db.unsynced_sensors(conn, config.SYNC_BATCH_SIZE)
    if not detections and not sensors:
        return False, 0

    payload = build_payload(detections, sensors)
    try:
        led.set("BLUE")  # syncing indicator
        resp = requests.post(config.BACKEND_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            local_db.mark_synced(conn, "detections", [d["uuid"] for d in detections])
            local_db.mark_synced(conn, "sensor_readings", [s["uuid"] for s in sensors])
            n = len(detections) + len(sensors)
            local_db.log_sync(conn, n, "ok")
            return True, n
        local_db.log_sync(conn, 0, f"http_{resp.status_code}")
    except Exception as exc:  # no network this cycle — try again later
        local_db.log_sync(conn, 0, f"error:{type(exc).__name__}")
    return True, 0


def report_url() -> str:
    """Cloud endpoint that recomputes scores + AI summary for the web app."""
    if config.CLOUD_REPORT_URL:
        return config.CLOUD_REPORT_URL
    base = config.BACKEND_URL
    if base.endswith("/sync"):
        base = base[: -len("/sync")]
    return f"{base}/farms/{config.FARM_ID}/report"


def trigger_report() -> bool:
    """Ask the cloud to refresh the farm report so the web app updates.

    Called after a sync (e.g. at the end of a run). Network-optional: a failure
    just logs and returns False, keeping the device offline-first."""
    import requests

    try:
        resp = requests.post(report_url(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[sync] cloud report refreshed: "
                  f"score={data.get('health_score')}/100")
            return True
        print(f"[sync] report trigger http_{resp.status_code}")
    except Exception as exc:  # no network — fine, the raw data is already synced
        print(f"[sync] report trigger skipped ({type(exc).__name__})")
    return False


def flush_and_report(conn) -> bool:
    """Push any remaining rows, then trigger the cloud report. For end-of-run."""
    sync_once(conn)
    return trigger_report()


def sync_loop(stop_event=None):
    conn = local_db.connect()
    print(f"[sync] loop started -> {config.BACKEND_URL} every {config.SYNC_INTERVAL_S}s")
    while True:
        if stop_event is not None and stop_event.is_set():
            break
        attempted, n = sync_once(conn)
        if n:
            print(f"[sync] pushed {n} records")
        time.sleep(config.SYNC_INTERVAL_S)


if __name__ == "__main__":
    sync_loop()
