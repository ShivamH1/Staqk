import { Plus, Rocket } from 'lucide-react'
import Link from 'next/link'

/** Dashboard zero-state — shown when the user has no projects yet. */
export function EmptyState() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="flex size-28 items-center justify-center rounded-3xl bg-gradient-to-br from-gradient-violet to-gradient-magenta">
        <Rocket className="size-12 text-white" />
      </div>
      <h1 className="mt-8 text-5xl font-medium tracking-[-0.04em]">No projects yet</h1>
      <p className="mt-3 max-w-sm text-sm text-ink-muted">
        Describe your idea and watch Staqk build the full stack in seconds.
      </p>
      <Link
        href="/new"
        className="mt-8 flex items-center gap-2 rounded-pill bg-white px-5 py-2.5 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
      >
        <Plus className="size-4" /> Create your first app
      </Link>
    </div>
  )
}
