---
upstream: https://docs.openclaw.ai/concepts/delegate-architecture.md
relevance: high
last-verified: 2026-05-04
audit_anchors: []
related_pages: [reference__templates__USER, reference__templates__SOUL, reference__templates__AGENTS]
---

# Delegate architecture — JamBot annotation

## What docs say (TL;DR)

Delegates = OpenClaw agents with their own identity acting on behalf of humans (never impersonating). Three tiers:

| Tier | Capabilities | Risk |
|------|--------------|------|
| 1: Read-Only + Draft | Read inbox/calendar/files; draft messages for human approval | Low |
| 2: Send on Behalf | Send emails, create calendar events under delegate identity with "on behalf of" headers | Medium |
| 3: Proactive | Autonomous scheduled operations via standing orders + cron | High — careful hardening required |

## Hard blocks (REQUIRED)

- Never send external emails without approval
- Never export sensitive data
- Never execute inbound commands
- Never modify identity settings

Tool restrictions enforced via per-agent policy (v2026.1.6+) at Gateway level, independent of agent instructions.

## Personality file split

| File | Purpose |
|------|---------|
| `AGENTS.md` | Role + standing orders |
| `SOUL.md` | Personality + hard blocks |
| `USER.md` | Principal info (whose delegate is this?) |

(JamBot already uses these files per Office system — consistent with delegate model.)

## Provider setup

### Microsoft 365

```powershell
Set-Mailbox -GrantSendOnBehalfTo
```

**CRITICAL warning:** application permissions grant "every mailbox access" without an access policy. Always create an Application Access Policy BEFORE granting `Mail.Read` permission. Otherwise you've handed full org-wide mail access.

### Google Workspace

Service account with **domain-wide delegation**, scoped to minimum required permissions only. **Leaked service account keys = full org access** — rotate on schedule.

## JamBot relevance — per-tenant filing cabinet

The Office system (`docs/jambot/office-system-overview.md`) is JamBot's analog: per-tenant Clerk-driven people/companies/matters files. Different model from OpenClaw's delegate-architecture (which is single-delegate-per-org), but same principle: agent has its own identity, never impersonates principal.

## Multi-org scaling

Multiple orgs share a Gateway via multi-agent routing with isolated agents/workspaces/credentials. JamBot's multi-tenant model maps cleanly:
- One delegate per JamBot client
- Isolated workspace per `/mnt/clients/<user>/openclaw/workspace/`
- Per-user auth via `auth-profiles.json` (NEVER shared)

## Audit trail locations

```
~/.openclaw/cron/runs/<jobId>.jsonl                       # cron run history
~/.openclaw/agents/delegate/sessions/                       # per-delegate session JSONL
~/.openclaw/agents/delegate/agent/auth-profiles.json        # delegate-specific creds (DO NOT SHARE)
```

## Sessions history filtering

Redacts credential/token-like text, truncates oversized content, strips thinking tags and tool-call XML from recall — separate concern from trajectory bundles (`tools/trajectory.md`).

## Routing

Multi-agent bindings route channels to specific delegate agents via `agentId` + `match` criteria — see `multi-agent.md` (Phase 2 annotation TODO).

## Could JamBot use a formal delegate?

For internal mail handling (e.g. agent reads Mike's gmail and drafts replies), Tier 1 makes sense. Currently this is handled outside OpenClaw via custom Gmail bridges. **Migration eval pending.**

## Related JamBot files

- `docs/jambot/office-system-overview.md` — JamBot's Office filing cabinet
- `docs/jambot/agent-repos-and-page-auth.md` — per-client auth model
- `/jambot-openclaw` skill — container + workspace isolation
