import Image from 'next/image'
import { ArrowRight } from 'lucide-react'
import { SplitText, Reveal } from './primitives'
import { IMAGES } from '@/lib/images'

const TRACKS = ['QNX', 'Anthropic', 'Arize', 'Poke']

export function CTA() {
  return (
    <section id="cta" className="bg-paper px-5 pb-24 pt-10 md:px-8">
      <div className="relative mx-auto min-h-[420px] max-w-6xl overflow-hidden rounded-[32px]">
        <Image
          src={IMAGES.fieldRows}
          alt=""
          fill
          sizes="(max-width: 768px) 100vw, 1152px"
          className="object-cover object-center"
          aria-hidden
        />
        <div className="absolute inset-0 bg-forest/82" />
        <div className="tech-grid absolute inset-0 opacity-20" />

        <div className="relative px-6 py-16 text-paper md:px-16 md:py-24">
          <div className="relative mx-auto max-w-2xl text-center">
            <h2 className="font-display text-4xl font-semibold leading-[1.04] tracking-tight md:text-6xl">
              <SplitText text={'Put AI eyes on'} />
              <SplitText text={'every acre.'} className="text-leaf" />
            </h2>
            <Reveal>
              <p className="mx-auto mt-5 max-w-lg text-[15px] leading-relaxed text-paper/75">
                Join the early-access list for the Acre scouting unit and farm
                intelligence dashboard. Built at the Berkeley AI Hackathon, 2026.
              </p>
            </Reveal>

            <Reveal>
              <div className="mx-auto mt-8 flex max-w-md flex-col gap-3 sm:flex-row">
                <input
                  type="email"
                  placeholder="you@farm.com"
                  aria-label="Email address"
                  className="w-full rounded-full border border-white/20 bg-white/10 px-5 py-3.5 text-sm text-paper placeholder:text-paper/45 outline-none backdrop-blur-sm transition-colors focus:border-leaf/60"
                />
                <button
                  type="button"
                  className="group inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 rounded-full bg-gold px-6 py-3.5 text-sm font-semibold text-forest-900 transition-colors duration-200 hover:bg-gold-deep"
                >
                  Request access
                  <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-1" />
                </button>
              </div>
            </Reveal>

            <Reveal>
              <div className="mt-10 flex flex-wrap items-center justify-center gap-2">
                <span className="font-mono text-[11px] uppercase tracking-wider text-paper/45">
                  Aligned with
                </span>
                {TRACKS.map((t) => (
                  <span
                    key={t}
                    className="rounded-full border border-white/20 bg-white/5 px-3 py-1 font-mono text-[11px] text-paper/75"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  )
}
