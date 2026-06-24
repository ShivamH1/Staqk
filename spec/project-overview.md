# Project Overview

## What is Staqk?

Staqk is a security-first, multi-agent AI app builder. You describe what you want to build in plain language. Staqk's agent pipeline — Plan, Code, Test, Security, Deploy — turns it into a tested, scanned, deployed application.

Most AI builders get you to 60%. Staqk gets you to production.

---

## The "Final 40% Problem"

Current AI builders (Lovable, Bolt.new, v0, Replit) excel at generating a working prototype quickly. What they don't do:

- **Security scanning** — generated code ships with known vulnerabilities
- **Automated testing** — no unit or integration tests
- **Real deployment** — preview URLs, not production apps
- **Monitoring** — no error tracking, no observability
- **Technical debt** — generated code accumulates fast with no review pass

Staqk closes this gap with a mandatory pipeline: every build is tested, every deploy is scanned.

---

## Competitive Landscape

| | Staqk | Lovable | Bolt.new | v0 (Vercel) | Replit |
|--|-------|---------|----------|-------------|--------|
| Multi-agent pipeline | ✅ | ❌ | ❌ | ❌ | ❌ |
| Security scanning | ✅ | ❌ | ❌ | ❌ | ❌ |
| Auto-generated tests | ✅ | ❌ | ❌ | ❌ | Partial |
| Live deployment | ✅ | ✅ | ✅ | ✅ | ✅ |
| Transparent credit costs | ✅ | ❌ | ❌ | ❌ | ❌ |
| No vendor lock-in | ✅ | ❌ | ❌ | ✅ | ❌ |
| Custom tech stack selection | ✅ | Partial | Partial | ❌ | ❌ |

---

## Target Users (ICP)

**Primary:**
- **Indie hackers and solo founders** — want to ship fast without compromising on quality
- **Junior developers** — need guardrails (security, tests) they don't yet know to add themselves

**Secondary:**
- **Agencies** — rapid prototyping for client projects with handoff-ready code
- **Non-technical founders** — idea to MVP without a developer hire

---

## Key Differentiators

1. **Security pipeline** — Semgrep scans every build. Critical findings block deployment.
2. **Multi-agent transparency** — users see each agent's progress in real time (Plan → Code → Test → Security → Deploy)
3. **Tech stack flexibility** — choose your framework, not ours
4. **Transparent credits** — every operation has a stated cost before it runs
5. **No lock-in** — export your code at any time; it's yours

---

## Monetization

| Plan | Price | Included Credits | Users |
|------|-------|-----------------|-------|
| Free | $0 | 100/month | 1 |
| Starter | $19/month | 500/month | 1 |
| Pro | $49/month | 1,500/month | 1 |
| Team | $99/month | 5,000/month | Up to 5 |
| Enterprise | Custom | Custom | Unlimited |

**Credit costs:**
- Full pipeline run (Plan → Deploy): 5 credits
- Chat iteration: 2 credits
- Version restore: 1 credit
- Security re-scan: 1 credit

**Top-up packs:** 100 credits ($5), 500 credits ($20), 2,000 credits ($60)

---

## Phase Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | MVP — natural language → deployed app | In Progress |
| Phase 2 | Multi-agent pipeline, security, tests, GitHub sync | Planned |
| Phase 3 | Production-readiness: CI/CD, monitoring, RBAC, custom domains | Planned |
| Phase 4 | Enterprise: SSO, HIPAA, SOC 2, private AI, on-premise | Planned |

See [spec.md](spec.md) for per-feature breakdowns.

---

## North Star Metric

**Deployed production apps per month** — not projects created, not chat messages sent. A user is successful when their app is live.

---

## Current Status

Early MVP. Core generation and deployment flow working. Multi-agent pipeline in active development.

See [progress-tracker.md](progress-tracker.md) for week-by-week status.
