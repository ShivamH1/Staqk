'use client'

import { Check, Download } from 'lucide-react'
import { Card, StatusBadge } from '@/components/app/primitives'
import { useCurrentUser } from '@/lib/hooks/use-user'

const packs = [
  { credits: '100', price: '$10' },
  { credits: '500', price: '$40', best: true },
  { credits: '2000', price: '$150' },
]

const planFeatures = ['Unlimited projects', 'Priority compute', 'Advanced IDE features']

const planLabels: Record<string, { name: string; price: string }> = {
  free: { name: 'Free Plan', price: '$0 / month' },
  starter: { name: 'Starter Plan', price: '$19 / month' },
  pro: { name: 'Pro Plan', price: '$49 / month' },
  team: { name: 'Team Plan', price: '$99 / month' },
  enterprise: { name: 'Enterprise', price: 'Custom' },
}

type Txn = { date: string; desc: string; type: string; amount: string }
const transactions: Txn[] = [
  { date: '2024-05-24', desc: '500 Credits Recharge', type: 'purchase', amount: '+$40.00' },
  { date: '2024-05-22', desc: 'Pipeline run — todo-app', type: 'spend', amount: '−5 cr' },
  { date: '2024-05-20', desc: 'Refund — failed run', type: 'refund', amount: '+5 cr' },
]

export default function BillingPage() {
  const { data: user } = useCurrentUser()
  const plan = planLabels[user?.plan ?? 'pro'] ?? planLabels.pro

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8 md:py-10">
      <h1 className="text-5xl font-medium uppercase tracking-[-0.05em] md:text-6xl">Billing</h1>

      <div className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-[1.6fr_1fr]">
        {/* Credit balance */}
        <Card className="p-7">
          <div className="flex items-baseline gap-3">
            <span className="text-6xl font-medium tracking-[-0.04em]">{user?.credits ?? '—'}</span>
            <span className="text-sm uppercase tracking-wider text-ink-muted">
              credits remaining
            </span>
          </div>
          <div className="mt-5 h-1.5 w-full overflow-hidden rounded-pill bg-surface-2">
            <div className="h-full w-[42%] rounded-pill bg-white" />
          </div>
          <p className="mt-3 text-sm text-ink-muted">
            You have used 58% of your monthly credit allowance. Your credits will reset in 12 days.
          </p>
          <button
            type="button"
            className="mt-6 rounded-pill bg-white px-5 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
          >
            Buy credits
          </button>
        </Card>

        {/* Active plan */}
        <Card className="flex flex-col p-7">
          <span className="w-fit rounded-pill bg-accent-blue/15 px-2.5 py-1 text-xs font-medium uppercase tracking-wider text-accent-blue">
            Active plan
          </span>
          <h2 className="mt-3 text-2xl font-medium tracking-[-0.02em]">{plan.name}</h2>
          <p className="text-sm text-ink-muted">{plan.price}</p>
          <ul className="mt-4 space-y-2">
            {planFeatures.map((feature) => (
              <li key={feature} className="flex items-center gap-2 text-sm text-ink">
                <Check className="size-4 text-success" />
                {feature}
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="mt-auto rounded-pill bg-surface-2 px-5 py-2 text-sm font-medium text-ink transition-colors hover:bg-hairline"
          >
            Manage plan
          </button>
        </Card>
      </div>

      {/* Recharge */}
      <h2 className="mt-12 text-2xl font-medium tracking-[-0.02em]">Recharge credits</h2>
      <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
        {packs.map((pack) => (
          <Card
            key={pack.credits}
            className={pack.best ? 'relative bg-surface-2 p-6' : 'relative p-6'}
          >
            {pack.best && (
              <span className="absolute right-4 top-4 rounded-pill bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-black">
                Best value
              </span>
            )}
            <div className="flex items-baseline justify-between">
              <span className="text-3xl font-medium tracking-[-0.03em]">{pack.credits}</span>
              <span className="text-sm text-ink-muted">{pack.price}</span>
            </div>
            <p className="text-xs uppercase tracking-wider text-ink-muted">Credits</p>
            <button
              type="button"
              className="mt-5 w-full rounded-pill bg-white px-5 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.99]"
            >
              Purchase
            </button>
          </Card>
        ))}
      </div>

      {/* History */}
      <div className="mt-12 flex items-center justify-between">
        <h2 className="text-2xl font-medium tracking-[-0.02em]">Transaction history</h2>
        <button
          type="button"
          className="flex items-center gap-1.5 text-sm text-ink-muted transition-colors hover:text-ink"
        >
          <Download className="size-4" /> Export CSV
        </button>
      </div>
      <Card className="mt-5 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left text-xs uppercase tracking-wider text-ink-muted">
              <th className="px-5 py-3 font-medium">Date</th>
              <th className="px-5 py-3 font-medium">Description</th>
              <th className="px-5 py-3 font-medium">Type</th>
              <th className="px-5 py-3 text-right font-medium">Amount</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => (
              <tr
                key={`${txn.date}-${txn.desc}`}
                className="border-b border-hairline-soft last:border-0"
              >
                <td className="px-5 py-3 font-mono text-ink-muted">{txn.date}</td>
                <td className="px-5 py-3">{txn.desc}</td>
                <td className="px-5 py-3">
                  <StatusBadge status={txn.type} />
                </td>
                <td className="px-5 py-3 text-right font-mono">{txn.amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
