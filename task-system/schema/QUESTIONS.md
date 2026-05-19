# Open questions / tentative choices in this snapshot

Document of choices I made where the inputs were ambiguous or silent. Proceeded
under each tentative interpretation rather than blocking the deliverable.

---

## 1. `email` as a `raised_by` value

**v0.1 §3** lists `raised_by: "voice|mesh|brief|manual|sms"` — no `email`.
**Rule 7** (folded into the Rule 8 amendment, PENDING_HOST_CONFIRM) names
"email" as a first-class channel ("All inbound (email, SMS, voice, mesh,
manual) writes task.json to intake/"). The brief I'm executing also asks
explicitly for an email-origin example.

**Tentative choice:** add `"email"` to `SOURCES` now (alongside the existing
five). If `email` ends up split between `email-inbound` and `gmail-thread`
or similar finer-grained tags in v0.2, the enum is a one-line change.

**Risk if wrong:** intake adapters writing `raised_by: "email"` validate
under v0.1.1 but would fail under a stricter future enum — handful of
records to migrate, low cost.

---

## 2. `recipient_role` value `null` in JSON Schema enum

The Python validator allows `recipient_role` to be `null` (PENDING field).
The JSON Schema represents this as `"type": ["string", "null"], "enum":
["mike","operator","client","other", null]`. Draft-07 permits `null` in an
`enum` provided `type` includes `"null"`, so this should be portable, but
some validators (notably older Ajv) historically choked on `null` enums.

**Tentative choice:** leave the schema literal; Python validator is the
source of truth. Downstream JS validators on modern Ajv (>= v7) handle this
correctly.

---

## 3. `state_history` ordering / append-only enforcement

bun-desktop's input says "append-only audit trail" but doesn't specify
whether the validator should enforce monotonic-time ordering or whitelist
specific state transitions.

**Tentative choice:** validator only checks shape (`{state, at, by}` with
right types). Ordering / legality of the transition graph is a separate
concern for the state-machine PoC owner (src-desktop seam B). Schema
catches obvious garbage; semantic legality is downstream.

---

## 4. `failure_modes` value vocabulary

src-desktop input says "host accepted on 2026-05-18 per AND-gate thread"
but I didn't track down the AND-gate thread to extract a canonical list
of `failure_mode` strings (e.g. `timeout`, `auth-blocked`,
`captcha-required`, ...).

**Tentative choice:** allow `list[str]` free-form. Once the AND-gate
thread settles a vocabulary, swap the type check to an enum and ratchet.

---

## 5. `defer_count` upper bound

src-desktop didn't bound it. A pathological lock-and-defer loop could
spin defer_count arbitrarily high.

**Tentative choice:** non-negative int, no upper bound. Daily-improvement
loop is supposed to surface high counts as a signal (per src), not the
validator.

---

If host@mesh / Mike see anything in this list worth tightening, the
schema is one file (`task_schema.py`) plus its mirror in
`task-json-schema.json`. Schema bump = re-snapshot under
`/agent-desk/snapshots/<date>-canonical-schema-vNNN/`.
