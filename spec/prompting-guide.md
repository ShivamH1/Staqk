# Prompting Guide

## Golden Rule

Paste this context header at the start of every AI coding session:

```
Project: Staqk — security-first, multi-agent AI app builder
Stack:
  Frontend: Next.js 15, TypeScript strict, Tailwind CSS, shadcn/ui
  Animations: GSAP (timelines/scroll), Framer Motion (React transitions), Locomotive Scroll (marketing pages)
  Backend: Python 3.12, FastAPI (async), SQLAlchemy async + Alembic
  AI: LangGraph + LangChain, providers: MistralAI, Groq, Gemini, OpenRouter
  DB: Neon (PostgreSQL, asyncpg)
  Auth: Clerk (JWT in FastAPI middleware)
  Payments: Stripe (credit-based)
  Sandbox: E2B (Python SDK)
  Deploy: Vercel (frontend), Render (backend)
  Dev method: Spec-Driven Development via fission-ai/openspec

Rules:
  - TypeScript: strict mode, no `any`, Zod at API boundaries, TanStack Query for server state
  - Python: type hints everywhere, mypy strict, Pydantic v2, Ruff linting, no sync I/O in async
  - No TODOs, no console.log, no print() debug, no hardcoded secrets
  - Follow code-standards.md exactly
  - If a spec exists for this feature, read it before implementing
```

---

## OpenSpec Workflow Templates

### Propose a New Feature

```
/opsx:propose <feature-name>

Context: [paste golden rule header]
Feature name: <name>
What the user wants: <one paragraph description>
Out of scope: <what it should NOT do>
```

### Implement from Spec

```
/opsx:implement <feature-name>

Context: [paste golden rule header]
Read specs/<feature-name>/design.md and specs/<feature-name>/specs/requirements.md first.
Implement only the tasks listed in specs/<feature-name>/tasks.md.
Check off each task as you complete it.
```

### Archive a Complete Feature

```
/opsx:archive <feature-name>

Mark all tasks in specs/<feature-name>/tasks.md as done.
Move the folder to specs/archived/<feature-name>/.
```

---

## Prompt Templates

### 1. Build a New Feature (Spec-Driven)

```
[paste golden rule]

Feature: <name>
Spec: specs/<feature-name>/ (read this first)

What to build:
- [user story from spec]

Files to create or modify:
- backend/app/routers/<name>.py
- backend/app/models/<name>.py
- frontend/components/<Name>.tsx
- [other files]

Constraints:
- [any constraints from spec design.md]
```

### 2. Fix a Bug

```
[paste golden rule]

Bug: <short title>

Repro steps:
1. [step 1]
2. [step 2]

Expected: [what should happen]
Actual: [what happens instead]

Relevant files:
- [file path]
- [file path]

Error output:
[paste error or log]
```

### 3. Build a FastAPI Route

```
[paste golden rule]

Add a route to backend/app/routers/<router>.py

Method + path: POST /projects/{id}/scan
Auth: required (Depends(get_current_user))
Credits: 1 credit per call

Request body schema (Pydantic v2):
{
  "force": bool = False
}

Response schema:
{
  "scan_id": str (UUID),
  "status": "queued"
}

Error cases:
- 402 if insufficient credits
- 404 if project not found or not owned by user
- 403 if project is deleted

Side effects:
- Deduct 1 credit atomically
- Create SecurityScan record with status "queued"
- Enqueue background task to run Security Agent
```

### 4. Build a React Component

```
[paste golden rule]

Component: <ComponentName>
File: frontend/components/<path>/<ComponentName>.tsx

Props:
- projectId: string
- onComplete: (url: string) => void

Visual description:
[describe layout, colours using design tokens, what it shows]

Behaviour:
- [interaction 1]
- [interaction 2]

Data: uses useQuery hook from lib/hooks/use-project.ts
State: [what local state it needs]

Do not:
- Add mock data
- Use `any`
- Add comments explaining what the code does
```

