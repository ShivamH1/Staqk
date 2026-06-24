# Feature Specifications

Status key: ✅ Done | 🔄 In Progress | 🔲 Not Started | 🔴 Blocked

---

## Phase 1: MVP

### F-01 — User Authentication

**Status:** ✅ Done

**User story:** As a new visitor, I want to sign up and sign in so I can access my projects.

**Acceptance criteria:**
- Sign up with email/password and social OAuth (Google, GitHub)
- Clerk handles all auth UI and session management
- On first sign-up, Clerk webhook creates a User record in Neon with 100 free credits
- JWT token is validated by FastAPI `ClerkJWTMiddleware` on every protected route
- Unauthenticated requests to protected routes return 401

**Technical notes:** Clerk Python SDK for JWT validation. Webhook at `POST /auth/webhook`.

---

### F-02 — Natural Language Project Generation

**Status:** 🔄 In Progress

**User story:** As a user, I want to describe what I want to build in plain English and get a working app.

**Acceptance criteria:**
- Input field accepts free-form natural language
- Plan Agent generates architecture JSON with components, routes, DB schema
- User sees the plan before code generation starts (confirmation step)
- 5 credits deducted atomically when pipeline starts
- Credits refunded in full if pipeline errors before completing

**Technical notes:** Plan Agent uses Gemini Flash 1.5. WebSocket at `ws://.../ai/stream/{project_id}`.

---

### F-03 — Tech Stack Selection

**Status:** 🔲 Not Started

**User story:** As a user, I want to choose my tech stack before generating so the output matches what I know.

**Acceptance criteria:**
- User selects from: framework (Next.js, React + Vite, SvelteKit), language (TypeScript, JavaScript), database (Neon/Postgres, none), styling (Tailwind, CSS modules)
- Selection is stored in `WebsiteProject.tech_stack` (JSONB)
- Plan Agent receives the tech stack and constrains output accordingly
- Default stack: Next.js + TypeScript + Tailwind (no database)

**Technical notes:** `POST /projects` body includes `tech_stack` field validated by Pydantic schema.

---

### F-04 — Multi-File Code Generation

**Status:** 🔄 In Progress

**User story:** As a user, I want the AI to generate all the files my project needs, not just a single file.

**Acceptance criteria:**
- Code Agent generates a complete file tree (all components, routes, config, package.json)
- Files are stored in `WebsiteProject.file_tree` as `{ path: content }` JSONB
- Build is verified in E2B sandbox before proceeding
- If build fails, Code Agent retries with error context (max 2 retries)
- All generated code passes TypeScript strict mode

**Technical notes:** Code Agent uses Mistral Large. E2B Python SDK for sandbox.

---

### F-05 — File Tree and Monaco Editor

**Status:** ✅ Done

**User story:** As a user, I want to browse and edit the generated files directly.

**Acceptance criteria:**
- File tree shows all generated files with folder structure
- Clicking a file opens it in Monaco editor
- Changes in Monaco are saved to local state immediately
- "Save" pushes changes to the backend and triggers a new version
- Monaco uses JetBrains Mono font and Staqk dark theme

**Technical notes:** Monaco Editor React wrapper. File changes debounced 500ms before save.

---

### F-06 — Live Preview

**Status:** ✅ Done

**User story:** As a user, I want to see my app running alongside the editor.

**Acceptance criteria:**
- Preview iframe shows the running app from E2B sandbox
- Preview refreshes automatically when files are saved
- Preview panel is resizable
- Preview shows a loading state while sandbox spins up

**Technical notes:** E2B sandbox serves the app on a temp URL. Preview pane embeds via iframe.

---

### F-07 — Chat Iteration

**Status:** 🔄 In Progress

**User story:** As a user, I want to describe changes in chat and have the AI update my app.

**Acceptance criteria:**
- Chat panel accepts follow-up instructions
- Chat iteration re-enters the pipeline at the Code Agent (skips Plan Agent)
- 2 credits per chat iteration
- Conversation history is preserved in the `Conversation` table
- Changes are diffed and only modified files are re-generated

**Technical notes:** `POST /ai/iterate` endpoint. LangGraph re-enters at `code_node` with existing `file_tree` in state.

---

### F-08 — Version History

**Status:** ✅ Done

**User story:** As a user, I want to restore a previous version of my project if something goes wrong.

**Acceptance criteria:**
- Every successful pipeline run saves a `Version` snapshot of the full file tree
- Version list shows timestamp and triggering message
- Restoring a version replaces the current file tree and creates a new version entry
- 1 credit to restore a version

**Technical notes:** `Version.snapshot` is the full `file_tree` JSONB. `GET /projects/{id}/versions`, `POST /projects/{id}/versions/{version_id}/restore`.

---

### F-09 — Stripe Credits and Billing

**Status:** 🔲 Not Started

**User story:** As a user, I want to purchase credits and manage my billing.

**Acceptance criteria:**
- Credits balance visible in header at all times
- "Buy credits" opens Stripe Checkout session
- Stripe webhook credits the user's account on successful payment
- Transaction history shows purchases and spends
- Insufficient credits shows 402 modal with direct link to purchase

**Technical notes:** `POST /payments/checkout` creates Stripe session. Webhook at `POST /payments/webhook` handles `checkout.session.completed`.

