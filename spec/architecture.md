# Architecture

## System Overview

```
Browser
  │
  ▼
Vercel (Next.js 15)
  │  REST + WebSocket
  ▼
Render (FastAPI / Python 3.12)
  ├── Neon PostgreSQL (SQLAlchemy async + asyncpg)
  ├── E2B Sandboxes (code execution)
  ├── Clerk (JWT validation)
  ├── Stripe (payments)
  └── AI Providers
        ├── MistralAI
        ├── Groq
        ├── Gemini
        └── OpenRouter
```

---

## Monorepo Layout

```
staqk/
├── frontend/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Sign-in / sign-up (Clerk)
│   │   ├── (dashboard)/        # Project list, billing, settings
│   │   └── workspace/[id]/     # Editor, chat, preview, file tree
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives
│   │   ├── workspace/          # Editor, FileTree, Preview, Chat
│   │   └── dashboard/          # ProjectCard, CreditMeter, etc.
│   ├── lib/
│   │   ├── api.ts              # Typed API client (fetch wrapper)
│   │   ├── ws.ts               # WebSocket client (agent streaming)
│   │   └── hooks/              # TanStack Query hooks
│   └── public/
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── routers/            # Route handlers (see API Routes below)
│   │   ├── agents/             # LangGraph nodes (see Agent Graph below)
│   │   ├── services/           # credits.py, projects.py, users.py
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic v2 schemas
│   │   └── middleware/         # Clerk JWT auth, rate limiting
│   ├── alembic/                # Migration scripts
│   └── tests/                  # pytest + httpx async tests
│
└── specs/                      # OpenSpec SDD artifacts
```

---

## Backend App Structure

```python
# app/main.py
app = FastAPI()
app.add_middleware(ClerkJWTMiddleware)
app.include_router(auth_router, prefix="/auth")
app.include_router(projects_router, prefix="/projects")
app.include_router(ai_router, prefix="/ai")
app.include_router(payments_router, prefix="/payments")
app.include_router(public_router, prefix="/public")
```

**Middleware order:** CORS → Rate limit → Clerk JWT → Route handler

---

## Database Schema

```
User
  id            UUID PK
  clerk_id      TEXT UNIQUE
  email         TEXT UNIQUE
  credits       INT DEFAULT 100
  plan          ENUM(free, starter, pro, team, enterprise)
  created_at    TIMESTAMPTZ

WebsiteProject
  id            UUID PK
  user_id       UUID FK → User
  name          TEXT
  description   TEXT
  tech_stack    JSONB
  file_tree     JSONB
  status        ENUM(draft, building, ready, deployed, error)
  created_at    TIMESTAMPTZ
  updated_at    TIMESTAMPTZ

Conversation
  id            UUID PK
  project_id    UUID FK → WebsiteProject
  role          ENUM(user, assistant, system)
  content       TEXT
  created_at    TIMESTAMPTZ

Version
  id            UUID PK
  project_id    UUID FK → WebsiteProject
  snapshot      JSONB        -- full file tree at this point
  message       TEXT
  created_at    TIMESTAMPTZ

Transaction
  id            UUID PK
  user_id       UUID FK → User
  amount        INT          -- positive = purchase, negative = spend
  type          ENUM(purchase, spend, refund)
  description   TEXT
  created_at    TIMESTAMPTZ

AIUsageLog
  id            UUID PK
  user_id       UUID FK → User
  project_id    UUID FK → WebsiteProject (nullable)
  agent         TEXT         -- plan, code, test, security, deploy
  provider      TEXT         -- mistral, groq, gemini, openrouter
  model         TEXT
  input_tokens  INT
  output_tokens INT
  credits_used  INT
  created_at    TIMESTAMPTZ

SecurityScan
  id            UUID PK
  project_id    UUID FK → WebsiteProject
  findings      JSONB        -- Semgrep results
  severity      ENUM(clean, low, medium, high, critical)
  auto_fixed    BOOLEAN
  created_at    TIMESTAMPTZ

Deployment
  id            UUID PK
  project_id    UUID FK → WebsiteProject
  url           TEXT
  provider      ENUM(vercel, github)
  status        ENUM(pending, deploying, live, failed)
  deployed_at   TIMESTAMPTZ
```

---

## API Routes

