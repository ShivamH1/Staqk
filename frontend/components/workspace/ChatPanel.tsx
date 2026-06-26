'use client'

import { ArrowUp, Sparkles } from 'lucide-react'
import { type FormEvent, useEffect, useRef, useState } from 'react'
import { AGENTS, type PipelineState } from '@/lib/pipeline-reducer'

interface ChatPanelProps {
  state: PipelineState
  disabled: boolean
  cost: number
  onSend: (message: string) => void
}

const LABELS: Record<(typeof AGENTS)[number], string> = {
  plan: 'Plan',
  code: 'Code',
  test: 'Test',
  security: 'Security',
  deploy: 'Deploy',
}

/** Build-activity log derived from the live pipeline state. */
function buildLog(
  state: PipelineState,
): { id: string; text: string; tone: 'ink' | 'muted' | 'success' | 'error' }[] {
  const lines: { id: string; text: string; tone: 'ink' | 'muted' | 'success' | 'error' }[] = []
  for (const agent of AGENTS) {
    const stage = state.stages[agent]
    if (stage.status === 'pending') continue
    if (stage.status === 'error') {
      lines.push({
        id: agent,
        text: `${LABELS[agent]} — ${stage.error ?? 'failed'}`,
        tone: 'error',
      })
    } else {
      const suffix = stage.message ?? (stage.status === 'complete' ? 'done' : 'working…')
      lines.push({ id: agent, text: `${LABELS[agent]} — ${suffix}`, tone: 'muted' })
    }
  }
  if (state.files.length > 0) {
    lines.push({ id: 'files', text: `Created ${state.files.length} files`, tone: 'ink' })
  }
  if (state.status === 'complete') {
    lines.push({
      id: 'done',
      text: `Pipeline complete · ${state.creditsUsed ?? 0} credits`,
      tone: 'success',
    })
  }
  if (state.status === 'error') {
    lines.push({ id: 'failed', text: state.errorMessage ?? 'Pipeline failed', tone: 'error' })
  }
  return lines
}

const toneClass = {
  ink: 'text-ink',
  muted: 'text-ink-muted',
  success: 'text-success',
  error: 'text-red-400',
} as const

export function ChatPanel({ state, disabled, cost, onSend }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const logRef = useRef<HTMLDivElement>(null)
  const lines = buildLog(state)

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll on every new line
  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight })
  }, [lines.length, state.status])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setInput('')
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div ref={logRef} className="flex-1 overflow-y-auto px-4 py-3">
        {state.status === 'idle' ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
            <Sparkles className="size-6 text-ink-muted" />
            <p className="text-sm text-ink-muted">
              Describe a change and Staqk will rebuild your app.
            </p>
          </div>
        ) : (
          <ul className="space-y-1.5 text-sm">
            {lines.map((line) => (
              <li key={line.id} className={toneClass[line.tone]}>
                {line.text}
              </li>
            ))}
          </ul>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-hairline p-3">
        <div className="flex items-center gap-2 rounded-xl border border-hairline bg-surface-1 px-3 py-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={disabled}
            placeholder="Describe a change…"
            className="flex-1 bg-transparent text-sm text-ink placeholder:text-ink-muted focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={disabled || !input.trim()}
            className="flex size-7 items-center justify-center rounded-pill bg-white text-black transition-opacity disabled:opacity-30"
          >
            <ArrowUp className="size-4" />
          </button>
        </div>
        <p className="mt-2 px-1 text-xs text-ink-muted">
          {disabled ? 'Building…' : `This costs ${cost} credits`}
        </p>
      </form>
    </div>
  )
}
