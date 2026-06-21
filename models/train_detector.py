"""Train the YOLOv8n weed/crop detector and export to ONNX.

Off-device only. Produces artifacts/detector.onnx for the Pi (fully offline at
inference time via edge/detect.py).

Matches the Kaggle notebook "crop-vs-weed-using-yolov8" but uses yolov8n (nano)
so it runs within the Pi 5 CPU budget.

Usage:
    # 1. Unzip Kaggle dataset locally, then prepare (no API):
    python prepare_kaggle_data.py crop-weed \\
        --src data/crop-and-weed-detection-data-with-bounding-boxes/agri_data/data

    # 2. Train + export ONNX:
    python train_detector.py --data data/weed_crop_prepared/data.yaml --epochs 30
"""
import argparse
import json
import sys
from pathlib import Path

ARTIFACTS = Path(__file__).parent / "artifacts"
LABELS = Path(__file__).parent / "labels"
IMG_SIZE = 416  # nano @ 416px fits the Pi 5 scan budget


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Ultralytics data.yaml")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--imgsz", type=int, default=IMG_SIZE)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr0", type=float, default=0.003)
    ap.add_argument("--weights", default="yolov8n.pt",
                    help="yolov8n.pt for Pi; notebook used yolov8s (heavier)")
    ap.add_argument("--workers", type=int, default=None,
                    help="dataloader workers (default 0 on Windows, 8 elsewhere)")
    args = ap.parse_args()
    workers = args.workers if args.workers is not None else (0 if sys.platform == "win32" else 8)

    from ultralytics import YOLO

    ARTIFACTS.mkdir(exist_ok=True)
    LABELS.mkdir(exist_ok=True)

    model = YOLO(args.weights)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=workers,
        optimizer="AdamW",
        lr0=args.lr0,
        lrf=0.01,
    )

    best = Path(results.save_dir) / "weights" / "best.pt"
    model = YOLO(str(best))

    onnx_path = model.export(format="onnx", imgsz=args.imgsz, opset=12, simplify=True)
    out = ARTIFACTS / "detector.onnx"
    Path(onnx_path).replace(out)

    names = model.names
    (LABELS / "detector.json").write_text(
        json.dumps({"imgsz": args.imgsz, "names": names}, indent=2)
    )
    print(f"Wrote {out} and labels/detector.json ({len(names)} classes: {list(names.values())})")
    print("Copy artifacts/*.onnx + labels/*.json to the Pi — inference is fully offline.")


if __name__ == "__main__":
    main()
