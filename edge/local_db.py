"""Offline-first local SQLite log (PRD section 8.4).

Every scan writes here first, unconditionally, with an RTC timestamp and a
client-generated UUID. The sync agent later pushes unsynced rows to the cloud
and is idempotent by that UUID.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Optional

from . import config, rtc

SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid          TEXT UNIQUE NOT NULL,
  zone_id       TEXT NOT NULL,
  captured_at   TEXT NOT NULL,
  type          TEXT NOT NULL CHECK(type IN ('weed','disease','pest','healthy')),
  class_name    TEXT NOT NULL,
  crop_type     TEXT,
  confidence    REAL NOT NULL,
  health_score  REAL,
  led_state     TEXT,
  bbox_x        INTEGER, bbox_y INTEGER, bbox_w INTEGER, bbox_h INTEGER,
  treatment_id  TEXT,
  image_path    TEXT,
  synced        INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sensor_readings (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid            TEXT UNIQUE NOT NULL,
  zone_id         TEXT NOT NULL,
  captured_at     TEXT NOT NULL,
  temperature_c   REAL,
  humidity_pct    REAL,
  gas_raw         REAL,
  synced          INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_log (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  synced_at     TEXT NOT NULL,
  records_sent  INTEGER,
  status        TEXT
);
"""


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def insert_detection(conn: sqlite3.Connection, *, zone_id: str, type: str,
                     class_name: str, confidence: float, crop_type=None,
                     health_score=None, led_state=None, bbox=None,
                     treatment_id=None, image_path=None) -> str:
    rec_uuid = str(uuid.uuid4())
    bx = bbox or (None, None, None, None)
    conn.execute(
        """INSERT INTO detections
           (uuid, zone_id, captured_at, type, class_name, crop_type, confidence,
            health_score, led_state, bbox_x, bbox_y, bbox_w, bbox_h,
            treatment_id, image_path, synced)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
        (rec_uuid, zone_id, rtc.now_iso(), type, class_name, crop_type, confidence,
         health_score, led_state, bx[0], bx[1], bx[2], bx[3],
         treatment_id, image_path),
    )
    conn.commit()
    return rec_uuid


def insert_sensor(conn: sqlite3.Connection, *, zone_id: str, temperature_c=None,
                  humidity_pct=None, gas_raw=None) -> str:
    rec_uuid = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO sensor_readings
           (uuid, zone_id, captured_at, temperature_c, humidity_pct, gas_raw, synced)
           VALUES (?,?,?,?,?,?,0)""",
        (rec_uuid, zone_id, rtc.now_iso(), temperature_c, humidity_pct, gas_raw),
    )
    conn.commit()
    return rec_uuid


def unsynced_detections(conn, limit: int) -> list[dict]:
    cur = conn.execute("SELECT * FROM detections WHERE synced = 0 LIMIT ?", (limit,))
    return [dict(r) for r in cur.fetchall()]


def unsynced_sensors(conn, limit: int) -> list[dict]:
    cur = conn.execute("SELECT * FROM sensor_readings WHERE synced = 0 LIMIT ?", (limit,))
    return [dict(r) for r in cur.fetchall()]


def mark_synced(conn, table: str, uuids: list[str]):
    conn.executemany(
        f"UPDATE {table} SET synced = 1 WHERE uuid = ?", [(u,) for u in uuids]
    )
    conn.commit()


def log_sync(conn, records_sent: int, status: str):
    conn.execute(
        "INSERT INTO sync_log (synced_at, records_sent, status) VALUES (?,?,?)",
        (rtc.now_iso(), records_sent, status),
    )
    conn.commit()
