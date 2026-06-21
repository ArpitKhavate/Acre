# Dataset folder (local only — not on GitHub)

## Easiest path: automatic bootstrap

From `models/`, one command downloads **equivalent** data (same classes as your
Kaggle notebooks) and trains all three ONNX models:

```bash
pip install -r requirements-train.txt datasets
python bootstrap_all.py
```

This uses Hugging Face mirrors of:
- crop / weed (aerial detection dataset)
- Healthy / Powdery / Rust (plant disease recognition)
- IP102 pests (aphids, Thrips, whitefly, spider mite subset)

Your Kaggle notebooks are copied to `models/notebooks/`.

## Manual Kaggle path (optional)

If you prefer the exact Kaggle zip files, download and unzip here:

```
models/data/
  crop-and-weed-detection-data-with-bounding-boxes/agri_data/data/
  plant-disease-recognition-dataset/
  ip02-dataset/
```

Then:

```bash
python prepare_kaggle_data.py crop-weed --src data/.../agri_data/data
python prepare_kaggle_data.py plant-disease --src data/plant-disease-recognition-dataset
python prepare_kaggle_data.py ip102 --src data/ip02-dataset --list-classes
```

## Pi deployment

Only `models/artifacts/*.onnx` + `models/labels/*.json` go on the Pi.
No raw data, no WiFi, no API calls at inference time.
