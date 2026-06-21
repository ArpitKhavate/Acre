import NextImage from 'next/image'
import {
  Sparkles,
  MapPin,
  TrendingDown,
  LayoutDashboard,
  Layers,
  Pill,
  FileText,
  Settings,
  Bell,
  ChevronDown,
  Wifi,
} from 'lucide-react'
import { Reveal, SplitText, SectionLabel } from './primitives'
import { IMAGES } from '@/lib/images'

type Zone = {
  id: string
  crop: string
  score: number
  top: string
  left: string
  w: string
  h: string
  flagged?: boolean
}

const ZONES: Zone[] = [
  { id: 'Z1', crop: 'tomato', score: 92, top: '12%', left: '8%', w: '26%', h: '34%' },
  { id: 'Z2', crop: 'tomato', score: 46, top: '10%', left: '38%', w: '24%', h: '36%', flagged: true },
  { id: 'Z3', crop: 'tomato', score: 71, top: '14%', left: '66%', w: '26%', h: '32%' },
  { id: 'Z4', crop: 'lettuce', score: 88, top: '52%', left: '10%', w: '28%', h: '30%' },
  { id: 'Z5', crop: 'pepper', score: 63, top: '54%', left: '42%', w: '24%', h: '28%' },
  { id: 'Z6', crop: 'lettuce', score: 90, top: '50%', left: '70%', w: '24%', h: '32%' },
]

function zoneStyle(score: number) {
  if (score >= 80)
    return { border: 'rgba(34,197,94,0.9)', bg: 'rgba(34,197,94,0.25)', badge: 'bg-ok text-forest-900' }
  if (score >= 50)
    return { border: 'rgba(244,165,34,0.9)', bg: 'rgba(244,165,34,0.25)', badge: 'bg-warn text-forest-900' }
  return { border: 'rgba(240,82,82,0.95)', bg: 'rgba(240,82,82,0.28)', badge: 'bg-alert text-white' }
}

const NAV = [
  { icon: LayoutDashboard, label: 'Overview', active: true },
  { icon: Layers, label: 'Zones', active: false },
  { icon: Pill, label: 'Treatments', active: false },
  { icon: FileText, label: 'Reports', active: false },
  { icon: Settings, label: 'Settings', active: false },
]

const FACTORS = [
  { label: 'Weed pressure', value: 33, tone: '#f4a522' },
  { label: 'Disease severity', value: 18, tone: '#22c55e' },
  { label: 'Pest pressure', value: 12, tone: '#22c55e' },
  { label: 'Sensor anomalies', value: 25, tone: '#f4a522' },
]

const TREATMENTS = [
  { zone: 'Z2', cls: 'bindweed', count: 3, conf: '0.87', treat: 'Spot-treat · glyphosate (UC IPM)', urgent: true },
  { zone: 'Z5', cls: 'aphids', count: 5, conf: '0.79', treat: 'Insecticidal soap', urgent: false },
  { zone: 'Z3', cls: 'early blight', count: 2, conf: '0.74', treat: 'Copper fungicide', urgent: false },
]

