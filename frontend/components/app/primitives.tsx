import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

/** Charcoal surface card with a hairline border (design.md workspace-card). */
export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <div className={cn('rounded-2xl border border-hairline bg-surface-1', className)}>
      {children}
    </div>
  )
}

const statusStyles: Record<string, string> = {
  // Project statuses
  draft: 'bg-surface-2 text-ink-muted',
  building: 'bg-accent-blue/15 text-accent-blue',
  ready: 'bg-success/15 text-success',
  deployed: 'bg-success/15 text-success',
  error: 'bg-red-500/15 text-red-400',
  // Transaction types
  purchase: 'bg-success/15 text-success',
  refund: 'bg-accent-blue/15 text-accent-blue',
  spend: 'bg-surface-2 text-ink-muted',
}

/** Project / transaction status pill. */
export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        'rounded-pill px-2 py-0.5 text-[11px] font-medium capitalize',
        statusStyles[status] ?? statusStyles.draft,
      )}
    >
      {status}
    </span>
  )
}
