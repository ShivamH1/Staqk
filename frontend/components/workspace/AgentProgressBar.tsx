'use client'

import { Check, CircleDashed, LoaderCircle, X } from 'lucide-react'
import { AGENTS, type PipelineState, type StageStatus } from '@/lib/pipeline-reducer'

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
      return <X className="size-4 text-red-500" />
    default:
      return <CircleDashed className="size-4 text-ink-muted" />
  }
}

export function AgentProgressBar({ state }: { state: PipelineState }) {
  return (
    <div className="flex items-center gap-2">
      {AGENTS.map((agent, i) => {
        const stage = state.stages[agent]
        const active = stage.status === 'running'
        return (
          <div key={agent} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-2 rounded-pill px-3 py-1.5 text-sm transition-colors ${
                active
                  ? 'bg-surface-2 text-ink'
                  : stage.status === 'complete'
                    ? 'bg-surface-1 text-ink'
                    : 'bg-surface-1 text-ink-muted'
              }`}
              title={stage.error ?? stage.message ?? LABELS[agent]}
            >
              <StatusIcon status={stage.status} />
              <span>{LABELS[agent]}</span>
            </div>
            {i < AGENTS.length - 1 && <div className="h-px w-4 bg-hairline" />}
          </div>
        )
      })}
    </div>
  )
}
