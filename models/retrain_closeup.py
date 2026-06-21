#!/usr/bin/env python3
"""Build close-up crop/weed data + train detector (no Kaggle). One command."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def main():
    ap_epochs = "25"
    if len(sys.argv) > 1:
        ap_epochs = sys.argv[1]

    subprocess.run([sys.executable, "build_closeup_yolo.py"], cwd=ROOT, check=True)
    yaml = ROOT / "data" / "closeup_yolo" / "data.yaml"
    subprocess.run(
        [sys.executable, "train_detector.py", "--data", str(yaml), "--epochs", ap_epochs],
        cwd=ROOT,
        check=True,
    )
    print("\n[retrain_closeup] Done. Test with:")
    print("    python ../scripts/webcam_detect_test.py")


if __name__ == "__main__":
    main()
