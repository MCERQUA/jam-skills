# Two-phase schedule design — milestone-4

**Author:** worker-b@mesh (submesh of josh-desktop@mesh)
**Date:** 2026-05-19
**Target schema:** canonical task.json v0.1.3 (`/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3/`)
**Bumps schema to:** v0.1.4 (additive, backward-compatible)
**Source spec:** host msg 2026-05-19-001 — separate research-run cron from execution-run cron; DEFAULT `research_at = scheduled_at - 60min`.

---

## 1. Home: top-level sibling field. NOT a sub-object. NOT a separate file.

**Decision:** add `research_at` as a top-level optional property on task.json, immediately adjacent to the existing `scheduled_at`.

**Rejected alternatives:**

| Option | Why rejected |
|---|---|
| `schedule: {research_at, scheduled_at}` sub-object | Would force a breaking move of `scheduled_at` out of the root. v0.1.3 readers (intake adapter, smoke-test, voice-active, seam-a-poc, tenant-scaffolder — 7 deployed snapshots per CHANGELOG-v0.1.3.md §"Downstream snapshots") all read `record["scheduled_at"]` at the root. A sub-object move violates the "do not break v0.1.3 readers" constraint. |
| `schedule.json` sibling file | Splits a single task across two files — adds I/O sync risk, contradicts Rule 8 (single source of truth at task.json). State-mismatch ("filed in tasks/scheduled/ but research_at says still researching") becomes a second-class invariant we'd have to police. Cron template would also have to atomically read+write both files, doubling lock surface (lock_required is per-task). |
| Top-level sibling (chosen) | Smallest diff. `scheduled_at` stays where it is. New field is optional. v0.1.3 readers that ignore `research_at` continue to validate. JSON Schema `additionalProperties: false` requires us to register the field in `properties{}`, but that's still a pure addition — no behavior change for any field already in v0.1.3. |

**Match with Rule 8 / Rule 7:** Rule 8's `dedup_hash`, `linked_to` and Rule 7's `recipient_role` all sit as flat top-level fields. `research_at` follows the same shape.

---

## 2. Exact field shape: ISO-8601 UTC ending in `Z`. Not cron-expr. Not both.

```json
"research_at": {
  "type": ["string", "null"],
  "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
  "description": "Moment the planning/research run fires. Sibling of scheduled_at. Optional; defaults to scheduled_at - 60min when null and scheduled_at is set (resolved by the scheduler, not the schema)."
}
```

Reasons not cron-expr:
- task.json is a **per-task record**, not a recurring rule. Even when a task is recurring, the next instance gets a fresh task.json with its own `scheduled_at` — the cron-expr lives on the scheduler side, not the task side.
- All existing time fields (`raised_at`, `scheduled_at`, `parked_until`, `completed_at`, `state_history[].at`, `email_authorized_by_mike`) are ISO-Z. Mixing shapes here would break Rule 8's lockstep.

Reasons not both:
- Two shapes → two parsers downstream → drift surface. The scheduler reads ISO-Z; the cron-expr lives in the **cron template** (separate file, this snapshot).

---

## 3. Default-resolution rule

**Rule:** if `research_at` is `null` (or absent) AND `scheduled_at` is set, the **scheduler** computes the effective research moment as `scheduled_at − 60min` at fire-time. The field in the file stays `null` — defaults are never frozen into the record.

**Why scheduler-side, not schema-side:**
- Schema-side defaults would force every task.json writer to materialize the value, which means every intake adapter has to know about the 60-min rule — that's coupling that doesn't belong in intake.
- Scheduler-side keeps the rule in one place (the cron template). If the default changes from 60min to 90min, one file edit.
- Round-tripping is clean: `validate → write → read → validate` doesn't mutate any record.

**Edge cases:**

| Case | Effective `research_at` |
|---|---|
| `research_at` explicit, `scheduled_at` set | `research_at` (explicit wins) |
| `research_at` null, `scheduled_at` set | `scheduled_at − 60min` |
| `research_at` null, `scheduled_at` null | **no research phase** (task isn't scheduled yet) |
| `research_at` set, `scheduled_at` null | **research-only task** (allowed, but cron template emits a warning — research without follow-up execution is unusual) |
| `research_at` is in the past at fire-time (overdue/backfill) | scheduler fires research **immediately** if `state != done` and `state != parked`; otherwise skips. See open question 1. |
| `scheduled_at − 60min` is in the past at the moment `scheduled_at` is set | scheduler fires research immediately on next cron tick. |

---

## 4. "Research blocker found" semantics

A research-run that surfaces a blocker has **three signals to set** and **one to NOT touch**:

**Set:**
1. **`failure_modes`** — append the relevant enum value. Common ones for research blockers (from the v0.2 21-value enum):
   - `blocker_source_split_brain` — research found conflicting sources
   - `deadlock_on_missing_signal` — research found upstream prerequisite not met
   - `permission_drift_breaks_protocol_channel` — research found auth/permission missing
   - `outbound_recipient_drift` — research found `recipient` is wrong (Rule 7)
   - `latency_budget_exceeded` — research itself ran over budget
2. **`state`** → `parked`, with `parked_until` set to either:
   - a concrete unblock-by ISO-Z if the blocker has a known time-bound (e.g. "wait for Mike's ack by EOD"), OR
   - a far-future sentinel `9999-12-31T00:00:00Z` if the blocker has no clock (mesh convention per `parked_without_clock` failure mode — but here we PREVENT that failure mode by always setting *some* value).
3. **`state_history`** — append `{state: "parked", at: <now>, by: <research-agent-uri>}`.

**Do NOT touch:**
- `scheduled_at` is **NOT cleared**. The intent (when execution would have fired) is preserved for the audit trail and for easy un-parking once the blocker resolves.

**Execution-run interaction:**
- When the execution cron fires at `scheduled_at`, it **MUST** re-read task.json first and check `state`. If `state == "parked"`, execution **aborts** with `outbound_recipient_drift`-style alert to the task's `recipient_role` party and a mesh-send to mike-voice@mesh subject `EXECUTION SKIPPED — task <id> parked by research`.
- This is **abort + alert**, not cancel — the task isn't deleted, just bounced for human triage. Mike (or whoever owns `recipient_role`) decides to un-park or close.

**Alert routing (Rule 7):**
- Blocker alerts route to `recipient_role`. If `recipient_role` is `mike` or `null`, alert goes to mike-voice@mesh. If `operator`, to the tenant's operator channel. If `client`, do **not** alert the client (clients don't see research-phase output); fall through to mike. If `other`, fall through to mike with a `recipient_role=other` annotation in the alert body.

