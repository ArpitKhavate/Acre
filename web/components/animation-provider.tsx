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

    const lenis = new Lenis({
      duration: 1.25,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      touchMultiplier: 1.1,
    })

    // Lenis ↔ ScrollTrigger — keeps scrub timelines smooth
    ScrollTrigger.scrollerProxy(document.documentElement, {
      scrollTop(value) {
        if (arguments.length) {
          lenis.scrollTo(value, { immediate: true })
        }
        return lenis.scroll
      },
      getBoundingClientRect() {
        return {
          top: 0,
          left: 0,
          width: window.innerWidth,
          height: window.innerHeight,
        }
      },
      pinType: document.documentElement.style.transform ? 'transform' : 'fixed',
    })

    lenis.on('scroll', ScrollTrigger.update)
    const raf = (time: number) => lenis.raf(time * 1000)
    gsap.ticker.add(raf)
    gsap.ticker.lagSmoothing(0)

    const ctx = gsap.context(() => {
      // ===== Hero intro (plays on load) =====
      const hero = document.querySelector('[data-hero]')
      if (hero) {
        const heroBg = hero.querySelector('[data-hero-bg]')
        if (heroBg) {
          gsap.to(heroBg, {
            y: '18%',
            scale: 1.08,
            ease: 'none',
            scrollTrigger: {
              trigger: hero,
              start: 'top top',
              end: 'bottom top',
              scrub: 0.6,
            },
          })
        }

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

      // ===== Tree scroll story — stick tree: trunk draw, branches, leaves, cards =====
      gsap.utils.toArray<HTMLElement>('[data-tree-story]').forEach((section) => {
        const trunk = section.querySelector<SVGPathElement>('[data-tree-trunk]')
        const root = section.querySelector<SVGGElement>('[data-tree-root]')
        const branches = section.querySelectorAll<SVGPathElement>('[data-tree-branch]')
        const leaves = section.querySelectorAll<SVGCircleElement>('[data-tree-leaf]')
        const dots = section.querySelectorAll<HTMLElement>('[data-tree-dot]')
        const nodes = section.querySelectorAll<HTMLElement>('[data-tree-node]')

        const treeTl = gsap.timeline({
          scrollTrigger: {
            trigger: section,
            start: 'top 68%',
            end: 'bottom 22%',
            scrub: 0.5,
          },
        })

        if (trunk) {
          const trunkLen = trunk.getTotalLength()
          gsap.set(trunk, { strokeDasharray: trunkLen, strokeDashoffset: trunkLen })
          treeTl.to(trunk, { strokeDashoffset: 0, duration: 0.34, ease: 'none' }, 0)
        }

        if (root) {
          gsap.set(root, { opacity: 0 })
          treeTl.to(root, { opacity: 0.6, duration: 0.08, ease: 'power1.out' }, 0.06)
        }

        branches.forEach((branch, i) => {
          const len = branch.getTotalLength()
          gsap.set(branch, { strokeDasharray: len, strokeDashoffset: len })
          treeTl.to(branch, { strokeDashoffset: 0, duration: 0.08, ease: 'none' }, 0.14 + i * 0.12)
        })

        leaves.forEach((leaf, i) => {
          gsap.set(leaf, { opacity: 0, scale: 0, transformOrigin: '50% 50%' })
          treeTl.to(
            leaf,
            { opacity: 0.9, scale: 1, duration: 0.08, ease: 'back.out(2)' },
            0.2 + i * 0.1,
          )
        })

        dots.forEach((dot, i) => {
          gsap.set(dot, { scale: 0, opacity: 0 })
          treeTl.to(dot, { scale: 1, opacity: 1, duration: 0.07, ease: 'back.out(2)' }, 0.22 + i * 0.12)
        })

        nodes.forEach((node, i) => {
          const left = node.dataset.treeSide === 'left'
          const card = node.querySelector<HTMLElement>('.tree-node-card')
          const healthBar = node.querySelector<HTMLElement>('[data-tree-health-bar]')
          const t = 0.24 + i * 0.12

          if (card) {
            gsap.set(card, { opacity: 0, x: left ? -28 : 28 })
            treeTl.to(card, { opacity: 1, x: 0, duration: 0.1, ease: 'power2.out' }, t)
          }

          if (healthBar) {
            gsap.set(healthBar, { width: '0%' })
            treeTl.to(healthBar, { width: '94%', duration: 0.12, ease: 'power1.inOut' }, t + 0.04)
          }
        })

        nodes.forEach((node) => {
          const card = node.querySelector('.tree-node-card')
          const branchIndex = node.dataset.treeIndex
          const branch = section.querySelector(`[data-branch-index="${branchIndex}"]`)
          if (!card) return

          ScrollTrigger.create({
            trigger: node,
            start: 'top 58%',
            end: 'bottom 42%',
            onEnter: () => {
              card.classList.add('tree-node-active')
              branch?.classList.add('tree-branch-active')
            },
            onEnterBack: () => {
              card.classList.add('tree-node-active')
              branch?.classList.add('tree-branch-active')
            },
            onLeave: () => {
              card.classList.remove('tree-node-active')
              branch?.classList.remove('tree-branch-active')
            },
            onLeaveBack: () => {
              card.classList.remove('tree-node-active')
              branch?.classList.remove('tree-branch-active')
            },
          })
        })
      })

      // ===== Signal loop (How it works) — pulse travels the perception chain =====
      gsap.utils.toArray<HTMLElement>('[data-signal-loop]').forEach((section) => {
        const path = section.querySelector<SVGPathElement>('[data-signal-path]')
        const pulse = section.querySelector<SVGCircleElement>('[data-signal-pulse]')
        const steps = section.querySelectorAll<HTMLElement>('[data-signal-step]')
        if (!path || !pulse) return

        const len = path.getTotalLength()
        gsap.set(path, { strokeDasharray: len, strokeDashoffset: len })

        ScrollTrigger.create({
          trigger: section,
          start: 'top 65%',
          end: 'bottom 35%',
          scrub: 0.55,
          onUpdate: (self) => {
            const p = self.progress
            gsap.set(path, { strokeDashoffset: len * (1 - p) })

            const point = path.getPointAtLength(len * p)
            gsap.set(pulse, { attr: { cx: point.x, cy: point.y }, opacity: p > 0.02 ? 1 : 0 })

            steps.forEach((step, i) => {
              const threshold = (i + 0.5) / steps.length
              step.classList.toggle('signal-step-active', p >= threshold - 0.08)
            })
          },
        })
      })

      // ===== Metrics — horizontal scan wipe reveals stats =====
      gsap.utils.toArray<HTMLElement>('[data-scan-stats]').forEach((section) => {
        const beam = section.querySelectorAll<HTMLElement>('[data-stats-beam]')
        const items = section.querySelectorAll<HTMLElement>('[data-stats-item]')
        if (!beam.length) return

        ScrollTrigger.create({
          trigger: section,
          start: 'top 75%',
          end: 'bottom 25%',
          scrub: 0.45,
          onUpdate: (self) => {
            const p = self.progress
            beam.forEach((b) => gsap.set(b, { left: `${p * 100}%` }))
            items.forEach((item, i) => {
              const threshold = (i + 0.3) / items.length
              item.classList.toggle('stats-item-lit', p >= threshold)
            })
          },
        })
      })

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
          scrollTrigger: { trigger: path, start: 'top 88%', scrub: 0.4 },
        })
      })

      // ===== Gentle parallax =====
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
              scrub: 0.5,
            },
          },
        )
      })
    })

    const onRefresh = () => lenis.resize()
    ScrollTrigger.addEventListener('refresh', onRefresh)
    const onLoad = () => ScrollTrigger.refresh()
    window.addEventListener('load', onLoad)
    const refreshId = window.setTimeout(() => ScrollTrigger.refresh(), 500)

    return () => {
      window.removeEventListener('load', onLoad)
      window.clearTimeout(refreshId)
      ScrollTrigger.removeEventListener('refresh', onRefresh)
      ctx.revert()
      gsap.ticker.remove(raf)
      lenis.destroy()
    }
  }, [])

  return <>{children}</>
}
