# OpenSpec Guide

## What is OpenSpec?

OpenSpec (fission-ai/openspec) is a Spec-Driven Development (SDD) methodology for AI coding assistants. Instead of feeding requirements through chat, you write a lightweight specification first. The AI then implements against the agreed spec — not against what it thinks you meant.

This solves the core problem with AI-assisted development: **drift**. Without a spec, the AI implements the most recent message's interpretation. With a spec, every implementation is anchored to an agreed contract.

---

## The SDD Workflow

```
1. PROPOSE  → describe the feature, get a spec draft
2. REVIEW   → read and edit the spec until it's right
3. IMPLEMENT → AI implements from the agreed spec
4. ARCHIVE  → mark spec complete, update if behaviour changes
```

These map to OpenSpec commands:

```bash
/opsx:propose <feature-name>     # creates specs/<feature-name>/
/opsx:implement <feature-name>   # AI reads spec, implements
/opsx:archive <feature-name>     # marks spec done
```

---

## Spec Folder Structure

Every feature gets its own folder under `/specs/`:

```
specs/
└── <feature-name>/
    ├── proposal.md    # What and why
    ├── specs/
    │   ├── requirements.md   # What it must do
    │   └── scenarios.md      # Concrete user scenarios
    ├── design.md      # How it will be built (technical approach)
    └── tasks.md       # Implementation checklist
```

---

## Spec File Templates

### `proposal.md`

```markdown
# Proposal: <Feature Name>

## Problem
What user problem does this solve?

## Solution
One paragraph describing the approach.

## Out of scope
What this feature deliberately does NOT do.

## Success criteria
How do we know it's working?
```

### `specs/requirements.md`

```markdown
# Requirements: <Feature Name>

## Functional requirements
- FR-01: The system must...
- FR-02: When the user...

## Non-functional requirements
- NFR-01: Response time under X ms
- NFR-02: Credit cost: N credits per operation

## Constraints
- Must work within existing auth flow
- Must not break existing project list
```

### `specs/scenarios.md`

```markdown
# Scenarios: <Feature Name>

## Happy path
Given: user has an active project
When: user clicks "Run Security Scan"
Then: scan starts, progress appears in real time, results shown with severity badges

## Edge cases
Given: user has 0 credits
When: user attempts to start scan
Then: 402 modal shown, no scan starts, no credits deducted

## Error cases
Given: E2B sandbox times out
When: security scan is running
Then: error message shown, credits fully refunded
```

### `design.md`

```markdown
# Design: <Feature Name>

## Architecture
Which files change, which new files are created.

## Data model changes
Any new DB tables, columns, or relations.

## API changes
New or modified endpoints.

## Frontend changes
New components, state changes, routes.

## Agent changes (if AI pipeline involved)
Which agents are affected, how state schema changes.

## Open questions
Unresolved decisions that need answering before implementation.
```

### `tasks.md`

```markdown
# Tasks: <Feature Name>

## Backend
- [ ] Add `SecurityScan` model to `app/models/security.py`
- [ ] Add `POST /projects/{id}/scan` route
- [ ] Implement `security_agent.py` LangGraph node
- [ ] Write pytest tests for scan route

## Frontend
- [ ] Add `SecurityPanel` component to workspace
- [ ] Add WebSocket handler for `security_finding` events
- [ ] Add scan button to workspace header

## Done
- [x] Design doc approved
```

---

## When to Write a Spec

**Always write a spec for:**
- Any new user-facing feature
- Any change to the database schema
- Any change to the AI pipeline (new agent, new model routing, state schema change)
- Any API contract change (new endpoint, modified response shape)
- Any refactor that touches more than 3 files

**Skip the spec for:**
- Bug fixes (just fix it, reference the failing behaviour in the commit)
- Copy/label changes
- Style tweaks within an existing component
- Dependency updates

---

## Rules for AI Coding Assistants

When implementing a feature that has a spec:

1. **Read the spec first** — `specs/<feature-name>/design.md` and `specs/<feature-name>/specs/requirements.md` before writing any code
2. **Follow the design** — implement what the design doc says, not what seems logical from the existing code
3. **Check the task list** — only implement tasks listed in `tasks.md`; do not add scope
4. **Flag open questions** — if `design.md` has unresolved open questions, ask before implementing that part
5. **Update tasks.md** — check off tasks as they are completed

---

## Referencing Specs in Commits and PRs

In commit messages:
```
feat(security): add semgrep scan to agent pipeline

Implements specs/security-scanning/tasks.md — backend tasks complete.
```

In PR descriptions, link to the spec folder so reviewers can check implementation against the contract.

---

## Archiving

When a feature is fully shipped, run `/opsx:archive <feature-name>`. This:
- Marks `tasks.md` as complete
- Moves the folder to `specs/archived/<feature-name>/`
- Keeps the spec as a historical record

Archived specs are useful when revisiting a feature — they show what was originally agreed and why.
