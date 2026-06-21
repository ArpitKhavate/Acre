import { Reveal } from './primitives'

const STATS = [
  { prefix: '<', value: '1', suffix: 's', counter: '1', label: 'detection → laser lock' },
  { prefix: 'up to ', value: '5', suffix: ' fps', counter: '5', label: 'on-device inference' },
  { prefix: '', value: '100', suffix: '%', counter: '100', label: 'offline at inference' },
  { prefix: '', value: '0', suffix: '', counter: '0', label: 'cloud + GPS needed' },
]

export function Metrics() {
  return (
    <section className="relative overflow-hidden bg-forest px-5 py-20 text-paper md:px-8">
      <div className="tech-grid absolute inset-0 opacity-30" />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-leaf/30 to-transparent"
      />
      <div className="relative mx-auto grid max-w-6xl gap-10 sm:grid-cols-2 lg:grid-cols-4">
        {STATS.map((s) => (
          <Reveal key={s.label} className="text-center sm:text-left">
            <p className="font-display text-5xl font-semibold tracking-tight md:text-6xl">
              {s.prefix}
              <span data-counter={s.counter}>{s.value}</span>
              {s.suffix}
            </p>
            <p className="mt-2 font-mono text-[11px] uppercase tracking-[0.18em] text-paper/45">
              {s.label}
            </p>
          </Reveal>
        ))}
      </div>
    </section>
  )
}
