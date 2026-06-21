import { cn } from '@/lib/utils'

export type PlantVariant = 'healthy' | 'disease' | 'weed'

const PALETTE = {
  healthy: {
    stem: '#15703e',
    leaf: '#41d869',
    leafDark: '#1c8049',
    accent: '#9fe0b3',
  },
  disease: {
    stem: '#6b4f2a',
    leaf: '#a8c96a',
    leafDark: '#8aab45',
    accent: '#e2a534',
    spot: '#c7861a',
  },
  weed: {
    stem: '#41544a',
    leaf: '#7a9e72',
    leafDark: '#5c7d55',
    accent: '#f05252',
  },
} as const

/** Minimal stylized plant — SVG, brand colors, no external assets. */
export function PlantSvg({
  variant = 'healthy',
  className,
  size = 80,
}: {
  variant?: PlantVariant
  className?: string
  size?: number
}) {
  const c = PALETTE[variant]
  const h = size
  const w = size * 0.72

  return (
    <svg
      viewBox="0 0 72 100"
      width={w}
      height={h}
      className={cn('plant-sway overflow-visible', className)}
      aria-hidden
    >
      {/* pot / soil mound */}
      <ellipse cx="36" cy="94" rx="22" ry="5" fill="rgba(107,79,42,0.35)" />
      <path
        d="M22 88 Q36 82 50 88 L48 94 Q36 98 24 94 Z"
        fill="#6b4f2a"
        opacity={0.55}
      />

      {/* stem */}
      <path
        d="M36 88 Q34 62 36 38 Q38 22 36 12"
        fill="none"
        stroke={c.stem}
        strokeWidth="2.5"
        strokeLinecap="round"
      />

      {/* leaves */}
      <g fill={c.leaf}>
        <path
          d="M36 42 C28 38 18 40 14 48 C18 52 28 50 36 46 Z"
          className="plant-leaf"
        />
        <path
          d="M36 42 C44 38 54 40 58 48 C54 52 44 50 36 46 Z"
          fill={c.leafDark}
          className="plant-leaf"
          style={{ animationDelay: '0.4s' }}
        />
        <path
          d="M36 58 C26 54 16 58 12 68 C18 70 28 66 36 62 Z"
          className="plant-leaf"
          style={{ animationDelay: '0.8s' }}
        />
        <path
          d="M36 58 C46 54 56 58 60 68 C54 70 44 66 36 62 Z"
          fill={c.leafDark}
          className="plant-leaf"
          style={{ animationDelay: '1.2s' }}
        />
        <path
          d="M36 28 C32 18 34 8 36 4 C38 8 40 18 36 28 Z"
          fill={c.accent}
          opacity={0.85}
          className="plant-leaf"
          style={{ animationDelay: '0.2s' }}
        />
      </g>

      {/* disease spots */}
      {variant === 'disease' && (
        <>
          <circle cx="22" cy="48" r="3" fill={PALETTE.disease.spot} opacity={0.8} />
          <circle cx="48" cy="64" r="2.5" fill={PALETTE.disease.spot} opacity={0.7} />
          <circle cx="30" cy="66" r="2" fill={PALETTE.disease.spot} opacity={0.6} />
        </>
      )}

      {/* weed — spindlier, red tip */}
      {variant === 'weed' && (
        <>
          <path
            d="M36 50 L32 20 M36 55 L42 25 M36 60 L28 35"
            stroke={c.accent}
            strokeWidth="1.5"
            strokeLinecap="round"
            opacity={0.7}
          />
          <circle cx="32" cy="20" r="2" fill={c.accent} />
        </>
      )}

      {/* healthy — tiny fruit */}
      {variant === 'healthy' && (
        <circle cx="36" cy="34" r="4" fill="#e2a534" opacity={0.9} />
      )}
    </svg>
  )
}
