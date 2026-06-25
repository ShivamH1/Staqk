# Environment Variables & Secrets

## Setup Checklist (New Developer)

- [ ] Copy `frontend/.env.example` → `frontend/.env.local`
- [ ] Copy `backend/.env.example` → `backend/.env`
- [ ] Set Clerk publishable + secret keys
- [ ] Set Neon database URLs (pooled + direct)
- [ ] Set AI provider keys (at least OpenRouter for local dev)
- [ ] Set E2B API key
- [ ] Set Stripe keys (test mode for local)
- [ ] Run `alembic upgrade head` to initialise the database

---

## Frontend (`frontend/.env.local`)

These are **public** — they are bundled into the client. Never put secrets here.

```bash
# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000     # local
# NEXT_PUBLIC_API_URL=https://api.staqk.com  # production

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Analytics
NEXT_PUBLIC_POSTHOG_KEY=phc_...
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
```

---

## Backend (`backend/.env`)

These are **secrets** — never expose to the client, never commit to git.

```bash
# ── Clerk ──────────────────────────────────────────────────────
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...

# ── Neon PostgreSQL ────────────────────────────────────────────
# Pooled connection — use for all runtime queries
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.us-east-2.aws.neon.tech/staqk?sslmode=require

# Direct connection — use ONLY for Alembic migrations
DATABASE_URL_DIRECT=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/staqk?sslmode=require

# ── Stripe ─────────────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Price IDs (create in Stripe dashboard)
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_TEAM=price_...
STRIPE_PRICE_CREDITS_100=price_...
STRIPE_PRICE_CREDITS_500=price_...
STRIPE_PRICE_CREDITS_2000=price_...

# ── AI Providers ───────────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-...
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
MISTRAL_API_KEY=...

# ── E2B ────────────────────────────────────────────────────────
E2B_API_KEY=e2b_...
# Optional: custom sandbox template id with more RAM/CPU than the ~512MB base.
# Required to build real Next.js apps (the base template OOMs on npm install/build).
E2B_TEMPLATE=

# ── Vercel ─────────────────────────────────────────────────────
VERCEL_ACCESS_TOKEN=...
VERCEL_TEAM_ID=team_...    # optional, only if deploying to a team

# ── Sentry ─────────────────────────────────────────────────────
SENTRY_DSN=https://...@sentry.io/...
SENTRY_AUTH_TOKEN=...      # for source map uploads in CI

# ── Resend (email) ─────────────────────────────────────────────
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=noreply@staqk.com

# ── Feature Flags ──────────────────────────────────────────────
ENABLE_RAG=false           # set to true to enable Phase 2 RAG context
```

---

## Example Files

### `frontend/.env.example`

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
NEXT_PUBLIC_POSTHOG_KEY=
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
```

### `backend/.env.example`

```bash
CLERK_SECRET_KEY=
CLERK_WEBHOOK_SECRET=
DATABASE_URL=
DATABASE_URL_DIRECT=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_STARTER=
STRIPE_PRICE_PRO=
STRIPE_PRICE_TEAM=
STRIPE_PRICE_CREDITS_100=
STRIPE_PRICE_CREDITS_500=
STRIPE_PRICE_CREDITS_2000=
OPENROUTER_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
MISTRAL_API_KEY=
E2B_API_KEY=
VERCEL_ACCESS_TOKEN=
VERCEL_TEAM_ID=
SENTRY_DSN=
SENTRY_AUTH_TOKEN=
RESEND_API_KEY=
RESEND_FROM_EMAIL=
ENABLE_RAG=false
```

---

## Notes for Local Development

**AI providers:** You only need one provider key for local dev. Set `OPENROUTER_API_KEY` — it routes to all models and the agent router will use it as the fallback.

**Neon dual URLs:** Neon requires a pooled connection URL for runtime (PgBouncer) and a direct URL for Alembic migrations. They look similar but use different ports/endpoints. Don't mix them up.

**Stripe webhooks:** Use the Stripe CLI to forward webhooks locally:
```bash
stripe listen --forward-to localhost:8000/payments/webhook
# Copy the webhook signing secret it prints → STRIPE_WEBHOOK_SECRET
```

**Clerk webhooks:** Use ngrok or similar to expose your local backend, then configure the URL in the Clerk dashboard under Webhooks.

---

## Security Rules

1. `.env` and `.env.local` are in `.gitignore` — **never commit them**
2. Use test/sandbox keys locally — never use live keys on dev machines
3. Rotate all keys if a key is ever accidentally exposed (push to git, shared in chat, etc.)
4. Production secrets live in Render environment variables (backend) and Vercel environment variables (frontend) — not in files
5. The `DATABASE_URL_DIRECT` connection bypasses the connection pool — only use it in migration scripts, never in the running application
