import Image from 'next/image'
import { ArrowRight, Play } from 'lucide-react'
import { SplitText, SectionLabel } from './primitives'
import { IMAGES } from '@/lib/images'

const STATS = [
  { value: '100%', label: 'offline inference' },
  { value: '<1s', label: 'detect to laser' },
  { value: '0–100', label: 'live health score' },
]

export function Hero() {
  return (
    <section id="top" data-hero className="relative min-h-[100svh] overflow-hidden">
      {/* full-page farmland background — subtle zoom on load via GSAP */}
      <div className="absolute inset-0" data-hero-bg>
        <Image
          src={IMAGES.heroBg}
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-center"
          aria-hidden
        />
      </div>

      {/* scrim — keeps copy readable, field visible on the right */}
      <div
        aria-hidden
        className="absolute inset-0"
        style={{
          background: `linear-gradient(
            105deg,
            rgba(243, 245, 238, 0.97) 0%,
            rgba(243, 245, 238, 0.94) 28%,
            rgba(243, 245, 238, 0.82) 40%,
            rgba(243, 245, 238, 0.45) 52%,
            rgba(243, 245, 238, 0.08) 64%,
            transparent 78%
          )`,
        }}
      />
      <div
        aria-hidden
        className="absolute inset-0 bg-gradient-to-t from-[#f3f5ee]/75 via-transparent to-[#f3f5ee]/15"
      />

      <div
        data-hero-visual
        className="relative z-10 mx-auto flex min-h-[100svh] max-w-6xl flex-col justify-center px-5 pb-20 pt-28 md:px-8 md:pb-24 md:pt-36"
      >
        <div className="max-w-xl lg:max-w-2xl">
          <span data-hero-fade>
            <SectionLabel>Edge-AI crop scouting</SectionLabel>
          </span>

          <h1 className="mt-6 font-display text-[2.85rem] font-semibold leading-[0.98] tracking-[-0.025em] text-ink md:text-[4.5rem] lg:text-[5rem]">
            <SplitText text={'Eyes on every acre.'} />
            <SplitText text={'Even offline.'} className="text-green" />
          </h1>

          <p
            data-hero-fade
            className="mt-6 max-w-lg text-pretty text-base leading-relaxed text-muted md:text-lg"
          >
            A field-deployable scouting turret that tells weeds from crops,
            flags disease and pests, and points treatment exactly where it&apos;s
            needed — then syncs a farm report when it finds a signal.
          </p>

          <div data-hero-fade className="mt-8 flex flex-wrap items-center gap-3">
            <a
              href="#cta"
              className="group inline-flex items-center gap-2 rounded-full bg-forest px-6 py-3.5 text-sm font-semibold text-paper shadow-[0_12px_32px_-12px_rgba(10,36,22,0.55)] transition-colors duration-200 hover:bg-pine"
            >
              Request early access
              <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-1" />
            </a>
            <a
              href="#how"
              className="group inline-flex items-center gap-2 rounded-full border border-line/80 bg-card/90 px-6 py-3.5 text-sm font-medium text-ink backdrop-blur-sm transition-colors duration-200 hover:border-green/30"
            >
              <Play className="size-4 fill-current text-green" />
              See the scan loop
            </a>
          </div>

          <dl
            data-hero-fade
            className="mt-10 flex flex-wrap gap-x-8 gap-y-3 border-t border-line/70 pt-7"
          >
            {STATS.map((s) => (
              <div key={s.label}>
                <dt className="font-display text-xl font-semibold tracking-tight text-ink md:text-2xl">
                  {s.value}
                </dt>
                <dd className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.14em] text-muted">
                  {s.label}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  )
}
