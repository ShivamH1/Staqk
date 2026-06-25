# Architecture Decision Records

Each ADR documents a settled technical choice. Re-read before reopening a discussion.

---

## ADR-001: Simple Folder Monorepo

**Status:** Accepted

**Decision:** Use a plain folder monorepo (`/frontend`, `/backend`, `/specs`) with no build orchestration tool.

**Considered:** Turborepo, Nx

**Rationale:** Turborepo is JavaScript-only and provides no value for a Python backend. Nx supports polyglot but adds significant config overhead for a team at this stage. A simple folder layout is immediately understandable, works with any IDE, and imposes no constraints on how each app is built or deployed. Orchestration can be added later if build caching becomes a pain point.

---

## ADR-002: Python 3.12 + FastAPI for Backend

**Status:** Accepted

**Decision:** Replace the previous Hono/Bun backend with Python 3.12 + FastAPI.

**Considered:** Hono on Bun, Node + Fastify, Express

**Rationale:** The AI pipeline (LangGraph, LangChain, Semgrep Python SDK, E2B Python SDK) is natively Python. Running it through a JS backend would require subprocess calls or a separate Python microservice — unnecessary complexity. FastAPI is async-first, has automatic OpenAPI docs, Pydantic v2 integration, and excellent performance. Python is the right language for this product's core value.

---

## ADR-003: SQLAlchemy (async) + Alembic

**Status:** Accepted

**Decision:** Use SQLAlchemy with async/asyncpg for database access and Alembic for migrations.

**Considered:** Prisma Python client, Tortoise ORM + Aerich

**Rationale:** SQLAlchemy is the battle-tested standard for Python database access. The async extension (`sqlalchemy[asyncio]` + `asyncpg`) handles Neon's serverless Postgres well. Alembic migrations are explicit, version-controlled, and familiar to any Python developer. Prisma's Python client is less mature and would add a Node.js dependency to the backend. Tortoise is solid but has a smaller ecosystem.

---

## ADR-004: LangGraph + LangChain for AI Orchestration

**Status:** Accepted

**Decision:** Use LangGraph for multi-agent state machine orchestration, with LangChain for tools, retrievers, and model wrappers.

**Considered:** Custom orchestration, CrewAI, AutoGen

**Rationale:** LangGraph is purpose-built for stateful, cyclic agent workflows — exactly what a Plan → Code → Test → Security → Deploy pipeline requires. It handles retries, conditional edges (e.g., "re-run Code if tests fail"), and streaming out of the box. LangChain provides a unified interface to all AI providers (MistralAI, Groq, Gemini, OpenRouter) without duplicating provider client code. CrewAI and AutoGen are higher-level abstractions that trade control for convenience — too opaque for a product where agent behavior is a core differentiator.

---

## ADR-005: Clerk for Authentication

**Status:** Accepted (carried over)

**Decision:** Keep Clerk as the authentication provider.

**Considered:** Better Auth, Auth.js, Lucia, custom JWT

**Rationale:** Clerk handles the full auth surface (sign-up, sign-in, MFA, social OAuth, org management, webhooks) with minimal code. The Clerk Python SDK validates JWTs in FastAPI middleware. Webhook events sync users to the Neon database. No reason to swap for the increased engineering overhead of a self-managed solution.

---

## ADR-006: E2B for Code Execution Sandboxing

**Status:** Accepted (carried over)

**Decision:** Keep E2B for sandboxed execution of user-generated code.

**Considered:** Modal, custom Docker + Fly.io, Firecracker

**Rationale:** E2B is purpose-built for AI-generated code execution. It provides fast sandbox spin-up (< 1s), file system access, process execution, and a Python SDK. It isolates user code from the host completely. Modal is powerful but optimized for ML workloads, not interactive previews. Custom Docker + Fly.io is a significant infrastructure investment that buys little over E2B at this stage.

---

## ADR-007: fission-ai/openspec for Spec-Driven Development

**Status:** Accepted

**Decision:** Adopt OpenSpec as the project's SDD methodology for all non-trivial features.

**Considered:** Ad-hoc prompting, Linear tickets, PRDs in Notion

**Rationale:** Without a spec layer, AI coding assistants drift — they implement what the most recent chat message said, not what was agreed. OpenSpec enforces a propose → implement → archive loop with lightweight Markdown artifacts (proposal, specs, design, tasks). It is language and framework agnostic, works with any AI assistant, and keeps specs co-located with the code in `/specs`. Linear/Notion are tracking tools, not specification contracts.

