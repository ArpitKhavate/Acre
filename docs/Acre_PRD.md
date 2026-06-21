# Acre — Product Requirements Document

**AI Hackathon @ Berkeley 2026**
**Status:** Draft for build kickoff | **Audience:** your team + Cursor
**Hardware constraint:** build uses only the inventory in section 6, plus generic wires/cables/tape/zip-ties for assembly. No outside hardware sourcing.

---

## 1. Executive summary

Acre is a handheld, field-deployable AI scouting unit. You carry it and point it at a plant; it identifies the plant, tells weeds apart from the crop, flags disease symptoms and pests, scores the plant's health 0-100, and lights an LED on the Raspberry Pi to tell the operator whether that plant needs treatment: red = needs a spray, green = healthy. Because real farmland often has no reliable Wi-Fi, all of that runs as inference fully offline on the Pi 5 / QNX edge board. When the unit gets a connection, it syncs its local log to a web app that turns raw detections into something a farmer wants: a map of the farm color-coded by where attention is needed, a 0-100 health score, a per-zone pesticide list, and a plain-English AI-generated summary.

The form factor is a handheld scanner, not a stationary turret and not a rover. The operator provides the motion, so there is no servo, no chassis control, and no laser-aiming step. The red/green LED replaces the laser/spray nozzle as the "treat this plant or not" signal. This is a deliberate, hardware-honest design choice that removes an entire category of mechanical risk while still satisfying every track being pursued.

---

## 2. Problem statement

Small and mid-size farms can't afford to pay someone to walk every row every day checking for weeds, disease, and pests, and the fields where this matters most are exactly the ones without reliable connectivity, so cloud-only AI scouting tools don't work there. Farmers end up either over-applying pesticide preventively or under-treating until a problem is visually obvious and already spread. Acre puts an offline scout in the operator's hand and gives an instant red/green treat-or-not call at each plant.

---

## 3. Demo scenario (what judges will see)

1. An arc of potted plants is arranged on a table: a few healthy, one or two with a "weed" planted nearby, one with visible mock leaf damage, one with a mock pest. Each pot has a small printed ArUco marker taped beside it (see section 8.2).
2. The operator picks up the Acre handheld unit and points it at the first plant. Camera and the status LED are on the same handheld body, so the operator reads the result while still pointing at the plant.
3. On each plant: live preview shows bounding boxes (plant vs. weed) and the plant ID + disease/pest classification with confidence scores. The onboard 1602 LCD shows the current zone and finding. The unit computes a 0-100 health score on-device.
4. The Pi's LED turns **green** if the plant beats the health threshold, or **red** if it has a disease/pest or scores below threshold. The buzzer optionally beeps on a red result. The LED is the spray-substitute: red means "spray this one."
5. Because the operator holds the unit still over each plant, the motion detector runs cleanly: if a small moving object (toy bug on a string) crosses near an otherwise-still plant, it's flagged, classified as a pest, and logged.
6. After scanning the arc, the team opens the **Acre web app**: a schematic map of the demo "farm" with zones colored green/amber/red, a farm health score, a per-zone pesticide list, and an AI-generated summary paragraph.
7. (Stretch) Arize dashboard shows model confidence trending across the run; Poke delivers the report conversationally.

---

## 4. Hackathon track alignment

| Track | What satisfies it | Owner focus |
|---|---|---|
| **QNX** | Inference (vision pipeline) runs on-device via an open-source AI module (OpenCV DNN / ONNX Runtime port) from oss.qnx.com; no cloud dependency at inference time | Edge team |
| **Ultimate Bots — Best Physical AI Hack** | A real perception->action loop: camera sees a plant, the system classifies and scores it on-device, and a real LED on the Pi physically signals the treat/no-treat decision. Handheld closed-loop physical AI device | Edge team |
| **Anthropic** | Built with Claude Code throughout; Claude API also generates the farmer-facing AI summary at runtime, a genuine product feature, not just a dev tool | Whole team |
| **Arize** | Every detection logged with confidence; synced to Arize for accuracy/drift tracking across the demo run | Cloud team |
| **Interaction Co / Poke** | Poke agent delivers the daily/weekly/monthly report conversationally, sourced from the same synced data as the web app | Cloud team |

