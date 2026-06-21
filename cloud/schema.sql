-- Acre cloud schema (PRD section 8.5). Postgres / Supabase.
-- Reporting-only: no inference here. Stores synced edge rows and rollups.

CREATE TABLE IF NOT EXISTS farms (
  id    TEXT PRIMARY KEY,
  name  TEXT
);

CREATE TABLE IF NOT EXISTS zones (
  id          TEXT PRIMARY KEY,            -- matches edge zone_id
  farm_id     TEXT REFERENCES farms(id),
  marker_id   INTEGER,
  map_x       REAL,
  map_y       REAL,
  crop_type   TEXT
);

CREATE TABLE IF NOT EXISTS devices (
  id              TEXT PRIMARY KEY,
  farm_id         TEXT REFERENCES farms(id),
  last_synced_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS treatments (
  id                  TEXT PRIMARY KEY,
  class_name          TEXT NOT NULL,
  pesticide_name      TEXT,
  organic_alternative TEXT,
  application_notes   TEXT,
  source              TEXT
);

CREATE TABLE IF NOT EXISTS detections (
  id            TEXT PRIMARY KEY,          -- = edge uuid
  device_id     TEXT REFERENCES devices(id),
  zone_id       TEXT REFERENCES zones(id),
  captured_at   TIMESTAMPTZ NOT NULL,
  received_at   TIMESTAMPTZ DEFAULT now(),
  type          TEXT NOT NULL,
  class_name    TEXT NOT NULL,
  crop_type     TEXT,
  confidence    REAL NOT NULL,
  health_score  REAL,
  led_state     TEXT,
  bbox          JSONB,
  treatment_id  TEXT REFERENCES treatments(id),
  image_url     TEXT
);

CREATE TABLE IF NOT EXISTS sensor_readings (
  id              TEXT PRIMARY KEY,
  device_id       TEXT REFERENCES devices(id),
  zone_id         TEXT REFERENCES zones(id),
  captured_at     TIMESTAMPTZ NOT NULL,
  temperature_c   REAL,
  humidity_pct    REAL,
  gas_raw         REAL
);

CREATE TABLE IF NOT EXISTS farm_health_scores (
  id            TEXT PRIMARY KEY,
  farm_id       TEXT REFERENCES farms(id),
  zone_id       TEXT REFERENCES zones(id),  -- NULL = farm-wide score
  computed_at   TIMESTAMPTZ DEFAULT now(),
  score         REAL,
  factors       JSONB
);

CREATE TABLE IF NOT EXISTS reports (
  id            TEXT PRIMARY KEY,
  farm_id       TEXT REFERENCES farms(id),
  period        TEXT,
  period_start  TIMESTAMPTZ,
  period_end    TIMESTAMPTZ,
  health_score  REAL,
  ai_summary    TEXT,
  generated_at  TIMESTAMPTZ DEFAULT now()
);
