'use client'

import { LoaderCircle, Plus } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useCreateProject } from '@/lib/hooks/use-projects'
import { cn } from '@/lib/utils'

const stacks = ['Next.js', 'React', 'Tailwind', 'Supabase']
const templates = [
  { name: 'SaaS Landing', desc: 'Modern, clean landing' },
  { name: 'CRM Dashboard', desc: 'Complex data tables' },
  { name: 'Personal Blog', desc: 'Markdown optimized' },
  { name: 'Fintech App', desc: 'Secure wallet UI' },
]

/** Derive a short project name from the first words of the prompt. */
function deriveName(prompt: string): string {
  const slug = prompt
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .split(/\s+/)
    .slice(0, 4)
    .join('-')
  return slug || 'untitled-app'
}

export default function NewProjectPage() {
  const router = useRouter()
  const createProject = useCreateProject()
  const [prompt, setPrompt] = useState('')
  const [selected, setSelected] = useState<string[]>(['Next.js'])

  const toggle = (stack: string) =>
    setSelected((current) =>
      current.includes(stack) ? current.filter((s) => s !== stack) : [...current, stack],
    )

  const handleGenerate = async () => {
    const trimmed = prompt.trim()
    if (!trimmed || createProject.isPending) return
    const project = await createProject.mutateAsync({
      name: deriveName(trimmed),
      description: trimmed,
      tech_stack: { stacks: selected },
    })
    // Hand the prompt to the workspace so it can kick off the pipeline.
    router.push(`/workspace/${project.id}?prompt=${encodeURIComponent(trimmed)}`)
  }

  return (
    <div className="mx-auto flex min-h-full max-w-4xl flex-col px-5 py-12 md:px-8 md:py-16">
      <h1 className="text-5xl font-medium leading-[0.95] tracking-[-0.05em] md:text-6xl">
        What do you want
        <br />
        to build?
      </h1>

      <div className="relative mt-10 rounded-2xl border border-hairline bg-surface-1">
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="A todo app with auth and a dashboard…"
          className="h-40 w-full resize-none bg-transparent p-5 text-base text-ink placeholder:text-ink-muted focus:outline-none"
        />
        <div className="flex items-center justify-end gap-4 border-t border-hairline px-5 py-3">
          <span className="text-sm text-ink-muted">This run costs 5 credits</span>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={!prompt.trim() || createProject.isPending}
            className="flex items-center gap-2 rounded-pill bg-white px-5 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {createProject.isPending && <LoaderCircle className="size-4 animate-spin" />}
            {createProject.isPending ? 'Creating…' : 'Generate'}
          </button>
        </div>
        {createProject.isError && (
          <p className="px-5 pb-3 text-sm text-red-400">
            Couldn’t create the project. Please try again.
          </p>
        )}
      </div>

      <div className="mt-8">
        <p className="text-sm text-ink-muted">Deployment stack</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {stacks.map((stack) => {
            const on = selected.includes(stack)
            return (
              <button
                key={stack}
                type="button"
                onClick={() => toggle(stack)}
                className={cn(
                  'flex items-center gap-2 rounded-pill px-4 py-1.5 text-sm transition-colors',
                  on
                    ? 'bg-surface-2 text-ink ring-1 ring-accent-blue'
                    : 'bg-surface-1 text-ink-muted hover:text-ink',
                )}
              >
                {on && <span className="size-1.5 rounded-full bg-accent-blue" />}
                {stack}
              </button>
            )
          })}
          <button
            type="button"
            aria-label="Add stack"
            className="flex size-8 items-center justify-center rounded-pill bg-surface-1 text-ink-muted transition-colors hover:text-ink"
          >
            <Plus className="size-4" />
          </button>
        </div>
      </div>

      <div className="mt-10">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium uppercase tracking-wider text-ink-muted">
            Start from a template
          </p>
          <button type="button" className="text-sm text-accent-blue hover:underline">
            View all
          </button>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {templates.map((template) => (
            <button key={template.name} type="button" className="text-left">
              <div className="aspect-[4/3] rounded-xl border border-hairline bg-gradient-to-br from-surface-2 to-canvas transition-colors hover:border-ink-muted/40" />
              <p className="mt-2 text-sm font-medium">{template.name}</p>
              <p className="text-xs text-ink-muted">{template.desc}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
