'use client'

import { File } from 'lucide-react'

interface FileTreeProps {
  files: string[]
  selected: string | null
  onSelect: (path: string) => void
}

export function FileTree({ files, selected, onSelect }: FileTreeProps) {
  return (
    <div className="flex flex-col gap-0.5 p-2">
      <div className="px-2 py-1 text-xs uppercase tracking-wide text-ink-muted">Files</div>
      {files.length === 0 ? (
        <div className="px-2 py-1 text-sm text-ink-muted">No files yet</div>
      ) : (
        files.map((path) => (
          <button
            type="button"
            key={path}
            onClick={() => onSelect(path)}
            className={`flex items-center gap-2 rounded-md px-2 py-1 text-left text-sm transition-colors ${
              selected === path ? 'bg-surface-2 text-ink' : 'text-ink-muted hover:bg-surface-1'
            }`}
          >
            <File className="size-3.5 shrink-0" />
            <span className="truncate font-mono">{path}</span>
          </button>
        ))
      )}
    </div>
  )
}
