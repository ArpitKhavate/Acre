# Acre demo runbook — QNX Pi + laptop report

Use this when one person has the **QNX Raspberry Pi** (camera + LED + LCD) and another
laptop on the **same Wi‑Fi** runs the **cloud API + web dashboard** (health scores,
pesticide table, AI summary).

```
  [QNX Pi]  scan + score + LED          [Laptop on Wi‑Fi]
       |    POST /api/sync  ----------------->  FastAPI (port 8000)
       |                                      Next.js (port 3000)
       +--- reads still JPEGs from            "Regenerate report" -> map + pesticides
            ACRE_FRAME_DIR (/tmp/frames)
```

Webcam testing on a dev laptop is separate: `python scripts/webcam_detect_test.py`.
On QNX you use **still images** from the camera folder bridge (see below).

---

## Roles

| Machine | Who | What runs |
|---------|-----|-----------|
| **Laptop** | Friend (or you) | `cloud` API + `web` dashboard |
| **QNX Pi 5** | Connected to friend's PC / SSH | `python3 -m edge.main` |

Both machines `git clone` the same repo: https://github.com/ArpitKhavate/Acre

---

## Part A — Laptop (report server)

Do this first. Find the laptop's LAN IP (same Wi‑Fi the Pi will use):

- **Windows:** `ipconfig` → IPv4 (e.g. `192.168.1.42`)
- **macOS/Linux:** `ip addr` or `ifconfig`

### One-command start (recommended)

**Windows (PowerShell):**
```powershell
cd Acre
.\scripts\start_laptop_demo.ps1
```

**macOS / Linux:**
```sh
cd Acre
sh scripts/start_laptop_demo.sh
```

This starts the API on `0.0.0.0:8000` and the web app on `0.0.0.0:3000`.

### Manual start (two terminals)

