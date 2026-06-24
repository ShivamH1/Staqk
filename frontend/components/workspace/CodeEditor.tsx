'use client'

import Editor from '@monaco-editor/react'

interface CodeEditorProps {
  path: string | null
  value: string
}

function languageFromPath(path: string): string {
  if (path.endsWith('.ts') || path.endsWith('.tsx')) return 'typescript'
  if (path.endsWith('.js') || path.endsWith('.jsx')) return 'javascript'
  if (path.endsWith('.json')) return 'json'
  if (path.endsWith('.css')) return 'css'
  if (path.endsWith('.md')) return 'markdown'
  if (path.endsWith('.py')) return 'python'
  if (path.endsWith('.html')) return 'html'
  return 'plaintext'
}

export function CodeEditor({ path, value }: CodeEditorProps) {
  if (!path) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-ink-muted">
        Select a file to view it
      </div>
    )
  }

  return (
    <Editor
      height="100%"
      theme="vs-dark"
      path={path}
      language={languageFromPath(path)}
      value={value}
      options={{
        readOnly: true,
        minimap: { enabled: false },
        fontSize: 13,
        fontFamily: 'var(--font-jetbrains-mono), monospace',
        scrollBeyondLastLine: false,
        padding: { top: 12 },
      }}
    />
  )
}
