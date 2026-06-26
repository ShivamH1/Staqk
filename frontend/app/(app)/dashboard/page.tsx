'use client'

import { Coins, Plus } from 'lucide-react'
import Link from 'next/link'
import { EmptyState } from '@/components/app/empty-state'
import { Card, StatusBadge } from '@/components/app/primitives'
import { useProjects } from '@/lib/hooks/use-projects'
import { useCurrentUser } from '@/lib/hooks/use-user'
import { formatRelativeTime } from '@/lib/utils'

export default function DashboardPage() {
  const { data: projects, isLoading, isError, refetch } = useProjects()
  const { data: user } = useCurrentUser()

  return (
    <div className="mx-auto max-w-6xl px-5 py-8 md:px-8 md:py-10">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-4xl font-medium tracking-[-0.04em] md:text-5xl">Your projects</h1>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 rounded-pill bg-surface-1 px-3 py-1.5 text-sm text-ink-muted">
            <Coins className="size-4 text-gradient-orange" />
            {user ? `${user.credits} credits` : '— credits'}
          </span>
          <Link
            href="/new"
            className="flex items-center gap-1.5 rounded-pill bg-white px-4 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
          >
            <Plus className="size-4" /> New project
          </Link>
        </div>
      </div>

      {isLoading && (
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-[232px] animate-pulse rounded-2xl border border-hairline bg-surface-1"
            />
          ))}
        </div>
      )}

      {isError && (
        <div className="mt-8 flex flex-col items-center gap-3 rounded-2xl border border-hairline bg-surface-1 py-16 text-center">
          <p className="text-sm text-ink-muted">Couldn’t load your projects.</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="rounded-pill bg-surface-2 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-hairline"
          >
            Try again
          </button>
        </div>
      )}

      {projects && projects.length === 0 && <EmptyState />}

      {projects && projects.length > 0 && (
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link key={project.id} href={`/workspace/${project.id}`}>
              <Card className="overflow-hidden transition-colors hover:border-ink-muted/40">
                <div className="aspect-video bg-gradient-to-br from-surface-2 to-canvas" />
                <div className="flex items-center justify-between px-4 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{project.name}</p>
                    <p className="text-xs text-ink-muted">
                      Last edited {formatRelativeTime(project.updated_at)}
                    </p>
                  </div>
                  <StatusBadge status={project.status} />
                </div>
              </Card>
            </Link>
          ))}

          <Link href="/new">
            <div className="flex h-full min-h-[180px] flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-hairline bg-surface-1/40 px-6 text-center transition-colors hover:border-ink-muted/40">
              <div className="flex size-10 items-center justify-center rounded-full bg-surface-2">
                <Plus className="size-5 text-ink-muted" />
              </div>
              <p className="text-sm font-medium">Start from scratch</p>
              <p className="text-xs text-ink-muted">
                Create a new app with our AI builder or start with a template.
              </p>
            </div>
          </Link>
        </div>
      )}

      {/* Single vibrant spotlight panel (design.md: scarce, never decoration). */}
      <div className="mt-8 overflow-hidden rounded-2xl bg-gradient-to-br from-gradient-violet to-gradient-magenta p-8">
        <p className="text-xs font-semibold uppercase tracking-wider text-white/70">Pro tip</p>
        <h2 className="mt-2 text-2xl font-medium tracking-[-0.02em] text-white">
          Unlock the full power of Staqk API
        </h2>
        <p className="mt-1 max-w-md text-sm text-white/80">
          Connect your projects directly to external data sources and custom logic with our new SDK.
        </p>
        <button
          type="button"
          className="mt-5 rounded-pill bg-white px-4 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
        >
          Read documentation
        </button>
      </div>
    </div>
  )
}