*Fetch AI track dropped — not pursuing.*

---

## 5. System architecture overview

```
[Pi Camera Module 3 (CSI)] ──────────────────────┐
                                                  ▼
[Pi 5 GPIO: RGB LED (red/green status),   [QNX board (Raspberry Pi 5):
 buzzer, 1602 I2C LCD, RTC,                 vision pipeline → plant ID →
 optional humiture/gas sensors]  ◄─GPIO/I2C─►  disease/pest → health score →
                                            LED decision]
                                                  │
                                                  ▼
                                  [Local SQLite log, RTC-stamped, offline-first]
                                                  │
                               (sync agent, opportunistic connectivity)
                                                  ▼
                              [Cloud (reporting only): Postgres/Supabase + API]
                                                  │
                       ┌──────────────────────────┼──────────────────────────┐
                       ▼                          ▼                           ▼
              [Farm health map]       [AI summary (Claude API)]        [Arize / Poke]
                       │                          │
                       └────────────┬─────────────┘
                                    ▼
                        [Web app: farm map + report]
```

**Local vs. cloud is a hard boundary.** Everything intelligent — camera capture, plant/weed detection, disease and pest classification, ArUco zone tagging, the 0-100 health score, and the red/green LED decision — runs on the Pi 5 / QNX board with no network dependency. The model weights and a small validation slice of the dataset live on the device; inference never calls out. The cloud is reporting-only: it stores synced rows and produces the map, the report, the Claude AI summary, and the Arize/Poke feeds. If the network is down, the device still scans, scores, and lights the LED; only the web report waits.

**Why drive the LED and peripherals straight from the Pi 5 GPIO** rather than through an Arduino: for a handheld unit the simplest, lightest path is the Pi's own GPIO header (the kit's GPIO Extension Board + 40-pin ribbon is built for exactly this). The red/green LED and buzzer are simple digital outputs. The one real unknown is QNX's GPIO/I2C driver support, so test that in hour 0 (see section 14). Environmental sensors (humiture/gas) and the RTC ride the same GPIO/I2C bus as optional add-ons; the core scan->score->LED loop never depends on them.

---

## 6. Hardware inventory (everything you're allowed to use)

### From the QNX kit

| Component | Role |
|---|---|
| Raspberry Pi 5 | QNX edge compute — vision pipeline, decision engine, LED driver |
| SD card, QNX pre-loaded | Boot media |
| Raspberry Pi Camera Module 3 | **Sole camera** — CSI, connects directly to the Pi 5. No backup camera in inventory; this is your #1 hour-0 risk (see section 14) |
| Micro HDMI → HDMI cable | Debug display while bringing up the board |
| Arduino | Not on the critical path for v1 (LED + peripherals go straight to Pi GPIO). Available as a fallback sensor bridge if QNX GPIO/I2C proves unreliable |
| Breadboard MB-102 | Prototyping the LED/buzzer/sensor wiring |
| 1× micro servo | **Unused in v1** — handheld design has no aiming axis. Listed so it's not forgotten |

### From the HiPi.io Sensor Kit v4.0 — components used in v1

| Component | Role |
|---|---|
| RGB LED | **Primary output: green = healthy (beats health score), red = needs treatment (disease/pest or below threshold).** This is the spray-substitute signal. Blue optionally = syncing |
| Active Buzzer | Audible beep on a red (treat) result |
| 1602 I2C LCD | On-device status display — shows current zone + finding, even with no laptop nearby. Good "fully offline" talking point for judges |
| RTC-DS1302 | **Authoritative time source.** QNX has no guaranteed network time sync in the field, so the system clock can drift or reset on power-down. Set the RTC once via an NTP-synced laptop during setup, then read it for every `captured_at` timestamp instead of trusting QNX's system clock |
| Humiture Sensor (temp + humidity) | **Optional** disease-risk environmental signal, wired to Pi I2C/analog |
| Gas Sensor | **Optional** air-quality / plant-respiration proxy |
| AD/DC Convert | Analog-to-digital conversion for the gas/temp sensors |
| GPIO Extension Board + 40-pin ribbon cable | Carries the LED, buzzer, LCD, RTC, and optional sensors from the Pi 5 header to the breadboard |
| Breadboard, jumper wires, pin cables | General wiring |

