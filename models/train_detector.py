"""Train the YOLOv8n weed/crop detector and export to ONNX.

Off-device only (needs a GPU ideally). Produces artifacts/detector.onnx, which
ships to the Pi and is loaded by edge/detect.py via OpenCV DNN / ONNX Runtime.

Usage:
    python train_detector.py --data data/weed_crop/data.yaml --epochs 50

The --data yaml is a standard Ultralytics dataset config (train/val paths +
class names), e.g. exported directly from Roboflow Universe.
"""
import argparse
import json
from pathlib import Path

ARTIFACTS = Path(__file__).parent / "artifacts"
LABELS = Path(__file__).parent / "labels"
IMG_SIZE = 416  # nano model at 416px = comfortable on the Pi 5 CPU


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Ultralytics dataset yaml")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=IMG_SIZE)
    ap.add_argument("--weights", default="yolov8n.pt")
    args = ap.parse_args()

    from ultralytics import YOLO

    ARTIFACTS.mkdir(exist_ok=True)
    LABELS.mkdir(exist_ok=True)

    model = YOLO(args.weights)
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=16)

    # Export to ONNX (opset 12 plays nicely with OpenCV's DNN module).
    onnx_path = model.export(format="onnx", imgsz=args.imgsz, opset=12, simplify=True)
    out = ARTIFACTS / "detector.onnx"
    Path(onnx_path).replace(out)

    # Persist the class-id -> name map for the edge side.
    names = model.names  # {0: 'crop', 1: 'weed', ...}
    (LABELS / "detector.json").write_text(
        json.dumps({"imgsz": args.imgsz, "names": names}, indent=2)
    )
    print(f"Wrote {out} and labels/detector.json ({len(names)} classes)")


if __name__ == "__main__":
    main()
