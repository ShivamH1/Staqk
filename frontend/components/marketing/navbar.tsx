import Link from 'next/link'

const links = [
  { label: 'Product', href: '#product' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'Docs', href: '#docs' },
]

/** Marketing top-nav: wordmark left, links center, pill CTAs right (design.md top-nav, 56px). */
export default function Navbar() {
  return (
    <header className="relative z-20 h-14 w-full">
      <nav className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 md:px-8">
        <Link href="/" className="text-lg font-medium tracking-[-0.03em] text-ink">
          Staqk
        </Link>

        <ul className="hidden items-center gap-8 md:flex">
          {links.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                className="text-sm text-ink-muted transition-colors hover:text-ink"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2">
          <Link
            href="/sign-in"
            className="rounded-pill bg-surface-1 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-surface-2"
          >
            Sign in
          </Link>
          <Link
            href="/sign-up"
            className="rounded-pill bg-white px-4 py-2 text-sm font-medium text-black transition-transform hover:scale-[0.97]"
          >
            Get started
          </Link>
        </div>
      </nav>
    </header>
  )
}
