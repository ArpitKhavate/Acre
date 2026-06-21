#!/bin/sh
# Run Acre edge scan loop on QNX (still-image camera bridge + sync to laptop).
#
# Before running:
#   export ACRE_BACKEND_URL=http://<LAPTOP_IP>:8000/api/sync
#   mkdir -p /tmp/frames && cp your_plant.jpg /tmp/frames/
#
# Usage:
#   sh scripts/qnx_run_demo.sh
#   sh scripts/qnx_run_demo.sh --once

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

: "${ACRE_FRAME_DIR:=/tmp/frames}"
: "${ACRE_FARM_ID:=demo-farm-1}"
: "${ACRE_DEVICE_ID:=acre-qnx-01}"

export ACRE_FRAME_DIR ACRE_FARM_ID ACRE_DEVICE_ID

mkdir -p "$ACRE_FRAME_DIR"

if [ -z "$ACRE_BACKEND_URL" ]; then
  echo "ERROR: set ACRE_BACKEND_URL first, e.g.:"
  echo '  export ACRE_BACKEND_URL=http://192.168.1.42:8000/api/sync'
  exit 1
fi

echo "[qnx_run_demo] device=$ACRE_DEVICE_ID farm=$ACRE_FARM_ID"
echo "[qnx_run_demo] frames=$ACRE_FRAME_DIR"
echo "[qnx_run_demo] sync -> $ACRE_BACKEND_URL"
echo "[qnx_run_demo] drop newest .jpg into $ACRE_FRAME_DIR before each scan"
echo ""

exec python3 -m edge.main "$@"