---

## ADR-008: GSAP + Framer Motion + Lenis (Scoped Roles)

**Status:** Accepted (amended 2026-06-25 — Lenis replaces Locomotive Scroll)

**Decision:** Use all three animation libraries, each with a distinct non-overlapping role.

**Considered:** GSAP only, Framer Motion only, CSS transitions only, Locomotive Scroll

**Rationale:** Each library excels in a different domain. GSAP handles complex timeline sequences, canvas/WebGL, and scroll-triggered animations that would be verbose in Framer. Framer Motion is idiomatic React — layout animations, enter/exit transitions, and drag are first-class. **Lenis** provides smooth native-feeling scroll that neither GSAP nor Framer handles cleanly out of the box. The key rule: **no library crosses into another's domain.** This prevents bloat and conflicts.

**Amendment (2026-06-25):** The original choice was Locomotive Scroll, but it has friction with React 19 / Next 16 (it predates the App Router and fights server-rendered layout). We switched to **Lenis** — by the same studio (Darkroom (Engineering)/studio-freight), actively maintained, framework-agnostic, and the library Locomotive itself now builds on. Role is unchanged: full-page smooth scroll on **marketing pages only**, mounted via a `'use client'` component that drives Lenis's RAF loop and honors `prefers-reduced-motion`.

| Library | Domain |
|---------|--------|
| GSAP | Complex timelines, SVG morphing, canvas, scroll-triggered |
| Framer Motion | React component transitions, layout animations, page transitions |
| Lenis | Full-page smooth scroll (marketing pages only) |

---

## ADR-009: Render for Python Backend Deployment

**Status:** Accepted

**Decision:** Deploy the FastAPI backend on Render.

**Considered:** Railway, Fly.io, AWS ECS, Vercel (serverless functions)

**Rationale:** Render has excellent Python support with zero-config Dockerfile or native Python detection. It handles long-running WebSocket connections (required for agent streaming) which Vercel serverless functions cannot. Railway is comparable but Render's free tier and pricing fit the current stage. Fly.io is ideal for container edge deployments but adds complexity (WireGuard, fly.toml, regions) not needed yet.

---

## ADR-010: Multi-Provider AI Routing via LangGraph

**Status:** Accepted

**Decision:** Route AI tasks across MistralAI, Groq, Gemini, and OpenRouter via LangGraph's model routing layer rather than a single provider or a managed gateway.

**Considered:** OpenRouter only, LiteLLM gateway, PortKey, single provider

**Rationale:** Different agents have different latency and capability requirements. Groq's Llama is fastest for test generation. Gemini Flash is cheap for planning. Mistral Large is strong for code. Using LangChain's provider wrappers, routing logic lives in Python code (`agents/router.py`) — version-controlled, testable, and without a third-party gateway dependency. OpenRouter is retained as a universal fallback when direct provider rate limits are hit.

---

## ADR-011: Dark Mode Only

**Status:** Accepted (carried over)

**Decision:** Staqk has no light mode. Dark mode is the only theme.

**Rationale:** Staqk targets technical users who live in dark IDEs and terminals. A single theme reduces the component surface area by half (no `dark:` variant sprawl), enables a more intentional visual language, and is a deliberate brand statement. If market research later shows strong demand for light mode, this decision can be revisited.

---

## ADR-012: Credit-Based Hybrid Pricing with Stripe

**Status:** Accepted (carried over)

**Decision:** Monetize via subscription plans (monthly credits included) with optional top-up credit packs, processed through Stripe.

**Considered:** Pure subscription, pure pay-per-use, Lemon Squeezy

**Rationale:** Pure subscriptions decouple revenue from usage — heavy users get a free ride, light users overpay. Pure pay-per-use creates anxiety around every action. A credit model ties cost to AI usage, is transparent to users, and allows the business to price each agent operation independently as costs change. Stripe is the industry standard with the best webhook reliability and fraud tooling. Lemon Squeezy is simpler for tax handling but lacks Stripe's depth for metered billing.

---

## Adding a New Decision

Copy this template:

```markdown
## ADR-XXX: Title

**Status:** Proposed | Accepted | Deprecated

**Decision:** One sentence.

**Considered:** Alternative A, Alternative B

**Rationale:** Why this choice over the alternatives.
```
