# Milestone-4 — `notification_policy` design

**Dispatch:** josh-desktop@mesh sub-task from host msg 2026-05-19-001.
**Worker:** worker-a@mesh.
**Target schema:** `2026-05-19-canonical-schema-v0.1.3/` → bumps to v0.1.4.
**Status:** ships with sensible defaults; Mike-input pending for threshold vocab.

---

## 1. Field shape

**Name:** `notification_policy`
**Cardinality:** ONE top-level field. The on-finding threshold lives **inside** the field as a nested object — single source of truth for "how does this task notify."
**Required:** **OPTIONAL.** Absent ⇒ reader treats as `{"mode": "roll_up_daily"}`. This preserves v0.1.3 record validity (no existing record gains a new required key).
**Reason for nesting (vs. two flat fields `notification_policy` + `notification_threshold`):** brief asks for "a field" (singular); threshold is conceptually subordinate to mode; embedding kills a cross-field invariant ("threshold only meaningful when mode=on_finding") that flat form would otherwise require.

### JSON-Schema fragment (Draft-07)

```json
"notification_policy": {
  "type": "object",
  "additionalProperties": false,
  "required": ["mode"],
  "description": "Milestone-4. Delivery cadence for task-completion notifications. Optional — absent = roll_up_daily.",
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["inline", "roll_up_daily", "on_finding"],
      "default": "roll_up_daily"
    },
    "on_finding_threshold": {
      "type": ["object", "null"],
      "default": null,
      "description": "Only meaningful when mode='on_finding'. Shape TBD pending Mike-input."
    }
  }
}
```

Enum strings are **snake_case, no aliases** per brief constraint — stable for future migrations (matches `failure_modes` v0.2 lock convention rather than `state` kebab-case).

---

## 2. Per-mode semantics — when each fires

| mode             | fires when…                                                                                       | recipient cadence              |
|------------------|---------------------------------------------------------------------------------------------------|--------------------------------|
| `inline`         | task transitions to `state="done"` (single shot)                                                  | reply immediately on done      |
| `roll_up_daily`  | next scheduled morning brief picks up all `done`-since-last-brief tasks                           | batched (DEFAULT)              |
| `on_finding`     | research-delta evaluator reports the task crossed `on_finding_threshold` (may fire 0+ times)      | event-driven, NOT done-bound   |

**Rule-1 still applies.** `inline` does NOT bypass `email_authorized_by_mike` — outbound writer gate is orthogonal to cadence.

**State interaction:** `roll_up_daily` and `inline` are tied to `done`. `on_finding` is decoupled from state and may fire while the task is still `in-flight` or `today`. Reaching `done` under `on_finding` does NOT auto-fire a notification; it's the threshold that decides.

---

## 3. `on_finding_threshold` — proposed shape (TBD until Mike-input)

```json
{
  "metric": "research_delta_score",
  "comparator": "gte",
  "value": 0.8,
  "cooldown_seconds": 3600
}
```

| key                | type     | purpose                                                                  | TBD-ness                                              |
|--------------------|----------|--------------------------------------------------------------------------|-------------------------------------------------------|
| `metric`           | string   | which signal to compare against (e.g. `research_delta_score`, `novelty`) | vocab unset — propose **free-form now**, enum-lock later (mirrors v0.1.2 → v0.2 `failure_modes` ratchet) |
| `comparator`       | enum     | `gte` / `gt` / `lte` / `lt`                                              | start with `gte` only; expand if needed               |
| `value`            | number   | threshold to compare against                                             | scale depends on `metric` — unitless until Mike-input |
| `cooldown_seconds` | int ≥ 0  | min seconds between firings for same task (anti-spam)                    | default proposal: 3600 (1h)                           |

**Validator behavior (v0.1.4):** accepts any `object` or `null` for `on_finding_threshold`. We deliberately do NOT enforce the inner shape yet — that's a v0.2 lock similar to how `failure_modes` ratcheted from free-form `list[str]` to a 21-value enum. This keeps the schema non-blocking while Mike's specifics land.

---

## 4. Interaction with `failure_modes` enum

**Short answer: no overlap. They live on orthogonal axes.**

- `failure_modes` is an **audit trail** of categorical incidents (`latency_budget_exceeded`, `silent_drift`, …) appended over the task's lifetime. Backward-looking. Used by the daily-improvement loop.
- `notification_policy` is a **delivery preference** for *outbound* signal to Mike/operator/client. Forward-looking. Used by the brief / inline writer / on-finding evaluator.

**Does `on_finding` cover failure events too?** **No** — by design.

