'use client'

import { motion } from 'framer-motion'
import { Check } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

type Tier = {
  name: string
  price: string
  credits: string
  features: string[]
  cta: string
  featured?: boolean
}

const tiers: Tier[] = [
  {
    name: 'Free',
    price: '$0',
    credits: '20 credits / mo',
    features: ['1 active project', 'Community support'],
    cta: 'Start free',
  },
  {
    name: 'Starter',
    price: '$19',
    credits: '200 credits / mo',
    features: ['Unlimited projects', 'Email support', 'Custom domains'],
    cta: 'Get Starter',
  },
  {
    name: 'Pro',
    price: '$49',
    credits: '600 credits / mo',
    features: ['Priority compute', 'Advanced security scans', 'Version history'],
    cta: 'Get Pro',
    featured: true,
  },
  {
    name: 'Team',
    price: '$99',
    credits: '1,500 credits / mo',
    features: ['5 seats', 'Shared projects', 'SSO'],
    cta: 'Get Team',
  },
]

export default function Pricing() {
  return (
    <section id="pricing" className="relative z-10 w-full bg-canvas py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-4 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7 }}
          className="text-center"
        >
          <p className="mb-5 text-xs font-medium uppercase tracking-[0.08em] text-ink-muted">
            Pricing
          </p>
          <h2 className="mx-auto max-w-3xl text-4xl font-medium leading-[1.0] tracking-[-0.03em] text-ink md:text-6xl">
            Simple, credit-based pricing
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-snug tracking-[-0.01em] text-ink-muted">
            A full pipeline run costs 5 credits; a chat iteration costs 2. Pick a plan and only
            spend on what you build.
          </p>
        </motion.div>

        <div className="mt-16 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={cn(
                'flex flex-col rounded-2xl border p-6',
                tier.featured ? 'border-ink-muted/30 bg-surface-2' : 'border-hairline bg-surface-1',
              )}
            >
              {tier.featured && (
                <span className="mb-3 w-fit rounded-pill bg-white px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-black">
                  Most popular
                </span>
              )}
              <h3 className="text-lg font-medium tracking-[-0.01em] text-ink">{tier.name}</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-4xl font-medium tracking-[-0.03em] text-ink">
                  {tier.price}
                </span>
                <span className="text-sm text-ink-muted">/ mo</span>
              </div>
              <p className="mt-1 text-sm text-ink-muted">{tier.credits}</p>

              <ul className="mt-5 flex-1 space-y-2.5">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-ink">
                    <Check className="mt-0.5 size-4 shrink-0 text-success" />
                    {feature}
                  </li>
                ))}
              </ul>

              <Link
                href="/sign-up"
                className={cn(
                  'mt-6 rounded-pill px-4 py-2 text-center text-sm font-medium transition-transform hover:scale-[0.98]',
                  tier.featured ? 'bg-white text-black' : 'bg-surface-2 text-ink hover:bg-hairline',
                )}
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* One vibrant enterprise spotlight (design.md: scarce). */}
        <div className="mt-6 flex flex-col items-start justify-between gap-5 overflow-hidden rounded-2xl bg-gradient-to-br from-gradient-violet to-gradient-magenta p-8 md:flex-row md:items-center">
          <div>
            <h3 className="text-2xl font-medium tracking-[-0.02em] text-white">
              Need more? Staqk for Enterprise
            </h3>
            <p className="mt-1 max-w-md text-sm text-white/80">
              Volume credits, dedicated compute, audit logs, and a custom security policy.
            </p>
          </div>
          <Link
            href="/sign-up"
            className="shrink-0 rounded-pill bg-white px-5 py-2.5 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
          >
            Contact sales
          </Link>
        </div>
      </div>
    </section>
  )
}
