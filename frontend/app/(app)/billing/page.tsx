'use client'

import { useQueryClient } from '@tanstack/react-query'
import { Check, LoaderCircle } from 'lucide-react'
import { useState } from 'react'
import { Card, StatusBadge } from '@/components/app/primitives'
import { useCreateOrder, usePacks, useTransactions } from '@/lib/hooks/use-billing'
import { useCurrentUser } from '@/lib/hooks/use-user'
import { openCheckout } from '@/lib/razorpay'
import type { CreditPack } from '@/lib/types'
import { formatCurrency, formatDate } from '@/lib/utils'

const planFeatures = ['Unlimited projects', 'Priority compute', 'Advanced IDE features']

const planLabels: Record<string, { name: string; price: string }> = {
  free: { name: 'Free Plan', price: '$0 / month' },
  starter: { name: 'Starter Plan', price: '$19 / month' },
  pro: { name: 'Pro Plan', price: '$49 / month' },
  team: { name: 'Team Plan', price: '$99 / month' },
  enterprise: { name: 'Enterprise', price: 'Custom' },
}

/** Best value = cheapest price per credit across the available packs. */
function bestPackId(packs: CreditPack[]): string | null {
  if (packs.length === 0) return null
  return packs.reduce((best, pack) =>
    pack.amount / pack.credits < best.amount / best.credits ? pack : best,
  ).id
}

/** "+500 cr" / "−5 cr" from a signed ledger amount. */
function formatCredits(amount: number): string {
  return `${amount >= 0 ? '+' : '−'}${Math.abs(amount)} cr`
}

export default function BillingPage() {
  const { data: user } = useCurrentUser()
  const { data: packs, isLoading: packsLoading } = usePacks()
  const { data: transactions, isLoading: txnsLoading } = useTransactions()
  const createOrder = useCreateOrder()
  const queryClient = useQueryClient()

  const [pendingPack, setPendingPack] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const plan = planLabels[user?.plan ?? 'free'] ?? planLabels.free
  const best = packs ? bestPackId(packs) : null

  const handlePurchase = async (packId: string) => {
    if (pendingPack) return
    setError(null)
    setPendingPack(packId)
    try {
      const order = await createOrder.mutateAsync(packId)
      await openCheckout({
        key: order.key_id,
        order_id: order.order_id,
        amount: order.amount,
        currency: order.currency,
        name: 'Staqk',
        description: `${order.credits} credits`,
        prefill: user?.email ? { email: user.email } : undefined,
        theme: { color: '#090909' },
        handler: () => {
          // Credits are granted server-side by the webhook; refetch to reflect them.
          queryClient.invalidateQueries({ queryKey: ['me'] })
          queryClient.invalidateQueries({ queryKey: ['transactions'] })
        },
      })
    } catch {
      setError('Could not start checkout. Please try again.')
    } finally {
      // Checkout has its own modal now — the button spinner only covers setup.
      setPendingPack(null)
    }
  }

  const scrollToRecharge = () => {
    document.getElementById('recharge')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8 md:py-10">
      <h1 className="text-5xl font-medium uppercase tracking-[-0.05em] md:text-6xl">Billing</h1>

      <div className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-[1.6fr_1fr]">
        {/* Credit balance */}
        <Card className="flex flex-col p-7">
          <div className="flex items-baseline gap-3">
            <span className="text-6xl font-medium tracking-[-0.04em]">{user?.credits ?? '—'}</span>
            <span className="text-sm uppercase tracking-wider text-ink-muted">
              credits remaining
            </span>
          </div>
          <p className="mt-3 max-w-sm text-sm text-ink-muted">
            Credits power the AI pipeline — 5 per full build, 2 per chat iteration. Failed runs are
            automatically refunded.
          </p>
          <button
            type="button"
            onClick={scrollToRecharge}
            className="mt-6 w-fit rounded-pill bg-white px-5 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
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
      <h2 id="recharge" className="mt-12 scroll-mt-8 text-2xl font-medium tracking-[-0.02em]">
        Recharge credits
      </h2>
      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
        {packsLoading &&
          [0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-[164px] animate-pulse rounded-2xl border border-hairline bg-surface-1"
            />
          ))}

        {packs?.map((pack) => {
          const isBest = pack.id === best
          const isPending = pendingPack === pack.id
          return (
            <Card key={pack.id} className={isBest ? 'relative bg-surface-2 p-6' : 'relative p-6'}>
              {isBest && (
                <span className="absolute right-4 top-4 rounded-pill bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-black">
                  Best value
                </span>
              )}
              <div className="flex items-baseline justify-between">
                <span className="text-3xl font-medium tracking-[-0.03em]">{pack.credits}</span>
                <span className="text-sm text-ink-muted">
                  {formatCurrency(pack.amount, pack.currency)}
                </span>
              </div>
              <p className="text-xs uppercase tracking-wider text-ink-muted">Credits</p>
              <button
                type="button"
                onClick={() => handlePurchase(pack.id)}
                disabled={Boolean(pendingPack)}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-pill bg-white px-5 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isPending && <LoaderCircle className="size-4 animate-spin" />}
                {isPending ? 'Starting…' : 'Purchase'}
              </button>
            </Card>
          )
        })}
      </div>

      {/* History */}
      <h2 className="mt-12 text-2xl font-medium tracking-[-0.02em]">Transaction history</h2>
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
            {txnsLoading && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-sm text-ink-muted">
                  Loading…
                </td>
              </tr>
            )}
            {transactions?.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-sm text-ink-muted">
                  No transactions yet.
                </td>
              </tr>
            )}
            {transactions?.map((txn) => (
              <tr key={txn.id} className="border-b border-hairline-soft last:border-0">
                <td className="px-5 py-3 font-mono text-ink-muted">{formatDate(txn.created_at)}</td>
                <td className="px-5 py-3">{txn.description}</td>
                <td className="px-5 py-3">
                  <StatusBadge status={txn.type} />
                </td>
                <td className="px-5 py-3 text-right font-mono">{formatCredits(txn.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
