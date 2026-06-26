import Link from 'next/link'
import type { ReactNode } from 'react'

/** Centered, branded shell for the Clerk auth screens on the dark canvas. */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-canvas px-4">
      <Link href="/" className="text-2xl font-medium tracking-[-0.03em] text-ink">
        Staqk
      </Link>
      {children}
    </div>
  )
}
