'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { Check, Copy, Download, ExternalLink, X } from 'lucide-react'
import { useState } from 'react'
import { downloadZip } from '@/lib/zip'

interface DeployGuideProps {
  open: boolean
  onClose: () => void
  name: string
  fileTree: Record<string, string>
}

function slugify(name: string): string {
  return (
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'staqk-app'
  )
}

const GIT_SNIPPET = `git init
git add .
git commit -m "Initial commit"
gh repo create my-app --public --source=. --push`

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <li className="flex gap-3">
      <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-2 text-xs font-semibold text-ink">
        {n}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-ink">{title}</p>
        <div className="mt-1.5 text-sm text-ink-muted">{children}</div>
      </div>
    </li>
  )
}

export function DeployGuide({ open, onClose, name, fileTree }: DeployGuideProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(GIT_SNIPPET)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            type="button"
            aria-label="Close deploy guide"
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.18 }}
            className="relative z-10 w-full max-w-lg rounded-2xl border border-hairline bg-surface-1 p-7"
          >
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="absolute right-4 top-4 flex size-8 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-2 hover:text-ink"
            >
              <X className="size-4" />
            </button>

            <h2 className="text-xl font-medium tracking-[-0.02em]">Deploy {name}</h2>
            <p className="mt-1.5 text-sm text-ink-muted">
              Staqk builds, tests and secures your code — you own the deploy. Ship it to Vercel in
              three steps.
            </p>

            <ol className="mt-6 space-y-5">
              <Step n={1} title="Download your project">
                <p>Grab a zip of every generated file.</p>
                <button
                  type="button"
                  onClick={() => downloadZip(`${slugify(name)}.zip`, fileTree)}
                  className="mt-2 flex items-center gap-2 rounded-pill bg-white px-4 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
                >
                  <Download className="size-4" /> Download project (.zip)
                </button>
              </Step>

              <Step n={2} title="Push to GitHub">
                <p>Unzip it, then from the project folder:</p>
                <div className="relative mt-2">
                  <pre className="overflow-x-auto rounded-lg border border-hairline bg-canvas p-3 pr-10 font-mono text-xs leading-relaxed text-ink">
                    {GIT_SNIPPET}
                  </pre>
                  <button
                    type="button"
                    onClick={handleCopy}
                    aria-label="Copy commands"
                    className="absolute right-2 top-2 flex size-7 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-2 hover:text-ink"
                  >
                    {copied ? (
                      <Check className="size-4 text-success" />
                    ) : (
                      <Copy className="size-4" />
                    )}
                  </button>
                </div>
              </Step>

              <Step n={3} title="Deploy on Vercel">
                <p>
                  Import the repo at Vercel, add any environment variables your app needs, and hit
                  Deploy. You get a live URL in under a minute.
                </p>
              </Step>
            </ol>

            <a
              href="https://vercel.com/new"
              target="_blank"
              rel="noreferrer"
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-pill bg-surface-2 px-5 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-hairline"
            >
              Open Vercel <ExternalLink className="size-4" />
            </a>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
