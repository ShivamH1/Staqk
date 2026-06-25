# Staqk

**Build. Secure. Ship.**

Staqk is a security-first, multi-agent AI app builder that solves the "Final 40% Problem" — the gap between a generated prototype and a production-ready application. Unlike Lovable or Bolt.new, Staqk runs a full pipeline: Plan → Code → Test → Security → Deploy, every time.

---

## Monorepo Structure

```
staqk/
├── frontend/          # Next.js 15 app (Vercel)
│   ├── app/           # App Router pages and layouts
│   ├── components/    # React components (shadcn/ui + custom)
│   ├── lib/           # Utilities, API client, hooks
│   └── public/        # Static assets
│
├── backend/           # Python 3.12 + FastAPI (Render)
│   ├── app/
│   │   ├── routers/   # FastAPI route handlers
│   │   ├── agents/    # LangGraph nodes (plan, code, test, security, deploy)
│   │   ├── services/  # Business logic (credits, projects, users)
│   │   ├── models/    # SQLAlchemy ORM models
│   │   └── schemas/   # Pydantic v2 request/response schemas
│   ├── alembic/       # Database migrations
│   └── tests/         # pytest test suite
│
└── specs/             # OpenSpec SDD artifacts
    └── <feature>/
        ├── proposal.md
        ├── specs/
        ├── design.md
        └── tasks.md
```

---

## Quick Start

**Frontend**
```bash
cd frontend
bun install
bun dev           # http://localhost:3000
```

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000
```

**Run tests**
```bash
cd frontend && bun test           # Vitest
cd backend && pytest              # pytest
cd frontend && bun run test:e2e   # Playwright
```

---

## OpenSpec Workflow (SDD)

Every non-trivial feature starts with a spec, not with code.

```
/opsx:propose <feature-name>   → creates specs/<feature-name>/
/opsx:implement <feature-name> → AI implements from agreed spec
/opsx:archive <feature-name>   → marks spec complete
```

See [openspec-guide.md](openspec-guide.md) for the full workflow.

---

## Documentation Index

| File | What it covers |
|------|---------------|
| [architecture.md](architecture.md) | System diagram, DB schema, API routes, LangGraph agent graph |
| [decisions.md](decisions.md) | Architecture Decision Records (ADRs) — why we chose each technology |
| [project-overview.md](project-overview.md) | Product positioning, ICP, monetization, roadmap phases |
| [design.md](design.md) | Design system: tokens, components, animation roles, layout |
| [ai-pipeline.md](ai-pipeline.md) | LangGraph agent pipeline spec (Plan → Code → Test → Security → Deploy) |
| [code-standards.md](code-standards.md) | TypeScript and Python coding conventions |
| [openspec-guide.md](openspec-guide.md) | Spec-Driven Development methodology and templates |
| [spec.md](spec.md) | Feature specifications with user stories and acceptance criteria |
| [env-and-secrets.md](env-and-secrets.md) | Environment variables reference and setup checklist |
| [progress-tracker.md](progress-tracker.md) | Phase/task status dashboard |
| [prompting-guide.md](prompting-guide.md) | Prompt templates for AI-assisted development |

---

## Tech Stack at a Glance

| Layer | Stack |
|-------|-------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Animations | GSAP (timelines), Framer Motion (transitions), Lenis (smooth scroll) |
| Backend | Python 3.12, FastAPI, SQLAlchemy async, Alembic |
| AI | LangGraph + LangChain, MistralAI, Groq, Gemini, OpenRouter |
| Database | Neon (PostgreSQL, serverless) |
| Auth | Clerk |
| Payments | Stripe (credit-based) |
| Sandbox | E2B |
| Deploy | Vercel (frontend), Render (backend) |
| Dev method | Spec-Driven Development via fission-ai/openspec |
