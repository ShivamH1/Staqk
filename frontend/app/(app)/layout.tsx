import type { ReactNode } from 'react'
import { NavRail } from '@/components/app/nav-rail'

/** Shell for the authenticated app: fixed nav rail + scrollable content. */
export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-canvas text-ink">
      <NavRail />
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}
