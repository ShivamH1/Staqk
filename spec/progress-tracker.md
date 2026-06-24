# Progress Tracker

**Last updated:** 2026-06-24
**Current phase:** Phase 1 MVP
**Current position:** Phase 1, Step 4 complete (Workspace UI). Next: wire a real agent (Plan/Code) or credit logic.

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
| Plan Agent (Gemini Flash) | 🟡 | Stub node emits events; no LLM call yet |
| Code Agent (Mistral Large) | 🟡 | Stub node; no generation/E2B yet |
| E2B sandbox integration (Python SDK) | 🔲 | |
| Test Agent (Groq Llama) | 🟡 | Stub node |
| Security Agent (Semgrep + Mistral Small) | 🟡 | Stub node |
| Deploy Agent (Vercel API) | 🟡 | Stub node returns placeholder URL |
| WebSocket streaming (agent events → frontend) | ✅ | `WS /ai/stream/{id}`, token query-param auth, custom stream |
| Credit deduction + refund logic | 🔲 | TODO marker in `routers/ai.py` |

### Workspace UI

| Task | Status | Notes |
|------|--------|-------|
| Monaco editor integration | ✅ | `CodeEditor` (read-only, vs-dark, JetBrains Mono) |
| File tree component | ✅ | `FileTree` driven by `file_created` events |
| Live preview panel (E2B iframe) | 🟡 | Placeholder + iframe-on-deploy; no E2B preview yet |
| Chat panel + iteration flow | 🟡 | `ChatPanel` sends initial message; `/ai/iterate` not wired |
| Agent progress pipeline UI | ✅ | `AgentProgressBar` consumes WS events via `usePipeline` |
| Version history panel | 🔲 | |
| GSAP + Framer Motion + Locomotive setup | 🟡 | GSAP + Framer installed; Locomotive + GT Walsheim font not wired |
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
| F-04 Multi-file code generation | 🟡 | Code Agent stub only |
| F-05 File tree + Monaco editor | 🔲 | |
| F-06 Live preview | 🔲 | |
| F-07 Chat iteration | 🔲 | |
| F-08 Version history | 🔲 | |
| F-09 Stripe credits + billing | 🔲 | |
| F-10 Vercel deployment | 🟡 | Deploy Agent stub only |
| F-11 Security scanning | 🟡 | Security Agent stub only |
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

1. Wire a real agent (Plan or Code) with live LLM + E2B — replaces stubs with actual output
2. Credit deduction/refund logic in the pipeline (TODO in `routers/ai.py`)
3. Projects router + DB (`POST /projects`, project list) so the workspace loads a real project
4. Chat iteration endpoint (`/ai/iterate`) wired to the chat panel

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
