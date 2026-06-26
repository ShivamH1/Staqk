import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = { title: 'Not found' }

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-canvas px-4 text-center">
      <p className="text-7xl font-medium tracking-[-0.05em] text-ink md:text-8xl">404</p>
      <div>
        <h1 className="text-2xl font-medium tracking-[-0.02em] text-ink">Page not found</h1>
        <p className="mt-2 text-sm text-ink-muted">
          The page you’re looking for doesn’t exist or has moved.
        </p>
      </div>
      <Link
        href="/"
        className="rounded-pill bg-white px-5 py-2.5 text-sm font-medium text-black transition-transform hover:scale-[0.98]"
      >
        Back home
      </Link>
    </div>
  )
}
