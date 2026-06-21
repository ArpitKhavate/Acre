# Acre — Design System (MASTER)

> Generated with `ui-ux-pro-max` reasoning engine, then tuned for Acre
> (offline-first AI crop-scouting turret + farm intelligence web app).

## Product
Field-deployable edge-AI hardware + agritech SaaS. Audience: small/mid farms,
hackathon judges. Tone: confident, grounded, precise — "hardware-honest".

## Pattern
Scroll-triggered storytelling + feature-rich showcase.
Hero → Trust → Problem → How it works (perception→action loop) → Hardware →
Offline-first architecture → Farm intelligence dashboard → Features → Metrics → CTA → Footer.
Primary CTA above the fold and repeated before the footer.

## Style
**Organic Biophilic + precision-tech edge.** Natural, rounded, flowing organic
shapes and earthy surfaces, overlaid with crisp telemetry motifs: scan-line /
laser sweep, targeting reticle, monospace data, zone-health color coding.

## Color tokens
| Role | Hex |
|------|-----|
| Paper (bg) | `#F5F4EC` |
| Paper alt | `#EEF2E8` |
| Forest (dark bg / ink) | `#0C2B1B` |
| Pine | `#0F3D27` |
| Green (primary) | `#16713F` |
| Leaf (bright) | `#34C759` |
| Gold (CTA) | `#C98A1A` |
| Soil (accent) | `#6B4F2A` |
| Card | `#FBFBF5` |
| Muted text | `#4B5D52` |

Semantic (device RGB LED + farm-map zone health):
`ok #22C55E` (≥80) · `warn #F4A522` (50–79) · `alert #EF4444` (<50) · `sync #3B82F6`.

## Typography
- Display: **Fraunces** (soft modern serif — biophilic warmth, editorial)
- Body: **Inter**
- Data/telemetry: **JetBrains Mono** (zone IDs, confidence %, serial commands)

## Effects
Rounded 16–24px, organic SVG curves, soft natural shadows, GSAP scroll reveals,
word mask-reveals, count-ups, draw-on charts, animated farm-map zones, laser scan.

## Guardrails (anti-patterns)
- No AI purple/pink gradients. No generic stock-template look.
- No scroll-jacking / heavy pinning (causes motion sickness) — gentle reveals only.
- Respect `prefers-reduced-motion`. WCAG AA contrast. cursor-pointer + focus states.
- SVG icons only (Lucide), never emoji.
