# Acre on QNX — Beginner Setup Guide

This is the step-by-step for getting Acre running on a Raspberry Pi 5 with **QNX**.

This build wires everything **directly to the Pi 5** (no Arduino):

- **RGB LED** — green = healthy, red = needs treatment (pest/disease/weed)
- **Laser emitter** — points at the detected target
- **Pan servo** — aims the camera+laser bracket (single axis, PRD 7.1)
- **I2C 1602 LCD** — shows the live `HEALTH NN/100` score + finding
- **Humiture sensor** — optional temp/humidity (disease-risk signal)
- **Camera Module 3** — the only camera (CSI)

> Big-picture: the LED, laser, and servo are the easy parts on QNX (GPIO via
> `gpio-rp1`, hardware PWM via the `rpi_gpio` Python module). The LCD needs the
> I2C driver running (Step 5). The camera and the AI model are the hard parts on
> QNX (see Step 7). Read the whole guide before sinking time into any one step.

---

## What each pin connects to (BCM numbers)

| Part | Pin (BCM) | Physical pin | Notes |
|---|---|---|---|
| LED red | GPIO 17 | 11 | through a 330Ω resistor |
| LED green | GPIO 27 | 13 | through a 330Ω resistor |
| LED blue (optional) | GPIO 23 | 16 | through a 330Ω resistor |
| Laser + | GPIO 24 | 18 | laser minus → GND |
| Servo signal | GPIO 18 | 12 | hardware PWM ch1; servo V+ → 5V, GND → GND |
| LCD SDA | GPIO 2 | 3 | I2C1 data |
| LCD SCL | GPIO 3 | 5 | I2C1 clock |
| Humiture (DHT11) data | GPIO 26 | 37 | single-wire; VCC → 3V3/5V, GND → GND |
| Ground | GND | 6 / 9 / 14 | common ground for all parts |

RGB LED: the longest leg is the common. If common-cathode, it goes to **GND**
(this is what the code assumes). If nothing lights or colors are inverted, your
LED is probably common-anode — flip the logic in `edge/led.py`.

Servo: power a hobby servo from the Pi's 5V (physical pin 4) and GND, signal on
GPIO 18. A larger/stalling servo can brown out the Pi — use a separate 5V supply
with a common ground if it misbehaves.

Camera: ribbon into the Pi's CSI port, power OFF when connecting. On Pi 5 the
metal contacts face the HDMI side.

SAFETY: never point the laser at anyone's eyes.

---

## Step 1 — Flash QNX onto the SD card

Follow QNX's "Quick Start Target Image (QSTI) for Raspberry Pi" guide and flash
the **Raspberry Pi 5** image (`com.qnx.qnx800.quickstart.rpi5`). Boot the Pi,
connect it to Wi-Fi, and get its IP address so you can SSH in.

## Step 2 — Get the code onto the Pi

```sh
git clone https://github.com/ArpitKhavate/Acre.git
cd Acre
```

## Step 3 — Test the LED, laser, and servo (no models needed)

These prove your wiring and QNX GPIO/PWM work before anything else:

```sh
sh scripts/qnx_led_test.sh      # RGB LED cycles red/green/blue
sh scripts/qnx_laser_test.sh    # laser blinks 3x
python3 scripts/qnx_servo_test.py   # servo sweeps + laser blink
```

Run one part at a time. If a part doesn't move/light, fix its wiring now —
nothing downstream matters until each part works on its own.

## Step 4 — Set the clock

QNX has no battery clock here, so set it once after each boot (UTC):

```sh
date -s "2026-06-21 01:30:00"
```

## Step 5 — Start the I2C driver and test the LCD

QNX exposes the I2C bus only after you start its driver. This creates
`/dev/i2c1`:

```sh
i2c-dwc-rpi5 -p0x1f00074000 -c200000000 -q0xa8 --u1
```

Then test the LCD (override the address if yours is 0x3F):

```sh
sh scripts/qnx_lcd_test.sh
# or:  ACRE_LCD_I2C_ADDR=0x3F sh scripts/qnx_lcd_test.sh
```

The LCD should read `ACRE LCD OK` / `HEALTH 100/100`. On QNX there is no
`read()`/`write()` for I2C — `edge/lcd.py` writes each byte with the `isendrecv`
utility, which is why LCD updates only happen when the displayed text changes.

