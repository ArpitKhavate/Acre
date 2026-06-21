import {
  WifiOff,
  QrCode,
  Clock,
  LineChart,
  MessageSquareText,
  ShieldCheck,
} from 'lucide-react'
import { Reveal, SplitText, SectionLabel } from './primitives'

function OfflineDiagram() {
  return (
    <svg viewBox="0 0 420 120" className="mt-5 w-full" fill="none">
      {/* nodes */}
      {[
        { x: 8, label: 'Edge · SQLite', sub: 'writes first', tone: '#34c759' },
        { x: 156, label: 'Sync agent', sub: 'opportunistic', tone: '#3b82f6' },
        { x: 304, label: 'Supabase', sub: 'upsert by uuid', tone: '#c98a1a' },
      ].map((n) => (
        <g key={n.label}>
          <rect x={n.x} y="40" width="108" height="44" rx="10" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.14)" />
          <circle cx={n.x + 14} cy={62} r="4" fill={n.tone} />
          <text x={n.x + 26} y={58} fontSize="11" fontWeight="600" className="fill-paper font-mono">
            {n.label}
          </text>
          <text x={n.x + 26} y={72} fontSize="9" className="font-mono" fill="rgba(245,244,236,0.5)">
            {n.sub}
          </text>
        </g>
      ))}
      <path data-draw d="M116 62 H156" stroke="rgba(52,199,89,0.6)" strokeWidth="2" strokeDasharray="2 5" />
      <path data-draw d="M264 62 H304" stroke="rgba(59,130,246,0.6)" strokeWidth="2" strokeDasharray="2 5" />
      <text x="214" y="100" textAnchor="middle" fontSize="9" className="font-mono" fill="rgba(245,244,236,0.45)">
        no network this cycle → retries later, never blocks
      </text>
    </svg>
  )
}

export function Platform() {
  return (
    <section id="platform" className="relative bg-paper-2 px-5 py-24 md:px-8 md:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
          <div>
            <Reveal>
              <SectionLabel>The platform</SectionLabel>
            </Reveal>
            <h2 className="mt-6 max-w-2xl font-display text-4xl font-semibold leading-[1.05] tracking-tight text-forest md:text-6xl">
              <SplitText text={'Built for the field,'} />
              <SplitText text={'not the lab.'} className="text-green" />
            </h2>
          </div>
          <Reveal className="max-w-sm text-[15px] leading-relaxed text-muted">
            Every design choice removes a category of risk — disconnection,
            clock drift, missing GPS — instead of pretending the field behaves
            like a demo bench.
          </Reveal>
        </div>

        <div className="mt-14 grid gap-4 md:grid-cols-3">
          {/* large offline-first tile */}
          <Reveal className="grain relative overflow-hidden rounded-card bg-forest p-7 text-paper shadow-[0_40px_80px_-45px_rgba(10,36,22,0.7)] md:col-span-2 md:row-span-2">
            <div className="tech-grid absolute inset-0 opacity-30" />
            <div className="relative">
              <span className="grid size-11 place-items-center rounded-xl bg-white/[0.06]">
                <WifiOff className="size-5 text-leaf" />
              </span>
              <h3 className="mt-5 font-display text-2xl font-semibold">Offline-first by default</h3>
              <p className="mt-2 max-w-md text-[14px] leading-relaxed text-paper/65">
                Detections hit local storage unconditionally, then a background
                agent syncs when it can. Retried batches are idempotent by
                client UUID, so a flaky connection never double-counts a weed.
              </p>
              <OfflineDiagram />
            </div>
          </Reveal>

          <BentoCard icon={QrCode} title="ArUco localization" body="Printed markers map each pot to a zone — accurate placement with no GPS hardware." accent="#c98a1a" />
          <BentoCard icon={Clock} title="RTC-stamped truth" body="A real-time clock is the authoritative timestamp, immune to QNX clock drift in the field." accent="#34c759" />

          <BentoCard icon={LineChart} title="Arize monitoring" body="Every detection logs its confidence, streamed to Arize for accuracy and drift tracking." accent="#3b82f6" spark />
          <BentoCard icon={MessageSquareText} title="Poke reports" body="A conversational agent delivers the daily, weekly, and monthly report from the same data." accent="#34c759" />
          <BentoCard icon={ShieldCheck} title="UC IPM treatments" body="Recommendations are grounded in extension-grade, California-specific pest guidance." accent="#c98a1a" />
        </div>
      </div>
    </section>
  )
}

function BentoCard({
  icon: Icon,
  title,
  body,
  accent,
  spark,
}: {
  icon: typeof WifiOff
  title: string
  body: string
  accent: string
  spark?: boolean
}) {
  return (
    <Reveal className="card-soft card-hover group rounded-card border border-line bg-card p-6 hover:border-green/30">
      <span
        className="grid size-11 place-items-center rounded-xl"
        style={{ background: `${accent}1f` }}
      >
        <Icon className="size-5" style={{ color: accent }} strokeWidth={1.9} />
      </span>
      <h3 className="mt-5 font-display text-xl font-semibold text-forest">{title}</h3>
      <p className="mt-2 text-[14px] leading-relaxed text-muted">{body}</p>
      {spark && (
        <svg viewBox="0 0 200 36" className="mt-4 w-full" fill="none">
          <path
            data-draw
            d="M2 30 L26 24 L50 27 L74 16 L98 20 L122 10 L146 14 L170 6 L198 9"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </Reveal>
  )
}
