import Image from 'next/image'
import { Footprints, WifiOff, Droplets } from 'lucide-react'
import { Reveal, SplitText, SectionLabel } from './primitives'
import { IMAGES } from '@/lib/images'

const POINTS = [
  {
    n: '01',
    icon: Footprints,
    stat: 'Hand-scouting every row',
    body: 'Nobody can afford to walk and inspect each row by hand. Problems get noticed only once they have already spread.',
  },
  {
    n: '02',
    icon: WifiOff,
    stat: 'No signal, no scouting',
    body: 'The fields where this matters most are the ones without reliable Wi-Fi — so cloud-only AI tools simply do not work there.',
  },
  {
    n: '03',
    icon: Droplets,
    stat: 'Spray it all, or too late',
    body: 'Farmers over-apply pesticide preventively, or under-treat until damage is obvious. Both are expensive and avoidable.',
  },
]

export function Problem() {
  return (
    <section className="relative bg-paper px-5 py-24 md:px-8 md:py-32">
      <div className="dot-grid pointer-events-none absolute inset-0 opacity-60" />
      <div className="relative mx-auto max-w-6xl">
        <div className="grid items-end gap-10 lg:grid-cols-[1.15fr_0.85fr]">
          <div>
            <Reveal>
              <SectionLabel>The problem</SectionLabel>
            </Reveal>
            <h2 className="mt-6 font-display text-4xl font-semibold leading-[1.05] tracking-tight text-ink md:text-[3.25rem]">
              <SplitText text={"Scouting by hand doesn't scale."} as="span" />
              <SplitText
                text={"And cloud AI can't reach the field."}
                as="span"
                className="text-green"
              />
            </h2>
          </div>
          <Reveal className="lg:pb-2">
            <p className="text-pretty text-[15px] leading-relaxed text-muted">
              The crops that need watching most often sit miles from a stable
              connection. Acre closes that gap — all the intelligence lives on
              the machine, in the dirt, where the decisions actually happen.
            </p>
          </Reveal>
        </div>

        <Reveal className="mt-14">
          <div className="card-soft relative overflow-hidden rounded-card border border-line">
            <div className="relative aspect-[21/9] min-h-[220px]">
              <Image
                src={IMAGES.cropClose}
                alt="Farmer walking between crop rows"
                fill
                sizes="(max-width: 768px) 100vw, 1152px"
                className="object-cover object-center"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-forest/85 via-forest/40 to-transparent" />
              <div className="absolute inset-0 flex items-end p-6 md:items-center md:p-10">
                <blockquote className="max-w-lg">
                  <p className="font-display text-xl font-medium leading-snug text-paper md:text-2xl">
                    &ldquo;By the time I spot it walking the rows, it&apos;s already in the
                    next bed.&rdquo;
                  </p>
                  <footer className="mt-4 font-mono text-[11px] uppercase tracking-wider text-paper/60">
                    — demo-farm-1 · 40 acres · no field Wi-Fi
                  </footer>
                </blockquote>
              </div>
            </div>
          </div>
        </Reveal>

        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {POINTS.map((p) => (
            <Reveal key={p.n}>
              <article className="card-soft card-hover group h-full rounded-card border border-line bg-card p-7">
                <div className="flex items-center justify-between">
                  <span className="grid size-11 place-items-center rounded-xl bg-paper-2 text-green transition-colors group-hover:bg-green group-hover:text-paper">
                    <p.icon className="size-5" strokeWidth={2} />
                  </span>
                  <span className="font-mono text-xs tracking-widest text-ink/25">{p.n}</span>
                </div>
                <h3 className="mt-6 font-display text-xl font-semibold leading-snug text-ink">
                  {p.stat}
                </h3>
                <p className="mt-3 text-[14.5px] leading-relaxed text-muted">{p.body}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
