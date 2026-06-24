'use client'

import { ArrowUp } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import type { PipelineState } from '@/lib/pipeline-reducer'

interface ChatPanelProps {
  state: PipelineState
  disabled: boolean
  onSend: (message: string) => void
}

export function ChatPanel({ state, disabled, onSend }: ChatPanelProps) {
  const [input, setInput] = useState('')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setInput('')
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-4 text-sm">
        {state.status === 'idle' ? (
          <p className="text-ink-muted">Describe the app you want to build.</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {Object.entries(state.stages).map(([agent, stage]) => (
              <li key={agent} className="text-ink-muted">
                <span className="text-ink capitalize">{agent}</span>
                {stage.message
                  ? ` — ${stage.message}`
                  : stage.status === 'complete'
                    ? ' — done'
                    : ''}
              </li>
            ))}
            {state.status === 'complete' && (
              <li className="mt-2 text-success">Pipeline complete · {state.creditsUsed} credits</li>
            )}
            {state.status === 'error' && (
              <li className="mt-2 text-red-500">{state.errorMessage ?? 'Pipeline failed'}</li>
            )}
          </ul>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-hairline p-3">
        <div className="flex items-center gap-2 rounded-md bg-surface-1 px-3 py-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={disabled}
            placeholder="Build a todo app with…"
            className="flex-1 bg-transparent text-sm text-ink placeholder:text-ink-muted focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={disabled || !input.trim()}
            className="flex size-7 items-center justify-center rounded-pill bg-ink text-canvas transition-opacity disabled:opacity-30"
          >
            <ArrowUp className="size-4" />
          </button>
        </div>
      </form>
    </div>
  )
}
