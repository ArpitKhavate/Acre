"""Acre handheld scan loop (PRD sections 3, 7, 9.2).

Per dwell, while the operator holds the unit over a plant:
  capture -> ArUco zone -> motion check -> detect+classify -> health score
  -> drive red/green LED -> log to local SQLite (synced later by sync_agent).

Runs anywhere: real hardware lights real LEDs; a dev laptop prints LED states
and uses synthetic frames if no camera/models are present.

    python -m edge.main              # continuous auto-dwell
    python -m edge.main --once       # single scan, then exit
    python -m edge.main --no-sync    # don't start the background sync thread
"""
from __future__ import annotations

import argparse
import threading
import time

from . import capture, config, detect, health_score, led, local_db, rtc, sensors
from .aruco_zones import ZoneResolver
from .sync_agent import sync_loop


def treatment_id_for(score_result) -> str | None:
    """Map a finding to a treatments-table key (resolved fully in the cloud)."""
    if score_result.type == "healthy":
        return None
    return f"{score_result.class_name.lower().replace('___', '_')}_treat"


class MotionDetector:
    """OpenCV MOG2 — surfaces moving pests near an otherwise-still plant."""

    def __init__(self, min_area: int = 500):
        self.min_area = min_area
        self._sub = None
        try:
            import cv2

            self._sub = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
        except Exception:
            self._sub = None

    def detect(self, frame) -> bool:
        if self._sub is None:
            return False
        import cv2

        mask = self._sub.apply(frame)
        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return any(cv2.contourArea(c) > self.min_area for c in contours)


def scan_once(cam, detector, zones, motion, conn, sensor_unit=None) -> dict | None:
    frame = cam.read()
    zone = zones.detect_zone(frame)
    zone_id = zone["zone_id"] if zone else "unknown"

    moved = motion.detect(frame)
    result = detector.analyze(frame, motion=moved)

    # Optional environmental signal feeds the sensor-anomaly score term.
    anomalies = 0
    if sensor_unit is not None and sensor_unit.backend != "disabled":
        reading = sensor_unit.read()
        anomalies = reading.anomaly_count()
        local_db.insert_sensor(
            conn, zone_id=zone_id, temperature_c=reading.temperature_c,
            humidity_pct=reading.humidity_pct, gas_raw=reading.gas_raw,
        )

    score = health_score.compute(result, sensor_anomaly_count=anomalies)

    state = led.signal_for_score(score.score)

    bbox = result.plant_box.xywh if result.plant_box else None
    rec_uuid = local_db.insert_detection(
        conn,
        zone_id=zone_id,
        type=score.type,
        class_name=score.class_name,
        crop_type=score.crop_type,
        confidence=score.confidence,
        health_score=score.score,
        led_state=state,
        bbox=bbox,
        treatment_id=treatment_id_for(score),
    )
    summary = {
        "uuid": rec_uuid,
        "zone": zone_id,
        "type": score.type,
        "class": score.class_name,
        "score": score.score,
        "led": state,
    }
    print(f"[scan] {zone_id}  {score.type}:{score.class_name}  "
          f"score={score.score}  LED={state}")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="single scan then exit")
    ap.add_argument("--no-sync", action="store_true", help="skip background sync")
    ap.add_argument("--interval", type=float, default=2.0, help="dwell seconds")
    args = ap.parse_args()

    print(f"[acre] device={config.DEVICE_ID} clock={rtc.source()} led={led.backend_name()}")
    cam = capture.Camera()
    print(f"[acre] camera backend={cam.backend}")
    detector = detect.Detector()
    print(f"[acre] model backends={detector.backends()}")
    zones = ZoneResolver()
    motion = MotionDetector()
    sensor_unit = sensors.Sensors()
    print(f"[acre] sensors backend={sensor_unit.backend}")
    conn = local_db.connect()

    if not args.no_sync:
        t = threading.Thread(target=sync_loop, daemon=True)
        t.start()

    led.set("GREEN")  # idle
    try:
        if args.once:
            scan_once(cam, detector, zones, motion, conn, sensor_unit)
        else:
            while True:
                scan_once(cam, detector, zones, motion, conn, sensor_unit)
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[acre] stopping")
    finally:
        led.cleanup()
        cam.close()


if __name__ == "__main__":
    main()
