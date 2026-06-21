# Acre — Web (the report the farmer sees)

Next.js dashboard (PRD section 10): a schematic farm map colored by health score,
a pesticide table grouped by zone, and the Claude AI summary card. Reads entirely
from the cloud API — no inference, no device coupling.

## Run

```bash
npm install
cp .env.example .env.local   # point NEXT_PUBLIC_ACRE_API at the cloud API
npm run dev                  # http://localhost:3000
```

Make sure the cloud API is running and seeded first:

```bash
# from repo root
uvicorn cloud.app.main:app --port 8000
python -m cloud.seed
```

## What's on the page

1. **Farm map** — SVG from each zone's normalized `map_x`/`map_y`, colored
   green (>=80) / amber (50-79) / red (<50). Logical layout, not satellite.
2. **AI summary card** — farm health score + Claude-generated paragraph, with a
   "Regenerate report" button that recomputes from the latest synced scans.
3. **Treatments table** — per-zone findings matched to UC IPM treatments.
