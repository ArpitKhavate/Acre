import Image from 'next/image'
import { Reveal, SplitText, SectionLabel } from './primitives'
import { IMAGES } from '@/lib/images'
import { Cpu, Camera, Crosshair, Clock, Thermometer, MonitorSmartphone } from 'lucide-react'

const SPECS = [
  { icon: Cpu, group: 'Compute', name: 'Raspberry Pi 5 · QNX', note: 'Vision + decision engine, on the edge' },
  { icon: Camera, group: 'Perception', name: 'Pi Camera Module 3', note: 'Single CSI camera, shared pan axis' },
  { icon: Crosshair, group: 'Actuation', name: 'Pan servo + laser', note: 'Co-mounted — sees it, points at it' },
  { icon: Thermometer, group: 'Sensing', name: 'Humiture · gas', note: 'Disease-risk environmental signal' },
  { icon: Clock, group: 'Timekeeping', name: 'RTC DS1302', note: 'Authoritative offline timestamp' },
  { icon: MonitorSmartphone, group: 'Status', name: '1602 LCD · RGB · buzzer', note: 'Zone + finding, no laptop needed' },
]

export function Hardware() {
  return (
    <section id="hardware" className="relative bg-paper-2 px-5 py-24 md:px-8 md:py-32">
      <div className="dot-grid pointer-events-none absolute inset-0 opacity-50" />
      <div className="relative mx-auto max-w-6xl">
        <div className="grid items-center gap-14 lg:grid-cols-[1fr_1.05fr]">
          <Reveal className="order-2 lg:order-1">
            <div className="card-soft overflow-hidden rounded-card border border-line">
              <div className="relative aspect-[4/3]">
                <Image
                  src={IMAGES.fieldRows}
                  alt="Crop rows in the field"
                  fill
                  sizes="(max-width: 1024px) 100vw, 520px"
                  className="object-cover object-center"
                />
              </div>
              <p className="border-t border-line bg-card px-5 py-3 font-mono text-[11px] text-muted">
                demo-farm-1 · row scouting · offline
              </p>
            </div>
          </Reveal>

          <div className="order-1 lg:order-2">
            <Reveal>
              <SectionLabel>The build</SectionLabel>
            </Reveal>
            <h2 className="mt-6 font-display text-4xl font-semibold leading-[1.05] tracking-tight text-ink md:text-[3.25rem]">
              <SplitText text={'One axis. One camera.'} />
              <SplitText text={'Zero guesswork.'} className="text-green" />
            </h2>
            <p className="mt-6 max-w-lg text-[15px] leading-relaxed text-muted">
              The camera and laser ride the same pan bracket, so aim needs no
              separate calibration. Sensors and status hardware route through an
              Arduino bridge — QNX only has to trust one reliable interface:
              USB serial.
            </p>

            <div className="mt-9 grid gap-3 sm:grid-cols-2">
              {SPECS.map((s) => (
                <Reveal key={s.name}>
                  <div className="card-soft flex gap-3.5 rounded-2xl border border-line bg-card p-4">
                    <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-paper">
                      <s.icon className="size-5 text-green" strokeWidth={1.8} />
                    </span>
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-wider text-muted">
                        {s.group}
                      </p>
                      <p className="font-display text-[15px] font-semibold leading-tight text-ink">
                        {s.name}
                      </p>
                      <p className="mt-0.5 text-[13px] leading-snug text-muted">{s.note}</p>
                    </div>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
