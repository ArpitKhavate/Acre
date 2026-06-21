import Image from 'next/image'
import { Radar, ScanSearch, Crosshair, Database, RefreshCw } from 'lucide-react'
import { Reveal, SplitText, SectionLabel } from './primitives'
import { IMAGES } from '@/lib/images'

const STEPS = [
  {
    icon: Radar,
    title: 'Sweep',
    body: 'A single pan servo sweeps the arc of crops, pausing at each printed zone marker.',
    detail: 'PAN:95° · ArUco Z2',
  },
  {
    icon: ScanSearch,
    title: 'Detect',
    body: 'Motion subtraction plus an on-device model tells crop from weed and flags disease and pests.',
    detail: 'YOLOv8n · MOG2',
  },
  {
    icon: Crosshair,
    title: 'Aim',
    body: 'Camera and laser share one axis, so whatever the camera centers, the laser already points at.',
    detail: 'LASER:ON · lock',
  },
  {
    icon: Database,
    title: 'Log',
    body: 'Every detection writes to local storage first, stamped by the on-board real-time clock.',
    detail: 'SQLite · RTC ts',
  },
  {
    icon: RefreshCw,
    title: 'Sync',
    body: 'When a connection appears, batches push to the backend — idempotent, never double-counted.',
    detail: 'POST /api/sync',
  },
]

export function HowItWorks() {
  return (
    <section id="how" className="relative overflow-hidden px-5 py-24 text-paper md:px-8 md:py-32">
      <Image
        src={IMAGES.fieldRows}
        alt=""
        fill
        sizes="100vw"
        className="object-cover object-center"
        aria-hidden
      />
      <div className="absolute inset-0 bg-forest/88" />
      <div className="tech-grid absolute inset-0 opacity-20" />

      <div className="relative mx-auto max-w-6xl">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
          <div>
            <Reveal>
              <SectionLabel tone="light">The loop</SectionLabel>
            </Reveal>
            <h2 className="mt-6 max-w-2xl font-display text-4xl font-semibold leading-[1.05] tracking-tight md:text-6xl">
              <SplitText text={'A real perception'} />
              <SplitText text={'to action loop.'} className="text-leaf" />
            </h2>
          </div>
          <Reveal className="max-w-sm text-[15px] leading-relaxed text-paper/70">
            Camera sees a target, the system computes where it is, and a real
            servo and laser physically point at it and hold. A closed-loop
            robot — stationary by design, not a downgrade.
          </Reveal>
        </div>

        <div className="relative mt-16">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5 lg:gap-5">
            {STEPS.map((s, i) => (
              <Reveal key={s.title} className="relative">
                <div className="flex items-center gap-3">
                  <span className="relative grid size-[68px] place-items-center rounded-2xl border border-white/15 bg-black/25 backdrop-blur-sm">
                    <s.icon className="size-6 text-leaf" strokeWidth={1.8} />
                    <span className="absolute -right-2 -top-2 grid size-6 place-items-center rounded-full bg-gold font-mono text-[11px] font-bold text-forest">
                      {i + 1}
                    </span>
                  </span>
                </div>
                <h3 className="mt-5 font-display text-xl font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-paper/65">{s.body}</p>
                <p className="mt-3 font-mono text-[11px] tracking-wide text-leaf-soft">
                  {s.detail}
                </p>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
