'use client'

import { useEffect, useState } from 'react'
import { ArrowUpRight } from 'lucide-react'
import { LogoMark } from './logo'
import { cn } from '@/lib/utils'

const LINKS = [
  { label: 'How it works', href: '#how' },
  { label: 'Hardware', href: '#hardware' },
  { label: 'Dashboard', href: '#dashboard' },
  { label: 'Platform', href: '#platform' },
]

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 48)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const overHero = !scrolled

  return (
    <div className="pointer-events-none fixed inset-x-0 top-0 z-50 flex justify-center px-3 pt-3 md:pt-4">
      <header
        className={cn(
          'pointer-events-auto flex w-full max-w-6xl items-center justify-between gap-4 rounded-full border px-3 py-2 pl-4 transition-all duration-300 md:px-3 md:pl-5',
          overHero
            ? 'border-white/20 bg-black/25 text-paper shadow-none backdrop-blur-md'
            : 'border-line bg-paper/85 text-forest shadow-[0_8px_32px_-12px_rgba(10,36,22,0.25)] backdrop-blur-xl',
        )}
      >
        <a href="#top" className="flex items-center gap-2.5">
          <LogoMark className="size-7" tone={overHero ? 'paper' : 'forest'} />
          <span
            className={cn(
              'font-display text-xl font-semibold tracking-tight',
              overHero ? 'text-paper' : 'text-forest',
            )}
          >
            Acre
          </span>
        </a>

        <nav className="hidden items-center gap-0.5 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className={cn(
                'rounded-full px-3.5 py-2 text-sm transition-colors duration-200',
                overHero
                  ? 'text-paper/80 hover:bg-white/10 hover:text-paper'
                  : 'text-muted hover:bg-forest/5 hover:text-forest',
              )}
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <a
            href="#dashboard"
            className={cn(
              'hidden rounded-full px-4 py-2 text-sm font-medium transition-colors sm:block',
              overHero
                ? 'text-paper/90 hover:bg-white/10'
                : 'text-forest hover:bg-forest/5',
            )}
          >
            Live demo
          </a>
          <a
            href="#cta"
            className={cn(
              'group inline-flex items-center gap-1.5 rounded-full px-4 py-2.5 text-sm font-semibold transition-colors duration-200',
              overHero
                ? 'bg-gold text-forest-900 hover:bg-gold-deep'
                : 'bg-forest text-paper hover:bg-pine',
            )}
          >
            Request access
            <ArrowUpRight className="size-4 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </a>
        </div>
      </header>
    </div>
  )
}
