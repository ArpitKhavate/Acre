"""Pydantic request/response models for the sync + report API (PRD 8.6)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BBox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class DetectionIn(BaseModel):
    uuid: str
    zone_id: str
    captured_at: datetime
    type: str
    class_name: str
    crop_type: Optional[str] = None
    confidence: float
    health_score: Optional[float] = None
    led_state: Optional[str] = None
    bbox: Optional[BBox] = None
    treatment_id: Optional[str] = None
    image_url: Optional[str] = None


class SensorReadingIn(BaseModel):
    uuid: str
    zone_id: str
    captured_at: datetime
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    gas_raw: Optional[float] = None


class SyncRecords(BaseModel):
    detections: list[DetectionIn] = []
    sensor_readings: list[SensorReadingIn] = []


class SyncRequest(BaseModel):
    device_id: str
    records: SyncRecords


class SyncResponse(BaseModel):
    synced: int
    duplicates_ignored: int
