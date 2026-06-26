'use client'

import { Globe } from 'lucide-react'
import type { PipelineState } from '@/lib/pipeline-reducer'

export function PreviewPanel({ state }: { state: PipelineState }) {
  const url = state.deploymentUrl

  return (
    <div className="flex h-full flex-col bg-canvas">
      {/* Browser chrome */}
      <div className="flex h-9 shrink-0 items-center gap-3 border-b border-hairline px-3">
        <div className="flex gap-1.5">
          <span className="size-2.5 rounded-full bg-surface-2" />
          <span className="size-2.5 rounded-full bg-surface-2" />
          <span className="size-2.5 rounded-full bg-surface-2" />
        </div>
        <div className="flex-1 truncate rounded-md bg-surface-1 px-3 py-1 font-mono text-xs text-ink-muted">
          {url ?? 'preview pending'}
        </div>
      </div>

      <div className="min-h-0 flex-1">
        {url ? (
          <iframe title="Live preview" src={url} className="h-full w-full border-0 bg-white" />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-ink-muted">
            <Globe className="size-8" />
            <p className="text-sm">
              {state.status === 'running' ? 'Building your app…' : 'Preview appears after deploy'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