### 5. Database Schema Change (SQLAlchemy + Alembic)

```
[paste golden rule]

Add a new model or modify an existing one.

Model: SecurityScan
File: backend/app/models/security.py

Fields to add:
- id: UUID, primary key, default uuid4
- project_id: UUID, FK → WebsiteProject, cascade delete
- findings: JSONB
- severity: Enum('clean','low','medium','high','critical')
- auto_fixed: Boolean, default False
- created_at: TIMESTAMPTZ, default now

After creating the model:
1. Run: alembic revision --autogenerate -m "add security scan"
2. Review the generated migration in alembic/versions/
3. Run: alembic upgrade head
```

### 6. LangGraph Agent Node

```
[paste golden rule]

Add or modify an agent node in backend/app/agents/

Node name: security_node
File: backend/app/agents/security_agent.py

State fields read: file_tree
State fields written: security_findings, security_cleared

Steps:
1. Write files to E2B sandbox using e2b_write_files tool
2. Run `semgrep --config=auto --json` in sandbox
3. Parse JSON output into list[SecurityFinding]
4. For severity medium/high: generate LLM fix using Mistral Small, apply to file_tree
5. For severity critical: set security_cleared=False, set error message
6. Return updated state fields

Model: Mistral Small via MistralAI SDK (fallback: OpenRouter)
```

### 7. Write Tests

```
[paste golden rule]

Write tests for: backend/app/routers/projects.py
Test file: backend/tests/test_projects.py
Framework: pytest + httpx AsyncClient

Test cases:
- POST /projects returns 201 with valid body
- POST /projects returns 422 if name is empty
- POST /projects returns 401 if unauthenticated
- GET /projects returns only projects owned by current user
- DELETE /projects/{id} soft-deletes (sets deleted_at)

Mocks needed:
- Clerk JWT (fixture that returns a test user)
- DB session (use test database, not mocks — real SQLAlchemy)

Do not use MagicMock on the database.
```

### 8. Refactor / Code Review

```
[paste golden rule]

Refactor: <area>

Goals:
- [goal 1, e.g. "eliminate repeated credit check logic across 4 routes"]
- [goal 2]

Constraints:
- Do not change public API contracts (route paths, response shapes)
- Do not change DB schema
- All existing tests must continue to pass

Files in scope:
- [file 1]
- [file 2]
```

### 9. Debugging Session

```
[paste golden rule]

Problem: <short title>

Repro:
1. [step]
2. [step]

Error output:
[paste full traceback or error]

What I've tried:
- [attempt 1]
- [attempt 2]

Relevant code (paste the failing function/component):
[code]
```

### 10. Generate a Full Page

```
[paste golden rule]

Page: <name>
Route: /dashboard/billing
File: frontend/app/(dashboard)/billing/page.tsx

Data fetching:
- useQuery(getCredits) → { balance, transactions[] }
- useQuery(getSubscription) → { plan, renewsAt }

Sections:
1. Credit balance card (large number + "credits remaining")
2. Current plan card (plan name + renewal date + upgrade button)
3. Transaction history table (date, description, amount, type badge)
4. "Buy credits" button → opens Stripe Checkout (POST /payments/checkout)

Loading state: skeleton cards for each section
Error state: error boundary with retry button

Animations: Framer Motion for card entrance (staggered, 100ms delay between cards)
```

---

## Pro Tips

1. **Be specific about file paths** — "create a component" is vague; "create `frontend/components/workspace/SecurityPanel.tsx`" is actionable
2. **Paste the actual failing code** — don't describe what's wrong, show it
3. **One feature per session** — don't chain multiple features in one prompt; start fresh for each
4. **Reference the spec** — "implement specs/security-scanning/" is better than re-describing the feature
5. **State what NOT to do** — prevents the AI from adding unasked-for abstractions or features
6. **Correct specifically** — "the loading state is wrong, here's what it should look like: ..." beats "fix the UI"
