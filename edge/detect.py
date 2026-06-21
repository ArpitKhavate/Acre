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
        ort_err: Optional[Exception] = None
        try:
            import onnxruntime as ort

            self._sess = ort.InferenceSession(
                str(onnx_path), providers=["CPUExecutionProvider"]
            )
            self._inp = self._sess.get_inputs()[0].name
            self.backend = "onnxruntime"
            return
        except Exception as exc:
            ort_err = exc
        try:
            import cv2

            self._net = cv2.dnn.readNetFromONNX(str(onnx_path))
            self.backend = "opencv"
            return
        except Exception as cv_exc:
            print(
                f"[detect] cannot load {onnx_path.name}: "
                f"onnxruntime ({ort_err}); opencv dnn ({cv_exc}) — stage disabled"
            )
            self.ok = False
            self.backend = None

    def run(self, blob: np.ndarray) -> np.ndarray:
        if not self.ok or self.backend is None:
            raise RuntimeError("model not loaded")
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


def _letterbox_blob(frame: np.ndarray, imgsz: int):
    """Match Ultralytics training: scale + pad to square (not stretch)."""
    import cv2

    h, w = frame.shape[:2]
    gain = min(imgsz / h, imgsz / w)
    nw, nh = int(round(w * gain)), int(round(h * gain))
    resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
    pad_w, pad_h = imgsz - nw, imgsz - nh
    top, left = pad_h // 2, pad_w // 2
    padded = cv2.copyMakeBorder(
        resized, top, pad_h - top, left, pad_w - left,
        cv2.BORDER_CONSTANT, value=(114, 114, 114),
    )
    blob = cv2.dnn.blobFromImage(padded, 1 / 255.0, (imgsz, imgsz), swapRB=True)
    return blob, gain, left, top


def _green_ratio(crop_bgr: np.ndarray) -> float:
    """Fraction of pixels in plant-like HSV green range."""
    if crop_bgr.size == 0:
        return 0.0
    import cv2

    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (25, 35, 35), (95, 255, 255))
    return float(mask.mean()) / 255.0


def _nms_boxes(boxes: List[Box], iou_thresh: float) -> List[Box]:
    """Suppress overlapping YOLO proposals (stops clocks/UI clutter becoming 'weed')."""
    if not boxes:
        return []
    import cv2

    rects, confs = [], []
    for b in boxes:
        x, y, w, h = b.xywh
        rects.append([int(x), int(y), int(w), int(h)])
        confs.append(float(b.conf))
    idxs = cv2.dnn.NMSBoxes(rects, confs, score_threshold=0.0, nms_threshold=iou_thresh)
    if idxs is None or len(idxs) == 0:
        return []
    flat = idxs.flatten() if hasattr(idxs, "flatten") else idxs
    return [boxes[int(i)] for i in flat]


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
    def _detect_boxes(self, frame: np.ndarray, conf_thresh: float = config.DETECTION_CONF) -> List[Box]:
        if not self.detector.ok:
            return []

        h, w = frame.shape[:2]
        blob, gain, pad_x, pad_y = _letterbox_blob(frame, self.det_imgsz)
        out = self.detector.run(blob)
        boxes = self._parse_yolov8(out, w, h, conf_thresh, gain, pad_x, pad_y)
        boxes = _nms_boxes(boxes, config.DETECTION_NMS_IOU)
        return self._filter_plant_boxes(frame, boxes)

    def _filter_plant_boxes(self, frame: np.ndarray, boxes: List[Box]) -> List[Box]:
        fh, fw = frame.shape[:2]
        frame_area = fw * fh
        kept: List[Box] = []
        for b in boxes:
            _, _, bw, bh = b.xywh
            if (bw * bh) / frame_area < config.DETECTION_MIN_BOX_AREA:
                continue
            crop = self._crop(frame, b)
            if _green_ratio(crop) < config.DETECTION_MIN_GREEN_RATIO:
                continue
            kept.append(b)
        return kept

    def _parse_yolov8(
        self,
        out: np.ndarray,
        w: int,
        h: int,
        conf_thresh: float,
        gain: float,
        pad_x: float,
        pad_y: float,
    ) -> List[Box]:
        # YOLOv8 ONNX output: (1, 4+nc, num). Transpose to (num, 4+nc).
        preds = np.squeeze(out)
        if preds.ndim != 2:
            return []
        if preds.shape[0] < preds.shape[1]:
            preds = preds.T
        nc = preds.shape[1] - 4
        boxes: List[Box] = []
        for row in preds:
            cx, cy, bw, bh = row[:4]
            scores = row[4:4 + nc]
            cid = int(np.argmax(scores))
            conf = float(scores[cid])
            if conf < conf_thresh:
                continue
            # Undo letterbox (coords are in imgsz space).
            cx = (cx - pad_x) / gain
            cy = (cy - pad_y) / gain
            bw = bw / gain
            bh = bh / gain
            x = max(0, cx - bw / 2)
            y = max(0, cy - bh / 2)
            bw = min(bw, w - x)
            bh = min(bh, h - y)
            name = self.det_names[cid] if cid < len(self.det_names) else str(cid)
            boxes.append(Box(cid, name, conf, (int(x), int(y), int(bw), int(bh))))
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
    def analyze(
        self,
        frame: np.ndarray,
        motion: bool = False,
        classify_pests: bool = True,
        conf_thresh: float = config.DETECTION_CONF,
    ) -> PlantResult:
        result = PlantResult()
        boxes = self._detect_boxes(frame, conf_thresh)

        plant_boxes = [b for b in boxes if b.cls_name != "weed"]
        weed_boxes = [b for b in boxes if b.cls_name == "weed"]

        # One best detection per frame — avoids clutter on walls/background.
        best_plant = max(plant_boxes, key=lambda b: b.conf) if plant_boxes else None
        best_weed = max(weed_boxes, key=lambda b: b.conf) if weed_boxes else None
        if best_plant and best_weed:
            margin = config.DETECTION_WEED_MARGIN
            if best_weed.conf >= best_plant.conf + margin:
                best_plant = None
            else:
                best_weed = None
        if best_weed:
            result.weed_boxes = [best_weed]
        if best_plant:
            result.plant_box = best_plant
        if result.plant_box:
            crop = self._crop(frame, result.plant_box)
            dclass, dconf = self._classify(self.disease, self.dis_names, self.dis_imgsz, crop)
            if dclass and dconf >= config.CLASSIFIER_MIN_CONF:
                result.disease_class = dclass
                result.disease_conf = dconf
                result.crop_type = dclass.split("___")[0] if "___" in dclass else None
                result.is_healthy = (
                    dclass.lower() == "healthy"
                    or dclass.lower().endswith("healthy")
                    or dclass.lower().endswith("___healthy")
                )

            # Pest classifier on every plant crop (motion still used for MOG2 elsewhere).
            if classify_pests or motion:
                pclass, pconf = self._classify(self.pest, self.pest_names, self.pest_imgsz, crop)
                if pclass and pconf >= config.CLASSIFIER_MIN_CONF:
                    # Diseased leaf texture can fool the pest model — require a clear win.
                    disease_wins = (
                        not result.is_healthy
                        and result.disease_conf >= config.CLASSIFIER_MIN_CONF
                        and pconf <= result.disease_conf + 0.12
                    )
                    if not disease_wins:
                        result.pest_class = pclass
                        result.pest_conf = pconf

        return result

    def backends(self) -> dict:
        return {
            "detector": self.detector.backend,
            "disease": self.disease.backend,
            "pest": self.pest.backend,
        }
