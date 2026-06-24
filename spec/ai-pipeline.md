# AI Pipeline

## Overview

Staqk's AI pipeline is a LangGraph state machine with 5 nodes. Every full build runs all 5 in sequence. Chat iterations re-enter at the Code node.

```
User message
     │
     ▼
 [Plan Agent]
     │  architecture JSON + file list
     ▼
 [Code Agent] ◄──────────── retry (max 2)
     │  generated files
     ▼
 [Test Agent] ──── fail ───►
     │  test results
     ▼
[Security Agent]
     │  scan results + auto-fixes
     ▼
[Deploy Agent]
     │  live URL
     ▼
  Done
```

---

## LangGraph State Schema

```python
from typing import TypedDict

class AgentState(TypedDict):
    # Input
    project_id: str
    user_message: str
    tech_stack: dict              # { framework, language, db, styling }
    existing_file_tree: dict      # path → content (for iterations)

    # Plan Agent output
    plan: dict                    # { components, routes, db_schema, notes }

    # Code Agent output
    file_tree: dict               # path → content (generated files)
    build_success: bool

    # Test Agent output
    test_results: list[dict]      # [{ file, passed, failed, errors }]
    tests_passed: bool

    # Security Agent output
    security_findings: list[dict] # [{ rule, severity, file, line, fix }]
    security_cleared: bool

    # Deploy Agent output
    deployment_url: str | None

    # Control
    error: str | None
    retry_count: int              # Code Agent retries
```

---

## Agents

### Plan Agent

**Role:** Convert the user's natural language request into a structured architecture plan.

**Model:** Gemini Flash 1.5 (fast, low cost for structured output)

**Input state fields:** `user_message`, `tech_stack`, `existing_file_tree`

**Output state fields:** `plan`

**Plan schema:**
```json
{
  "components": ["ComponentName"],
  "routes": [{ "path": "/", "component": "Home", "auth": false }],
  "db_schema": [{ "model": "User", "fields": ["id", "email"] }],
  "api_endpoints": [{ "method": "GET", "path": "/api/users" }],
  "notes": "string"
}
```

**Tools:** None (pure generation)

**System prompt excerpt:**
```
You are the Plan Agent for Staqk. Given a user request and tech stack, output a structured JSON plan.
Rules:
- Be specific about component names and file paths
- Keep the scope minimal — only what the user asked for
- Do not invent features not mentioned
- Output valid JSON only, no markdown
```

---

### Code Agent

**Role:** Generate all files in the project based on the plan.

**Model:** Mistral Large (via MistralAI direct) — fallback: OpenRouter Mistral

**Input state fields:** `plan`, `tech_stack`, `existing_file_tree`, `retry_count`

**Output state fields:** `file_tree`, `build_success`

**Behaviour:**
1. Generate all files as `{ path: content }` dict
2. Write files to E2B sandbox
3. Run `npm install && npm run build` in sandbox
4. If build fails and `retry_count < 2`: increment `retry_count`, re-enter Code Agent with error context
5. If build fails after 2 retries: set `error`, halt pipeline

**Tools:** `e2b_write_files`, `e2b_run_command`, `e2b_read_file`

**System prompt excerpt:**
```
You are the Code Agent for Staqk. Generate complete, production-ready files.
Rules:
- Every file must be complete — no placeholders, no TODOs
- Follow the project's code-standards.md exactly
- Never include hardcoded secrets or API keys
- TypeScript strict mode — no 'any'
- If iterating on existing code, preserve unrelated functionality
```

---

### Test Agent

**Role:** Write and execute unit tests for the generated code.

**Model:** Llama 3.1 70B (via Groq — fastest for test generation) — fallback: OpenRouter Llama

**Input state fields:** `file_tree`, `plan`

**Output state fields:** `test_results`, `tests_passed`

**Behaviour:**
1. Generate Vitest unit tests for each component and utility
2. Generate Playwright e2e tests for primary user flows
3. Run `npx vitest run` in E2B sandbox
4. Parse results into `test_results`
5. Set `tests_passed = True` if no failures; `False` triggers Code Agent retry

**Tools:** `e2b_write_files`, `e2b_run_command`

