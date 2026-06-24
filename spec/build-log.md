# Build Log

A running, append-only record of what was built each step, why, and any deviations from the specs. This is the project's working memory — read it to get back up to speed quickly. Newest step at the bottom.

**Build cadence:** phase by phase, step by step. Each step is completed, verified (quality gate), reported, and only continued on the user's explicit "go".

**Quality gate per step:**
- Backend: `ruff check` + `mypy --strict` + `pytest` all pass
- Frontend: `biome check` + `tsc --noEmit` (+ `build` / `vitest` when relevant) all pass

---

## Standing deviations from spec docs

These are intentional and apply everywhere — the spec prose hasn't been back-updated:

- **Next.js 16** (latest stable), not 15 as specs say. `middleware.ts` → `proxy.ts` (Next 16 convention).
- **bun** is the package manager / runner, not pnpm.
- **Clerk JWT** is verified via a FastAPI `get_current_user` dependency using `python-jose` + Clerk's JWKS endpoint — not a `ClerkJWTMiddleware` class or the Clerk SDK verify, despite architecture.md.
- **design.md** is the Framer-style dark system (white-on-`#090909`, GT Walsheim display, blue `#0099ff` accent for links/focus only, gradient spotlight cards) — the authoritative design source.
- Status truth lives in [progress-tracker.md](progress-tracker.md), not spec.md's status column.

---

## Phase 1 — MVP

### Step 1 — Scaffold both apps ✅ (2026-06-24)

**Frontend** (`/frontend`): Next.js 16 + React 19 + TS strict + Tailwind v4 + shadcn/ui. Biome (lint/format), Vitest + Playwright. Installed TanStack Query, Clerk, Zod, Framer Motion, GSAP. Added `lib/api.ts` (Clerk-authed fetch wrapper) and `lib/ws.ts` (WS client + `AgentEvent` types). Folder structure for components/workspace, components/dashboard, lib/hooks, tests.

**Backend** (`/backend`): Python 3.12 + FastAPI + SQLAlchemy 2 async + asyncpg + Alembic. LangGraph + LangChain + provider SDKs (Mistral/Groq/Gemini/OpenRouter). E2B, Stripe, Clerk SDK, Sentry, Resend. Ruff + mypy strict + pytest-asyncio. `app/main.py`, `app/config.py` (Pydantic Settings), `app/database.py`, Alembic scaffold.

**Verified:** `GET /health` → ok. App imports cleanly with env set.

### Step 2 — Auth + Database ✅ (2026-06-24)

- `models/user.py`: `User` (StrEnum `Plan`, 100 default credits). Alembic `0001` creates users table + indexes + plan enum (validated via offline SQL gen).
- `schemas/user.py`: `UserResponse`. `services/users.py`: `get_by_clerk_id`, `create_user`.
- `middleware/auth.py`: Clerk JWT verification via JWKS (cached, auto-refresh on unknown kid), `get_current_user` dependency, `verify_token_get_user` helper (for WS).
- `routers/auth.py`: `POST /auth/webhook` (svix signature verify, syncs new users) + `GET /auth/me`.
- Frontend: `ClerkProvider` in root layout, `proxy.ts` (Clerk middleware), sign-in / sign-up catch-all pages.

**Verified:** mypy clean; tests for health + protected-route 401.

### Step 3 — LangGraph pipeline skeleton ✅ (2026-06-24)

- `agents/state.py`: `AgentState` TypedDict (matches ai-pipeline.md) + `MAX_CODE_RETRIES`.
- `agents/events.py`: typed event emitters via LangGraph `get_stream_writer()`.
- `agents/router.py`: model routing table (Plan→Gemini Flash, Code→Mistral Large, Test→Groq Llama, Security→Mistral Small) + OpenRouter fallback slugs.
- `agents/{plan,code,test,security,deploy}_agent.py`: five **stub** nodes emitting lifecycle events (no real LLM/E2B/Semgrep/Vercel yet).
- `agents/graph.py`: `StateGraph` with conditional edges — test pass→security, test fail+retries→code, fail+exhausted→end; security cleared→deploy else end.
- `routers/ai.py`: `WS /ai/stream/{project_id}`, token query-param auth, runs `pipeline.astream(stream_mode="custom")`, forwards each event, sends `pipeline_complete`. Credit deduction left as TODO for a later step.

**Verified (full gate):** backend ruff + mypy (25 files) + 6 pytest (incl. live WS pipeline stream); frontend biome + tsc + `next build` (4 routes) + 3 vitest.

### Step 4 — Workspace UI ✅ (2026-06-24)

Built the workspace that consumes the Step 3 WebSocket stream end-to-end.

- **Design foundation**: design.md tokens added to `globals.css` via `@theme` (`bg-canvas` `#090909`, `text-ink`, `text-ink-muted`, `bg-surface-1/2`, `border-hairline`, `text-accent-blue`, gradient + success colors, `rounded-pill`). Loaded Inter (body) + JetBrains Mono; mapped `font-sans`/`font-mono` tokens. GT Walsheim is a paid font — using Inter as the substitute per design.md's substitution note (swap later).
- **`app/providers.tsx`**: TanStack Query `QueryClientProvider`, wired into root layout.
- **`lib/pipeline-reducer.ts`**: pure reducer mapping `AgentEvent` → `PipelineState` (stage statuses, files, test results, security findings, completion/error). Testable in isolation.
- **`lib/hooks/use-pipeline.ts`**: opens `WS /ai/stream/{id}` with Clerk token query-param, sends the initial message, dispatches events into the reducer.
- **Components** (`components/workspace/`): `AgentProgressBar` (5-stage live status), `FileTree` (driven by `file_created`), `CodeEditor` (Monaco, read-only vs-dark), `PreviewPanel` (placeholder → iframe on deploy), `ChatPanel` (prompt input + live agent log).
- **`app/workspace/[id]/page.tsx`**: header (progress bar) + file tree / editor / preview body + chat, matching architecture.md's workspace layout.

**Deviations / notes:** Editor is read-only and file content is empty for now (stub agents emit `file_created` paths but no content — real content arrives when the Code Agent is wired). Chat sends only the initial generate message; `/ai/iterate` not yet connected. No real project loading yet (uses the route `id` directly to drive the pipeline).

**Verified (full gate):** biome (exit 0) + tsc (exit 0) + 9 vitest (2 files, incl. pipeline-reducer) + `next build` (5 routes incl. `/workspace/[id]`).

### Step 5 — (next) Real agent or credit logic 🔲

Candidates: wire the Plan or Code agent to a live LLM (+ E2B for Code), add credit deduction/refund, or build the projects router so the workspace loads a real project. See progress-tracker.md → Upcoming Priorities.
