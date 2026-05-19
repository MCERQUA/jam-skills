# Open questions — milestone-4

9 collated questions for host@mesh. Numbered Q1–Q9. None blocks the v0.1.4 schema ship; all are tightening questions or downstream-policy questions.

---

## Notification cadence (worker-a)

**Q1 — `inline` firing scope.** Does `inline` fire only on `state="done"`, or also on intermediate transitions (`parked → today`, `in-flight → parked`)? Current draft: `done` only.

**Q2 — `on_finding_threshold.metric` ratchet timing.** Lock the metric vocabulary at v0.1.4 (now) or leave free-form until v0.2 (mirrors `failure_modes` v0.1→0.2 path)? Current draft: free-form.

**Q3 — Per-recipient-role override.** Should `recipient_role = "client"` force `mode = "roll_up_daily"` regardless of task setting? Current draft: policy honored as-written, writer agent owns discretion.

## Schedule semantics (worker-b)

**Q4 — Overdue-research behavior.** If `research_at` (explicit or computed) is in the past at cron fire-time: (a) fire research immediately and run execution as planned (accept < 60min gap), (b) skip research entirely, or (c) push `scheduled_at` forward? Current draft: (a).

**Q5 — `research_completed_at` field.** Add a top-level `research_completed_at` (ISO-Z or null) for O(1) "did research run?" checks, vs scanning `state_history`? Current draft: not added; `state_history` is canonical.

**Q6 — `DEFAULT_RESEARCH_LEAD_SECONDS` constant location.** Keep the 60-min default scheduler-side only, or also expose as a `task_schema.py` constant for downstream tools? Current draft: scheduler-side only — **but see synthesis §3b recommendation to expose it via `apply_defaults`.**

## Synthesis-level (josh-desktop)

**Q7 — Enum casing ratification.** Worker-a chose snake_case (`roll_up_daily`/`on_finding`) to match failure_modes v0.2. Worker-c used kebab-case per host-msg phrasing. Recommend snake_case. Confirm or override.

**Q8 — `apply_defaults` helper.** Synthesis recommends adding `task_schema.apply_defaults(record)` to materialize both defaults (worker-a + worker-b) at the schema layer. Approve, reject, or place elsewhere?

**Q9 — Worker-c fixup ownership.** Worker-c's smoke patch needs §3a casing + §3c shape alignment after Q7/Q8 land. Should worker-c handle the fixup pass, or should josh-desktop do it inline as part of synthesis?
