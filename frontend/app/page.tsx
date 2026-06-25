import Background3D from '@/components/marketing/background-3d'
import Navbar from '@/components/marketing/navbar'

export default function Home() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      {/* Rotating WebGL city backdrop */}
      <Background3D className="z-0" />
      {/* Legibility scrim — subtle, keeps the color cycling visible */}
      <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-black/30 via-transparent to-canvas/80" />

      <div className="relative z-10 flex min-h-screen flex-col">
        <Navbar />

        <main className="flex flex-1 flex-col items-center justify-center px-4 text-center md:px-8">
          <span className="mb-6 rounded-pill bg-surface-1/60 px-4 py-1.5 text-xs font-medium tracking-[-0.01em] text-ink-muted backdrop-blur-sm">
            Security-first multi-agent AI app builder
          </span>

          <h1 className="max-w-4xl text-5xl font-medium leading-[0.95] tracking-[-0.05em] text-ink md:text-7xl lg:text-8xl">
            Build. Secure. Ship.
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-snug tracking-[-0.01em] text-ink-muted">
            Staqk takes your idea from prompt to a tested, security-scanned, deployed app —
            finishing the last 40% that other builders leave behind.
          </p>

          <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
            <a
              href="/sign-up"
              className="rounded-pill bg-white px-6 py-3 text-sm font-medium text-black transition-transform hover:scale-[0.97]"
            >
              Start building
            </a>
            <a
              href="#product"
              className="rounded-pill bg-surface-1/70 px-6 py-3 text-sm font-medium text-ink backdrop-blur-sm transition-colors hover:bg-surface-2"
            >
              See how it works
            </a>
          </div>
        </main>
      </div>
    </div>
  )
}
