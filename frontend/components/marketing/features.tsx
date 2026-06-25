'use client'

import { motion, useInView } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'

/** Types `text` out one character at a time after `delay`ms. */
function useTypingAnimation(text: string, speed = 50, delay = 0) {
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    setIsTyping(true)
    setDisplayedText('')
    let currentIndex = 0
    let interval: ReturnType<typeof setInterval>

    const timeoutId = setTimeout(() => {
      interval = setInterval(() => {
        currentIndex++
        setDisplayedText(text.slice(0, currentIndex))
        if (currentIndex >= text.length) {
          setIsTyping(false)
          clearInterval(interval)
        }
      }, speed)
    }, delay)

    return () => {
      clearTimeout(timeoutId)
      clearInterval(interval)
    }
  }, [text, speed, delay])

  return { displayedText, isTyping }
}

const TOP_ROW = ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P']
const MIDDLE_ROW = ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L']
const BOTTOM_ROW = ['Z', 'X', 'C', 'V', 'B', 'N', 'M']

function Key({ index }: { index: number }) {
  return (
    <motion.div
      className="h-9 w-9 rounded-[7px] border border-white/[0.06] bg-white/[0.035] md:h-11 md:w-11"
      initial={{ opacity: 0.45 }}
      animate={{ opacity: [0.45, 0.9, 0.45] }}
      transition={{ duration: 2.5, repeat: Number.POSITIVE_INFINITY, delay: index * 0.08 }}
    />
  )
}

/** Faux keyboard whose keys gently pulse — a calm, ambient build visual. */
function KeyboardVisual() {
  return (
    <div className="relative mx-auto mt-10 w-fit">
      <div className="rounded-[18px] border border-hairline bg-surface-1 p-3">
        <div className="rounded-[12px] bg-surface-2 px-4 py-4 md:px-5 md:py-5">
          <div className="mb-2 flex gap-2">
            {TOP_ROW.map((key, i) => (
              <Key key={key} index={i} />
            ))}
          </div>
          <div className="mb-2 flex gap-2 pl-4 md:pl-6">
            {MIDDLE_ROW.map((key, i) => (
              <Key key={key} index={i + 10} />
            ))}
          </div>
          <div className="flex gap-2 pl-8 md:pl-12">
            {BOTTOM_ROW.map((key, i) => (
              <Key key={key} index={i + 19} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Features() {
  const sectionRef = useRef(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })

  const { displayedText: query1, isTyping: isTyping1 } = useTypingAnimation(
    'build a SaaS dashboard',
    60,
    500,
  )
  const { displayedText: query2, isTyping: isTyping2 } = useTypingAnimation(
    'a secure, tested, deployed app',
    60,
    3000,
  )

  return (
    <section
      id="product"
      ref={sectionRef}
      className="relative z-10 w-full bg-canvas py-24 md:py-32"
    >
      <div className="mx-auto max-w-6xl px-4 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <p className="mb-5 text-xs font-medium uppercase tracking-[0.08em] text-ink-muted">
            How it works
          </p>
          <h2 className="mx-auto max-w-3xl text-4xl font-medium leading-[1.0] tracking-[-0.03em] text-ink md:text-6xl">
            Describe it. Watch it ship.
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-snug tracking-[-0.01em] text-ink-muted">
            Tell Staqk to{' '}
            <span className="font-medium text-ink">
              {query1}
              {isTyping1 && <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-ink" />}
            </span>{' '}
            and it returns{' '}
            <span className="font-medium text-ink">
              {query2}
              {isTyping2 && <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-ink" />}
            </span>{' '}
            — planned, coded, tested, and security-scanned in one pass.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <KeyboardVisual />
        </motion.div>
      </div>
    </section>
  )
}
