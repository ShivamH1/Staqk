'use client'

import { FileCode } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FileTreeProps {
  files: string[]
  selected: string | null
  onSelect: (path: string) => void
}

export function FileTree({ files, selected, onSelect }: FileTreeProps) {
  const sorted = [...files].sort()

  return (
    <div className="flex h-full flex-col">
      <div className="px-3 py-2.5 text-[11px] font-medium uppercase tracking-wider text-ink-muted">
        Files{files.length > 0 ? ` (${files.length})` : ''}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        {sorted.length === 0 ? (
          <p className="px-2 py-1 text-sm text-ink-muted">No files yet</p>
        ) : (
          sorted.map((path) => {
            const slash = path.lastIndexOf('/')
            const dir = slash >= 0 ? path.slice(0, slash + 1) : ''
            const name = slash >= 0 ? path.slice(slash + 1) : path
            const active = selected === path
            return (
              <button
                type="button"
                key={path}
                onClick={() => onSelect(path)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors',
                  active ? 'bg-surface-2' : 'hover:bg-surface-1',
                )}
              >
                <FileCode className="size-3.5 shrink-0 text-ink-muted" />
                <span className="truncate font-mono text-xs">
                  {dir && <span className="text-ink-muted/60">{dir}</span>}
                  <span className={active ? 'text-ink' : 'text-ink-muted'}>{name}</span>
                </span>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
