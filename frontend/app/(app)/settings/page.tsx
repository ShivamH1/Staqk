'use client'

import { useUser } from '@clerk/nextjs'
import { useState } from 'react'
import { Card } from '@/components/app/primitives'
import { useCurrentUser } from '@/lib/hooks/use-user'
import { cn } from '@/lib/utils'

function Toggle({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className={cn(
        'relative h-6 w-11 shrink-0 rounded-pill transition-colors',
        checked ? 'bg-white' : 'bg-surface-2',
      )}
    >
      <span
        className={cn(
          'absolute top-0.5 size-5 rounded-full transition-transform',
          checked ? 'translate-x-[22px] bg-black' : 'translate-x-0.5 bg-ink-muted',
        )}
      />
    </button>
  )
}

const fieldLabel = 'text-xs font-medium uppercase tracking-wider text-ink-muted'
const fieldInput =
  'mt-1.5 w-full rounded-md border border-hairline bg-canvas px-3.5 py-2.5 text-sm text-ink focus:border-accent-blue focus:outline-none'

const planNames: Record<string, string> = {
  free: 'Free plan',
  starter: 'Starter plan',
  pro: 'Pro plan',
  team: 'Team plan',
  enterprise: 'Enterprise',
}

export default function SettingsPage() {
  const { user } = useUser()
  const { data: account } = useCurrentUser()
  const [telemetry, setTelemetry] = useState(true)
  const [beta, setBeta] = useState(false)

  const planName = planNames[account?.plan ?? ''] ?? 'Free plan'

  return (
    <div className="mx-auto max-w-3xl px-5 py-10 md:px-8 md:py-12">
      <h1 className="text-4xl font-medium tracking-[-0.04em] md:text-5xl">Settings</h1>
      <p className="mt-2 text-sm text-ink-muted">
        Manage your account preferences and developer environment.
      </p>

      {/* Profile */}
      <Card className="mt-10 p-7">
        <h2 className="text-lg font-medium tracking-[-0.01em]">Profile</h2>
        <div className="mt-5 flex gap-5">
          {user?.imageUrl ? (
            // biome-ignore lint/performance/noImgElement: Clerk-hosted avatar, not a local asset
            <img
              src={user.imageUrl}
              alt=""
              className="size-20 shrink-0 rounded-full object-cover ring-1 ring-hairline"
            />
          ) : (
            <div className="size-20 shrink-0 rounded-full bg-surface-2 ring-1 ring-hairline" />
          )}
          <div className="flex-1 space-y-4">
            <div>
              <label className={fieldLabel} htmlFor="name">
                Full name
              </label>
              <input
                id="name"
                key={user?.fullName ?? 'name'}
                defaultValue={user?.fullName ?? ''}
                className={fieldInput}
              />
            </div>
            <div>
              <label className={fieldLabel} htmlFor="email">
                Email address
              </label>
              <input
                id="email"
                key={user?.primaryEmailAddress?.emailAddress ?? 'email'}
                defaultValue={user?.primaryEmailAddress?.emailAddress ?? ''}
                readOnly
                className={fieldInput}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Plan */}
      <Card className="mt-6 flex items-center justify-between p-7">
        <div>
          <h2 className="text-lg font-medium tracking-[-0.01em]">Plan</h2>
          <p className="mt-1 text-sm text-ink-muted">You are currently on the professional tier.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-pill bg-surface-2 px-3 py-1 text-xs font-semibold uppercase tracking-wider">
            {planName}
          </span>
          <button
            type="button"
            className="rounded-pill bg-surface-2 px-4 py-2 text-sm font-medium transition-colors hover:bg-hairline"
          >
            Manage
          </button>
        </div>
      </Card>

      {/* Preferences */}
      <Card className="mt-6 p-7">
        <h2 className="text-lg font-medium tracking-[-0.01em]">API / Preferences</h2>
        <div className="mt-5 flex items-center justify-between border-b border-hairline-soft pb-4">
          <div>
            <p className="text-sm font-medium">Telemetry</p>
            <p className="text-sm text-ink-muted">
              Anonymous usage data helps us improve the IDE experience.
            </p>
          </div>
          <Toggle checked={telemetry} onChange={() => setTelemetry((value) => !value)} />
        </div>
        <div className="mt-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Beta features</p>
            <p className="text-sm text-ink-muted">
              Get early access to experimental building tools and AI models.
            </p>
          </div>
          <Toggle checked={beta} onChange={() => setBeta((value) => !value)} />
        </div>
      </Card>

      {/* Danger zone */}
      <Card className="mt-6 border-red-500/30 p-7">
        <h2 className="text-lg font-medium tracking-[-0.01em] text-red-400">Danger zone</h2>
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-ink-muted">
            Permanently delete your account and all associated projects.
          </p>
          <button
            type="button"
            className="rounded-pill border border-red-500/40 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10"
          >
            Delete account
          </button>
        </div>
      </Card>
    </div>
  )
}
