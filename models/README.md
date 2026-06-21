# Acre — Models (train on laptop, run offline on Pi / QNX)

Train **once** on your laptop with the Kaggle datasets from your notebooks.
Export to **ONNX**. Copy the small `.onnx` files to the Pi — the farm scan loop
runs **fully offline** (no WiFi, no API calls at inference time).

## The three models → Acre classes

| Model | Acre output | Kaggle dataset | Your notebook |
|---|---|---|---|
| `detector.onnx` | **crop**, **weed** | [crop-and-weed-detection-data-with-bounding-boxes](https://www.kaggle.com/datasets) | crop-vs-weed-using-yolov8 |
| `disease.onnx` | **Healthy**, **Powdery**, **Rust** | [plant-disease-recognition-dataset](https://www.kaggle.com/datasets) | plant-disease-classification |
| `pest.onnx` | pest names from IP102 | [ip02-dataset](https://www.kaggle.com/datasets) | pest-classification |

The edge pipeline (`edge/detect.py`) loads these three ONNX files plus `labels/*.json`
and maps results to **crop / weed / disease / pest / healthy** for the LED, LCD, and
reports.

> We use **YOLOv8n** + **MobileNetV3-Small** (not yolov8s / ResNet34 from the
> notebooks) so all three models fit the Pi 5 CPU scan budget.

## Step 0 — Download datasets manually (one time, in browser)

On [kaggle.com](https://www.kaggle.com), download and unzip each dataset into
`models/data/`:

```
models/data/
  crop-and-weed-detection-data-with-bounding-boxes/
    agri_data/data/          ← .jpeg + .txt YOLO labels (flat folder)
  plant-disease-recognition-dataset/
    Train/Train/             ← Healthy, Powdery, Rust
    Validation/Validation/
  ip02-dataset/
    classes.txt
    classification/train/0..101/
    classification/val/0..101/
```

No scripts in this repo download anything — you bring the folders locally.

## Step 1 — Install training deps (laptop only, not the Pi)

```bash
cd models
pip install -r requirements-train.txt
```

## Step 2 — Prepare + train each model

### Crop / weed detector

```bash
python prepare_kaggle_data.py crop-weed \
    --src data/crop-and-weed-detection-data-with-bounding-boxes/agri_data/data

python train_detector.py --data data/weed_crop_prepared/data.yaml --epochs 30
```

### Plant disease (Healthy / Powdery / Rust)

```bash
python prepare_kaggle_data.py plant-disease \
    --src data/plant-disease-recognition-dataset

python train_disease_classifier.py \
    --data data/plant_disease_prepared/train \
    --val-data data/plant_disease_prepared/val \
    --epochs 15 --workers 0
```

### Pest (IP102 — subset to demo pests)

```bash
python prepare_kaggle_data.py ip102 \
    --src data/ip02-dataset \
    --classes aphids,whitefly,thrips,spider_mites

python train_pest_classifier.py \
    --data data/ip102_prepared/train \
    --val-data data/ip102_prepared/val \
    --epochs 15 --workers 0
```

Each script writes to `artifacts/*.onnx` and updates `labels/*.json`.

## Step 3 — Test on your laptop webcam (offline after training)

```bash
pip install opencv-python onnxruntime
python ../scripts/webcam_detect_test.py          # crop / weed / disease
python ../scripts/webcam_detect_test.py --pest   # + pest classifier
```

Press `q` to quit. You should see green **crop** boxes, red **weed** boxes, and a
banner like `disease: Powdery  health 72/100` or `healthy: Healthy  health 100/100`.

## Step 4 — Deploy to the Pi (QNX, no WiFi needed)

Copy these to the Pi SD card (same paths as in the repo):

```
models/artifacts/detector.onnx
models/artifacts/disease.onnx
models/artifacts/pest.onnx
models/labels/detector.json
models/labels/disease.json
models/labels/pest.json
```

The scan loop (`edge/main.py`) picks them up automatically. Inference uses
ONNX Runtime or OpenCV DNN — **zero network calls**.

## Reference notebooks

Your Kaggle notebooks (local copies) document the original training approach:

- `crop-vs-weed-using-yolov8.ipynb` — YOLOv8s, 80/20 split, classes `crop`/`weed`
- `plant-disease-classification.ipynb` — ResNet34, Healthy/Powdery/Rust
- `pest-classification.ipynb` — IP102 folder loader

Acre's scripts mirror the same datasets but export Pi-sized ONNX models.

## Why three models (not one)

The detector finds *where* a plant or weed is. The classifiers say *whether* it is
healthy, diseased, or has pests. Splitting keeps each model small enough to run
within ~1 s on the Pi 5 CPU (PRD section 12).
