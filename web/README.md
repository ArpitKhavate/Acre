# Acre — Web UI

Next.js marketing site and farmer dashboard: hero, product story, hardware overview,
and a live dashboard panel (farm map, treatments table, AI summary) when the API is configured.

## Run

```bash
npm install
cp .env.example .env.local   # optional: NEXT_PUBLIC_ACRE_API
npm run dev                  # http://localhost:3000
```

## Page sections

1. **Hero** — full-bleed farm photography, product positioning
2. **Problem / tree timeline** — scroll-driven scan pipeline story
3. **How it works / hardware / platform** — device and architecture
4. **Dashboard** — zone map, treatments, AI summary (requires API)
5. **Metrics / CTA** — stats and signup

## Design system

See [design-system/MASTER.md](./design-system/MASTER.md) for colors, type, and spacing.
