'use client'

import { Check, CircleDashed, LoaderCircle, X } from 'lucide-react'
import { AGENTS, type PipelineState, type StageStatus } from '@/lib/pipeline-reducer'
import { cn } from '@/lib/utils'

const LABELS: Record<(typeof AGENTS)[number], string> = {
  plan: 'Plan',
  code: 'Code',
  test: 'Test',
  security: 'Security',
  deploy: 'Deploy',
}

function StatusIcon({ status }: { status: StageStatus }) {
  switch (status) {
    case 'running':
      return <LoaderCircle className="size-4 animate-spin text-accent-blue" />
    case 'complete':
      return <Check className="size-4 text-success" />
    case 'error':
      return <X className="size-4 text-red-400" />
    default:
      return <CircleDashed className="size-4 text-ink-muted" />
  }
}

/** Vertical 5-stage pipeline tracker with the live progress message per stage. */
export function AgentPipeline({ state }: { state: PipelineState }) {
  return (
    <div className="border-b border-hairline p-4">
      <p className="mb-3 text-[11px] font-medium uppercase tracking-wider text-ink-muted">
        Pipeline
      </p>
      <ol className="space-y-2.5">
        {AGENTS.map((agent) => {
          const stage = state.stages[agent]
          return (
            <li key={agent} className="flex items-start gap-3">
              <span className="mt-0.5">
                <StatusIcon status={stage.status} />
              </span>
              <div className="min-w-0 flex-1">
                <p
                  className={cn(
                    'text-sm leading-tight',
                    stage.status === 'pending' ? 'text-ink-muted' : 'text-ink',
                  )}
                >
                  {LABELS[agent]}
                </p>
                {stage.error ? (
                  <p className="truncate text-xs text-red-400">{stage.error}</p>
                ) : stage.message ? (
                  <p className="truncate text-xs text-ink-muted">{stage.message}</p>
                ) : null}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