| Method | Path | Auth | Credits | Description |
|--------|------|------|---------|-------------|
| POST | `/auth/webhook` | Clerk webhook | — | Sync new Clerk user to DB |
| GET | `/auth/me` | JWT | — | Current user + credits |
| GET | `/projects` | JWT | — | List user's projects |
| POST | `/projects` | JWT | — | Create new project |
| GET | `/projects/{id}` | JWT | — | Get project + file tree |
| PUT | `/projects/{id}` | JWT | — | Update project metadata |
| DELETE | `/projects/{id}` | JWT | — | Soft delete project |
| GET | `/projects/{id}/versions` | JWT | — | List versions |
| POST | `/projects/{id}/versions` | JWT | — | Save version snapshot |
| WS | `/ai/stream/{project_id}` | JWT | 5/op | Run agent pipeline, stream events |
| POST | `/ai/iterate` | JWT | 5/op | Chat iteration on existing project |
| GET | `/payments/credits` | JWT | — | Credit balance + history |
| POST | `/payments/checkout` | JWT | — | Create Stripe checkout session |
| POST | `/payments/webhook` | Stripe webhook | — | Handle payment events |
| GET | `/public/templates` | None | — | List starter templates |
| GET | `/public/preview/{id}` | None | — | Read-only project preview |

---

## LangGraph Agent Graph

```
START
  │
  ▼
[Plan Agent]  ──────────────────────────────────────────────────┐
  │  Generates architecture JSON + file list                    │
  ▼                                                             │
[Code Agent]  ──────────────────────────────────────────────────┤
  │  Generates all files, runs in E2B to verify no syntax errors │
  ▼                                                             │
[Test Agent]  ──────────────────────────────────────────────────┤
  │  Writes + runs Vitest unit tests in E2B                     │
  │  If tests fail → retry Code Agent (max 2 retries)          │
  ▼                                                             │
[Security Agent]  ──────────────────────────────────────────────┤
  │  Semgrep scan → LLM auto-fix for medium/high findings      │
  │  If critical → halt, notify user                           │
  ▼                                                             │
[Deploy Agent]  ────────────────────────────────────────────────┘
  │  Vercel API deploy → return live URL
  ▼
END
```

**LangGraph state schema:**
```python
class AgentState(TypedDict):
    project_id: str
    user_message: str
    tech_stack: dict
    file_tree: dict[str, str]   # path → content
    plan: dict
    test_results: list[dict]
    security_findings: list[dict]
    deployment_url: str | None
    error: str | None
    retry_count: int
```

---

## Model Routing

| Agent | Default Model | Fallback |
|-------|--------------|---------|
| Plan | Gemini Flash 1.5 (via Google) | OpenRouter Gemini |
| Code | Mistral Large (via MistralAI) | OpenRouter Mistral |
| Test | Llama 3.1 70B (via Groq) | OpenRouter Llama |
| Security | Mistral Small (via MistralAI) | OpenRouter Mistral |
| Deploy | No LLM — Vercel API only | — |

Routing logic lives in `backend/app/agents/router.py`. Falls back to OpenRouter if direct provider rate-limits.

---

## Clerk JWT Validation (FastAPI)

```python
# app/middleware/auth.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = clerk_client.verify_token(token)   # Clerk Python SDK
    user = await user_service.get_by_clerk_id(payload["sub"])
    if not user:
        raise HTTPException(401)
    return user
```

All protected routes receive `current_user: User = Depends(get_current_user)`.

---

## E2B Sandbox Lifecycle

1. **Create** — `sandbox = await Sandbox.create(template="base")` at start of Code Agent
2. **Write files** — upload generated files into sandbox filesystem
3. **Execute** — run `npm install && npm run build` to catch errors
4. **Test** — run `npx vitest run` (Test Agent)
5. **Destroy** — `await sandbox.close()` on success or error
6. **Timeout** — sandboxes auto-terminate after 5 minutes of inactivity

---

## Credit System Rules

- Credits are checked **before** every AI operation — insufficient credits = 402 error, no operation starts
- Credits are deducted **atomically** inside a SQLAlchemy transaction alongside the operation log
- Failed operations (agent error, timeout) trigger a **full refund** to the transaction table
- Credit cost: **5 credits per full pipeline run**, **2 credits per chat iteration**
- Purchases add credits via Stripe webhook → `Transaction(type=purchase)`

---

## Security Rules

1. All user-generated code runs **only inside E2B sandboxes** — never on the host
2. Semgrep scan is **required** before every deployment — cannot be skipped
3. All API routes validate Clerk JWT — no unauthenticated mutations
4. Secrets/env vars are never included in code generation output
5. SQL queries go through SQLAlchemy ORM — no raw string interpolation