### From the HiPi.io kit — available, not used in v1 (don't force these in; list them so nothing's forgotten)

Double Color LED, Auto-Flash LED, Relay Module, Button, Tilt Switch, Vibration Switch, IR Receiver, Passive Buzzer, Reed Switch, Photo-Interrupt, RainDrop Sensor, Joystick PS2, Potentiometer, Hall Switch, Thermistor, Sound Sensor, Photoresistor, Flame Sensor, Remote Control, Touch Switch, HC-SR04, Rotary Encoder, IR Obstacle, Barometer, MPU6050, Tracking Sensor, Laser Emitter (the laser is no longer needed — the LED replaces it).

A couple worth knowing about if you have spare time: **Button** as a manual "trigger scan" input so the operator decides when to capture each plant, and **Double Color LED** as a second red/green indicator if the RGB LED placement is awkward on the handheld body. Neither is required.

### Assembly consumables (allowed beyond the kit)

Wires, cables, tape, zip ties, hot glue, or a cardboard/foam-core handheld housing that holds the camera + LED + LCD in one grip. No 3D-printed part is assumed unless your team confirms 3D printer access — a hand-built housing works fine for a handheld unit.

---

## 7. Edge software

### 7.1 Handheld scanning (operator-driven, no servo)

The operator supplies all motion: pick up the unit, point the camera at a plant, hold steady for the dwell. There is no pan servo and no laser-aiming step, so there is no aim-calibration math. The camera and the status LED share the handheld body, so the operator reads the red/green result while still aimed at the plant. An optional **Button** lets the operator explicitly trigger a capture instead of relying on auto-dwell timing.

### 7.2 Camera bring-up (highest risk item — no fallback)

Pi Camera Module 3 via CSI is your only camera. Test it on QNX in the **first hour**, before writing any detection code. If the QNX BSP's camera service doesn't pick it up cleanly, check QNX's official Raspberry Pi reference BSP documentation for camera support status immediately, and loop in the QNX sponsor booth — there's no USB webcam fallback in this build, so this single item blocks everything downstream.

### 7.3 Detection + scoring pipeline (all local)

Because the operator holds the unit still over each plant, the motion detector has no camera-ego-motion problem during a dwell. The full per-plant pipeline:

- **Motion detector**: OpenCV `MOG2` during each dwell, used to surface moving pests near an otherwise-still plant.
- **Detector (YOLOv8n)**: trained off-device, exported to ONNX, run via `cv2.dnn` (or ONNX Runtime) at ~3-5 fps. Detects plant vs. weed and locates the plant crop. Nano-sized models at 416px run comfortably on the Pi 5 CPU.
- **Plant ID + disease classifier**: lightweight MobileNet/EfficientNet-lite on the detected plant crop, outputs crop species + healthy/diseased class.
- **Pest classifier**: lightweight classifier on motion-triggered crops.
- **Health score**: combines disease/pest/weed signals (and optional sensor anomalies) into a 0-100 score (see section 9.2).
- **LED decision**: green if score >= threshold, red otherwise; drives the Pi GPIO LED and optional buzzer; logs the event to SQLite.

### 7.4 Pi GPIO control — LED, buzzer, LCD

The LED, buzzer, and 1602 LCD are driven directly from the Pi 5 GPIO header (no Arduino, no serial protocol). Use a GPIO library on Linux for bring-up (`lgpio`/`RPi.GPIO`) and the equivalent QNX GPIO/I2C calls on the device. Keep a thin hardware-abstraction module so the rest of the pipeline calls `led.set("RED")` / `led.set("GREEN")` regardless of backend.

