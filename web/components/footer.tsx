import { LogoMark } from './logo'

const COLS = [
  {
    heading: 'Product',
    links: ['How it works', 'Hardware', 'Dashboard', 'Platform'],
  },
  {
    heading: 'Platform',
    links: ['Offline sync', 'Health score', 'AI summaries', 'Treatments'],
  },
  {
    heading: 'Build',
    links: ['Architecture', 'QNX edge', 'Serial protocol', 'Roadmap'],
  },
  {
    heading: 'Company',
    links: ['About', 'Hackathon', 'Contact', 'Press'],
  },
]

export function Footer() {
  return (
    <footer className="relative overflow-hidden bg-forest px-5 pb-10 pt-20 text-paper md:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-12 md:grid-cols-[1.4fr_2fr]">
          <div>
            <div className="flex items-center gap-2.5">
              <LogoMark className="size-8" tone="paper" />
              <span className="font-display text-2xl font-semibold">Acre</span>
            </div>
            <p className="mt-4 max-w-xs text-[14px] leading-relaxed text-paper/55">
              Field-deployable AI crop scouting that works offline, then turns
              raw detections into a report a farmer actually wants.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
            {COLS.map((c) => (
              <div key={c.heading}>
                <h3 className="font-mono text-[11px] uppercase tracking-wider text-leaf">
                  {c.heading}
                </h3>
                <ul className="mt-4 space-y-2.5">
                  {c.links.map((l) => (
                    <li key={l}>
                      <a
                        href="#"
                        className="text-[14px] text-paper/60 transition-colors duration-200 hover:text-paper"
                      >
                        {l}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 select-none">
          <p className="font-display text-[18vw] font-semibold leading-[0.8] tracking-tight text-paper/[0.07] md:text-[12rem]">
            Acre
          </p>
        </div>

        <div className="mt-8 flex flex-col items-center justify-between gap-3 border-t border-white/10 pt-6 text-center md:flex-row md:text-left">
          <p className="font-mono text-[12px] text-paper/45">
            © {new Date().getFullYear()} Acre · Berkeley AI Hackathon
          </p>
          <p className="font-mono text-[12px] text-paper/45">
            Inference at the edge. Decisions in the field.
          </p>
        </div>
      </div>
    </footer>
  )
}
