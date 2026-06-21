type Tone = 'forest' | 'paper' | 'green'

const TONES: Record<Tone, string> = {
  forest: '#0c2b1b',
  paper: '#f5f4ec',
  green: '#34c759',
}

/**
 * Acre mark — a targeting reticle (scouting / precision aim) wrapped around a
 * sprout (agriculture). Single stroke language, scales cleanly.
 */
export function LogoMark({
  className,
  tone = 'forest',
}: {
  className?: string
  tone?: Tone
}) {
  const c = TONES[tone]
  return (
    <svg viewBox="0 0 32 32" className={className} role="img" aria-label="Acre">
      <circle cx="16" cy="16" r="13" fill="none" stroke={c} strokeWidth="1.6" opacity="0.4" />
      <g stroke={c} strokeWidth="1.6" strokeLinecap="round">
        <path d="M16 1.6V6" />
        <path d="M16 26v4.4" />
        <path d="M1.6 16H6" />
        <path d="M26 16h4.4" />
      </g>
      <path
        d="M16 23c0-3.4 0-5.6-1.3-7.4C13.2 13.6 10.6 13 8.4 13c.2 2.3.9 4.6 2.6 5.9 1.6 1.2 3.4 1.3 5 1.3"
        fill="none"
        stroke={c}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16 20c0-3 .4-5 1.9-6.6C19.5 11.7 22 11 24 11c-.1 2.3-.7 4.4-2.3 5.8C20.1 18 18 19 16 19"
        fill="none"
        stroke={c}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M16 23v-9" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

export function Wordmark({
  className,
  tone = 'forest',
}: {
  className?: string
  tone?: Tone
}) {
  return (
    <span className={`flex items-center gap-2 ${className ?? ''}`}>
      <LogoMark className="size-7" tone={tone} />
      <span
        className="font-display text-[1.35rem] font-semibold tracking-tight"
        style={{ color: tone === 'paper' ? '#f5f4ec' : '#0c2b1b' }}
      >
        Acre
      </span>
    </span>
  )
}
