'use client'

import { motion } from 'framer-motion'
import { Code2, Rocket, ShieldCheck, Sparkles, TestTube2 } from 'lucide-react'

const agents = [
  {
    name: 'Plan',
    icon: Sparkles,
    desc: 'Turns your prompt into a concrete architecture and file plan.',
  },
  { name: 'Code', icon: Code2, desc: 'Generates the full multi-file app and verifies it builds.' },
  {
    name: 'Test',
    icon: TestTube2,
    desc: 'Writes a Vitest suite and runs it in an isolated sandbox.',
  },
  {
    name: 'Security',
    icon: ShieldCheck,
    desc: 'Scans with Semgrep and auto-fixes what it can — halts on critical.',
  },
  { name: 'Deploy', icon: Rocket, desc: 'Ships the finished app live to a real URL.' },
]

/** The 5-agent pipeline story — static cards with a single reveal (no looping animation). */
export default function Pipeline() {
  return (
    <section id="pipeline" className="relative z-10 w-full bg-canvas py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-4 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7 }}
          className="text-center"
        >
          <p className="mb-5 text-xs font-medium uppercase tracking-[0.08em] text-ink-muted">
            The pipeline
          </p>
          <h2 className="mx-auto max-w-3xl text-4xl font-medium leading-[1.0] tracking-[-0.03em] text-ink md:text-6xl">
            Five agents. One pass.
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-snug tracking-[-0.01em] text-ink-muted">
            Every build runs the full chain — so you ship something tested and scanned, not a
            half-finished draft.
          </p>
        </motion.div>

        <div className="mt-16 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {agents.map((agent, index) => (
            <motion.div
              key={agent.name}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ duration: 0.5, delay: index * 0.08 }}
              className="rounded-2xl border border-hairline bg-surface-1 p-5"
            >
              <div className="flex items-center gap-2">
                <span className="flex size-8 items-center justify-center rounded-lg bg-surface-2 text-ink">
                  <agent.icon className="size-4" />
                </span>
                <span className="text-[11px] font-medium uppercase tracking-wider text-ink-muted">
                  Step {index + 1}
                </span>
              </div>
              <h3 className="mt-4 text-lg font-medium tracking-[-0.01em] text-ink">{agent.name}</h3>
              <p className="mt-1.5 text-sm leading-snug text-ink-muted">{agent.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
