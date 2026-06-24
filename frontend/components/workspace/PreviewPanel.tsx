'use client'

import { Globe } from 'lucide-react'
import type { PipelineState } from '@/lib/pipeline-reducer'

export function PreviewPanel({ state }: { state: PipelineState }) {
  if (state.status === 'complete' && state.deploymentUrl) {
    return (
      <iframe
        title="Live preview"
        src={state.deploymentUrl}
        className="h-full w-full border-0 bg-white"
      />
    )
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-ink-muted">
      <Globe className="size-8" />
      <p className="text-sm">
        {state.status === 'running' ? 'Building your app…' : 'Preview appears after deploy'}
      </p>
    </div>
  )
}
