"""Train the insect-pest classifier (MobileNetV3-Small) and export ONNX.

Off-device only. Produces artifacts/pest.onnx + labels/pest.json.

Expects an ImageFolder layout (subset IP102 to your demo pests first with
`python prepare_data.py ip102-subset --classes aphids,whitefly,thrips`):

    data/ip102_subset/
        aphids/
        whitefly/
        thrips/

Usage:
    python train_pest_classifier.py --data data/ip102_subset --epochs 15
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
        out_onnx=ARTIFACTS / "pest.onnx",
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
    )
    (LABELS / "pest.json").write_text(
        json.dumps({"imgsz": args.imgsz, "names": classes}, indent=2)
    )
    print(f"Wrote artifacts/pest.onnx and labels/pest.json ({len(classes)} classes)")


if __name__ == "__main__":
    main()
