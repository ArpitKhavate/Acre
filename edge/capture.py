"""Camera capture for the Pi Camera Module 3 (CSI), with graceful fallbacks.

Tries, in order:
  1. picamera2 (the Pi Camera Module 3 path on Linux),
  2. OpenCV VideoCapture (USB/dev webcam, useful on a laptop),
  3. a synthetic frame generator (so the pipeline runs with no camera at all).

On QNX, swap the picamera2 branch for the BSP's camera service once it's up
(PRD section 7.2 — this is the #1 hour-0 risk, no hardware fallback in the kit).
"""
from __future__ import annotations

import numpy as np

from . import config


class Camera:
    def __init__(self):
        self.backend = None
        self._cap = None
        self._picam = None
        self._init_backend()

    def _init_backend(self):
        # 1. picamera2 (Pi Camera Module 3)
        try:
            from picamera2 import Picamera2

            self._picam = Picamera2()
            cfg = self._picam.create_still_configuration(
                main={"size": (config.FRAME_WIDTH, config.FRAME_HEIGHT)}
            )
            self._picam.configure(cfg)
            self._picam.start()
            self.backend = "picamera2"
            return
        except Exception:
            pass

        # 2. OpenCV VideoCapture
        try:
            import cv2

            cap = cv2.VideoCapture(config.CAMERA_INDEX)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
                self._cap = cap
                self.backend = "opencv"
                return
            cap.release()
        except Exception:
            pass

        # 3. Synthetic
        self.backend = "synthetic"
        print("[capture] No camera found; using synthetic frames.")

    def read(self) -> np.ndarray:
        """Return a single BGR frame as an HxWx3 uint8 numpy array."""
        if self.backend == "picamera2":
            rgb = self._picam.capture_array()
            return rgb[:, :, ::-1].copy()  # RGB -> BGR
        if self.backend == "opencv":
            ok, frame = self._cap.read()
            if not ok:
                raise RuntimeError("OpenCV camera read failed")
            return frame
        # synthetic: a noisy green-ish field so downstream code has real arrays
        h, w = config.FRAME_HEIGHT, config.FRAME_WIDTH
        frame = np.random.randint(0, 60, (h, w, 3), dtype=np.uint8)
        frame[:, :, 1] = np.random.randint(60, 160, (h, w), dtype=np.uint8)
        return frame

    def close(self):
        if self._cap is not None:
            self._cap.release()
        if self._picam is not None:
            self._picam.stop()
