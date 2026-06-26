'use client'

import { useQueryClient } from '@tanstack/react-query'
import { use, useEffect, useMemo, useRef, useState } from 'react'
import { AgentPipeline } from '@/components/workspace/AgentPipeline'
import { ChatPanel } from '@/components/workspace/ChatPanel'
import { CodeEditor } from '@/components/workspace/CodeEditor'
import { FileTree } from '@/components/workspace/FileTree'
import { PreviewPanel } from '@/components/workspace/PreviewPanel'
import { WorkspaceHeader } from '@/components/workspace/WorkspaceHeader'
import { usePipeline } from '@/lib/hooks/use-pipeline'
import { useProject } from '@/lib/hooks/use-projects'
import { useCurrentUser } from '@/lib/hooks/use-user'
import type { ProjectStatus } from '@/lib/types'
import { cn } from '@/lib/utils'

export default function WorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const queryClient = useQueryClient()
  const { state, start, iterate } = usePipeline(id)
  const { data: project } = useProject(id)
  const { data: user } = useCurrentUser()

  const [selected, setSelected] = useState<string | null>(null)
  const [view, setView] = useState<'code' | 'preview'>('code')

  const running = state.status === 'running'
  const fileTree = useMemo(() => project?.file_tree ?? {}, [project])
  const hasFiles = Object.keys(fileTree).length > 0
  const files = useMemo(
    () => Array.from(new Set([...Object.keys(fileTree), ...state.files])).sort(),
    [fileTree, state.files],
  )

  // Auto-start the pipeline when arriving from /new with ?prompt= (once).
  const startedRef = useRef(false)
  useEffect(() => {
    if (startedRef.current || state.status !== 'idle') return
    const prompt = new URLSearchParams(window.location.search).get('prompt')
    if (prompt) {
      startedRef.current = true
      start({ userMessage: prompt })
    }
  }, [state.status, start])

  // When a run finishes, refetch the project (new file_tree) and the credit balance.
  useEffect(() => {
    if (state.status === 'complete') {
      queryClient.invalidateQueries({ queryKey: ['projects', id] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
    }
  }, [state.status, id, queryClient])

  // Select the first file once files exist.
  useEffect(() => {
    if (!selected && files.length > 0) setSelected(files[0])
  }, [files, selected])

  const handleSend = (message: string) => {
    if (hasFiles) iterate(message)
    else start({ userMessage: message })
  }

  const headerStatus: ProjectStatus = running ? 'building' : (project?.status ?? 'draft')
  const content = selected ? (fileTree[selected] ?? '') : ''

  return (
    <div className="flex h-screen flex-col bg-canvas text-ink">
      <WorkspaceHeader
        name={project?.name ?? 'Loading…'}
        status={headerStatus}
        credits={user?.credits}
        deploymentUrl={state.deploymentUrl}
      />

      <div className="flex min-h-0 flex-1">
        {/* Build panel: pipeline tracker + chat */}
        <aside className="flex w-[360px] shrink-0 flex-col border-r border-hairline">
          <AgentPipeline state={state} />
          <ChatPanel state={state} disabled={running} cost={hasFiles ? 2 : 5} onSend={handleSend} />
        </aside>

        {/* Main: Code / Preview */}
        <main className="flex min-w-0 flex-1 flex-col">
          <div className="flex h-11 shrink-0 items-center justify-between border-b border-hairline px-3">
            <div className="flex items-center gap-1 rounded-pill bg-surface-1 p-0.5 text-sm">
              {(['code', 'preview'] as const).map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setView(option)}
                  className={cn(
                    'rounded-pill px-3 py-1 capitalize transition-colors',
                    view === option ? 'bg-surface-2 text-ink' : 'text-ink-muted hover:text-ink',
                  )}
                >
                  {option}
                </button>
              ))}
            </div>
            {view === 'code' && selected && (
              <span className="truncate font-mono text-xs text-ink-muted">{selected}</span>
            )}
          </div>

          <div className="min-h-0 flex-1">
            {view === 'code' ? (
              <div className="flex h-full">
                <aside className="w-56 shrink-0 border-r border-hairline">
                  <FileTree files={files} selected={selected} onSelect={setSelected} />
                </aside>
                <div className="min-w-0 flex-1">
                  <CodeEditor path={selected} value={content} />
                </div>
              </div>
            ) : (
              <PreviewPanel state={state} />
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