```python
# led.py — Pi GPIO red/green status (spray-substitute)
# Backend chosen at import time: lgpio on Linux Pi, QNX GPIO on device,
# no-op stub on a dev laptop so the pipeline runs anywhere.

RED_PIN = 17
GREEN_PIN = 27
BUZZER_PIN = 22

def set(color: str):
    """color in {'GREEN','RED','OFF'}: GREEN = healthy, RED = needs treatment."""
    ...

def beep(ms: int = 150):
    ...
```

Bring the LED up standalone (blink red/green from a one-line script) before wiring it into the vision loop — it's independently debuggable, which is exactly why driving it straight from the Pi is low-risk.

---

## 8. Data pipeline: edge chip → web app

### 8.1 The core problem

1. How does data get off the chip, given no reliable Wi-Fi in the field?
2. How does a detection know *where* on the farm it happened, given no GPS hardware?
3. How does a pile of timestamped detections become a map, a score, and a pesticide list?

### 8.2 Solving "where" without GPS: printed zone markers

Print small ArUco markers, one per pot, detected directly in the same camera feed via OpenCV's `cv2.aruco` module — no extra hardware. When the operator points the handheld unit at a plant, the marker taped beside that plant lands in-frame and tags the detection's `zone_id`. Each marker ID maps to a `zone_id` in a config file set once during setup:

```json
{
  "farm_id": "demo-farm-1",
  "zones": [
    { "zone_id": "Z1", "marker_id": 1, "map_x": 0.1, "map_y": 0.2, "crop_type": "tomato" },
    { "zone_id": "Z2", "marker_id": 2, "map_x": 0.3, "map_y": 0.2, "crop_type": "potato" },
    { "zone_id": "Z3", "marker_id": 3, "map_x": 0.5, "map_y": 0.2, "crop_type": "pepper" }
  ]
}
```

`map_x`/`map_y` are normalized 0-1 coordinates for the web app's schematic map only. (The old `pan_angle` field is gone — there's no servo in the handheld design.)

### 8.3 Solving "how data gets off the chip": offline-first sync

1. Every event writes to local SQLite first, unconditionally — using the **RTC's timestamp**, not QNX's system clock (see section 6).
2. A background sync agent on the device wakes on a timer, checks connectivity, batches unsynced rows, and `POST`s them to the backend. No network this cycle → does nothing, tries again later. No crash, no blocking.
3. Idempotent by client-generated UUID, so a retried batch never double-counts.

```python
# sync_agent.py — runs continuously on the device
import sqlite3, requests, time

BACKEND_URL = "https://acre-api.example.com/api/sync"
BATCH_SIZE = 50

def get_unsynced(conn):
    cur = conn.execute("SELECT * FROM detections WHERE synced = 0 LIMIT ?", (BATCH_SIZE,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def sync_loop(db_path):
    conn = sqlite3.connect(db_path)
    while True:
        rows = get_unsynced(conn)
        if rows:
            try:
                resp = requests.post(BACKEND_URL,
                    json={"device_id": "acre-01", "records": rows}, timeout=5)
                if resp.status_code == 200:
                    ids = [(r["uuid"],) for r in rows]
                    conn.executemany("UPDATE detections SET synced = 1 WHERE uuid = ?", ids)
                    conn.commit()
            except requests.exceptions.RequestException:
                pass  # no network this cycle — try again later
        time.sleep(30)
```

You don't need to prove the device is disconnected during the demo — judges care that the architecture *tolerates* it, not that you cut Wi-Fi live. It's fine to demo connected to venue Wi-Fi the whole time.

### 8.4 Edge-side schema (local SQLite, on the device)

