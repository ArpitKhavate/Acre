"""Prepare Kaggle datasets locally for Acre training (no network calls).

Download the zip files once from Kaggle in your browser, unzip under
models/data/, then run the matching subcommand below. Nothing here hits an API.

Datasets (from your Kaggle notebooks):
  crop-weed      crop-and-weed-detection-data-with-bounding-boxes
  plant-disease  plant-disease-recognition-dataset  (Healthy / Powdery / Rust)
  ip102          ip02-dataset                       (102 pest classes)

Examples:
    python prepare_kaggle_data.py crop-weed \\
        --src data/crop-and-weed-detection-data-with-bounding-boxes/agri_data/data

    python prepare_kaggle_data.py plant-disease \\
        --src data/plant-disease-recognition-dataset

    python prepare_kaggle_data.py ip102 \\
        --src data/ip02-dataset \\
        --classes aphids,whitefly,thrips,spider_mites
"""
from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

DATA = Path(__file__).parent / "data"
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _copy_images(src_dir: Path, dst_dir: Path) -> int:
    dst_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for img in src_dir.iterdir():
        if img.is_file() and img.suffix.lower() in IMG_EXT:
            shutil.copy2(img, dst_dir / img.name)
            n += 1
    return n


def prepare_crop_weed(src: Path, dst: Path, val_ratio: float, seed: int) -> Path:
    """Flat .jpeg + .txt YOLO labels -> Ultralytics train/val layout."""
    if not src.is_dir():
        raise SystemExit(f"Missing source folder: {src}")

    img_dir = dst / "images"
    lbl_dir = dst / "labels"
    for split in ("train", "val"):
        (img_dir / split).mkdir(parents=True, exist_ok=True)
        (lbl_dir / split).mkdir(parents=True, exist_ok=True)

    images = sorted(f for f in src.iterdir() if f.suffix.lower() in IMG_EXT)
    random.seed(seed)
    random.shuffle(images)
    split_at = int(len(images) * (1.0 - val_ratio))
    splits = {"train": images[:split_at], "val": images[split_at:]}

    copied = 0
    for split, files in splits.items():
        for img in files:
            lbl = img.with_suffix(".txt")
            if not lbl.exists():
                continue
            shutil.copy2(img, img_dir / split / img.name)
            shutil.copy2(lbl, lbl_dir / split / lbl.name)
            copied += 1

    yaml = dst / "data.yaml"
    yaml.write_text(
        f"train: { (img_dir / 'train').as_posix() }\n"
        f"val: { (img_dir / 'val').as_posix() }\n"
        "nc: 2\n"
        "names: ['crop', 'weed']\n",
        encoding="utf-8",
    )
    print(f"crop-weed: {copied} image/label pairs -> {dst}")
    print(f"  data.yaml: {yaml}")
    return yaml


def _resolve_nested(root: Path, *candidates: str) -> Path | None:
    for name in candidates:
        p = root / name
        if p.is_dir():
            return p
    return None


def prepare_plant_disease(src: Path, dst: Path) -> tuple[Path, Path]:
    """Kaggle Plant Disease Recognition -> train/ + val/ ImageFolders."""
    train_src = _resolve_nested(src, "Train/Train", "Train", "train")
    val_src = _resolve_nested(src, "Validation/Validation", "Validation", "val")
    if train_src is None:
        raise SystemExit(
            f"Could not find Train folder under {src}\n"
            "Expected: Train/Train/{{Healthy,Powdery,Rust}}/..."
        )
    if val_src is None:
        raise SystemExit(
            f"Could not find Validation folder under {src}\n"
            "Expected: Validation/Validation/{{Healthy,Powdery,Rust}}/..."
        )

    train_dst = dst / "train"
    val_dst = dst / "val"
    total = 0
    for label_dir in sorted(d for d in train_src.iterdir() if d.is_dir()):
        n = _copy_images(label_dir, train_dst / label_dir.name)
        total += n
    for label_dir in sorted(d for d in val_src.iterdir() if d.is_dir()):
        _copy_images(label_dir, val_dst / label_dir.name)

    print(f"plant-disease: {total} train images -> {train_dst}")
    print(f"               val -> {val_dst}")
    return train_dst, val_dst


