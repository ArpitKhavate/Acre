"""Local inference: YOLOv8n detector + disease/pest classifiers (PRD section 7.3).

All three models are ONNX, loaded from models/artifacts/ and run via ONNX Runtime
(preferred) or OpenCV DNN. Fully offline — no network calls at inference time.

If a model file is missing (e.g. before training is done), that stage degrades
to an empty/neutral result and logs a warning, so the rest of the pipeline,
LED, and DB logging still run end-to-end during development.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np

from . import config

# Must match models/common_classifier.py
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


@dataclass
class Box:
    cls_id: int
    cls_name: str
    conf: float
    xywh: tuple  # x, y, w, h in pixels


@dataclass
class PlantResult:
    crop_type: Optional[str] = None
    disease_class: Optional[str] = None   # e.g. "Tomato___Early_blight" or healthy
    disease_conf: float = 0.0
    is_healthy: bool = True
    weed_boxes: List[Box] = field(default_factory=list)
    plant_box: Optional[Box] = None
    pest_class: Optional[str] = None
    pest_conf: float = 0.0


def _load_labels(path: Path):
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    names = data["names"]
    if isinstance(names, dict):  # {"0": "crop", ...}
        names = [names[str(i)] for i in range(len(names))]
    return data.get("imgsz", 224), names


class _OnnxModel:
    """Thin ONNX Runtime wrapper with an OpenCV DNN fallback."""

    def __init__(self, onnx_path: Path):
        self.ok = onnx_path.exists()
        self.backend = None
        self._sess = None
        self._net = None
        if not self.ok:
            print(f"[detect] model missing: {onnx_path.name} (stage disabled)")
            return
        try:
            import onnxruntime as ort

            self._sess = ort.InferenceSession(
                str(onnx_path), providers=["CPUExecutionProvider"]
            )
            self._inp = self._sess.get_inputs()[0].name
            self.backend = "onnxruntime"
        except Exception:
            import cv2

            self._net = cv2.dnn.readNetFromONNX(str(onnx_path))
            self.backend = "opencv"

    def run(self, blob: np.ndarray) -> np.ndarray:
        if self.backend == "onnxruntime":
            return self._sess.run(None, {self._inp: blob})[0]
        self._net.setInput(blob)
        return self._net.forward()


def _classifier_blob(crop_bgr: np.ndarray, imgsz: int) -> np.ndarray:
    import cv2

    img = cv2.resize(crop_bgr, (imgsz, imgsz))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    img = (img - _MEAN) / _STD
    return np.transpose(img, (2, 0, 1))[None, ...].astype(np.float32)


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()


class Detector:
    def __init__(self):
        self.detector = _OnnxModel(config.DETECTOR_ONNX)
        self.disease = _OnnxModel(config.DISEASE_ONNX)
        self.pest = _OnnxModel(config.PEST_ONNX)

        det_labels = _load_labels(config.LABELS_DIR / "detector.json")
        dis_labels = _load_labels(config.LABELS_DIR / "disease.json")
        pest_labels = _load_labels(config.LABELS_DIR / "pest.json")
        self.det_imgsz, self.det_names = det_labels or (416, [])
        self.dis_imgsz, self.dis_names = dis_labels or (224, [])
        self.pest_imgsz, self.pest_names = pest_labels or (224, [])

    # --- detector ---------------------------------------------------------
    def _detect_boxes(self, frame: np.ndarray) -> List[Box]:
        if not self.detector.ok:
            return []
        import cv2

        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            frame, 1 / 255.0, (self.det_imgsz, self.det_imgsz), swapRB=True
        )
        out = self.detector.run(blob)
        return self._parse_yolov8(out, w, h)

    def _parse_yolov8(self, out: np.ndarray, w: int, h: int) -> List[Box]:
        # YOLOv8 ONNX output: (1, 4+nc, num). Transpose to (num, 4+nc).
        preds = np.squeeze(out)
        if preds.ndim != 2:
            return []
        if preds.shape[0] < preds.shape[1]:
            preds = preds.T
        nc = preds.shape[1] - 4
        boxes: List[Box] = []
        sx, sy = w / self.det_imgsz, h / self.det_imgsz
        for row in preds:
            cx, cy, bw, bh = row[:4]
            scores = row[4:4 + nc]
            cid = int(np.argmax(scores))
            conf = float(scores[cid])
            if conf < config.DETECTION_CONF:
                continue
            x = (cx - bw / 2) * sx
            y = (cy - bh / 2) * sy
            name = self.det_names[cid] if cid < len(self.det_names) else str(cid)
            boxes.append(Box(cid, name, conf, (int(x), int(y), int(bw * sx), int(bh * sy))))
        return boxes

    # --- classifiers ------------------------------------------------------
    def _classify(self, model: _OnnxModel, names, imgsz, crop):
        if not model.ok or crop.size == 0:
            return None, 0.0
        blob = _classifier_blob(crop, imgsz)
        logits = np.squeeze(model.run(blob))
        probs = _softmax(logits)
        idx = int(np.argmax(probs))
        name = names[idx] if idx < len(names) else str(idx)
        return name, float(probs[idx])

    def _crop(self, frame, box: Box):
        x, y, w, h = box.xywh
        x, y = max(0, x), max(0, y)
        return frame[y:y + h, x:x + w]

    # --- full per-plant inference ----------------------------------------
    def analyze(self, frame: np.ndarray, motion: bool = False) -> PlantResult:
        result = PlantResult()
        boxes = self._detect_boxes(frame)

        plant_boxes = [b for b in boxes if b.cls_name not in ("weed",)]
        result.weed_boxes = [b for b in boxes if b.cls_name == "weed"]

        # Pick the most confident plant box (fall back to whole frame).
        if plant_boxes:
            result.plant_box = max(plant_boxes, key=lambda b: b.conf)
            crop = self._crop(frame, result.plant_box)
        else:
            crop = frame

        dclass, dconf = self._classify(self.disease, self.dis_names, self.dis_imgsz, crop)
        if dclass:
            result.disease_class = dclass
            result.disease_conf = dconf
            result.crop_type = dclass.split("___")[0] if "___" in dclass else None
            result.is_healthy = dclass.lower().endswith("healthy")

        # Pest classifier runs on motion-triggered crops (PRD 7.3).
        if motion:
            pclass, pconf = self._classify(self.pest, self.pest_names, self.pest_imgsz, crop)
            if pclass:
                result.pest_class = pclass
                result.pest_conf = pconf

        return result

    def backends(self) -> dict:
        return {
            "detector": self.detector.backend,
            "disease": self.disease.backend,
            "pest": self.pest.backend,
        }
