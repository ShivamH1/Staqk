'use client'

import { ChevronLeft, Coins, ExternalLink, Rocket } from 'lucide-react'
import Link from 'next/link'
import { StatusBadge } from '@/components/app/primitives'
import type { ProjectStatus } from '@/lib/types'

interface WorkspaceHeaderProps {
  name: string
  status: ProjectStatus
  credits?: number
  deploymentUrl?: string
  canDeploy?: boolean
  onDeploy?: () => void
}

export function WorkspaceHeader({
  name,
  status,
  credits,
  deploymentUrl,
  canDeploy,
  onDeploy,
}: WorkspaceHeaderProps) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-hairline px-4">
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard"
          aria-label="Back to projects"
          className="flex size-8 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-1 hover:text-ink"
        >
          <ChevronLeft className="size-5" />
        </Link>
        <div className="flex size-7 items-center justify-center rounded-md bg-white text-xs font-semibold text-black">
          S
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-ink">{name}</span>
          <StatusBadge status={status} />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1.5 rounded-pill bg-surface-1 px-3 py-1.5 text-sm text-ink-muted">
          <Coins className="size-4 text-gradient-orange" />
          {credits ?? '—'} credits
        </span>
        {deploymentUrl ? (
          <a
            href={deploymentUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-pill bg-white px-4 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
          >
            <ExternalLink className="size-4" /> Open app
          </a>
        ) : (
          <button
            type="button"
            onClick={onDeploy}
            disabled={!canDeploy}
            title={canDeploy ? 'Get deployment instructions' : 'Finish a build to deploy'}
            className="flex items-center gap-1.5 rounded-pill bg-white px-4 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.98] disabled:cursor-not-allowed disabled:bg-surface-1 disabled:text-ink-muted"
          >
            <Rocket className="size-4" /> Deploy
          </button>
        )}
      </div>
    </header>
  )
}
