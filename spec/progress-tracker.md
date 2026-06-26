# Progress Tracker

**Last updated:** 2026-06-26
**Current phase:** Phase 1 MVP
**Current position:** Phase 1, Step 11 complete (pipeline now persists into `WebsiteProject` — building→ready/deployed/error + saved `file_tree`; new `WS /ai/iterate` at 2 credits; `PUT /projects/{id}`; offline-verified). Full AI-pipeline logic (Plan→Code→Test→Security) is real; Deploy remains a stub. Next: live-verify end-to-end (needs ≥2GB E2B template + Neon + Clerk), or wire the Deploy agent to Vercel. (Frontend landing parked at F3.)

Status key: ✅ Done | 🟡 Partial / stub | 🔲 Not started | 🔴 Blocked

> See [build-log.md](build-log.md) for the step-by-step history of what was built and why.

---

## Phase 1: MVP

### Foundation & Infrastructure

| Task | Status | Notes |
|------|--------|-------|
| Monorepo setup (frontend + backend folders) | ✅ | Simple folder monorepo |
| Next.js + Tailwind + shadcn/ui scaffolding | ✅ | **Next.js 16** (not 15), Tailwind v4, Biome |
| Python FastAPI + SQLAlchemy async setup | ✅ | FastAPI 0.138, SQLAlchemy 2 async |
| Neon database + Alembic migrations | 🟡 | Migration `0001` written + validated offline; no live Neon connection yet |
| Clerk auth (frontend + FastAPI JWT) | ✅ | JWT via `get_current_user` dependency (jose + JWKS), not a middleware class |
| Render deployment (backend) | 🔲 | |
| Vercel deployment (frontend) | 🔲 | |
| CI: GitHub Actions (lint + test on PR) | 🔲 | |

### Core AI Pipeline

| Task | Status | Notes |
|------|--------|-------|
| LangGraph state schema + graph setup | ✅ | `AgentState`, conditional edges (retry/security gating) |
| Model factory (provider + OpenRouter fallback) | ✅ | `agents/models.py` — Gemini/Mistral/Groq direct or OpenRouter |
| Plan Agent (Gemini Flash) | ✅ | Real LLM call + JSON parse; error path handled |
| Code Agent (Mistral Large) | ✅ | Real generation + sandbox build check; build-fail retries (max 2). Not live-verified (no E2B/Mistral key) |
| E2B sandbox integration (Python SDK) | ✅ | `app/sandbox/e2b.py` async wrapper; `sandbox_session()` kills in finally. Live test pending an E2B key |
| Test Agent (Groq Llama) | ✅ | Real Vitest gen + sandbox run; test-fail retries back to Code. Not live-verified (E2B RAM) |
| Security Agent (Semgrep + Mistral Small) | ✅ | Real Semgrep scan in E2B + Mistral-Small auto-fix; halt on critical. Not live-verified (E2B RAM) |
| Deploy Agent (Vercel API) | 🟡 | Stub node returns placeholder URL |
| WebSocket streaming (agent events → frontend) | ✅ | `WS /ai/stream/{id}`, token query-param auth, custom stream |
| Credit deduction + refund logic | ✅ | Atomic deduct (FOR UPDATE) + `spend`/`AIUsageLog`; refund on failure. `Transaction`/`AIUsageLog` models + migration 0002 (offline) |

### Workspace UI

| Task | Status | Notes |
|------|--------|-------|
| Monaco editor integration | ✅ | `CodeEditor` (read-only, vs-dark, JetBrains Mono) |
| File tree component | ✅ | `FileTree` driven by `file_created` events |
| Live preview panel (E2B iframe) | 🟡 | Placeholder + iframe-on-deploy; no E2B preview yet |
| Chat panel + iteration flow | 🟡 | `WS /ai/iterate` wired backend (2 credits, seeds existing file tree); `ChatPanel` frontend not yet pointed at it |
| Agent progress pipeline UI | ✅ | `AgentProgressBar` consumes WS events via `usePipeline` |
| Version history panel | 🔲 | |
| GSAP + Framer Motion + Lenis setup | 🟡 | Framer Motion (keyboard) + Lenis smooth scroll wired on landing; GSAP + GT Walsheim font not yet used |
| Design tokens foundation | ✅ | design.md tokens in globals.css (`bg-canvas`, `text-ink`, etc.); Inter + JetBrains Mono loaded |

### Dashboard & Billing

| Task | Status | Notes |
|------|--------|-------|
| Project list dashboard | 🔲 | |
| Create project flow (tech stack selection) | 🔲 | |
| Stripe Checkout integration | 🔲 | |
| Credit balance display | 🔲 | |
| Stripe webhook handler | 🔲 | |

### F-01 to F-12 Features (see spec.md)

| Feature | Status | Notes |
|---------|--------|-------|
| F-01 User authentication | ✅ | Backend + frontend wired; needs live Clerk+Neon to verify e2e |
| F-02 Natural language generation | 🟡 | Pipeline + WS + workspace UI in place; agents are stubs |
| F-03 Tech stack selection | 🔲 | |
| F-04 Multi-file code generation | 🟡 | Code Agent real (gen + build check); needs live keys + Test/Security/Deploy real |
| F-05 File tree + Monaco editor | 🔲 | |
| F-06 Live preview | 🔲 | |
| F-07 Chat iteration | 🟡 | `WS /ai/iterate` backend done; needs frontend wiring + live verify |
| F-08 Version history | 🔲 | |
| F-09 Stripe credits + billing | 🟡 | Credit ledger (deduct/refund/`AIUsageLog`) done; Stripe Checkout + webhook still to do |
| F-10 Vercel deployment | 🟡 | Deploy Agent stub only |
| F-11 Security scanning | 🟡 | Security Agent real (Semgrep + auto-fix); needs live E2B to verify e2e |
| F-12 Neon DB provisioning | 🔲 | |

---

## Phase 2: Core Platform

| Feature | Status |
|---------|--------|
| F-13 Multi-agent pipeline UI | 🔲 |
| F-14 GitHub sync | 🔲 |
| F-15 Custom domains | 🔲 |
| F-16 Template library | 🔲 |
| F-17 AI cost tracking | 🔲 |

---

## Phase 3–4

See [spec.md](spec.md) — not yet in active planning.

---

## Current Blockers

_None. Live Neon DB + real Clerk keys needed before end-to-end auth verification._

---

## Upcoming Priorities

1. Live-verify end-to-end once an `E2B_TEMPLATE` (≥2GB) + live Neon + a real Clerk token are available: create → `WS /ai/stream` → persisted `file_tree`/`status`, credits settled
2. Deploy agent → real Vercel API (replace the stub URL; add a `Deployment` row + table) so `status=deployed` is real
3. Stripe Checkout + webhook to buy credits (`Transaction(type=purchase)`); credit-balance display
4. Point the frontend `ChatPanel` at `WS /ai/iterate`; load a real project into the workspace via the projects API
5. Resume frontend landing (parked at F3): pipeline section, footer, anchor-aware Lenis

---

## Known Bugs

_None logged_

---

## Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Projects created | — | 100 (end of Phase 1) |
| Paid users | — | 10 (end of Phase 1) |
| MRR | — | $200 (end of Phase 1) |
| Avg credits/user/month | — | — |
| Deployed apps | — | 50 (end of Phase 1) |
| Gross margin | — | >70% |
