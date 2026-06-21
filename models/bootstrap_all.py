#!/usr/bin/env python3
"""One-shot bootstrap: fetch notebook-equivalent data + train + export ONNX.

Uses Hugging Face mirrors of your three Kaggle datasets (same classes):
  - Francesco/weed-crop-aerial        -> crop / weed detector (YOLO)
  - NouRed/plant-disease-recognition  -> Healthy / Powdery / Rust
  - hibana2077/IP102                  -> pest classifier (subset)

Training is off-device only. The Pi runs the exported ONNX files offline.

Usage (from models/):
    python bootstrap_all.py
    python bootstrap_all.py --epochs-det 15 --epochs-cls 8 --skip-train   # data only
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
NOTEBOOKS = ROOT / "notebooks"

# IP102 class indices from hibana2077/IP102 labels (matches classes.txt order)
PEST_SUBSET = {
    "aphids": 25,
    "Thrips": 55,
    "Trialeurodes_vaporariorum": 72,  # whitefly proxy
    "longlegged_spider_mite": 33,
}


def _log(msg: str) -> None:
    print(f"[bootstrap] {msg}", flush=True)


def copy_notebooks() -> None:
    desktop = Path.home() / "OneDrive" / "Desktop"
    NOTEBOOKS.mkdir(exist_ok=True)
    names = [
        "crop-vs-weed-using-yolov8.ipynb",
        "plant-disease-classification.ipynb",
        "pest-classification.ipynb",
    ]
    for name in names:
        src = desktop / name
        if src.is_file():
            shutil.copy2(src, NOTEBOOKS / name)
            _log(f"copied notebook -> {NOTEBOOKS / name}")
        else:
            _log(f"notebook not on Desktop (skip): {name}")


def export_plant_disease(val_ratio: float = 0.15, seed: int = 42) -> tuple[Path, Path]:
    import gc
    from datasets import load_dataset

    _log("downloading plant disease (Healthy / Powdery / Rust)...")
    ds = load_dataset("NouRed/plant-disease-recognition")
    n = ds["train"].num_rows
    indices = list(range(n))
    random.seed(seed)
    random.shuffle(indices)
    n_val = max(1, int(n * val_ratio))
    val_set = set(indices[:n_val])

    train_root = DATA / "plant_disease_prepared" / "train"
    val_root = DATA / "plant_disease_prepared" / "val"
    for root in (train_root, val_root):
        for cls in ("Healthy", "Powdery", "Rust"):
            (root / cls).mkdir(parents=True, exist_ok=True)

    n_train = n_val_count = 0
    for i in indices:
        row = ds["train"][i]
        cls = row["text"]
        root = val_root if i in val_set else train_root
        tag = "val" if i in val_set else "train"
        row["image"].save(root / cls / f"{cls}_{i:05d}.jpg")
        if tag == "val":
            n_val_count += 1
        else:
            n_train += 1
        if (i + 1) % 200 == 0:
            gc.collect()

    _log(f"plant disease: {n_train} train, {n_val_count} val")
    return train_root, val_root


def _coco_to_yolo_line(cat_id: int, bbox, w: int, h: int) -> str | None:
    # Francesco categories: 0=weed-crop-aerial (skip), 1=crop, 2=weed
    if cat_id == 0:
        return None
    name_to_yolo = {1: 0, 2: 1}  # crop=0, weed=1
    if cat_id not in name_to_yolo:
        return None
    x, y, bw, bh = bbox
    cx = (x + bw / 2) / w
    cy = (y + bh / 2) / h
    nw = bw / w
    nh = bh / h
    return f"{name_to_yolo[cat_id]} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}"


def export_crop_weed() -> Path:
    """Close-up crop/weed YOLO data (phone/webcam + handheld Pi). No Kaggle."""
    import subprocess

    _log("building close-up crop/weed dataset (HF plant leaves + DeepWeeds)...")
    subprocess.run([sys.executable, "build_closeup_yolo.py"], cwd=ROOT, check=True)
    return DATA / "closeup_yolo" / "data.yaml"


def export_ip102_pests() -> tuple[Path, Path]:
    from datasets import load_dataset

    _log("downloading IP102 pest dataset (subset)...")
    ds = load_dataset("hibana2077/IP102")
    idx_to_name = {v: k for k, v in PEST_SUBSET.items()}
    wanted = set(PEST_SUBSET.values())

    train_root = DATA / "ip102_prepared" / "train"
    val_root = DATA / "ip102_prepared" / "val"
    for root in (train_root, val_root):
        root.mkdir(parents=True, exist_ok=True)

    counts = {"train": 0, "val": 0}
    for hf_split, out_split in (("train", "train"), ("val", "val")):
        root = train_root if out_split == "train" else val_root
        for i, row in enumerate(ds[hf_split]):
            label = int(row["label"])
            if label not in wanted:
                continue
            cname = idx_to_name[label]
            cdir = root / cname
            cdir.mkdir(parents=True, exist_ok=True)
            row["image"].save(cdir / f"{cname}_{i:05d}.jpg")
            counts[out_split] += 1

    _log(f"ip102 subset: {counts['train']} train, {counts['val']} val")
    return train_root, val_root


def run_train(epochs_det: int, epochs_cls: int) -> None:
    yaml = DATA / "closeup_yolo" / "data.yaml"
    dis_train = DATA / "plant_disease_prepared" / "train"
    dis_val = DATA / "plant_disease_prepared" / "val"
    pest_train = DATA / "ip102_prepared" / "train"
    pest_val = DATA / "ip102_prepared" / "val"

    steps = [
        [sys.executable, "train_detector.py",
         "--data", str(yaml), "--epochs", str(epochs_det)],
        [sys.executable, "train_disease_classifier.py",
         "--data", str(dis_train), "--val-data", str(dis_val),
         "--epochs", str(epochs_cls), "--workers", "0"],
        [sys.executable, "train_pest_classifier.py",
         "--data", str(pest_train), "--val-data", str(pest_val),
         "--epochs", str(epochs_cls), "--workers", "0"],
    ]
    for cmd in steps:
        _log("running: " + " ".join(cmd))
        subprocess.run(cmd, cwd=ROOT, check=True)


def verify_artifacts() -> None:
    art = ROOT / "artifacts"
    needed = ["detector.onnx", "disease.onnx", "pest.onnx"]
    missing = [n for n in needed if not (art / n).exists()]
    if missing:
        raise SystemExit(f"Missing artifacts: {missing}")
    _log("all three ONNX models ready in models/artifacts/")
    _log("Test: python ../scripts/webcam_detect_test.py")
    _log("Pi: copy artifacts/*.onnx + labels/*.json — fully offline on QNX")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs-det", type=int, default=15,
                    help="detector epochs (notebook used 30-70; 15 is a quick demo)")
    ap.add_argument("--epochs-cls", type=int, default=10,
                    help="classifier epochs")
    ap.add_argument("--skip-train", action="store_true")
    ap.add_argument("--skip-notebooks", action="store_true")
    ap.add_argument("--skip-export", action="store_true",
                    help="reuse existing models/data/*_prepared folders")
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    if not args.skip_notebooks:
        copy_notebooks()

    if not args.skip_export:
        if not (DATA / "closeup_yolo" / "data.yaml").exists():
            export_crop_weed()
        else:
            _log("closeup_yolo already prepared — skip (delete folder to redo)")
        export_plant_disease()
        export_ip102_pests()
    else:
        _log("using existing prepared data")

    if not args.skip_train:
        run_train(args.epochs_det, args.epochs_cls)
        verify_artifacts()
    else:
        _log("data prepared under models/data/ — run training manually or re-run without --skip-train")


if __name__ == "__main__":
    main()
