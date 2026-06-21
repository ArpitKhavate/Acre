"""Train the plant-ID + disease classifier (MobileNetV3-Small) and export ONNX.

Off-device only. Produces artifacts/disease.onnx + labels/disease.json.

Uses the Kaggle "plant-disease-recognition-dataset" (Healthy / Powdery / Rust).
We export MobileNetV3-Small (not ResNet34 from the notebook) so inference fits
the Pi 5 CPU budget.

Usage:
    python prepare_kaggle_data.py plant-disease \\
        --src data/plant-disease-recognition-dataset
    python train_disease_classifier.py \\
        --data data/plant_disease_prepared/train \\
        --val-data data/plant_disease_prepared/val \\
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
    ap.add_argument("--val-data", default=None, help="ImageFolder val root (Kaggle Validation/)")
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
        out_onnx=ARTIFACTS / "disease.onnx",
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        val_dir=args.val_data,
    )
    # Class names encode "Crop___Condition"; the edge side splits on "___" to get
    # crop_type + disease/healthy. Healthy classes end in "healthy".
    (LABELS / "disease.json").write_text(
        json.dumps({"imgsz": args.imgsz, "names": classes}, indent=2)
    )
    print(f"Wrote artifacts/disease.onnx and labels/disease.json ({len(classes)} classes)")


if __name__ == "__main__":
    main()
