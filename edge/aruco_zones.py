"""ArUco-based zone localization (the GPS-free "where", PRD section 8.2).

When the operator points the handheld unit at a plant, the printed marker taped
beside that plant lands in-frame. We map its marker_id -> zone_id via the config
file set once at setup. No extra hardware.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from . import config


class ZoneResolver:
    def __init__(self, zones_path: Path | None = None):
        path = zones_path or config.ZONES_CONFIG
        data = json.loads(Path(path).read_text())
        self.farm_id = data.get("farm_id", config.FARM_ID)
        # marker_id -> zone dict
        self._by_marker = {z["marker_id"]: z for z in data["zones"]}
        self._setup_aruco()

    def _setup_aruco(self):
        self._aruco = None
        try:
            import cv2

            # OpenCV >= 4.7 API
            self._dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
            self._detector = cv2.aruco.ArucoDetector(
                self._dict, cv2.aruco.DetectorParameters()
            )
            self._aruco = "cv2"
        except Exception:
            print("[aruco] OpenCV aruco unavailable; zone detection disabled.")

    def detect_zone(self, frame) -> Optional[dict]:
        """Return the zone dict for the first known marker in frame, or None."""
        if self._aruco != "cv2":
            return None
        import cv2

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self._detector.detectMarkers(gray)
        if ids is None:
            return None
        for mid in ids.flatten():
            zone = self._by_marker.get(int(mid))
            if zone:
                return zone
        return None

    def zone_for_marker(self, marker_id: int) -> Optional[dict]:
        return self._by_marker.get(marker_id)