## Step 6 — Python + the light dependencies

Acre's edge code is Python. Confirm Python is on your QNX image (`python3
--version`). The "light" parts (scoring, LED, laser, servo, LCD, database, sync)
need only the standard library plus `numpy` and `requests`:

```sh
python3 -m pip install numpy requests
```

Then run the full backends self-check (fires no laser):

```sh
python3 -m edge.hwcheck
```

It prints which concrete backend each part resolved to. On the Pi you should see
`qnx-gpio-rp1` (LED/laser), `qnx-rpi_gpio` (servo), and `qnx-isendrecv` (LCD).
Anything showing `stub`/`synthetic` is not wired up / not detected yet.

**Humiture (DHT11 on GPIO 26):** enable it with `ACRE_SENSORS_ENABLED=1`. Test
it standalone:

```sh
ACRE_SENSORS_ENABLED=1 python3 scripts/qnx_humiture_test.py
```

The DHT11 is single-wire and timing-critical. `edge/drivers/humiture.py`
bit-bangs it best-effort via the `rpi_gpio` module, retries a few times, and the
scan loop falls back to "no reading" when a read misses — so it never blocks the
core loop. The first read after power-on often fails; just run the test again.
If reads are consistently empty on QNX, that's the expected real-time limitation
of bit-banging from Python: leave it on synthetic (it's only a corroborating
signal) or swap in an I2C humiture part (AHT20/DHT20) over `/dev/i2c1`.

## Step 7 — The two hard parts on QNX (plan for these)

### 7a. The AI model (OpenCV / ONNX Runtime)

Detection needs OpenCV or ONNX Runtime, which must be **cross-compiled for QNX**
(aarch64le) — they don't `pip install` on QNX. Options, easiest first:
- Check **oss.qnx.com** for prebuilt `opencv` / `onnxruntime` ports.
- Use the QNX Camera + **TensorFlow Lite** sample (C) from the QNX Pi BSP, which
  already runs on-device, and have it write results the Python side reads.
- Until then, the pipeline runs with detection disabled (everything green), but
  the LCD, LED, servo, and laser still demo the full physical loop.

### 7b. The camera

QNX supports the Camera Module 3 through its **Sensor Framework / Camera library
(C)** — not Python's picamera2. The simplest bridge: have a QNX camera tool save
JPEG frames into a folder, and point Acre at that folder:

```sh
export ACRE_FRAME_DIR=/tmp/frames
python3 -m edge.main
```

Acre reads the newest image in `/tmp/frames` each scan. You can even test the
whole pipeline by manually copying plant photos into that folder.

## Step 8 — Point the Pi at the cloud (your laptop)

On the laptop (same Wi-Fi), start the backend and web app (see the main
[README](../README.md)). Then on the Pi:

```sh
export ACRE_BACKEND_URL="http://<laptop-ip>:8000/api/sync"
python3 -m edge.main
```

The Pi scans, shows the score on the LCD, lights the LED, aims the servo+laser
on a detection, logs locally, and syncs to the laptop. Open the web dashboard
and click "Regenerate report" to update the map and summary.

---

## Recommended test order (one part at a time)

1. `sh scripts/qnx_led_test.sh` — RGB LED.
2. `sh scripts/qnx_laser_test.sh` — laser.
3. `python3 scripts/qnx_servo_test.py` — pan servo (+ laser blink).
4. Start the I2C driver, then `sh scripts/qnx_lcd_test.sh` — LCD.
5. `ACRE_SENSORS_ENABLED=1 python3 scripts/qnx_humiture_test.py` — humiture.
6. `python3 -m edge.hwcheck` — everything at once, no laser fired.
7. `ACRE_FRAME_DIR=/tmp/frames python3 -m edge.main --once` — full scan loop.
8. Laptop runs cloud + web; regenerate the report to show the map.

If OpenCV/ONNX on QNX becomes a time sink, you still have a genuine QNX
physical-AI demo: QNX driving real GPIO/PWM/I2C hardware (LED + laser + pan
servo + LCD health score) from the on-device decision logic, syncing to a live
cloud dashboard.
