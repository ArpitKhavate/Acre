"""Local UC IPM treatment lookup (edge/config/treatments.json).

Used for on-device reports, webcam banner, and cloud sync treatment_id mapping.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Optional

from . import config

# Maps detection class_name -> cloud treatments.id (see cloud/seed.py).
_CLOUD_IDS = {
    "weed": "weed_treat",
    "aphids": "aphids_treat",
    "Thrips": "thrips_treat",
    "thrips": "thrips_treat",
    "Trialeurodes_vaporariorum": "whitefly_treat",
    "whitefly": "whitefly_treat",
    "longlegged_spider_mite": "spider_mites_treat",
    "spider_mites": "spider_mites_treat",
    "Powdery": "powdery_treat",
    "Rust": "rust_treat",
    "Healthy": None,
    "Tomato___Early_blight": "tomato_early_blight_treat",
    "Tomato___Late_blight": "tomato_late_blight_treat",
    "Potato___Late_blight": "potato_late_blight_treat",
    "Pepper_bell___Bacterial_spot": "pepper_bell_bacterial_spot_treat",
}


@lru_cache(maxsize=1)
def _table() -> dict:
    if not config.TREATMENTS_CONFIG.exists():
        return {}
    return json.loads(config.TREATMENTS_CONFIG.read_text()).get("treatments", {})


def lookup(class_name: str) -> Optional[dict]:
    """Return {pesticide, organic, notes} for a class label, or None."""
    if not class_name:
        return None
    tbl = _table()
    if class_name in tbl:
        return tbl[class_name]
    low = class_name.lower()
    for key, val in tbl.items():
        if key.lower() == low:
            return val
    return None


def pesticide_for(class_name: str) -> Optional[str]:
    row = lookup(class_name)
    return row["pesticide"] if row else None


def treatment_id_for(finding_type: str, class_name: str) -> Optional[str]:
    """Cloud DB treatment id for sync, or None if healthy / unknown."""
    if finding_type == "healthy":
        return None
    if class_name in _CLOUD_IDS:
        return _CLOUD_IDS[class_name]
    # disease keys like Tomato___Early_blight
    norm = class_name.replace("___", "_").lower()
    for key, tid in _CLOUD_IDS.items():
        if key.replace("___", "_").lower() == norm:
            return tid
    return f"{norm}_treat" if norm else None


def primary_pesticide(finding_type: str, class_name: str) -> Optional[str]:
    """Best-effort pesticide string for the primary finding."""
    if finding_type == "healthy":
        return "None"
    if finding_type == "weed":
        return pesticide_for("weed") or "Glyphosate (spot)"
    row = lookup(class_name)
    if row:
        return row.get("pesticide")
    return None
