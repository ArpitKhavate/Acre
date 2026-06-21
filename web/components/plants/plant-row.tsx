import { cn } from '@/lib/utils'
import { PlantSvg, type PlantVariant } from './plant-svg'

const ROW: { variant: PlantVariant; label: string; score: string; led: string }[] = [
  { variant: 'healthy', label: 'Healthy', score: '94', led: 'GREEN' },
  { variant: 'disease', label: 'Early blight', score: '61', led: 'RED' },
  { variant: 'weed', label: 'Weed pressure', score: '48', led: 'RED' },
]

/** Three plant states side-by-side — used in problem / education sections. */
export function PlantRow({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-end justify-center gap-6 sm:gap-10 md:gap-14',
        className,
      )}
      data-plant-row
    >
      {ROW.map((p) => (
        <figure
          key={p.label}
          className="flex flex-col items-center gap-3"
          data-plant
        >
          <PlantSvg variant={p.variant} size={88} />
          <figcaption className="text-center">
            <p className="font-display text-sm font-semibold text-ink">{p.label}</p>
            <p className="mt-0.5 font-mono text-[10px] uppercase tracking-wider text-muted">
              score {p.score} · LED {p.led}
            </p>
          </figcaption>
        </figure>
      ))}
    </div>
  )
}
