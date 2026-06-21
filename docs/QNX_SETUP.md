# Acre on QNX — Beginner Setup Guide

This is the step-by-step for getting Acre running on a Raspberry Pi 5 with **QNX**.
Skipping the 1602 LCD and DS1302 RTC. We wire only: **camera + RGB LED + buzzer**.

> Big-picture: the LED and buzzer work easily on QNX (via the `gpio-rp1` tool).
> The camera and the AI model are the hard parts on QNX (see Step 6). Read the
> whole guide before buying time on any one step.

---

## What each pin connects to (BCM numbers)

| Part | Pin (BCM) | Physical pin | Notes |
|---|---|---|---|
| LED red | GPIO 17 | 11 | through a 330Ω resistor |
| LED green | GPIO 27 | 13 | through a 330Ω resistor |
| LED blue (optional) | GPIO 23 | 16 | through a 330Ω resistor |
| Buzzer + | GPIO 22 | 15 | buzzer minus → GND |
| Ground | GND | 6 | LED common leg + buzzer minus |

RGB LED: the longest leg is the common. If common-cathode, it goes to **GND**
(this is what the code assumes). If nothing lights or colors are inverted, your
LED is probably common-anode — tell the dev to flip the logic in `edge/led.py`.

Camera: ribbon into the Pi's CSI port, power OFF when connecting. On Pi 5 the
metal contacts face the HDMI side.

---

## Step 1 — Flash QNX onto the SD card

On your friend's computer, follow QNX's "Quick Start Target Image (QSTI) for
Raspberry Pi" guide and flash the **Raspberry Pi 5** image
(`com.qnx.qnx800.quickstart.rpi5`). Boot the Pi, connect it to Wi-Fi, and get
its IP address so you can SSH in.

## Step 2 — Get the code onto the Pi

```sh
git clone https://github.com/ArpitKhavate/Acre.git
cd Acre
```

## Step 3 — Test the LED + buzzer (no Python needed)

This proves your wiring and QNX GPIO work before anything else:

```sh
sh scripts/qnx_led_test.sh
```

Each color should light in turn and the buzzer should beep. If not, fix wiring
now — nothing else matters until this works.

## Step 4 — Set the clock

QNX has no battery clock here, so set it once after each boot:

```sh
date -s "2026-06-21 01:30:00"     # use the real current UTC time
```

## Step 5 — Python + the light dependencies

Acre's edge code is Python. Confirm Python is on your QNX image (`python3
--version`). The "light" parts (scoring, LED, database, sync) need only the
standard library plus `numpy` and `requests`. Install what's available:

```sh
python3 -m pip install numpy requests
```

If you can run `python3 -m edge.main --once` now, the LED will light based on
the health score — even before the camera/model are ready (it will read every
plant as "healthy/green" until the model is added in Step 6).

## Step 6 — The two hard parts on QNX (plan for these)

### 6a. The AI model (OpenCV / ONNX Runtime)

Detection needs OpenCV or ONNX Runtime, which must be **cross-compiled for QNX**
(aarch64le) — they don't `pip install` on QNX. Options, easiest first:
- Check **oss.qnx.com** for prebuilt `opencv` / `onnxruntime` ports.
- Use the QNX Camera + **TensorFlow Lite** sample (C) from the QNX Pi BSP, which
  already runs on-device, and have it write results the Python side reads.
- Until then, the pipeline runs with detection disabled (everything green).

### 6b. The camera

QNX supports the Camera Module 3 through its **Sensor Framework / Camera library
(C)** — not Python's picamera2. The simplest bridge: have a QNX camera tool save
JPEG frames into a folder, and point Acre at that folder:

```sh
export ACRE_FRAME_DIR=/tmp/frames
python3 -m edge.main
```

Acre will read the newest image in `/tmp/frames` each scan. You can even test
the whole pipeline by manually copying plant photos into that folder.

## Step 7 — Point the Pi at the cloud (your friend's laptop)

On the laptop (same Wi-Fi), start the backend and web app (see the main
[README](../README.md) Steps 8 & 10). Then on the Pi:

```sh
export ACRE_BACKEND_URL="http://<laptop-ip>:8000/api/sync"
python3 -m edge.main
```

The Pi scans, lights the LED, logs locally, and syncs to the laptop. Open the
web dashboard and click "Regenerate report" to update the map and summary.

---

## The simplest path to a working demo

1. Wiring + `qnx_led_test.sh` (LED works). ← do this first
2. `python3 -m edge.main --once` with no model (LED logic + sync work end to end).
3. Add plant photos to `ACRE_FRAME_DIR` and a trained `disease.onnx` to
   `models/artifacts/` (only if OpenCV/ONNX is available on your QNX image).
4. Laptop runs the cloud + web; regenerate the report to show the map.

If OpenCV/ONNX on QNX becomes a time sink during the hackathon, you still have a
genuine QNX physical-AI demo: QNX driving real GPIO hardware (the red/green LED)
from the on-device decision logic, syncing to a live cloud dashboard.
