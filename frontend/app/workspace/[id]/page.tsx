'use client'

import { use, useState } from 'react'
import { AgentProgressBar } from '@/components/workspace/AgentProgressBar'
import { ChatPanel } from '@/components/workspace/ChatPanel'
import { CodeEditor } from '@/components/workspace/CodeEditor'
import { FileTree } from '@/components/workspace/FileTree'
import { PreviewPanel } from '@/components/workspace/PreviewPanel'
import { usePipeline } from '@/lib/hooks/use-pipeline'

export default function WorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { state, start } = usePipeline(id)
  const [selected, setSelected] = useState<string | null>(null)

  const running = state.status === 'running'

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-hairline px-4">
        <span className="text-sm font-medium">Project {id}</span>
        <AgentProgressBar state={state} />
        <span className="text-sm text-ink-muted">
          {state.status === 'complete' ? `${state.creditsUsed} credits` : '—'}
        </span>
      </header>

      {/* Body: file tree | editor | preview */}
      <div className="flex min-h-0 flex-1">
        <aside className="w-56 shrink-0 overflow-y-auto border-r border-hairline">
          <FileTree files={state.files} selected={selected} onSelect={setSelected} />
        </aside>

        <main className="min-w-0 flex-1 border-r border-hairline">
          <CodeEditor path={selected} value="" />
        </main>

        <aside className="w-80 shrink-0">
          <PreviewPanel state={state} />
        </aside>
      </div>

      {/* Chat */}
      <section className="h-64 shrink-0 border-t border-hairline">
        <ChatPanel
          state={state}
          disabled={running}
          onSend={(message) => start({ userMessage: message })}
        />
      </section>
    </div>
  )
}
