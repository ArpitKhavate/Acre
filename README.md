# Acre — Web UI

Marketing site and farmer dashboard for **Acre**, the offline-first handheld plant scanner.

This branch contains only the Next.js frontend (`web/`).

## Run

```bash
cd web
npm install
cp .env.example .env.local   # optional: NEXT_PUBLIC_ACRE_API for live dashboard data
npm run dev                  # http://localhost:3000
```

## What's in `web/`

| Path | Purpose |
|---|---|
| `app/` | Next.js App Router pages and global styles |
| `components/` | Landing sections, scroll animations, plant graphics |
| `design-system/` | Brand tokens and layout notes |
| `lib/` | API client, image paths, utilities |
| `public/images/` | Farm photography and static assets |

## Build

```bash
cd web && npm run build
```
