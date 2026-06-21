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

from . import aim, capture, config, detect, health_score, lcd, led, local_db, rtc, sensors
from .aruco_zones import ZoneResolver
from .sync_agent import flush_and_report, sync_loop

# Findings that warrant pointing the laser and turning the LED red.
_TREATABLE = {"weed", "disease", "pest"}


def treatment_id_for(score_result) -> str | None:
    """Map a finding to a treatments-table key (resolved fully in the cloud)."""
    if score_result.type == "healthy":
        return None
    return f"{score_result.class_name.lower().replace('___', '_')}_treat"


def _target_cx(result, frame_width: int) -> float:
    """Horizontal centroid of the thing to aim at (weed box, else plant, else center)."""
    if result.weed_boxes:
        box = max(result.weed_boxes, key=lambda b: b.conf)
    elif result.plant_box is not None:
        box = result.plant_box
    else:
        return frame_width / 2.0
    x, _, w, _ = box.xywh
    return x + w / 2.0


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

    if score is None:
        # No plants or weeds detected. Stand down.
        lcd.show("Scanning...", zone_id)
        aim.laser("OFF")
        aim.set_angle(config.SERVO_CENTER_ANGLE)
        return {"zone": zone_id, "type": "none"}

    # RGB LED: green = healthy, red = needs treatment. Buzzer only if wired.
    state = led.signal_for_score(score.score, buzz_on_red=config.BUZZER_ENABLED)

    # On-device display: zone + 0-100 health score + the finding (PRD 6).
    finding = "healthy" if score.type == "healthy" else f"{score.type}:{score.class_name}"
    lcd.show_score(zone_id, score.score, finding)

    # Perception -> action: center the pan servo on the target and hold the
    # laser on it while the operator dwells (PRD 3, 7.1). Otherwise stand down.
    if score.type in _TREATABLE:
        frame_w = frame.shape[1]

        def fresh_target_cx():
            # Re-measure after each servo move (camera shares the pan axis).
            res = detector.analyze(cam.read(), motion=False)
            if res.weed_boxes or res.plant_box is not None:
                return _target_cx(res, frame_w)
            return None

        locked = aim.center_on(_target_cx(result, frame_w), frame_w,
                               get_target_cx=fresh_target_cx)
        aim.laser("ON")
        print(f"[aim] {zone_id} target {score.type}:{score.class_name} "
              f"locked={locked}")
    else:
        aim.laser("OFF")
        aim.set_angle(config.SERVO_CENTER_ANGLE)

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
    print(f"[acre] lcd backend={lcd.backend_name()}  aim {aim.backend_name()}")
    lcd.show("ACRE booting", "")
    cam = capture.Camera()
    print(f"[acre] camera backend={cam.backend}")
    detector = detect.Detector()
    print(f"[acre] model backends={detector.backends()}")
    zones = ZoneResolver()
    motion = MotionDetector()
    sensor_unit = sensors.Sensors()
    print(f"[acre] sensors backend={sensor_unit.backend}")
    conn = local_db.connect()
    aim.reset()

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
        # End of run: push any remaining rows and refresh the cloud/web report.
        if not args.no_sync:
            try:
                flush_and_report(conn)
            except Exception as exc:
                print(f"[acre] final sync/report failed ({exc})")
        aim.cleanup()
        lcd.show("ACRE stopped", "")
        lcd.cleanup()
        led.cleanup()
        cam.close()


if __name__ == "__main__":
    main()
