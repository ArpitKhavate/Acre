"""SQLAlchemy ORM models mirroring schema.sql (PRD section 8.5)."""
from __future__ import annotations

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, JSON, String, func,
)

from .db import Base


class Farm(Base):
    __tablename__ = "farms"
    id = Column(String, primary_key=True)
    name = Column(String)


class Zone(Base):
    __tablename__ = "zones"
    id = Column(String, primary_key=True)
    farm_id = Column(String, ForeignKey("farms.id"))
    marker_id = Column(Integer)
    map_x = Column(Float)
    map_y = Column(Float)
    crop_type = Column(String)


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    farm_id = Column(String, ForeignKey("farms.id"))
    last_synced_at = Column(DateTime(timezone=True))


class Treatment(Base):
    __tablename__ = "treatments"
    id = Column(String, primary_key=True)
    class_name = Column(String, nullable=False)
    pesticide_name = Column(String)
    organic_alternative = Column(String)
    application_notes = Column(String)
    source = Column(String)


class Detection(Base):
    __tablename__ = "detections"
    id = Column(String, primary_key=True)  # = edge uuid
    device_id = Column(String, ForeignKey("devices.id"))
    zone_id = Column(String, ForeignKey("zones.id"))
    captured_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    crop_type = Column(String)
    confidence = Column(Float, nullable=False)
    health_score = Column(Float)
    led_state = Column(String)
    bbox = Column(JSON)
    treatment_id = Column(String, ForeignKey("treatments.id"))
    image_url = Column(String)


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(String, primary_key=True)
    device_id = Column(String, ForeignKey("devices.id"))
    zone_id = Column(String, ForeignKey("zones.id"))
    captured_at = Column(DateTime(timezone=True), nullable=False)
    temperature_c = Column(Float)
    humidity_pct = Column(Float)
    gas_raw = Column(Float)


class FarmHealthScore(Base):
    __tablename__ = "farm_health_scores"
    id = Column(String, primary_key=True)
    farm_id = Column(String, ForeignKey("farms.id"))
    zone_id = Column(String, ForeignKey("zones.id"))  # NULL = farm-wide
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    score = Column(Float)
    factors = Column(JSON)


class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True)
    farm_id = Column(String, ForeignKey("farms.id"))
    period = Column(String)
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    health_score = Column(Float)
    ai_summary = Column(String)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
