#!/usr/bin/env python3
"""Live webcam test constrained to Acre's classes: crop / weed / disease / pest.

Acre never uses generic object classes. This test runs frames through Acre's own
pipeline so the only possible outputs are crop / weed / disease / pest / healthy.

Modes:
  (default) acre  -- run edge/detect.py + health_score and draw ONLY our classes.
                     Needs trained ONNX models in models/artifacts/. With none
                     present it says so and detects nothing (it will not invent
                     other classes). Add --pest to also run the pest classifier.
  --coco-plants   -- NO-training stopgap: pretrained YOLOv8n filtered to the COCO
                     "potted plant" class only, relabeled "crop", so you can see
                     plants-only detection today (no people/cups). This is a
                     placeholder until the real crop/weed/disease/pest weights
                     are trained.

Install:  pip install opencv-python            (and ultralytics for --coco-plants)
Run:
    python scripts/webcam_detect_test.py
    python scripts/webcam_detect_test.py --pest
    python scripts/webcam_detect_test.py --coco-plants
Press q in the window to quit.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402

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


def _banner(frame, text, color=WHITE):
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 28), (0, 0, 0), -1)
    cv2.putText(frame, text, (8, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def run_acre(args):
    from edge import detect as edet
    from edge import health_score

    det = edet.Detector()
    has_model = det.detector.ok
    print(f"[webcam] Acre pipeline  model backends={det.backends()}  "
          f"detector={'loaded' if has_model else 'MISSING'}")

    cap = _open(args.source)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            result = det.analyze(frame, motion=args.pest, conf_thresh=args.conf)
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

            if has_model:
                if score is not None:
                    text = f"{score.type}: {score.class_name}   health {score.score}/100"
                else:
                    text = "Scanning for plants or weeds..."
            else:
                text = "NO TRAINED MODEL in models/artifacts/  -> detector disabled"
            _banner(frame, text)
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

    potted_plant = 58  # COCO class id
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
            _banner(frame, "plants-only stopgap (COCO potted-plant -> crop)")
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
    ap.add_argument("--pest", action="store_true",
                    help="also run the pest classifier (Acre mode)")
    ap.add_argument("--source", default="0", help="webcam index or video path")
    ap.add_argument("--conf", type=float, default=0.55,
                    help="detector confidence (default 0.55; raise if too many false boxes)")
    ap.add_argument("--imgsz", type=int, default=416)
    args = ap.parse_args()

    if args.coco_plants:
        run_coco_plants(args)
    else:
        run_acre(args)


if __name__ == "__main__":
    main()
