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

## Rules enforced (Rule 1-8 of the spec)

See `/home/mike/MIKE-AI/docs/jambot/task-system.md` section 1. Rule 8 fields (`dedup_hash`, `recipient_role`, `linked_to`) are PENDING — currently optional in validator. Will be required in v0.1.2 once host ratifies.

## Build owner

josh-desktop@mesh under the hybrid handoff protocol. Spec evolution + new milestones come from josh's sub-mesh (worker-a/b/c). Host (mike-ai) does the deploy and per-tenant rollout.
