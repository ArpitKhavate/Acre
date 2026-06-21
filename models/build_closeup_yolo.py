"""Build a close-up crop/weed YOLO dataset (no Kaggle).

Sources (Hugging Face, free):
  crop -> NouRed/plant-disease-recognition  (close-up plant leaves)
  weed -> ButterChicken98/deepweeds_clip_corpus_90_10  (field weed photos)

Each image is single-object: one full-frame YOLO box (crop=0, weed=1).
Works for phone/webcam demos and handheld Pi scans.

Usage (from models/):
    python build_closeup_yolo.py
    python train_detector.py --data data/closeup_yolo/data.yaml --epochs 25
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = DATA / "closeup_yolo"
CROP_LABEL = "0 0.5 0.5 0.92 0.92\n"
WEED_LABEL = "1 0.5 0.5 0.92 0.92\n"


def _log(msg: str) -> None:
    print(f"[closeup-yolo] {msg}", flush=True)


def _write_pair(img_dir: Path, lbl_dir: Path, stem: str, image, label: str) -> None:
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    image.save(img_dir / f"{stem}.jpg")
    (lbl_dir / f"{stem}.txt").write_text(label, encoding="utf-8")


def export_crop(split: str, indices: list[int], start_idx: int = 0) -> int:
    from datasets import load_dataset

    ds = load_dataset("NouRed/plant-disease-recognition")["train"]
    img_dir = OUT / "images" / split
    lbl_dir = OUT / "labels" / split
    for j, i in enumerate(indices):
        row = ds[i]
        _write_pair(img_dir, lbl_dir, f"crop_{start_idx + j:05d}", row["image"], CROP_LABEL)
    return len(indices)


def export_weed(split: str, indices: list[int], start_idx: int = 0) -> int:
    from datasets import load_dataset

    ds = load_dataset("ButterChicken98/deepweeds_clip_corpus_90_10")["train"]
    img_dir = OUT / "images" / split
    lbl_dir = OUT / "labels" / split
    for j, i in enumerate(indices):
        row = ds[i]
        _write_pair(img_dir, lbl_dir, f"weed_{start_idx + j:05d}", row["image"], WEED_LABEL)
    return len(indices)


def export_synthetic_negatives(split: str, n: int, seed: int) -> int:
    """Background images with empty labels — reduces person/wall false positives."""
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(seed + 99)
    img_dir = OUT / "images" / split
    lbl_dir = OUT / "labels" / split
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    for j in range(n):
        kind = j % 5
        if kind == 0:
            arr = rng.integers(170, 220, (480, 640, 3), dtype=np.uint8)
        elif kind == 1:
            arr = np.clip(rng.normal(160, 25, (480, 640, 3)), 0, 255).astype(np.uint8)
        elif kind == 2:
            arr = rng.integers(120, 190, (480, 640, 3), dtype=np.uint8)
            arr[:, :, 0] = np.clip(arr[:, :, 0] + 30, 0, 255)
        elif kind == 3:
            arr = rng.integers(0, 80, (480, 640, 3), dtype=np.uint8)
        else:
            arr = rng.integers(0, 256, (480, 640, 3), dtype=np.uint8)
        stem = f"neg_{j:05d}"
        Image.fromarray(arr).save(img_dir / f"{stem}.jpg")
        (lbl_dir / f"{stem}.txt").write_text("", encoding="utf-8")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop-train", type=int, default=1000)
    ap.add_argument("--crop-val", type=int, default=150)
    ap.add_argument("--weed-train", type=int, default=1000)
    ap.add_argument("--weed-val", type=int, default=150)
    ap.add_argument("--neg-train", type=int, default=400,
                    help="synthetic background images with no labels (reduces false positives)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--force",
        action="store_true",
        help="Delete and rebuild even if data/closeup_yolo already exists",
    )
    ap.add_argument(
        "--neg-only",
        action="store_true",
        help="Only add synthetic negative images (skip crop/weed export)",
    )
    args = ap.parse_args()

    if args.neg_only:
        _log(f"adding {args.neg_train} negative background images...")
        export_synthetic_negatives("train", args.neg_train, args.seed)
        return

    random.seed(args.seed)
    expected_train = args.crop_train + args.weed_train
    train_dir = OUT / "images" / "train"
    has_negs = (
        len(list(train_dir.glob("neg_*.jpg"))) >= args.neg_train
        if train_dir.is_dir() else False
    )
    if OUT.exists() and not args.force:
        n_train = len(list(train_dir.glob("*.jpg"))) if train_dir.is_dir() else 0
        if (OUT / "data.yaml").is_file() and n_train >= expected_train and has_negs:
            _log(f"dataset already complete ({n_train} train images) — skip (use --force to rebuild)")
            return
        _log(f"incomplete dataset ({n_train}/{expected_train} train, negs={has_negs}) — rebuilding")
    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    _log("exporting close-up crop images (plant leaves)...")
    crop_idx = list(range(1322))
    random.shuffle(crop_idx)
    n_ct, n_cv = args.crop_train, args.crop_val
    export_crop("train", crop_idx[:n_ct])
    export_crop("val", crop_idx[n_ct:n_ct + n_cv], start_idx=n_ct)

    _log("exporting close-up weed images (DeepWeeds)...")
    weed_idx = list(range(15759))
    random.shuffle(weed_idx)
    n_wt, n_wv = args.weed_train, args.weed_val
    export_weed("train", weed_idx[:n_wt])
    export_weed("val", weed_idx[n_wt:n_wt + n_wv], start_idx=n_wt)

    _log(f"exporting {args.neg_train} negative background images...")
    export_synthetic_negatives("train", args.neg_train, args.seed)

    yaml = OUT / "data.yaml"
    yaml.write_text(
        f"train: {(OUT / 'images' / 'train').as_posix()}\n"
        f"val: {(OUT / 'images' / 'val').as_posix()}\n"
        "nc: 2\n"
        "names: ['crop', 'weed']\n",
        encoding="utf-8",
    )
    _log(f"done: {n_ct + n_wt + args.neg_train} train, {n_cv + n_wv} val -> {OUT}")
    _log("train with:")
    _log(f'    python train_detector.py --data "{yaml}" --epochs 25')


if __name__ == "__main__":
    main()