**Terminal 1 — API**
```sh
pip install -r requirements.txt -r cloud/requirements.txt
python -m cloud.seed
uvicorn cloud.app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Web**
```sh
cd web
cp .env.example .env.local
# Edit .env.local:
#   NEXT_PUBLIC_ACRE_API=http://<LAPTOP_IP>:8000
#   NEXT_PUBLIC_ACRE_FARM=demo-farm-1
npm install
npm run dev -- -H 0.0.0.0 -p 3000
```

Open in a browser: **http://\<LAPTOP_IP\>:3000**

Optional: set `ANTHROPIC_API_KEY` on the laptop for a real Claude summary; without it
the report still shows scores, zones, and pesticides (offline fallback text).

---

## Part B — QNX Pi (scanner)

Full hardware wiring: [QNX_SETUP.md](QNX_SETUP.md).

### 1. Clone on the Pi

```sh
git clone https://github.com/ArpitKhavate/Acre.git
cd Acre
```

### 2. Copy ONNX models (not in Git)

Models are gitignored. From the **laptop** (after training or copying artifacts):

```sh
# On laptop, from repo root:
scp -r models/artifacts/*.onnx models/labels/*.json pi@<PI_IP>:~/Acre/models/
```

Or USB stick → `Acre/models/artifacts/` and `Acre/models/labels/` on the Pi.

Files needed on the Pi:
- `models/artifacts/detector.onnx`, `disease.onnx`, `pest.onnx`
- `models/labels/detector.json`, `disease.json`, `pest.json`

If OpenCV/ONNX Runtime are **not** on QNX yet, the LED/LCD/sync loop still runs;
detection stays disabled until those libs are installed (see QNX_SETUP §7a).

### 3. Python deps on QNX (`apk`, not `pip`)

QNX uses **apk** — do not run `pip install` on the Pi for these deps.

```sh
sudo apk update
python3 -c "import numpy; print('numpy', numpy.__version__)" 2>/dev/null || echo "numpy missing"
sudo apk list --available | grep -iE 'numpy|requests'
sudo apk add python3-dev python3-wheel
# if your image lists them:
# sudo apk add py3-numpy py3-requests
```

Many QSTI images already include NumPy (see `~/projects/READMEs/python_numpy.md`).
OpenCV/ONNX are separate QNX ports (QNX_SETUP §7a).

### 4. Camera → still images (QNX path)

QNX does not use `picamera2`. Point Acre at a folder of JPEGs:

```sh
mkdir -p /tmp/frames
export ACRE_FRAME_DIR=/tmp/frames
```

**Demo without CSI camera yet:** copy a plant photo into the folder before each scan:
```sh
cp ~/test_plant.jpg /tmp/frames/scan.jpg
```

**With QNX camera tool:** configure it to write the latest frame into `/tmp/frames/`
(e.g. `frame.jpg`). Acre always reads the **newest** `.jpg`/`.png` in that folder.

### 5. Point the Pi at the laptop

Replace `<LAPTOP_IP>` with the IP from Part A:

```sh
export ACRE_BACKEND_URL="http://<LAPTOP_IP>:8000/api/sync"
export ACRE_FARM_ID="demo-farm-1"
export ACRE_DEVICE_ID="acre-qnx-01"
```

### 6. Run the scan loop

```sh
sh scripts/qnx_run_demo.sh
# or manually:
export ACRE_FRAME_DIR=/tmp/frames
export ACRE_BACKEND_URL="http://<LAPTOP_IP>:8000/api/sync"
python3 -m edge.main
```

Single scan then exit:
```sh
python3 -m edge.main --once
```

Hardware-only demo (no models): seed fake detections, then sync:
```sh
python3 -m edge.seed_demo
python3 -m edge.sync_agent
```

### 7. What you should see

| Where | What |
|-------|------|
| **Pi LCD** | `HEALTH NN/100` + finding |
| **Pi LED** | Green = healthy, red = treat |
| **Laptop :3000** | Farm map, zone scores, pesticide table |
| **Laptop** | Click **Regenerate report** after scans sync |

Sync runs every 30s by default (`ACRE_SYNC_INTERVAL_S`). On exit, `edge.main` flushes
remaining rows and triggers a cloud report refresh.

---

## Part C — Switching from webcam (dev) to QNX

| Setting | Webcam / laptop dev | QNX Pi |
|---------|---------------------|--------|
| Capture | `python scripts/webcam_detect_test.py` | `ACRE_FRAME_DIR=/tmp/frames` |
| Entry point | `scripts/webcam_detect_test.py` | `python3 -m edge.main` |
| Sync | optional | `ACRE_BACKEND_URL=http://<LAPTOP_IP>:8000/api/sync` |
| Models | `models/artifacts/*.onnx` locally | same files on Pi |

Unset `ACRE_FRAME_DIR` on Pi OS with picamera2; on QNX **keep it set**.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Pi can't reach laptop | Same Wi‑Fi; Windows firewall allow ports **8000** and **3000** |
| Web shows "No report yet" | Run scans on Pi; click **Regenerate report**; check API `http://<LAPTOP_IP>:8000/docs` |
| Sync fails | `curl http://<LAPTOP_IP>:8000/health` from Pi; verify `ACRE_BACKEND_URL` ends with `/api/sync` |
| No detections on QNX | OpenCV/ONNX missing — use `edge.seed_demo` for hardware demo or install ports from oss.qnx.com |
| Empty `/tmp/frames` | `RuntimeError: no images` — copy a JPEG before `--once` |

---

## Quick checklist

- [ ] Laptop: API + web running, firewall open
- [ ] Laptop IP written down
- [ ] Pi: repo cloned, ONNX + labels copied
- [ ] Pi: `ACRE_FRAME_DIR` + `ACRE_BACKEND_URL` set
- [ ] Pi: LED/LCD tests pass (`scripts/qnx_*`)
- [ ] Browser: http://\<LAPTOP_IP\>:3000 → regenerate report after scans