**Test coverage targets:**
- All exported functions in `lib/`
- All API route handlers (mocked DB)
- Critical user flows (auth, project create, generate, deploy)

**System prompt excerpt:**
```
You are the Test Agent. Write Vitest tests that actually catch bugs.
Rules:
- Test behaviour, not implementation
- One test file per source file
- Mock external services (AI providers, Stripe, E2B)
- No snapshot tests
- Cover edge cases and error paths
```

---

### Security Agent

**Role:** Scan generated code for vulnerabilities and auto-fix what it can.

**Model:** Mistral Small (via MistralAI) — fast, sufficient for fix suggestions

**Input state fields:** `file_tree`

**Output state fields:** `security_findings`, `security_cleared`

**Behaviour:**
1. Write files to E2B sandbox
2. Run `semgrep --config=auto --json` in sandbox
3. Parse findings by severity
4. For `medium` and `high` findings: generate LLM fix, apply to `file_tree`
5. For `critical` findings: set `security_cleared = False`, halt pipeline, notify user
6. Re-run Semgrep to verify fixes resolved the findings

**Severity thresholds:**
| Severity | Action |
|----------|--------|
| info | Log only, continue |
| low | Log only, continue |
| medium | Auto-fix, re-scan |
| high | Auto-fix, re-scan |
| critical | Halt, notify user |

**Tools:** `e2b_write_files`, `e2b_run_command`, `e2b_read_file`

---

### Deploy Agent

**Role:** Deploy the final file tree to Vercel and return a live URL.

**Model:** None — utility node, no LLM calls.

**Input state fields:** `file_tree`, `project_id`

**Output state fields:** `deployment_url`

**Behaviour:**
1. Create a Vercel deployment via API with the file tree
2. Poll deployment status until `READY` or `ERROR` (timeout: 120s)
3. On success: set `deployment_url`, save `Deployment` record to DB
4. On error: set `error`, mark deployment as `failed`

**Tools:** `vercel_deploy`, `vercel_get_status`

---

## WebSocket Streaming Schema

The frontend connects to `ws://.../ai/stream/{project_id}`. The pipeline emits events as each agent progresses.

```typescript
type AgentEvent =
  | { type: 'agent_start';    agent: AgentName; timestamp: string }
  | { type: 'agent_progress'; agent: AgentName; message: string; timestamp: string }
  | { type: 'agent_complete'; agent: AgentName; timestamp: string }
  | { type: 'agent_error';    agent: AgentName; error: string; timestamp: string }
  | { type: 'file_created';   path: string; timestamp: string }
  | { type: 'test_result';    file: string; passed: number; failed: number }
  | { type: 'security_finding'; severity: string; rule: string; file: string }
  | { type: 'pipeline_complete'; deployment_url: string; credits_used: number }
  | { type: 'pipeline_error';   error: string; credits_refunded: number }

type AgentName = 'plan' | 'code' | 'test' | 'security' | 'deploy'
```

---

## Error Handling and Retries

| Scenario | Behaviour |
|----------|-----------|
| Code Agent build fails | Retry with error context (max 2) |
| Test Agent failures | Re-run Code Agent with failing tests as context (counted in Code retries) |
| Security critical finding | Halt, refund credits, notify user via WebSocket |
| Provider rate limit | Switch to OpenRouter fallback, continue |
| E2B sandbox timeout (5min) | Emit error, refund credits |
| Any unhandled exception | Emit `pipeline_error`, full credit refund |

---

## RAG Context Injection

When enabled (Phase 2), the Plan Agent retrieves relevant context before generating:

```python
retriever = NeonVectorRetriever(
    collection="project_templates",
    k=3,
    score_threshold=0.7
)
context_docs = retriever.invoke(user_message)
# Injected into Plan Agent system prompt as additional context
```

RAG is off by default. Enable via `ENABLE_RAG=true` in backend env.

---

## Context Window Management

For large projects (> 50 files):
1. Summarize unchanged files into a compact manifest: `{ path: sha256_hash }`
2. Pass full content only for files the current agent needs to modify
3. Use the manifest to detect which files changed between agent runs
4. Never exceed 60% of the model's context window with file content
