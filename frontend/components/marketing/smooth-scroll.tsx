'use client'

import Lenis from 'lenis'
import 'lenis/dist/lenis.css'
import { useEffect } from 'react'

/**
 * Full-page smooth scroll for marketing routes (design.md animation domain).
 * Mounts Lenis on the window scroll and drives its RAF loop; renders nothing.
 * Honors `prefers-reduced-motion` by staying out of the way entirely.
 */
export default function SmoothScroll() {
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const lenis = new Lenis({
      duration: 1.1,
      easing: (t) => 1 - (1 - t) ** 3,
    })

    let frame = 0
    const loop = (time: number) => {
      lenis.raf(time)
      frame = requestAnimationFrame(loop)
    }
    frame = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(frame)
      lenis.destroy()
    }
  }, [])

  return null
}
