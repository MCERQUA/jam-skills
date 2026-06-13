---
name: task-system
description: Canonical task pipeline for JamBot tenants. Per-tenant tasks/{intake,shop-floor,planned,scheduled,today,done,in-flight,parked}/ skeleton with task.json schema, scaffolder, voice-active AND-gate for lock-and-defer, and E2E smoke test. Use when creating, transitioning, or executing any task in a tenant workspace.
---

# Task System v0.1.1

Deployed 2026-05-18 from josh-desktop@mesh's verified bundle. Full spec: `/home/mike/MIKE-AI/docs/jambot/task-system.md` (host) and `/mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md` (mesh).

## Modules

| Module | Path | Use |
|---|---|---|
| schema | `/mnt/shared-skills/task-system/schema/` | `task_schema.py` validator + `task-json-schema.json` Draft-07 + examples |
| scaffold | `/mnt/shared-skills/task-system/scaffold/` | `scaffold_tenant.py` — idempotent 8-state directory skeleton |
| voice-active | `/mnt/shared-skills/task-system/voice-active/` | AND-gate predicate (Clerk cookie + OVU heartbeat). Reader only — writers ship separately. |
| smoke-test | `/mnt/shared-skills/task-system/smoke-test/` | `smoke_test.py` E2E harness. Run after scaffold to verify tenant install. |

## Quick checks

```bash
# Validate a task.json
python3 /mnt/shared-skills/task-system/schema/task_schema.py /path/to/task.json

# Scaffold a tenant
python3 /mnt/shared-skills/task-system/scaffold/scaffold_tenant.py /home/node/.openclaw/workspace/tasks

# Read voice-active state (AND-gate)
python3 /mnt/shared-skills/task-system/voice-active/voice_active.py --debug

# Run E2E smoke against a tenant
python3 /mnt/shared-skills/task-system/smoke-test/smoke_test.py
```

## Task Completion — MANDATORY (every agent, every finished task)

When you finish a task, you MUST close it through the ONE canonical helper — this
is what makes completed work visible to the operator and the fleet roll-up. Do
NOT hand-move files or hand-write receipts.

```bash
python3 /mnt/shared-skills/task-system/complete_task.py \
  --workspace /home/node/.openclaw/workspace \
  --task-id <YYYY-MM-DD-HHMM-slug> \
  --by <your-agent-uri> \
  --summary "<one line: what got delivered>" \
  --postmortem "<what happened / how>"
```

- **task-agent** (desktop/mesh): completes from `today` → `done`  (`--by <name>-desktop@mesh`)
- **voice-agent**: completes from `in-flight` → `done`  (`--by <name>ai@voice`)

The helper does three writes in one call (do not replicate them yourself):
1. moves `task.json` → `tasks/done/` with `postmortem.md` + `state_history` + `completed_at`/`outcome`, matrix-validated;
2. a `work-done` row into your daily ledger (`ledger/<date>.md`);
3. a `kind:task-done` receipt → the bookkeeper roll-up (`DONE.md`), tagged `📦 task-done` — distinct from git-commit churn.

A task must reach `today` or `in-flight` first (matrix rule); `done` is terminal.
**Do NOT edit `complete_task.py`** — it is the fleet-wide canonical contract. Flag
bugs to `host@mesh`.

## Rules enforced (Rule 1-8 of the spec)

See `/home/mike/MIKE-AI/docs/jambot/task-system.md` section 1. Schema is **v0.1.4**
(ratified): Rule 8 fields (`dedup_hash`, `recipient_role`, `linked_to`) are
**REQUIRED**; `failure_modes` 21-value enum required since v0.1.3;
`notification_policy` + two-phase schedule added v0.1.4.

## Build owner

josh-desktop@mesh under the hybrid handoff protocol. Spec evolution + new milestones come from josh's sub-mesh (worker-a/b/c). Host (mike-ai) does the deploy and per-tenant rollout.
