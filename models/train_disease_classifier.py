"""Train the plant-ID + disease classifier (MobileNetV3-Small) and export ONNX.

Off-device only. Produces artifacts/disease.onnx + labels/disease.json.

Expects an ImageFolder layout (one subdir per class), e.g. PlantVillage merged
with PlantDoc:

    data/plantvillage/
        Tomato___healthy/
        Tomato___Early_blight/
        Potato___Late_blight/
        ...

Usage:
    python train_disease_classifier.py --data data/plantvillage --epochs 15
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
    ap.add_argument("--data", required=True, help="ImageFolder root")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--imgsz", type=int, default=IMG_SIZE)
    ap.add_argument("--batch", type=int, default=64)
    args = ap.parse_args()

    ARTIFACTS.mkdir(exist_ok=True)
    LABELS.mkdir(exist_ok=True)

    classes = train_classifier(
        data_dir=args.data,
        out_onnx=ARTIFACTS / "disease.onnx",
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
    )
    # Class names encode "Crop___Condition"; the edge side splits on "___" to get
    # crop_type + disease/healthy. Healthy classes end in "healthy".
    (LABELS / "disease.json").write_text(
        json.dumps({"imgsz": args.imgsz, "names": classes}, indent=2)
    )
    print(f"Wrote artifacts/disease.onnx and labels/disease.json ({len(classes)} classes)")


if __name__ == "__main__":
    main()
