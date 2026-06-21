"""Dataset prep helpers (off-device).

Subcommands:
    ip102-subset   Copy a chosen subset of IP102 classes into data/ip102_subset/
                   so the pest classifier trains on only the pests you can stage.
    merge-disease  Merge PlantDoc class folders into a PlantVillage ImageFolder
                   so the disease classifier sees in-the-wild images too.

These are convenience utilities, not a download manager. Download the raw
datasets manually (see README.md) into models/data/ first.
"""
import argparse
import shutil
from pathlib import Path

DATA = Path(__file__).parent / "data"


def ip102_subset(classes: list[str], src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for cls in classes:
        src_dir = src / cls
        if not src_dir.is_dir():
            print(f"  skip (missing): {src_dir}")
            continue
        out_dir = dst / cls
        out_dir.mkdir(exist_ok=True)
        for img in src_dir.glob("*"):
            shutil.copy2(img, out_dir / img.name)
        print(f"  {cls}: {len(list(out_dir.glob('*')))} images")
    print(f"Wrote subset to {dst}")


def merge_disease(plantvillage: Path, plantdoc: Path):
    """Copy PlantDoc folders into the PlantVillage tree (matching class names)."""
    merged = 0
    for cls_dir in plantdoc.iterdir():
        if not cls_dir.is_dir():
            continue
        target = plantvillage / cls_dir.name
        target.mkdir(exist_ok=True)
        for img in cls_dir.glob("*"):
            shutil.copy2(img, target / f"plantdoc_{img.name}")
            merged += 1
    print(f"Merged {merged} PlantDoc images into {plantvillage}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("ip102-subset")
    s1.add_argument("--classes", required=True, help="comma-separated class names")
    s1.add_argument("--src", default=str(DATA / "ip102"))
    s1.add_argument("--dst", default=str(DATA / "ip102_subset"))

    s2 = sub.add_parser("merge-disease")
    s2.add_argument("--plantvillage", default=str(DATA / "plantvillage"))
    s2.add_argument("--plantdoc", default=str(DATA / "plantdoc"))

    args = ap.parse_args()
    if args.cmd == "ip102-subset":
        ip102_subset([c.strip() for c in args.classes.split(",")],
                     Path(args.src), Path(args.dst))
    elif args.cmd == "merge-disease":
        merge_disease(Path(args.plantvillage), Path(args.plantdoc))


if __name__ == "__main__":
    main()