def _read_classes_txt(root: Path) -> list[str]:
    path = root / "classes.txt"
    if not path.is_file():
        return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _sanitize(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_")


def prepare_ip102(src: Path, dst: Path, classes: list[str] | None) -> tuple[Path, Path | None]:
    """IP102 numeric folders + classes.txt -> named ImageFolder train/ (+ val/)."""
    cls_root = src / "classification"
    if not cls_root.is_dir():
        raise SystemExit(f"Missing {cls_root} (expected ip02-dataset layout)")

    names = _read_classes_txt(src)
    if not names:
        raise SystemExit(f"Missing classes.txt under {src}")

    wanted: set[str] | None = None
    if classes:
        wanted = {c.strip().lower() for c in classes if c.strip()}

    train_dst = dst / "train"
    val_dst = dst / "val"
    train_dst.mkdir(parents=True, exist_ok=True)
    val_dst.mkdir(parents=True, exist_ok=True)

    def _copy_split(split: str, out_root: Path) -> int:
        split_dir = cls_root / split
        if not split_dir.is_dir():
            return 0
        n = 0
        for class_dir in sorted(split_dir.iterdir(), key=lambda p: int(p.name)):
            if not class_dir.is_dir() or not class_dir.name.isdigit():
                continue
            idx = int(class_dir.name)
            if idx >= len(names):
                continue
            cname = _sanitize(names[idx])
            if wanted is not None and cname.lower() not in wanted:
                continue
            out = out_root / cname
            out.mkdir(parents=True, exist_ok=True)
            for img in class_dir.rglob("*"):
                if img.is_file() and img.suffix.lower() in IMG_EXT:
                    shutil.copy2(img, out / img.name)
                    n += 1
        return n

    n_train = _copy_split("train", train_dst)
    n_val = _copy_split("val", val_dst)
    print(f"ip102: {n_train} train + {n_val} val images -> {dst}")
    if n_train == 0:
        raise SystemExit("No training images copied — check --classes filter or dataset path")
    val_path = val_dst if n_val else None
    return train_dst, val_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    cw = sub.add_parser("crop-weed", help="prepare crop/weed YOLO dataset")
    cw.add_argument("--src", required=True, help="agri_data/data folder with .jpeg+.txt")
    cw.add_argument("--dst", default=str(DATA / "weed_crop_prepared"))
    cw.add_argument("--val-ratio", type=float, default=0.2)
    cw.add_argument("--seed", type=int, default=42)

    pd = sub.add_parser("plant-disease", help="prepare Healthy/Powdery/Rust folders")
    pd.add_argument("--src", required=True, help="plant-disease-recognition-dataset root")
    pd.add_argument("--dst", default=str(DATA / "plant_disease_prepared"))

    ip = sub.add_parser("ip102", help="prepare IP102 pest ImageFolder")
    ip.add_argument("--src", required=True, help="ip02-dataset root")
    ip.add_argument("--dst", default=str(DATA / "ip102_prepared"))
    ip.add_argument("--classes", default=None,
                    help="comma-separated pest names to keep (matches classes.txt)")
    ip.add_argument("--list-classes", action="store_true",
                    help="print classes.txt and exit (pick exact names for --classes)")

    args = ap.parse_args()

    if args.cmd == "crop-weed":
        yaml = prepare_crop_weed(Path(args.src), Path(args.dst), args.val_ratio, args.seed)
        print("\nTrain with:")
        print(f'    python train_detector.py --data "{yaml}" --epochs 30')
    elif args.cmd == "plant-disease":
        train_p, val_p = prepare_plant_disease(Path(args.src), Path(args.dst))
        print("\nTrain with:")
        print(f'    python train_disease_classifier.py --data "{train_p}" '
              f'--val-data "{val_p}" --epochs 15')
    elif args.cmd == "ip102":
        src = Path(args.src)
        if args.list_classes:
            names = _read_classes_txt(src)
            if not names:
                raise SystemExit(f"No classes.txt under {src}")
            for i, n in enumerate(names):
                print(f"{i:3d}  {n}")
            return
        classes = [c.strip() for c in args.classes.split(",")] if args.classes else None
        train_p, val_p = prepare_ip102(Path(args.src), Path(args.dst), classes)
        cmd = f'    python train_pest_classifier.py --data "{train_p}" --epochs 15'
        if val_p:
            cmd += f' --val-data "{val_p}"'
        print("\nTrain with:")
        print(cmd)


if __name__ == "__main__":
    main()
