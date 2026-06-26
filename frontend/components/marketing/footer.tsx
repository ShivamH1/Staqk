import Link from 'next/link'

const columns = [
  {
    title: 'Product',
    links: [
      { label: 'How it works', href: '#product' },
      { label: 'Pipeline', href: '#pipeline' },
      { label: 'Pricing', href: '#pricing' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '#' },
      { label: 'Blog', href: '#' },
      { label: 'Careers', href: '#' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy', href: '#' },
      { label: 'Terms', href: '#' },
      { label: 'Security', href: '#' },
    ],
  },
]

export default function Footer() {
  return (
    <footer className="relative z-10 w-full border-t border-hairline bg-canvas">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-10 px-4 py-16 md:grid-cols-5 md:px-8">
        <div className="col-span-2">
          <Link href="/" className="text-lg font-medium tracking-[-0.03em] text-ink">
            Staqk
          </Link>
          <p className="mt-3 max-w-xs text-sm text-ink-muted">
            The security-first AI app builder. Build. Secure. Ship.
          </p>
        </div>

        {columns.map((column) => (
          <div key={column.title}>
            <p className="text-xs font-medium uppercase tracking-wider text-ink-muted">
              {column.title}
            </p>
            <ul className="mt-4 space-y-2.5">
              {column.links.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-ink-muted transition-colors hover:text-ink"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mx-auto flex max-w-6xl items-center justify-between border-t border-hairline-soft px-4 py-6 md:px-8">
        <p className="text-xs text-ink-muted">© 2026 Staqk. All rights reserved.</p>
        <p className="text-xs text-ink-muted">Build. Secure. Ship.</p>
      </div>
    </footer>
  )
}