```sql
CREATE TABLE detections (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid          TEXT UNIQUE NOT NULL,
  zone_id       TEXT NOT NULL,
  captured_at   TEXT NOT NULL,            -- from RTC, ISO 8601
  type          TEXT NOT NULL CHECK(type IN ('weed','disease','pest','healthy')),
  class_name    TEXT NOT NULL,
  crop_type     TEXT,
  confidence    REAL NOT NULL,
  health_score  REAL,                     -- 0-100, drives LED color
  led_state     TEXT,                     -- 'GREEN' | 'RED'
  bbox_x        INTEGER, bbox_y INTEGER, bbox_w INTEGER, bbox_h INTEGER,
  treatment_id  TEXT,
  image_path    TEXT,
  synced        INTEGER DEFAULT 0
);

CREATE TABLE sensor_readings (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid            TEXT UNIQUE NOT NULL,
  zone_id         TEXT NOT NULL,
  captured_at     TEXT NOT NULL,          -- from RTC
  temperature_c   REAL,
  humidity_pct    REAL,
  gas_raw         REAL,
  synced          INTEGER DEFAULT 0
);

CREATE TABLE sync_log (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  synced_at     TEXT NOT NULL,
  records_sent  INTEGER,
  status        TEXT
);
```

### 8.5 Backend schema (Postgres — recommend Supabase, see section 9.1)

```sql
CREATE TABLE farms (
  id    TEXT PRIMARY KEY,
  name  TEXT
);

CREATE TABLE zones (
  id          TEXT PRIMARY KEY,           -- matches edge zone_id
  farm_id     TEXT REFERENCES farms(id),
  marker_id   INTEGER,
  map_x       REAL,
  map_y       REAL,
  crop_type   TEXT
);

CREATE TABLE devices (
  id              TEXT PRIMARY KEY,
  farm_id         TEXT REFERENCES farms(id),
  last_synced_at  TIMESTAMPTZ
);

CREATE TABLE treatments (
  id                  TEXT PRIMARY KEY,
  class_name          TEXT NOT NULL,
  pesticide_name      TEXT,
  organic_alternative TEXT,
  application_notes   TEXT,
  source              TEXT               -- e.g. "UC IPM"
);

CREATE TABLE detections (
  id            UUID PRIMARY KEY,         -- = edge uuid
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

CREATE TABLE sensor_readings (
  id              UUID PRIMARY KEY,
  device_id       TEXT REFERENCES devices(id),
  zone_id         TEXT REFERENCES zones(id),
  captured_at     TIMESTAMPTZ NOT NULL,
  temperature_c   REAL,
  humidity_pct    REAL,
  gas_raw         REAL
);

CREATE TABLE farm_health_scores (
  id            UUID PRIMARY KEY,
  farm_id       TEXT REFERENCES farms(id),
  zone_id       TEXT REFERENCES zones(id),  -- NULL = farm-wide score
  computed_at   TIMESTAMPTZ DEFAULT now(),
  score         REAL,
  factors       JSONB
);

CREATE TABLE reports (
  id            UUID PRIMARY KEY,
  farm_id       TEXT REFERENCES farms(id),
  period        TEXT,                       -- 'daily' | 'weekly' | 'monthly'
  period_start  TIMESTAMPTZ,
  period_end    TIMESTAMPTZ,
  health_score  REAL,
  ai_summary    TEXT,
  generated_at  TIMESTAMPTZ DEFAULT now()
);
```

### 8.6 Sync API contract

```
POST /api/sync
Content-Type: application/json

{
  "device_id": "acre-01",
  "records": {
    "detections": [
      {
        "uuid": "a1b2c3...",
        "zone_id": "Z2",
        "captured_at": "2026-06-20T14:32:01Z",
        "type": "disease",
        "class_name": "tomato_early_blight",
        "crop_type": "tomato",
        "confidence": 0.87,
        "health_score": 42.0,
        "led_state": "RED",
        "bbox": {"x": 120, "y": 80, "w": 60, "h": 70},
        "treatment_id": "early_blight_treat"
      }
    ],
    "sensor_readings": [
      {
        "uuid": "d4e5f6...",
        "zone_id": "Z2",
        "captured_at": "2026-06-20T14:32:00Z",
        "temperature_c": 24.1,
        "humidity_pct": 58.0,
        "gas_raw": 410
      }
    ]
  }
}

→ 200 OK { "synced": 2, "duplicates_ignored": 0 }
```

Server-side upsert on `uuid` (`ON CONFLICT (id) DO NOTHING`) makes retried batches safe.