---

### F-10 — Vercel Deployment

**Status:** 🔲 Not Started

**User story:** As a user, I want to deploy my app to a live URL with one click.

**Acceptance criteria:**
- "Deploy" button triggers the Deploy Agent
- Deployment status shown in real time via WebSocket
- Live URL displayed on success and persisted to `Deployment` table
- Failed deployments show Vercel error output
- Deployment is blocked if Security Agent found critical findings

**Technical notes:** Deploy Agent uses Vercel REST API. Polls deployment status until `READY` or `ERROR` (120s timeout).

---

### F-11 — Security Scanning

**Status:** 🔲 Not Started

**User story:** As a user, I want my generated code automatically scanned for vulnerabilities before it deploys.

**Acceptance criteria:**
- Security Agent runs Semgrep on every build before deployment
- Findings displayed with severity, file, line, and rule name
- Medium/high findings are auto-fixed and shown as diffs
- Critical findings block deployment with explanation
- Scan results persisted to `SecurityScan` table

**Technical notes:** Semgrep runs in E2B sandbox via Python SDK. Mistral Small generates fix suggestions.

---

### F-12 — Neon DB Provisioning

**Status:** 🔲 Not Started

**User story:** As a user, I want to add a database to my project without manual setup.

**Acceptance criteria:**
- User selects "Neon/Postgres" in tech stack selection
- Plan Agent includes DB schema in the plan
- Code Agent generates Drizzle ORM models and migration files
- A Neon project is provisioned via API and the connection URL injected into the deployment environment

**Technical notes:** Neon Management API for project creation. Requires `NEON_API_KEY` in backend env.

---

## Phase 2: Core Platform

### F-13 — Multi-Agent Pipeline UI

**Status:** 🔲 Not Started

**User story:** As a user, I want to see each agent's progress in real time so I know what's happening.

**Acceptance criteria:**
- Pipeline progress bar shows 5 steps: Plan → Code → Test → Security → Deploy
- Each step shows: pending / running (with spinner) / complete / error state
- Clicking a complete step shows its output (plan JSON, test results, security findings)
- Agent log stream visible in a collapsible panel

---

### F-14 — GitHub Sync

**Status:** 🔲 Not Started

**User story:** As a user, I want my project synced to a GitHub repository.

**Acceptance criteria:**
- "Connect GitHub" flow using GitHub App OAuth
- On deploy: creates/updates a GitHub repo with the current file tree
- Commit message includes the triggering user prompt
- Branch: `main` for deploys, `staqk/iteration-{n}` for chat iterations

---

### F-15 — Custom Domains

**Status:** 🔲 Not Started

**User story:** As a user, I want to use my own domain for deployed apps.

**Acceptance criteria:**
- User enters a custom domain in project settings
- Staqk adds the domain to Vercel via API
- DNS instructions shown for CNAME setup
- SSL certificate provisioned automatically

---

### F-16 — Template Library

**Status:** 🔲 Not Started

**User story:** As a user, I want to start from a template instead of building from scratch.

**Acceptance criteria:**
- Template gallery on dashboard with categories (SaaS, landing page, dashboard, API)
- Each template has a preview screenshot and description
- Selecting a template pre-populates tech stack and generates from a known-good base
- Templates available via `GET /public/templates`

---

### F-17 — AI Cost Tracking

**Status:** 🔲 Not Started

**User story:** As a user, I want to see how many tokens and credits each operation used.

**Acceptance criteria:**
- `AIUsageLog` records every LLM call with provider, model, tokens, and credits
- Usage breakdown visible in account settings
- Per-project cost visible in project settings
- Monthly credit spend chart in billing dashboard

---

## Phase 3: Production-Ready

| ID | Feature | Status |
|----|---------|--------|
| F-18 | Staging environments (separate preview URL before promoting to production) | 🔲 |
| F-19 | CI/CD — auto-redeploy on GitHub push | 🔲 |
| F-20 | Error monitoring — Sentry integration in generated apps | 🔲 |
| F-21 | Performance budgets — Lighthouse scores shown post-deploy | 🔲 |
| F-22 | Accessibility scan — axe-core checks in Test Agent | 🔲 |
| F-23 | API documentation — auto-generate OpenAPI docs for generated backends | 🔲 |
| F-24 | Database migrations — Alembic migration files generated alongside schema changes | 🔲 |
| F-25 | RBAC — role-based access for Team plan projects | 🔲 |
| F-26 | Audit logs — who changed what, when | 🔲 |
| F-27 | Code export — download full project as zip | 🔲 |
| F-28 | Mobile preview — responsive preview at 375px and 768px | 🔲 |

---

## Phase 4: Enterprise

| ID | Feature | Status |
|----|---------|--------|
| F-29 | SSO (SAML/OIDC via Clerk Organizations) | 🔲 |
| F-30 | HIPAA compliance mode | 🔲 |
| F-31 | SOC 2 Type II compliance | 🔲 |
| F-32 | Private AI — run models on customer's own infrastructure | 🔲 |
| F-33 | Fine-tuning — custom models trained on company codebase | 🔲 |
| F-34 | Enterprise SLA (99.9% uptime guarantee) | 🔲 |
| F-35 | On-premise deployment | 🔲 |
