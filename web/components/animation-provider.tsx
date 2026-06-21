'use client'

import { useEffect, type ReactNode } from 'react'
import Lenis from 'lenis'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

const EASE = 'power3.out'

export function AnimationProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) return

    gsap.registerPlugin(ScrollTrigger)

    // ---- Lenis smooth scroll, synced to the GSAP ticker ----
    const lenis = new Lenis({
      duration: 1.05,
      easing: (t) => 1 - Math.pow(1 - t, 3),
    })
    lenis.on('scroll', ScrollTrigger.update)
    const raf = (time: number) => lenis.raf(time * 1000)
    gsap.ticker.add(raf)
    gsap.ticker.lagSmoothing(0)

    const ctx = gsap.context(() => {
      // ===== Hero intro (plays on load) =====
      const hero = document.querySelector('[data-hero]')
      if (hero) {
        const words = hero.querySelectorAll('[data-split] .word')
        const tl = gsap.timeline({ delay: 0.15 })
        if (words.length) {
          gsap.set(words, { yPercent: 120, opacity: 0 })
          tl.to(words, {
            yPercent: 0,
            opacity: 1,
            duration: 0.85,
            ease: EASE,
            stagger: 0.04,
          })
        }
        const fades = hero.querySelectorAll('[data-hero-fade]')
        if (fades.length) {
          gsap.set(fades, { opacity: 0, y: 20 })
          tl.to(
            fades,
            { opacity: 1, y: 0, duration: 0.7, ease: EASE, stagger: 0.1 },
            '-=0.5',
          )
        }
        const visual = hero.querySelector('[data-hero-visual]')
        if (visual) {
          gsap.set(visual, { opacity: 0, scale: 0.94, y: 30 })
          tl.to(
            visual,
            { opacity: 1, scale: 1, y: 0, duration: 1, ease: 'power3.out' },
            '-=0.8',
          )
        }
      }

      // ===== Scroll word-mask reveals (everything except hero) =====
      gsap.utils.toArray<HTMLElement>('[data-split]').forEach((el) => {
        if (el.closest('[data-hero]')) return
        const words = el.querySelectorAll('.word')
        gsap.set(words, { yPercent: 120, opacity: 0 })
        gsap.to(words, {
          yPercent: 0,
          opacity: 1,
          duration: 0.8,
          ease: EASE,
          stagger: 0.035,
          scrollTrigger: { trigger: el, start: 'top 86%' },
        })
      })

      // ===== Generic fade-up reveals with stagger batching =====
      const reveals = gsap.utils
        .toArray<HTMLElement>('[data-reveal]')
        .filter((el) => !el.closest('[data-hero]'))
      gsap.set(reveals, { opacity: 0, y: 34 })
      ScrollTrigger.batch(reveals, {
        start: 'top 88%',
        onEnter: (els) =>
          gsap.to(els, {
            opacity: 1,
            y: 0,
            duration: 0.85,
            ease: EASE,
            stagger: 0.1,
            overwrite: true,
          }),
      })

      // ===== Pop-in (icons, chips) =====
      gsap.utils.toArray<HTMLElement>('[data-pop]').forEach((el) => {
        gsap.from(el, {
          scale: 0,
          opacity: 0,
          duration: 0.5,
          ease: 'back.out(2)',
          clearProps: 'transform',
          scrollTrigger: { trigger: el, start: 'top 90%' },
        })
      })

      // ===== Count-up numbers =====
      gsap.utils.toArray<HTMLElement>('[data-counter]').forEach((el) => {
        const target = Number(el.dataset.counter || '0')
        const decimals = Number(el.dataset.decimals || '0')
        const obj = { v: 0 }
        el.textContent = (0).toFixed(decimals)
        ScrollTrigger.create({
          trigger: el,
          start: 'top 90%',
          once: true,
          onEnter: () =>
            gsap.to(obj, {
              v: target,
              duration: 1.4,
              ease: 'power2.out',
              onUpdate: () => {
                el.textContent = obj.v.toFixed(decimals)
              },
            }),
        })
      })

      // ===== SVG path draw-on =====
      gsap.utils.toArray<SVGPathElement>('[data-draw]').forEach((path) => {
        const len = path.getTotalLength()
        gsap.set(path, { strokeDasharray: len, strokeDashoffset: len })
        gsap.to(path, {
          strokeDashoffset: 0,
          duration: 1.5,
          ease: 'power2.inOut',
          scrollTrigger: { trigger: path, start: 'top 88%' },
        })
      })

      // ===== Gentle parallax (small, never scroll-jacking) =====
      gsap.utils.toArray<HTMLElement>('[data-parallax]').forEach((el) => {
        const amt = Number(el.dataset.parallax || '40')
        gsap.fromTo(
          el,
          { y: amt },
          {
            y: -amt,
            ease: 'none',
            scrollTrigger: {
              trigger: el,
              start: 'top bottom',
              end: 'bottom top',
              scrub: 1,
            },
          },
        )
      })
    })

    const onLoad = () => ScrollTrigger.refresh()
    window.addEventListener('load', onLoad)
    const refreshId = window.setTimeout(() => ScrollTrigger.refresh(), 450)

    return () => {
      window.removeEventListener('load', onLoad)
      window.clearTimeout(refreshId)
      ctx.revert()
      gsap.ticker.remove(raf)
      lenis.destroy()
    }
  }, [])

  return <>{children}</>
}