---

## 9. Backend & report generation (cloud, reporting-only)

### 9.1 Recommended stack

| Layer | Recommendation |
|---|---|
| Database + REST API | Supabase (Postgres) |
| Logic / scheduled jobs | Supabase Edge Functions, or a small FastAPI service |
| AI summary | Claude API (`claude-sonnet-4-6`) |
| Frontend | Next.js / React, deployed to Vercel for the demo |
| Model monitoring | Arize, fed from the `detections` table |
| Conversational reports | Poke agent, reads from the same backend |

Note: no inference runs in the cloud. The health score is computed on-device per scan and synced up; the backend only *aggregates* per-scan scores into zone/farm rollups for the map.

### 9.2 Health score (computed on-device, per plant)

```
score = 100
      − min(40, weed_pressure        × 40)
      − min(30, disease_severity     × 30)
      − min(20, pest_pressure        × 20)
      − min(10, sensor_anomaly_count ×  2)   # optional term

clamped to [0, 100]

LED = GREEN if score >= HEALTH_THRESHOLD (default 70) else RED
```

- `disease_severity` = confidence of the disease classifier on this plant (0 if classified healthy).
- `weed_pressure` = 1 if a weed is detected in/near this plant's crop, else 0 (or a graded value from weed area).
- `pest_pressure` = 1 if a pest is detected on/near this plant, else 0.
- `sensor_anomaly_count` = optional; readings outside a configured healthy range (e.g. humidity > 85%, gas above threshold). Omitted entirely if sensors aren't wired.

The device computes this per plant, drives the LED, and writes `health_score` + `led_state` to SQLite. The cloud later computes per-zone and farm-wide rollups (mean of recent scans) for the map, storing the `factors` breakdown in `farm_health_scores.factors` so the UI can explain *why*, not just show a number.

### 9.3 AI summary generation (Claude API)

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

