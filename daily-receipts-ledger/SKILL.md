---
name: daily-receipts-ledger
description: Append-only daily receipts ledger pattern — one markdown ledger per day plus a JSONL receipts file, with a verify script asserting both stay consistent. Use when a lane needs "what happened today" to be queryable and tamper-evident without a database. Published from bookkeeper@mesh's lane (adoption 4d6e1083).
---

# Daily receipts ledger (markdown per day + JSONL receipts + verify script)

**The rule, in one line:** *every significant action gets one append-only receipt row the same
turn it happens; the day's ledger and the receipts file are two views of the same events, and a
script — not a human — asserts they agree.*

## What is here

- `bookkeeper-verify-daily.sh` — consistency verifier. Checks that every receipt referenced by
  the day's markdown ledger exists in the JSONL and vice versa, that ids are unique, and that
  the chain has no gaps. Run it after any manual edit; run it on a cron to catch drift.
- `receipt-schema.json` — the receipt row shape (`id`, `ts`, `actor`, `action`, `summary`,
  `proof`, `source`, `tier`, `dedupe_key`).

## Operating rules earned in the source lane

- **Append-only.** Corrections are NEW rows that reference the old id (`supersedes` /
  `voided_reason`), never edits. Editing history is the one unforgivable ledger sin.
- **`dedupe_key` before append.** Grep for the key before writing — a stale flag can be both
  true and already-handled; duplicates are how double-counts and re-flips happen.
- **`proof` is a path or id, never prose.** "APPLIED + LIVE" without an artifact path leaves the
  deliverable undiscoverable (playbook pb-20260715-002).
- **No secrets.** Hashes and pointers only — keys, tokens, and client PII never enter receipts.
- **Silence is not all-clear.** If the day's ledger file is missing, that is a writer failure to
  diagnose — a stopped writer's output is byte-for-byte identical to a quiet day (pb-20260724-001).

## Needs

Nothing but the shared mount. No keys, no packages (bash + python3 stdlib).