export function Dashboard() {
  return (
    <section id="dashboard" className="relative bg-[#eef1e8] px-5 py-24 md:px-8 md:py-32">
      <div className="relative mx-auto max-w-6xl">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
          <div>
            <Reveal>
              <SectionLabel>The report a farmer actually sees</SectionLabel>
            </Reveal>
            <h2 className="mt-6 max-w-2xl font-display text-4xl font-semibold leading-[1.05] tracking-tight text-ink md:text-[3.25rem]">
              <SplitText text={'Raw detections become'} />
              <SplitText text={'a decision.'} className="text-green" />
            </h2>
          </div>
          <Reveal className="max-w-sm text-[15px] leading-relaxed text-muted">
            A schematic farm map colored by health, a 0–100 score that explains
            itself, the pesticide needed where, and a plain-English summary.
          </Reveal>
        </div>

        <Reveal className="mt-14">
          <div className="overflow-hidden rounded-[20px] border border-[#c8d0bc] bg-[#f7f9f3] shadow-[0_40px_100px_-40px_rgba(10,36,22,0.45)]">
            {/* macOS chrome */}
            <div className="flex items-center gap-3 border-b border-[#d4dcc8] bg-[#eef2e8] px-4 py-2.5">
              <div className="flex gap-1.5">
                <span className="size-3 rounded-full bg-[#ff5f57]" />
                <span className="size-3 rounded-full bg-[#febc2e]" />
                <span className="size-3 rounded-full bg-[#28c840]" />
              </div>
              <div className="mx-auto flex min-w-0 max-w-md flex-1 items-center justify-center gap-2 rounded-lg border border-[#d4dcc8] bg-white px-3 py-1 font-mono text-[11px] text-muted">
                <span className="size-1.5 shrink-0 rounded-full bg-ok" />
                <span className="truncate">app.acre.farm/demo-farm-1</span>
              </div>
            </div>

            <div className="flex min-h-[520px]">
              {/* sidebar */}
              <aside className="hidden w-52 shrink-0 flex-col border-r border-[#d4dcc8] bg-[#f0f3eb] md:flex">
                <div className="border-b border-[#d4dcc8] px-4 py-4">
                  <p className="font-display text-lg font-semibold text-ink">Acre</p>
                  <button
                    type="button"
                    className="mt-2 flex w-full items-center justify-between rounded-lg border border-[#d4dcc8] bg-white px-2.5 py-1.5 text-left"
                  >
                    <span className="truncate font-mono text-[11px] text-ink">demo-farm-1</span>
                    <ChevronDown className="size-3.5 shrink-0 text-muted" />
                  </button>
                </div>
                <nav className="flex-1 space-y-0.5 p-2">
                  {NAV.map((n) => (
                    <button
                      key={n.label}
                      type="button"
                      className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-[13px] transition-colors ${
                        n.active
                          ? 'bg-white font-medium text-ink shadow-sm'
                          : 'text-muted hover:bg-white/60'
                      }`}
                    >
                      <n.icon className="size-4 shrink-0" strokeWidth={n.active ? 2 : 1.6} />
                      {n.label}
                    </button>
                  ))}
                </nav>
                <div className="border-t border-[#d4dcc8] p-3">
                  <div className="flex items-center gap-2 rounded-lg bg-white px-2.5 py-2">
                    <span className="grid size-7 place-items-center rounded-full bg-green text-[11px] font-semibold text-paper">
                      JD
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-[12px] font-medium text-ink">Jordan Lee</p>
                      <p className="truncate font-mono text-[10px] text-muted">owner</p>
                    </div>
                  </div>
                </div>
              </aside>

              {/* main */}
              <div className="min-w-0 flex-1 bg-[#fafbf7]">
                {/* app top bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#d4dcc8] px-4 py-3 md:px-5">
                  <div>
                    <h3 className="font-display text-lg font-semibold text-ink">Farm overview</h3>
                    <p className="font-mono text-[10px] text-muted">Last sync · 2 min ago · 50 rows queued</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="hidden items-center gap-1.5 rounded-full border border-[#d4dcc8] bg-white px-3 py-1 font-mono text-[10px] text-muted sm:flex">
                      <Wifi className="size-3 text-sync" />
                      online
                    </span>
                    <button
                      type="button"
                      className="grid size-8 place-items-center rounded-lg border border-[#d4dcc8] bg-white text-muted"
                      aria-label="Notifications"
                    >
                      <Bell className="size-4" />
                    </button>
                  </div>
                </div>

                <div className="grid gap-4 p-4 md:p-5 lg:grid-cols-[1.35fr_1fr]">
                  <div className="space-y-4">
                    <FarmMap />
                    <TreatmentTable />
                  </div>
                  <div className="space-y-4">
                    <HealthScore />
                    <AISummary />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

function FarmMap() {
  return (
    <div className="overflow-hidden rounded-xl border border-[#d4dcc8] bg-white">
      <div className="flex items-center justify-between border-b border-[#d4dcc8] px-4 py-2.5">
        <span className="flex items-center gap-1.5 font-mono text-[11px] text-muted">
          <MapPin className="size-3.5 text-green" />
          demo-farm-1 · zone map
        </span>
        <span className="font-mono text-[10px] text-muted">6 zones · ArUco</span>
      </div>
      <div className="relative aspect-[16/10] overflow-hidden bg-[#2a3d1a]">
        <NextImage
          src={IMAGES.heroBg}
          alt="Aerial view of farm fields"
          fill
          sizes="(max-width: 768px) 100vw, 640px"
          className="object-cover saturate-[0.85]"
        />
        <div className="absolute inset-0 bg-forest/15" />
        {ZONES.map((z) => {
          const s = zoneStyle(z.score)
          return (
            <div
              key={z.id}
              className="absolute rounded-lg border-2 backdrop-blur-[1px]"
              style={{
                top: z.top,
                left: z.left,
                width: z.w,
                height: z.h,
                borderColor: s.border,
                backgroundColor: s.bg,
              }}
            >
              <div className="flex h-full flex-col justify-between p-2">
                <span className={`inline-flex w-fit rounded px-1.5 py-0.5 font-mono text-[10px] font-bold ${s.badge}`}>
                  {z.id}
                </span>
                <div>
                  <p className="font-mono text-[10px] font-medium text-white drop-shadow-md">{z.crop}</p>
                  <p className="font-display text-lg font-bold text-white drop-shadow-md">{z.score}</p>
                </div>
              </div>
              {z.flagged && (
                <span className="absolute -right-1 -top-1 grid size-5 place-items-center rounded-full border-2 border-white bg-alert shadow-lg">
                  <span className="size-1.5 rounded-full bg-white" />
                </span>
              )}
            </div>
          )
        })}
      </div>
      <div className="flex flex-wrap items-center gap-4 border-t border-[#d4dcc8] px-4 py-2.5 font-mono text-[10px] text-muted">
        <Legend color="#22c55e" label="≥80 healthy" />
        <Legend color="#f4a522" label="50–79 watch" />
        <Legend color="#ef4444" label="<50 act now" />
      </div>
    </div>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="inline-block size-2.5 rounded-[3px]" style={{ background: color }} />
      {label}
    </span>
  )
}

function HealthScore() {
  const score = 72
  const pct = score / 100
  const r = 52
  const circ = Math.PI * r
  return (
    <div className="rounded-xl border border-[#d4dcc8] bg-white p-5">
      <p className="font-mono text-[10px] uppercase tracking-wider text-muted">Farm health score</p>
      <div className="mt-1 flex items-end gap-4">
        <div className="relative">
          <svg viewBox="0 0 140 84" className="w-32">
            <path d="M14 76 A52 52 0 0 1 126 76" fill="none" stroke="#e4ead8" strokeWidth="9" strokeLinecap="round" />
            <path
              data-draw
              d="M14 76 A52 52 0 0 1 126 76"
              fill="none"
              stroke="#f4a522"
              strokeWidth="9"
              strokeLinecap="round"
              strokeDasharray={circ}
              strokeDashoffset={circ * (1 - pct)}
            />
          </svg>
          <div className="absolute inset-x-0 bottom-1 text-center">
            <span className="font-display text-3xl font-bold text-ink" data-counter="72">
              72
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-warn/15 px-2.5 py-1 font-mono text-[11px] font-medium text-gold-deep">
          <TrendingDown className="size-3.5" /> watch · Z2 weed
        </div>
      </div>
      <div className="mt-4 space-y-2.5">
        {FACTORS.map((f) => (
          <div key={f.label}>
            <div className="flex justify-between font-mono text-[10px] text-muted">
              <span>{f.label}</span>
              <span>−{f.value}</span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-forest/8">
              <span
                className="block h-full rounded-full"
                style={{ width: `${f.value}%`, background: f.tone }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function AISummary() {
  return (
    <div className="relative overflow-hidden rounded-xl border border-green/20 bg-gradient-to-br from-[#0f3d27] to-[#05150d] p-5 text-paper">
      <div className="tech-grid absolute inset-0 opacity-25" />
      <div className="relative">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 font-mono text-[11px] text-leaf">
            <Sparkles className="size-3.5" /> AI summary
          </span>
          <span className="rounded-full border border-white/15 bg-white/5 px-2 py-0.5 font-mono text-[9px] text-paper/60">
            claude-sonnet
          </span>
        </div>
        <p className="mt-3 text-[14px] leading-relaxed text-paper/85">
          Most of the farm looks healthy, but{' '}
          <span className="font-semibold text-leaf">Zone 2 needs attention first</span> —
          bindweed showed up in three scans today at high confidence. Zone 5 has
          early aphid pressure worth watching. Everywhere else is green.
        </p>
        <div className="mt-3 rounded-lg border border-leaf/20 bg-leaf/10 px-3 py-2.5">
          <p className="font-mono text-[10px] uppercase tracking-wider text-leaf-soft">
            Next action
          </p>
          <p className="mt-1 text-[13px] font-medium leading-snug text-paper">
            Spot-treat Z2 this afternoon before it spreads to adjacent tomato rows.
          </p>
        </div>
      </div>
    </div>
  )
}

function TreatmentTable() {
  return (
    <div className="overflow-hidden rounded-xl border border-[#d4dcc8] bg-white">
      <div className="flex items-center justify-between border-b border-[#d4dcc8] px-4 py-2.5">
        <span className="font-mono text-[11px] text-muted">recommended treatments</span>
        <span className="font-mono text-[10px] text-muted">source: UC IPM</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px] text-left">
          <thead>
            <tr className="bg-[#f4f6ef] font-mono text-[10px] uppercase tracking-wider text-muted">
              <th className="px-4 py-2 font-medium">Zone</th>
              <th className="px-2 py-2 font-medium">Class</th>
              <th className="px-2 py-2 font-medium">Conf</th>
              <th className="px-4 py-2 font-medium">Treatment</th>
            </tr>
          </thead>
          <tbody>
            {TREATMENTS.map((t) => (
              <tr
                key={t.zone}
                className={`border-t border-[#e8ede0] text-[13px] ${t.urgent ? 'bg-alert/[0.04]' : ''}`}
              >
                <td className="px-4 py-2.5 font-mono font-semibold text-ink">{t.zone}</td>
                <td className="px-2 py-2.5 text-ink">
                  {t.cls}{' '}
                  <span className="font-mono text-[11px] text-muted">×{t.count}</span>
                </td>
                <td className="px-2 py-2.5 font-mono text-muted">{t.conf}</td>
                <td className="px-4 py-2.5 text-[12.5px] text-muted">{t.treat}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
