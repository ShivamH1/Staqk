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

### Step 5 — Real Plan Agent ✅ (2026-06-24)

Replaced the Plan stub with a live LLM call — the first real agent, chosen because it needs no E2B (pure generation), so it validates the LangChain provider wiring + model routing in isolation.

- **`agents/models.py`**: `get_chat_model(agent)` builds the direct-provider chat model when its key is set (Gemini `ChatGoogleGenerativeAI`, Mistral `ChatMistralAI`, Groq `ChatGroq`), else falls back to OpenRouter via `ChatOpenAI(base_url=openrouter)` — per ADR-010. Keys wrapped in `SecretStr`. Provider modules imported lazily inside the factory.
- **`agents/plan_agent.py`**: `plan_node` now calls the model with `PLAN_SYSTEM_PROMPT` (from ai-pipeline.md) + a user prompt built from `user_message` + `tech_stack`. `parse_plan_json` tolerates ```json fences and content-block lists. Errors (bad JSON / provider failure) emit `agent_error` and set `state.error` instead of crashing the pipeline.
- **`events.py`**: `emit()` now no-ops when there's no active LangGraph stream context (`get_stream_writer()` raises outside a run) — so nodes are callable directly in unit tests.
- **`tests/conftest.py`** (new): centralised dummy env + an **autouse `mock_chat_model`** fixture that replaces `get_chat_model` with a fake returning a valid plan JSON — keeps all pipeline/WS tests offline. `fake_model_returning()` helper lets a test supply a specific response.
- **`tests/test_plan_agent.py`**: covers JSON parsing (plain + fenced), the happy path, and the bad-JSON error path.

**Deviations / notes:** Runtime rate-limit fallback (primary → OpenRouter on 429) is deferred — current logic picks OpenRouter only when the direct provider key is absent. Real LLM calls require actual API keys; tests mock the model so no network/credits are used.

**Verified (full gate):** ruff + mypy (26 files) + 10 pytest (incl. plan agent + offline full-pipeline + WS).

**Live verified (2026-06-24):** ran the pipeline once against the real model with `OPENROUTER_API_KEY` set in `backend/.env.local`. The Plan agent produced a valid architecture plan for "build a todo app" (Todo model, REST endpoints, routes). Fixes made during this live test:
- `config.py` now reads `(".env", ".env.local")` so either backend env file works.
- Updated Plan model slugs to current ones: direct `gemini-2.5-flash`, OpenRouter fallback `google/gemini-3.1-flash-lite` (the old `google/gemini-flash-1.5` returned 404 "no endpoints").
- Added `MAX_OUTPUT_TOKENS = 4096` cap in `models.py` (all providers) — fixes OpenRouter 402 on low-balance accounts that reserve the model's full 65k output budget, and controls cost.
- ⚠️ The OpenRouter fallback slugs for **code / test / security** agents in `router.py` are still the old-style guesses and likely 404 — update them when those agents go real (verify against `https://openrouter.ai/api/v1/models`).

### Step 6 — Code Agent + E2B ✅ (2026-06-25)

Replaced the Code stub with real LLM generation + an E2B sandbox build check.