def generate_summary(period_data: dict) -> str:
    prompt = f"""You are writing a short status update for a farmer who has
60 seconds to read it. Here is this period's data from their field scans:

{period_data}

Write a 3-4 sentence plain-language summary covering: what needs attention
first, which zones, and what to do about it. No jargon. End with one
concrete next action."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

Pass aggregated period JSON (zone-level counts, health score + factors, treatments needed) — not raw rows — to keep the summary accurate and the prompt small.

---

## 10. Frontend: the report the farmer actually sees

1. **Farm map** — schematic grid/SVG from `zones.map_x`/`map_y`, colored by latest `farm_health_scores.score` (green >=80, amber 50-79, red <50). Click a zone → detections, sensor readings, recommended treatments. This is a *logical* layout, not satellite imagery — a deliberate choice given no GPS hardware, worth saying explicitly in your judge pitch.
2. **Pest/pesticide summary table** — grouped by zone: `class_name`, count, confidence, matched `treatments` row.
3. **AI summary card** — text from section 9.3, regenerated per period, with the health score displayed above it.

---

## 11. Treatment / pesticide knowledge base

Source from **UC IPM** (UC Statewide Integrated Pest Management Program) — public, extension-grade, California-specific, nice local tie-in for a Berkeley hackathon. Use Claude Code to scrape/structure UC IPM's guidelines for your chosen crops into the `treatments` table at build time — a legitimate, demo-able Claude Code use for your Anthropic track writeup.

---

## 12. Non-functional requirements

- Inference must run fully offline on the Pi 5 / QNX board.
- Sync must be lossless and idempotent.
- Scan-to-LED (capture → classify → score → LED color) under ~1 second.
- Motion detector tuned against real conditions in your actual demo environment.
- Web app must render a coherent report even with a sparse dataset — seed a few hours of synthetic historical data so the demo map/score doesn't look empty on a fresh table.

---

## 13. Build milestones (rough sequencing)

| Phase | Focus |
|---|---|
| Hour 0-2 | Camera bring-up on QNX (highest, sole-point-of-failure risk) + Pi GPIO LED/buzzer blink test, in parallel |
| Hour 1-4 | Supabase project + schema migration; RTC set via NTP-synced laptop before going offline |
| Hour 2-8 | Train YOLOv8n (weed/crop detector) + disease classifier (PlantVillage/PlantDoc) + pest classifier (IP102 subset) off-device → export ONNX (parallel track) |
| Hour 4-10 | OpenCV DNN inference loop on Pi; ArUco zone detection wired in |
| Hour 6-10 | Build handheld housing (camera + LED + LCD in one grip); wire RGB LED, buzzer, 1602 LCD to Pi GPIO |
| Hour 10-16 | Wire detection → health score → LED decision end to end; local SQLite logging with RTC timestamps |
| Hour 12-18 | Sync agent + backend `/api/sync`; treatments table populated from UC IPM |
| Hour 16-22 | Health-score aggregation, AI summary generation, frontend map + report UI |
| Hour 20-26 | Arize + Poke integration |
| Remaining | Seed demo data, rehearse, Devpost writeups per track |

---

## 14. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Pi Camera Module 3 doesn't work cleanly under the QNX BSP, and there's no backup camera | Test it in hour 0, before anything else; check QNX's official Pi reference BSP docs immediately if it fails; loop in the QNX sponsor booth early rather than late |
| QNX GPIO/I2C driver support for the LED/buzzer/LCD is unproven | Blink the LED from a standalone script in hour 0; if QNX GPIO is unreliable, fall back to the Arduino as a serial-driven LED bridge (kept in inventory for this reason) |
| Three models to train (detector + 2 classifiers) eats time | Train in parallel on Roboflow/Colab; PlantVillage + IP102 are pre-labeled; freeze scope to the crops/pests actually present in the demo |
| PlantVillage's clean-background images don't generalize to real potted plants | Mix in PlantDoc's in-the-wild images; validate on photos of the actual demo plants before rehearsal |
| RTC not set correctly | Set it once via an NTP-synced laptop at the start of the event, before relying on offline operation |
| Motion detector false-triggers on ambient vibration/wind | Tune contour area + persistence threshold against your actual demo setup before final rehearsal |
| Sparse demo data makes the map/report look empty | Pre-seed synthetic historical records in the backend |
| Sync never succeeds live during demo | Not required — architecture only needs to tolerate disconnection; demo can run on venue Wi-Fi the whole time |

---

## 15. Out of scope for this hackathon

- Self-propelled / multi-row navigation (no drive motors; design is a handheld scanner)
- Stationary turret / servo aiming (handheld, operator-driven — servo unused)
- Laser targeting (the red/green LED replaces it as the treat/no-treat signal)
- Real GPS-based mapping (ArUco markers solve localization instead)
- Actual pesticide spraying mechanism (red LED stands in for "spray this plant")
- On-device model training (train off-device, deploy inference only)
- Cloud inference (all detection/scoring is on-device; cloud is reporting-only)
- Production-grade weatherproofing
- Fetch AI track (dropped)

---

## 16. Appendix

**Glossary**
- **Zone** — a logical pot/location identified by an ArUco marker, not GPS.
- **Sync** — the opportunistic, idempotent push of local SQLite rows to the backend.
- **Health score** — a 0-100 weighted score per plant from detection pressure and optional sensor anomalies; drives the red/green LED.
- **LED signal** — green = healthy (beats threshold), red = needs treatment; the spray-substitute.

**Datasets (locked)**
- **PlantVillage** — ~54k leaf images, 38 classes / 14 crops; base for plant ID + disease classifier.
- **PlantDoc** — ~2.6k in-the-wild images; mixed in for field robustness.
- **DeepWeeds** / Roboflow crop-vs-weed — YOLOv8n weed/crop detector training data.
- **IP102** — ~75k images, 102 pest classes; subset for the pest classifier.

**Useful links**
- oss.qnx.com — search `opencv` / `onnx` for QNX-ported AI packages
- UC IPM — https://ipm.ucanr.edu/ — pesticide/treatment reference data
- Roboflow Universe — pre-labeled weed/disease/pest datasets to fork
