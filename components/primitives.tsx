import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

/**
 * Splits text into per-word spans wrapped in overflow-hidden lines so GSAP can
 * mask-reveal each word upward. Newlines (\n) become separate lines.
 * Pure markup — safe in server components. Add `data-split` so the provider
 * finds it; falls back to fully visible if JS/GSAP never runs.
 */
export function SplitText({
  text,
  className,
  as: Tag = 'span',
}: {
  text: string
  className?: string
  as?: 'span' | 'h1' | 'h2' | 'h3' | 'p'
}) {
  const lines = text.split('\n')
  return (
    <Tag className={cn('block', className)} data-split>
      {lines.map((line, li) => (
        <span key={li} className="line-mask">
          {line.split(' ').map((w, wi) => (
            <span key={wi} className="word">
              {w}
              {wi < line.split(' ').length - 1 ? '\u00A0' : ''}
            </span>
          ))}
        </span>
      ))}
    </Tag>
  )
}

/** Marks a block for the provider's fade-up reveal. Visible by default. */
export function Reveal({
  children,
  className,
  as: Tag = 'div',
}: {
  children: ReactNode
  className?: string
  as?: 'div' | 'section' | 'li' | 'span'
}) {
  return (
    <Tag className={cn('js-reveal', className)} data-reveal>
      {children}
    </Tag>
  )
}

export function SectionLabel({
  children,
  tone = 'dark',
  className,
}: {
  children: ReactNode
  tone?: 'dark' | 'light'
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 font-mono text-[11px] font-medium uppercase tracking-[0.22em]',
        tone === 'dark' ? 'text-green' : 'text-leaf-soft',
        className,
      )}
    >
      <span
        className={cn(
          'inline-block h-[6px] w-[6px] rounded-full',
          tone === 'dark' ? 'bg-gold' : 'bg-leaf',
        )}
      />
      {children}
    </span>
  )
}