- A failure event (e.g. `deadlock_on_missing_signal` appended to `failure_modes`) is surfaced through the **blocker.json escalation channel** (per src-desktop seam B), NOT through `notification_policy`. Conflating them would force every alert-fatigue-control tradeoff onto a single field.
- Concretely: a task with `notification_policy.mode = "on_finding"` that hits `failure_modes: ["latency_budget_exceeded"]` does **not** fire a notification on the failure alone — the blocker channel handles that. `on_finding` watches research-delta only.
- If Mike later wants failure events to fire under `on_finding`, the clean migration is a v0.2 threshold field like `{"trigger_on_failure_mode": [...]}` rather than overloading existing semantics.

---

## 5. Example `task.json` snippets — one per mode

### 5.1 `inline` — operator callback (Rule-1 outbound)

```json
{
  "id": "2026-05-18-1830-cca-followup-decking",
  "state": "scheduled",
  "summary": "Operator asked for callback re Seattle decking install timing",
  "tenant": "cca",
  "raised_by": "sms",
  "recipient_role": "operator",
  "operator_phone": "+14374559131",
  "notification_policy": {"mode": "inline"}
}
```

Inline because: operator-requested callback → reply on `done`, don't wait for morning batch.

### 5.2 `roll_up_daily` — intake from a vendor email (DEFAULT)

```json
{
  "id": "2026-05-18-0915-cca-domain-quote-acme",
  "state": "intake",
  "summary": "Acme Roofing asked for an updated domain + hosting quote",
  "tenant": "cca",
  "raised_by": "email",
  "recipient_role": null,
  "notification_policy": {"mode": "roll_up_daily"}
}
```

Could also be **omitted entirely** — readers default to `roll_up_daily`. Shown explicit here for the example.

### 5.3 `on_finding` — long-running research with delta threshold

```json
{
  "id": "2026-05-18-1411-kitchen-cabinets-upload",
  "state": "in-flight",
  "summary": "MP4 walkthrough of kitchen-cabinets job — Danielle canvas upload",
  "tenant": "danielle",
  "raised_by": "voice",
  "notification_policy": {
    "mode": "on_finding",
    "on_finding_threshold": {
      "metric": "research_delta_score",
      "comparator": "gte",
      "value": 0.8,
      "cooldown_seconds": 3600
    }
  }
}
```

Fires when the evaluator emits `research_delta_score ≥ 0.8` and at least 3600s have elapsed since the last firing for this task id.

---

## 6. Backward compatibility

- v0.1.3 records lacking `notification_policy` validate clean under v0.1.4 (field is not in `required[]`).
- v0.1.4 records carrying `notification_policy` are rejected by strict v0.1.3 readers (`additionalProperties: false`) — this is the expected one-direction breakage of schema evolution and is acceptable because all readers are updated lockstep at the v0.1.4 bump.
- The `notification_policy` field travels with the task across all states (`intake → … → done`). Intake adapters MAY populate; readers MUST default-on-absence.

---

## 7. Open questions to surface to host@mesh

> **For josh-desktop@mesh to forward — these block tightening but NOT shipping v0.1.4.**

**Q1 — `inline` firing scope.** Does `inline` fire only on `state="done"`, or also on intermediate transitions (`parked → today`, `in-flight → parked`)? Current draft = `done` only. Long-running `in-flight` tasks with operator-facing milestones may want a richer trigger set.

**Q2 — Should we ratchet `on_finding_threshold.metric` to an enum at v0.2?** Free-form string now follows the v0.1.2 `failure_modes` precedent (free → enum-locked once vocab settles). Asking Mike whether the metric vocabulary should be predetermined now (we lock at v0.1.4) or left open until we have field data (we lock at v0.2 like failure_modes did).

**Q3 — Per-recipient-role override.** Should `recipient_role = "client"` force `notification_policy.mode = "roll_up_daily"` regardless of task setting? Client-facing channels typically should not fire inline. If yes, this becomes a Rule-1-style cross-field invariant in v0.1.4. If no, the policy is honored as-written and the writer agent owns the discretion.

---

## 8. Out of scope (NOT in this deliverable)

- The brief mentioned "pydantic model update". `task_schema.py` is **not** a pydantic model — it's a hand-rolled dict-driven validator (`TASK_FIELDS` + `_check_type`). The patch matches the existing style. Flagging in case host expected a pydantic rewrite; if so, it's a separate task.
- Threshold-evaluator implementation. This deliverable defines the schema slot only; the on-finding evaluator service is a downstream concern.
- Migration script. No existing records need touching — they validate as-is under v0.1.4.
