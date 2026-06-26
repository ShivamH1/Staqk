'use client'

import { CreditCard, FolderClosed, Plus, Settings } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const items = [
  { href: '/dashboard', label: 'Projects', icon: FolderClosed },
  { href: '/new', label: 'New project', icon: Plus },
  { href: '/billing', label: 'Billing', icon: CreditCard },
  { href: '/settings', label: 'Settings', icon: Settings },
]

/** Slim left navigation rail for the authenticated app (design.md dark canvas). */
export function NavRail() {
  const pathname = usePathname()

  return (
    <nav className="flex w-16 shrink-0 flex-col items-center border-r border-hairline bg-[#0c0c0c] py-4">
      <Link
        href="/dashboard"
        aria-label="Staqk home"
        className="mb-6 flex size-9 items-center justify-center rounded-lg bg-white text-sm font-semibold text-black"
      >
        S
      </Link>

      <ul className="flex flex-1 flex-col items-center gap-1">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== '/dashboard' && pathname.startsWith(href))
          return (
            <li key={href}>
              <Link
                href={href}
                title={label}
                aria-label={label}
                className={cn(
                  'flex size-10 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-1 hover:text-ink',
                  active && 'bg-surface-1 text-ink',
                )}
              >
                <Icon className="size-5" />
              </Link>
            </li>
          )
        })}
      </ul>

      <div className="mt-auto size-9 rounded-full bg-surface-2 ring-1 ring-hairline" />
    </nav>
  )
}
