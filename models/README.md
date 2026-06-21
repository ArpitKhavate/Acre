# Acre — Models (trained off-device, run on the Pi)

All three models are trained **off-device** (Colab / a laptop GPU / Roboflow) and
exported to **ONNX**. The exported `.onnx` files are the only artifacts copied to
the Pi 5; inference there runs fully offline via OpenCV DNN / ONNX Runtime.

## The three models

| Model | Task | Dataset(s) | Script | Output |
|---|---|---|---|---|
| Detector | plant vs. weed, locate plant crop | DeepWeeds / Roboflow crop-vs-weed | `train_detector.py` | `artifacts/detector.onnx` |
| Disease classifier | crop species + healthy/diseased | PlantVillage + PlantDoc | `train_disease_classifier.py` | `artifacts/disease.onnx` |
| Pest classifier | insect pest class | IP102 (subset) | `train_pest_classifier.py` | `artifacts/pest.onnx` |

The edge pipeline (`edge/detect.py`) loads these three ONNX files plus the label
maps in `labels/`.

## Quick start

```bash
pip install -r requirements-train.txt

# 1. Detector (Ultralytics handles ONNX export directly)
python train_detector.py --data data/weed_crop/data.yaml --epochs 50

# 2. Disease classifier
python train_disease_classifier.py --data data/plantvillage --epochs 15

# 3. Pest classifier (subset IP102 to your demo pests first)
python prepare_data.py ip102-subset --classes aphids,whitefly,thrips
python train_pest_classifier.py --data data/ip102_subset --epochs 15
```

Each script writes its `.onnx` to `artifacts/` and a `labels/<name>.json` class map.

## Dataset sources

- **PlantVillage** — ~54k leaf images, 38 classes / 14 crops. Kaggle: "PlantVillage Dataset" / "New Plant Diseases Dataset".
- **PlantDoc** — ~2.6k in-the-wild images, 13 species / 17 diseases. GitHub: `pratikkayal/PlantDoc-Dataset`. Mixed in so the classifier survives real backgrounds.
- **DeepWeeds** — 17.5k field images, 8 weed species + negatives. Or a Roboflow Universe crop-vs-weed set already in YOLO format.
- **IP102** — ~75k images, 102 insect pest classes. Subset to the pests you can stage in the demo.

> Place raw datasets under `models/data/` (gitignored). Only the small exported
> ONNX files + label maps are meant to ship to the device.

## Why classifiers + a detector (not one big model)

The detector finds *where* a plant/weed is; the classifiers say *what* it is and
whether it's sick. Splitting keeps each model nano-sized so all three run within
the ~1s scan-to-LED budget on the Pi 5 CPU (see PRD section 12).
