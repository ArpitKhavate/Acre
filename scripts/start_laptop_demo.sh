#!/bin/sh
# Start Acre cloud API + web dashboard for LAN demo (macOS/Linux).
# Usage:  sh scripts/start_laptop_demo.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
[ -z "$IP" ] && IP="$(ipconfig getifaddr en0 2>/dev/null || echo 127.0.0.1)"

echo ""
echo "=== Acre laptop demo ==="
echo "LAN IP:     $IP"
echo "API:        http://${IP}:8000"
echo "Web:        http://${IP}:3000"
echo "Pi sync:    export ACRE_BACKEND_URL=http://${IP}:8000/api/sync"
echo ""

cat > web/.env.local <<EOF
NEXT_PUBLIC_ACRE_API=http://${IP}:8000
NEXT_PUBLIC_ACRE_FARM=demo-farm-1
EOF

pip install -q -r requirements.txt -r cloud/requirements.txt
python -m cloud.seed

echo "Starting API on 0.0.0.0:8000 (background)..."
uvicorn cloud.app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
trap "kill $API_PID 2>/dev/null" EXIT INT TERM
sleep 2

cd web
[ -d node_modules ] || npm install
echo "Starting web on 0.0.0.0:3000 ..."
exec npm run dev -- -H 0.0.0.0 -p 3000
