"""Train the insect-pest classifier (MobileNetV3-Small) and export ONNX.

Off-device only. Produces artifacts/pest.onnx + labels/pest.json.

Uses the Kaggle ip02-dataset (IP102, 102 pest classes). Subset to demo pests
with prepare_kaggle_data.py --classes.

Usage:
    python prepare_kaggle_data.py ip102 \\
        --src data/ip02-dataset \\
        --classes aphids,whitefly,thrips,spider_mites
    python train_pest_classifier.py \\
        --data data/ip102_prepared/train \\
        --val-data data/ip102_prepared/val \\
        --epochs 15
"""
import argparse
import json
from pathlib import Path

from common_classifier import train_classifier

ARTIFACTS = Path(__file__).parent / "artifacts"
LABELS = Path(__file__).parent / "labels"
IMG_SIZE = 224


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="ImageFolder train root")
    ap.add_argument("--val-data", default=None, help="ImageFolder val root")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--imgsz", type=int, default=IMG_SIZE)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--workers", type=int, default=0,
                    help="DataLoader workers (0 is safest on Windows)")
    args = ap.parse_args()

    ARTIFACTS.mkdir(exist_ok=True)
    LABELS.mkdir(exist_ok=True)

    classes = train_classifier(
        data_dir=args.data,
        out_onnx=ARTIFACTS / "pest.onnx",
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        val_dir=args.val_data,
    )
    (LABELS / "pest.json").write_text(
        json.dumps({"imgsz": args.imgsz, "names": classes}, indent=2)
    )
    print(f"Wrote artifacts/pest.onnx and labels/pest.json ({len(classes)} classes)")


if __name__ == "__main__":
    main()