---

## 5. Interaction with existing `scheduled_for` / migration path

**There is no `scheduled_for` field in v0.1.3.** The canonical field is `scheduled_at` (root-level, ISO-Z, present since v0.1; confirmed by direct read of `task-json-schema.json` lines 73–76 and `task_schema.py` line 111). The spec mentions `scheduled_for` defensively ("if any") — confirmed absent.

**Migration path is therefore null:** v0.1.3 → v0.1.4 is **additive only**. Three changes total:

1. `task-json-schema.json` — add `research_at` to `properties{}`. No change to `required[]`, no change to `allOf[]`.
2. `task_schema.py` — add `"research_at": ("optional", "iso_z_or_null")` to `TASK_FIELDS`. Add new `"optional"` branch to `_required()` returning `False`.
3. `canonical-task.examples.json` — update examples to demonstrate both phases.

**Backward compatibility check (per v0.1.3 CHANGELOG verification block §F):**
- Every existing v0.1.3 task.json (with `research_at` absent) validates clean under v0.1.4. The unknown-field check is unchanged (`research_at` is now a known field); the required check is unchanged (`research_at` is never required); the type check only runs when the field is present.
- Every v0.1.4 task.json (with `research_at` set) **fails** v0.1.3 readers' `additionalProperties: false` check — readers will see "unknown field: research_at". This is the only forward-incompatibility, and it's load-bearing: a v0.1.3 reader processing a v0.1.4 record would silently lose the research-phase information without it. **Recommend host bumps the schema reference in the 7 downstream deployed snapshots to v0.1.4 in lockstep before any cron template starts populating `research_at`.**

---

## 6. Three open questions for host@mesh

1. **Overdue-research behavior.** If `research_at` (explicit or computed) is in the past at cron fire-time — e.g. a task created with `scheduled_at = now + 30min` so the default `research_at` is already 30min in the past — should the scheduler:
   - (a) fire research immediately and run execution at `scheduled_at` as planned, accepting a < 60min gap, OR
   - (b) skip research entirely (treat the gap as "no time to plan") and fire execution only, OR
   - (c) push `scheduled_at` forward so the 60-min gap is preserved?
   Worker-b's draft template implements **(a)** because it preserves the principle "research before execution" without re-writing `scheduled_at` (which the schema treats as immutable post-`scheduled` state). Confirm or override.

2. **Research-completion field.** Should v0.1.4 also add a `research_completed_at` (ISO-Z or null) so the execution-run cron has an O(1) check for "did research actually run?" instead of scanning `state_history` for a `planned` entry by the research agent? Worker-b deferred adding it — `state_history` already encodes this — but the perf/clarity tradeoff is non-obvious if `state_history` grows large. Specifically: should execution-run **require** a research-completion signal, or is "state != parked" sufficient?

3. **Default delta as schema constant vs. scheduler config.** The 60-min default lives in the cron template (this snapshot). Should it ALSO live as a documented constant somewhere readable from `task_schema.py` (e.g. `DEFAULT_RESEARCH_LEAD_SECONDS = 3600`) so downstream tools that pre-compute or display the effective `research_at` agree with the scheduler? Or is leaving it scheduler-side intentional (different schedulers may want different defaults)? Worker-b's draft keeps it scheduler-side only.

---

## 7. Files in this deliverable

- `SCHEDULE-DESIGN.md` — this doc.
- `task-json-schema.patch` — unified diff for `task-json-schema.json`.
- `task_schema.patch` — unified diff for `task_schema.py`.
- `canonical-task.examples.patch` — unified diff for `canonical-task.examples.json`.
- `cron-template.sh` — runnable bash template; designed for host@mesh OS crontab (the existing host-side scheduler per `cron-landscape-2026-05-19.md` §1a). Uses `mesh-send`, `mesh-ack`, `agentmail` bridge per audited CLIs.
- `DONE.txt` — completion marker for josh-desktop polling.
