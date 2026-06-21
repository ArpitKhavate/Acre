#!/usr/bin/env python3
"""Live webcam test constrained to Acre's classes: crop / weed / disease / pest.

Acre never uses generic object classes. This test runs frames through Acre's own
pipeline so the only possible outputs are crop / weed / disease / pest / healthy.

Run:
    python scripts/webcam_detect_test.py
    python scripts/webcam_detect_test.py --conf 0.6
Press q in the window to quit.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402

from edge import config  # noqa: E402
from edge import treatments as trt  # noqa: E402

GREEN = (0, 200, 0)
RED = (0, 0, 255)
AMBER = (0, 170, 255)
WHITE = (255, 255, 255)


def _open(source):
    src = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise SystemExit(f"could not open camera/source {source!r}")
    return cap


def _banner(frame, lines, color=WHITE):
    h = 22 + 20 * len(lines)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], h), (0, 0, 0), -1)
    for i, line in enumerate(lines):
        cv2.putText(frame, line, (8, 18 + i * 20), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, color, 2)


def _status_lines(result, score, has_model):
    if not has_model:
        return ["NO MODEL in models/artifacts/"], WHITE
    if score is None:
        return ["Scanning for plant or weed..."], WHITE

    if score.type == "weed":
        chem = trt.pesticide_for("weed") or score.pesticide or "Glyphosate (spot)"
        return [
            f"WEED detected ({score.confidence:.0%})",
            f"Treat: {chem}",
        ], RED

    # Plant / crop path
    disease = result.disease_class or "crop"
    line1 = f"PLANT: {disease}   health {score.score}/100"
    if result.pest_class and result.pest_conf >= config.CLASSIFIER_MIN_CONF:
        pchem = trt.pesticide_for(result.pest_class) or "see IPM guide"
        line2 = f"Pest: {result.pest_class} ({result.pest_conf:.0%}) — {pchem}"
    else:
        line2 = "Pests: none detected"

    if score.type == "disease":
        dchem = score.pesticide or trt.pesticide_for(disease)
        if dchem and dchem != "None":
            line1 += f"   fungicide: {dchem}"
        color = AMBER
    elif score.type == "pest":
        color = RED
    else:
        color = GREEN if score.led_state == "GREEN" else RED
    return [line1, line2], color


def run_acre(args):
    from edge import detect as edet
    from edge import health_score

    det = edet.Detector()
    has_model = det.detector.ok
    print(f"[webcam] Acre pipeline  backends={det.backends()}  "
          f"detector={'loaded' if has_model else 'MISSING'}")

    cap = _open(args.source)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            result = det.analyze(frame, classify_pests=True, conf_thresh=args.conf)
            score = health_score.compute(result)

            for b in result.weed_boxes:
                x, y, w, h = b.xywh
                cv2.rectangle(frame, (x, y), (x + w, y + h), RED, 2)
                cv2.putText(frame, f"weed {b.conf:.2f}", (x, max(y - 6, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, RED, 2)
            if result.plant_box is not None:
                x, y, w, h = result.plant_box.xywh
                label = result.disease_class or result.crop_type or "crop"
                color = GREEN if result.is_healthy else AMBER
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f"{label} {result.disease_conf:.2f}",
                            (x, max(y - 6, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            color, 2)
                if result.pest_class:
                    cv2.putText(frame, f"pest:{result.pest_class} {result.pest_conf:.2f}",
                                (x, min(y + h + 14, frame.shape[0] - 4)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, RED, 1)

            lines, color = _status_lines(result, score, has_model)
            _banner(frame, lines, color)
            cv2.imshow("Acre detection (crop/weed/disease/pest)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def run_coco_plants(args):
    try:
        from ultralytics import YOLO
    except ImportError:
        raise SystemExit("pip install ultralytics opencv-python")

    potted_plant = 58
    model = YOLO("yolov8n.pt")
    print("[webcam] plants-only stopgap: COCO 'potted plant' -> 'crop'")
    cap = _open(args.source)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            res = model.predict(frame, classes=[potted_plant], conf=args.conf,
                                imgsz=args.imgsz, verbose=False)[0]
            for box in res.boxes:
                x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])
                conf = float(box.conf[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), GREEN, 2)
                cv2.putText(frame, f"crop {conf:.2f}", (x1, max(y1 - 6, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 2)
            _banner(frame, ["plants-only stopgap (COCO potted-plant -> crop)"], WHITE)
            cv2.imshow("Acre plants-only (stopgap)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def main():
    ap = argparse.ArgumentParser(description="Webcam test (Acre classes only)")
    ap.add_argument("--coco-plants", action="store_true",
                    help="no-training plants-only stopgap via pretrained YOLOv8n")
    ap.add_argument("--source", default="0", help="webcam index or video path")
    ap.add_argument("--conf", type=float, default=0.55,
                    help="detector confidence (default 0.55)")
    ap.add_argument("--imgsz", type=int, default=416)
    args = ap.parse_args()

    if args.coco_plants:
        run_coco_plants(args)
    else:
        run_acre(args)


if __name__ == "__main__":
    main()