- **`app/sandbox/e2b.py`** (new): async E2B wrapper. `sandbox_session()` is an `@asynccontextmanager` that creates an `AsyncSandbox` and **always `kill()`s it in `finally`** (per CLAUDE.md: user code runs only in sandboxes, closed in finally). `Sandbox.write_files` writes the `{path: content}` tree under `WORK_DIR=/home/user/app`; `Sandbox.run` executes a command there and returns a `CommandOutcome(exit_code, stdout, stderr, ok)` — a non-zero exit is **returned, not raised** (catches E2B's `CommandExitException`). `SANDBOX_TIMEOUT=300`, `COMMAND_TIMEOUT=240`.
- **`app/agents/code_agent.py`**: `code_node` now calls Mistral Large (OpenRouter fallback) with `CODE_SYSTEM_PROMPT`, parses a `{path: content}` JSON tree (`parse_file_tree` — tolerates ```json fences, rejects non-object / non-string values), emits `file_created` per file, then `_verify_build` writes the tree to a sandbox and runs `npm install && npm run build`. Outcomes:
  - build ok → `build_success=True`, clears `error`/`build_error`.
  - build fails, retries left → `build_success=False`, `build_error`=truncated log, `retry_count+1` (graph routes back to `code`; the log is fed into the next prompt so the model fixes its own output).
  - build fails, retries exhausted → sets `error`, halting the pipeline.
  - bad model output / sandbox failure → sets `error`, `build_success=False`.
- **`app/agents/state.py`**: added `build_error: str | None` (retry context).
- **`app/agents/graph.py`**: new `_after_code` conditional edge — build ok → `test`, `error` set → `END`, otherwise → `code`. Replaces the unconditional `code → test` edge.
- **Tests**: `conftest.py` fake model now branches by agent (plan JSON vs file-tree JSON) and gains an autouse **`mock_sandbox`** fixture (+ `fake_sandbox_session(*exit_codes)` helper) so all pipeline/WS tests stay offline. New `tests/test_code_agent.py` covers parsing (plain/fenced/bad shape/non-string), the success path, build-failure-requests-retry, halt-after-retries, and invalid-output.

**Deviations / notes:** Test-failure-driven retries (`_after_test` → `code`) don't yet increment `retry_count`; harmless while the Test Agent is a stub returning `tests_passed=True`, to be fixed when the Test Agent goes real (Step 7). The OpenRouter fallback slugs for **code / test / security** are still unverified and likely 404 — verify against `https://openrouter.ai/api/v1/models` at live-test time.

**Verified (full gate):** ruff check + ruff format (Step 6 files) + mypy strict (28 files) + 19 pytest (incl. 9 code-agent tests, offline full-pipeline, WS).

**Live verified (2026-06-25):** ran Plan → Code against real Mistral Large (direct) + a real E2B sandbox.
- Plan agent produced a valid plan (~5s). Code agent generated a valid 8-file Next.js tree (`package.json`, `app/layout.tsx`, `app/page.tsx`, `app/globals.css`, `tailwind.config.ts`, `postcss.config.js`, `tsconfig.json`, `next.config.js`) and wrote it to the sandbox.
- Build-success path verified directly against real E2B with a trivial Node project: `npm install --no-audit --no-fund` + `npm run build` → `build_success=True`.
- **Fixes made during the live test:**
  - `parse_file_tree` now serialises object/array values to JSON text — models emit config files (`package.json`, `tsconfig.json`) as nested JSON objects, not strings. Numbers/bools/null are still rejected.
  - Leaned the install command to `npm install --no-audit --no-fund`.
- **Infra finding:** the E2B **base template has only ~482MB RAM** (Node 20, npm 10, 2 vCPU). A full Next.js `npm install`/`build` OOMs ("JavaScript heap out of memory"). The Code Agent handled it correctly (captured the log, would retry) but a retry can't fix an OOM. Added a configurable **`E2B_TEMPLATE`** setting (`config.py`) passed to `AsyncSandbox.create(template=...)`; set it to a custom template with ≥2GB RAM to build real Next.js apps. Empty → base template (fine for trivial/non-Next projects).

### Step 7 — Test Agent + E2B ✅ (2026-06-25)

Replaced the Test stub with real Groq-Llama test generation + Vitest execution in E2B.

- **`app/agents/test_agent.py`**: `test_node` calls Groq Llama (OpenRouter fallback) with `TEST_SYSTEM_PROMPT` (from ai-pipeline.md) to generate Vitest test files as a `{path: content}` JSON tree (reuses `code_agent.parse_file_tree`), emits `file_created` per test, then `_run_tests` writes code + tests to an E2B sandbox, runs `npm install --no-audit --no-fund` + `npx --yes vitest run`. **Pass/fail is driven by the runner exit code**; `_parse_results` best-effort-extracts pass/fail counts from the vitest summary line. Outcomes mirror the Code Agent:
  - tests pass → `tests_passed=True`, clears `test_failures`.
  - tests fail, retries left → `tests_passed=False`, `test_failures`=truncated log, `retry_count+1` (graph routes back to `code`).
  - tests fail, retries exhausted → sets `error`, halting the pipeline.
  - bad model output / sandbox failure → sets `error`, `tests_passed=False`.
- **`app/agents/state.py`**: added `test_failures: str | None` (retry context).
- **`app/agents/graph.py`**: rewrote `_after_test` to mirror `_after_code` — tests pass → `security`, `error` set → `END`, else → `code`. The retry-budget check + `retry_count` increment now live in `test_node` (was a bare `retry_count < MAX` check in the router that never incremented — the gap flagged in Step 6). Dropped the now-unused `MAX_CODE_RETRIES` import.
- **`app/agents/code_agent.py`**: `_build_messages` now also feeds `test_failures` back on a test-driven retry ("the code built but failed its tests — fix the code, not the tests") alongside the existing `build_error` path.
- **Tests**: `conftest.py` gains a `_FAKE_TEST_TREE`, the fake model branches for the `test` agent, and `mock_sandbox` now also patches `app.agents.test_agent.sandbox_session`. New `tests/test_test_agent.py` (6 tests) covers `_parse_results`, the pass path, fail-requests-retry, halt-after-retries, and invalid-output. (The agent function is `test_node`, which pytest would otherwise collect as a test — imported `as run_test_node` to avoid that.)

**Deviations / notes:** Playwright e2e generation is deferred — Vitest unit tests only for now (e2e in the sandbox is heavier and flakier). `_after_test → code` and `_after_code → code` share the `retry_count` budget (`MAX_CODE_RETRIES`), per ai-pipeline.md. OpenRouter fallback slug for `test` (`meta-llama/llama-3.1-70b-instruct`) is still unverified.

**Verified (full gate):** ruff + mypy strict (28 files) + 25 pytest (incl. 6 test-agent tests, offline full-pipeline, WS).

**Not live-verified:** same E2B base-template RAM limit as Step 6 — `npm install` + `npx vitest` on a real Next.js app needs the larger `E2B_TEMPLATE`. Logic is exercised offline via the mocked sandbox.

### Step 8 — Security Agent + Semgrep ✅ (2026-06-26)

Replaced the Security stub with a real Semgrep scan in E2B + Mistral-Small auto-fix.

- **`app/agents/security_agent.py`**: `security_node` writes `file_tree` to an E2B sandbox and runs `python3 -m pip install --quiet semgrep && semgrep --config=auto --json .`. Semgrep exits **1 when it finds issues**, so the JSON on stdout is authoritative — `parse_findings` reads `data["results"]`, not the exit code. Each result is normalised by `_normalize_severity` onto a single scale (info/low/medium/high/critical): it prefers an explicit `extra.metadata.severity`/`impact` (so a rule tagged `CRITICAL` is honoured), else maps the CLI `extra.severity` (`ERROR→high`, `WARNING→medium`, `INFO→low`). Outcomes:
  - **critical present** → `_halt`: `security_cleared=False` + `error` set, pipeline ends (graph `_after_security` only routes `deploy`/`END`).
  - **medium/high present, no critical** → one auto-fix pass: Mistral Small (`SECURITY_SYSTEM_PROMPT`) returns the FULL corrected tree (reuses `code_agent.parse_file_tree`), merged over `file_tree`, then **re-scanned once**. If the re-scan surfaces a critical → halt (carrying the fixed `file_tree`); otherwise clear with the post-fix findings and the updated `file_tree`.
  - **only low/info, or clean** → `security_cleared=True`, findings logged.
  - bad fix output → non-critical, so log and continue (don't block on an unfixable medium). Sandbox/network failure or unparseable scan → `error`, `security_cleared=False`.
  - emits a `security_finding` event per non-info finding.
- Unlike Code/Test, the Security Agent runs its **own** in-place fix+rescan rather than routing back through Code — the graph edge out of `security` only leads to `deploy` or `END`. Model routing already had `security → mistral-small-latest` (OpenRouter `mistralai/mistral-small`).
- **Tests**: `conftest.py` — fake model gains a `security` branch (returns a corrected tree); `_FakeSandbox.run` returns `{"results": []}` for any `semgrep` command (clean scan keeps the full-pipeline test green); new `_ScriptedSandbox` + `fake_semgrep_session(*scans)` helper scripts successive scan/rescan stdout; `mock_sandbox` now also patches `app.agents.security_agent.sandbox_session`. New `tests/test_security_agent.py` (8 tests): severity normalisation, non-semgrep output rejected, clean→clear, critical→halt, medium→autofix→clean-rescan, medium→autofix→critical-rescan→halt, scan-failure→error, low→pass-through.

**Deviations / notes:** Auto-fix is a single pass + one re-scan (per ai-pipeline.md step 6), not a loop — persistent medium/high after one fix are logged, not retried (only critical halts). Semgrep is `pip install`ed at scan time (no-op if the template ships it); on the larger `E2B_TEMPLATE` this should be baked in. OpenRouter fallback slug `mistralai/mistral-small` still unverified.

**Verified (full gate):** ruff check (app/tests) + mypy strict (28 files) + 33 pytest (incl. 8 security-agent tests, offline full-pipeline, WS).

**Not live-verified:** same E2B base-template RAM limit as Steps 6–7 — a real Semgrep run on a full tree needs the larger `E2B_TEMPLATE`. Logic is exercised offline via the scripted sandbox.

### Step 9 — Credit deduction + refund logic ✅ (2026-06-26)

Wired the credit ledger into the pipeline: pre-check + atomic deduct before any AI work, refund on failure.

- **`app/models/transaction.py`** (new): `Transaction` + `TransactionType` StrEnum (purchase/spend/refund). Signed `amount` (positive purchase/refund, negative spend), FK → `users.id`. Immutable ledger — a refund is a new positive row, never an edit/reversal of the spend.
- **`app/models/ai_usage.py`** (new): `AIUsageLog` — one row per deduction (FK → `users.id`, nullable `project_id` **without an FK** until the projects table exists, agent/provider/model, token counts, `credits_used`).
- **`app/models/__init__.py`**: exports both new models (so Alembic autogenerate/metadata sees them).
- **`app/services/credits.py`** (new): `PIPELINE_COST=5`, `CHAT_ITERATION_COST=2` (fixed product pricing, per CLAUDE.md), `InsufficientCreditsError(available, required)`.
  - `deduct_credits(...)`: `async with db.begin()` → `SELECT … FOR UPDATE` the user row (blocks concurrent double-spend) → if balance short, raise (transaction rolls back, nothing persisted) → else decrement + add `spend` `Transaction` + `AIUsageLog`, all in one commit.
  - `refund_credits(...)`: locks the user, increments credits, adds a `refund` `Transaction`. No-op (logged) if the user is gone.
- **`app/routers/ai.py`**: the WS handler now (1) deducts `PIPELINE_COST` *after* receiving the start message but *before* `pipeline.astream` — on `InsufficientCreditsError` it sends `pipeline_error` (`credits_refunded: 0`) and closes `1008`, nothing runs; (2) watches the stream for `agent_error` — since an agent failure ends the stream **without raising**, an `errored` flag drives a refund + `pipeline_error`; (3) refunds on `WebSocketDisconnect` and on any unexpected exception via a best-effort `_refund_run` helper (its own session; a refund failure is logged, never masks the original error). Imported as `credit_service` (the bare name `credits` shadows a Python builtin — ruff A004).
- **`alembic/versions/0002_credits_ledger.py`** (new, hand-written like 0001): creates `transactions` + `ai_usage_logs` (+ `transaction_type` enum, user-id indexes); `downgrade` drops both and the enum.
- **Tests**: new `tests/test_credits.py` (5) exercises deduct (decrement + spend txn + usage log committed), insufficient (raises, nothing added, rolled back), missing-user, refund (positive txn, +balance), refund-missing-user — via a `_FakeSession` (records `add`s, `begin()` tracks commit/rollback) so no DB is needed. `tests/test_ws.py`: existing pipeline test now stubs `deduct_credits` and asserts it's called once for 5 + `credits_used==5`; new test asserts insufficient credits emits `pipeline_error`/`credits_refunded: 0` and the pipeline **never runs**.

**Deviations / notes:** `AIUsageLog.project_id` has no FK yet (projects table is a later step). One `AIUsageLog`/`spend` row per **run** (5 credits), not per-agent — the per-agent token breakdown can be split out once agents report token usage. `CHAT_ITERATION_COST` is defined but unused until the `/ai/iterate` endpoint lands. Migration 0002 is written + offline-validated only; no live Neon apply yet (same as 0001). Credit tests use a fake session (no `aiosqlite` in the venv) — they verify the ledger logic, not real Postgres `FOR UPDATE` locking.

**Verified (full gate):** ruff check (app/tests) + mypy strict (31 files) + 39 pytest (incl. 5 credits tests + WS insufficient-credits test, offline full-pipeline).

### Step 10 — Projects router + DB ✅ (2026-06-26)

Added the `WebsiteProject` model, migration, and a CRUD projects router; gave `AIUsageLog.project_id` its FK.

- **`app/models/project.py`** (new): `WebsiteProject` + `ProjectStatus` StrEnum (draft/building/ready/deployed/error). FK → `users.id`; `tech_stack`/`file_tree` as `JSONB` (default `{}`); `created_at`/`updated_at` (`onupdate=now()`); **`deleted_at`** for soft-delete (CLAUDE.md: never hard-delete user data).
- **`app/models/ai_usage.py`**: `project_id` now carries its real `ForeignKey("website_projects.id")` (the deferral noted in Step 9 is resolved).
- **`app/models/__init__.py`**: exports `WebsiteProject`/`ProjectStatus`.
- **`app/schemas/project.py`** (new): `ProjectCreate` (`name` `Field(min_length=1, max_length=200)`, optional `description`/`tech_stack`), `ProjectResponse` (full, incl. `file_tree`), `ProjectSummary` (list view — **omits `file_tree`** to keep listings light).
- **`app/services/projects.py`** (new): `create_project` (flush+refresh), `list_projects` (selects **specific columns** — not `SELECT *` — newest-first, `deleted_at IS NULL`), `get_project` (scoped to owner + not-deleted), `soft_delete_project` (sets `deleted_at`, returns False if absent). All reads are user-scoped so one user can't touch another's projects.
- **`app/routers/projects.py`** (new): `POST /projects` (201), `GET /projects` (`list[ProjectSummary]`), `GET /projects/{id}` (404 if absent), `DELETE /projects/{id}` (204 soft-delete, 404 if absent) — all behind `Depends(get_current_user)`. Mutations run inside `async with db.begin()`; the create returns inside the block (commit fires on exit; `expire_on_commit=False` keeps attrs).
- **`app/main.py`**: registers `projects.router`.
- **`alembic/versions/0003_create_website_projects.py`** (new, hand-written): creates `website_projects` (+ `project_status` enum, JSONB columns, user-id index) then `op.create_foreign_key` for `ai_usage_logs.project_id`. `downgrade` drops the FK, table, and enum in order.
- **Tests**: new `tests/test_projects.py` (8) via FastAPI `dependency_overrides` (`get_current_user` → fake user, `get_db` → `_FakeDB` whose `begin()` is an async CM) + monkeypatched `project_service`: auth-required (401), create (201), empty-name rejected (422), list (200, **asserts `file_tree` absent**), get found/404, delete 204/404.

**Deviations / notes:** `PUT /projects/{id}` (metadata update) from the architecture routes table is **not** implemented yet — create/list/get/soft-delete cover what the workspace needs now. The **pipeline does not yet persist** into `WebsiteProject` (the WS handler still streams `file_tree` without saving it or flipping `status`) — that wiring is a follow-up. Migration 0003 is offline-validated only (no live Neon apply). Project tests use overrides/fakes (no `aiosqlite`) — they verify routing/auth/serialisation, not real Postgres FKs or the `JSONB`/`deleted_at` filter.

**Verified (full gate):** ruff check (app/tests) + mypy strict (35 files) + 47 pytest (incl. 8 projects tests).

### Step 11 — (next, backend) Persist pipeline results + `/ai/iterate` 🔲

Wire the WS pipeline to a real `WebsiteProject`: flip `status` (building → ready/deployed/error) and save the generated `file_tree`/`deployment_url`, and add the `/ai/iterate` chat-iteration endpoint (`CHAT_ITERATION_COST=2`, loads the project's `existing_file_tree`). Alternatives: `PUT /projects/{id}`; live-verify the agents on a ≥2GB `E2B_TEMPLATE`. See progress-tracker.md → Upcoming Priorities.

---

## Frontend — Marketing landing (parallel track)

Building the public landing page step by step. Reference vibe is borrowed from the separate `D:\Product-SAAS\staqk` prototype (only the rotating 3D background + the keyboard animation), reconciled with [design.md](design.md).

**Decisions (2026-06-25):**
- **Smooth scroll → Lenis**, not Locomotive Scroll (which design.md/CLAUDE.md name). Locomotive has friction with React 19 / Next 16; Lenis is its modern successor. design.md's animation-domain rule should be updated to say Lenis when it's wired (Step F3).
- **Background-3D keeps the tinted color cycling** from the reference (navy→purple→teal→…) rather than being muted to strict `#090909` monochrome — a deliberate, user-approved bend of design.md's monochrome rule for atmosphere.

### Step F1 — Background-3D + hero shell ✅ (2026-06-25)

- Installed `three@0.185` + `@types/three`.
- **`components/marketing/background-3d.tsx`** (new, `'use client'`): the reference Three.js rotating wireframe-city — 100 buildings, 300 particles, 60 "cars", fog, color cycling, cursor parallax on ≥1280px (auto-rotate below). Adapted to our Biome style; added `renderer.setPixelRatio(min(dpr, 2))` for crisp-but-smooth rendering; disposes geometries/materials/renderer on unmount. Renders `fixed inset-0`.
- **`components/marketing/navbar.tsx`** (new): design.md `top-nav` (56px) — wordmark left, center links, `Sign in` (charcoal pill → `/sign-in`) + `Get started` (white pill → `/sign-up`).
- **`app/page.tsx`**: replaced the Next boilerplate with the dark hero shell — fixed Background3D backdrop (`z-0`) + a subtle legibility scrim, content at `z-10`: eyebrow chip, `Build. Secure. Ship.` display headline (Inter substitute, `tracking-[-0.05em]`, `leading-[0.95]`), ink-muted subhead, white-pill + charcoal-pill CTAs.

**Deviations / notes:** GT Walsheim is paid — display type uses Inter with tight negative tracking per design.md's substitution note. The keyboard animation (reference `features.tsx`) and Lenis smooth scroll are later steps (F2, F3).

**Verified (full gate):** biome check (31 files) + tsc (clean) + `next build` (5 routes, `/` static).

### Step F2 — Keyboard animation section ✅ (2026-06-25)

- **`components/marketing/features.tsx`** (new, `'use client'`): ported the reference keyboard visual + typing-text effect, restyled to design.md.
  - `useTypingAnimation` hook (cleaned up: interval id captured and cleared in the effect cleanup) types example prompts char-by-char.
  - `KeyboardVisual`: 3 rows of keys that gently pulse opacity via Framer Motion (`repeat: Infinity`, staggered `delay`). Restyled to tokens — outer `bg-surface-1` `rounded-[20px]`, inner `bg-surface-2` `rounded-[10px]`, keys `bg-canvas` `border-hairline` `rounded-[6px]`. Keys shrink on mobile (`h-8 w-8` → `md:h-10 md:w-10`).
  - Section reveal via Framer Motion `useInView` (`once: true`). Staqk-specific copy: eyebrow "How it works", headline "Describe it. Watch it ship.", with two typed prompts inline.
- **`app/page.tsx`**: restructured into a scrollable page — hero is now a `min-h-[calc(100vh-3.5rem)]` section, `<Features />` sits below it. Root switched to `overflow-x-hidden` (was `overflow-hidden`) so the page scrolls vertically while the fixed Background3D persists behind both bands. The Features section is `bg-canvas` so it reads as a solid dark band over the 3D as you scroll past the hero.

**Deviations / notes:** Animation domains respected — Framer Motion for these React component transitions (per CLAUDE.md). Keyboard is ambient/decorative (no real key-to-text wiring). Smooth scroll (Lenis) is the next step.

**Verified (full gate):** biome check (32 files) + tsc (clean) + `next build` (5 routes, `/` static).

### Step F3 — Lenis smooth scroll ✅ (2026-06-25)

- Installed `lenis@1.3`.
- **`components/marketing/smooth-scroll.tsx`** (new, `'use client'`): mounts Lenis on the window scroll, drives its RAF loop, imports `lenis/dist/lenis.css`, and **destroys on unmount**. `duration: 1.1` with a cubic ease-out. **Honors `prefers-reduced-motion`** — bails out entirely so reduced-motion users keep native scroll. Renders `null`.
- **`app/page.tsx`**: rendered `<SmoothScroll />` at the top of the landing tree — scoped to the marketing route only (not workspace/dashboard), per the animation-domain rule.
- **Docs updated Locomotive → Lenis:** `decisions.md` ADR-008 (amended with rationale: Locomotive has React 19 / Next 16 friction; Lenis is by the same studio, maintained, framework-agnostic, and what Locomotive now builds on), `CLAUDE.md` animation-domains line, `README.md` stack table, `prompting-guide.md` context header, `progress-tracker.md` row.

**Deviations / notes:** Anchor links (e.g. "See how it works" → `#product`) still use native jump — Lenis-driven `scrollTo` for in-page anchors can be added later if desired.

**Verified (full gate):** biome check (33 files) + tsc (clean) + `next build` (5 routes, `/` static).

### Step F4 — (next) more landing sections / polish 🔲

Candidates: features/benefits band, gradient spotlight cards (design.md signature), pricing teaser, footer; or anchor-aware Lenis `scrollTo`. Decide scope next.
