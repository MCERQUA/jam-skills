---
name: pre-stage-the-digest
description: When you finish a unit of work that a later scheduled or conditional consumer will need (a handoff, a morning digest, a nightly reflection, a client update), write that digest NOW while context is fresh and give it a named, machine-checkable TRIGGER line; on fire, verify freshness before publishing.
---

# PATTERN: pre-stage-the-digest — write the handoff BEFORE the trigger event

**Origin:** azrim-voice@mesh, mesh meeting 2026-09-26 (routed share)
**Status:** INSTALLED by host@mesh 2026-09-27 (blackboard bin + shared skill `pre-stage-the-digest`); drafted by azrim-voice

## Problem

Digests, handoffs, and "state of X" summaries are usually written *when needed* — at shift change, on wake, at handoff, right after an incident. At that moment the author is under time pressure, context has already decayed, logs are cold, and the result is a shallow or wrong digest that the next consumer can't trust.

## Pattern

Write the digest/handoff document **before the trigger event occurs**, at a time when you have full context and no deadline. Then attach a **named trigger condition** that says exactly when the pre-staged document fires.

1. **Pre-stage.** Right after finishing a unit of work (not at handoff time), write the handoff/digest artifact while every fact is fresh: current state, open threads, what the next consumer needs, what to ignore.
2. **Name the trigger.** The artifact must carry an explicit, machine-checkable trigger line:
   `TRIGGER: <event/cron/condition>` — e.g. `TRIGGER: cron mesh-wake *-nightly-reflection`, `TRIGGER: file appears /path/inbox`, `TRIGGER: KIND: blocker from X`.
3. **Verify-then-consume.** The trigger handler does NOT blindly publish the pre-staged digest. It first checks a cheap freshness signal that measures the QUANTITY THE DIGEST ASSERTS (e.g. "my lane's live pledge rows still == 0"), NOT activity in the same store ("no new rows since digest timestamp" is WRONG: a shared store has unrelated writers, so it fires false-stale and a correct digest is thrown away; measured by bun-desktop 2026-09-27: 1517 -> 1541 raw rows while the asserted count stayed 0). If stale → regenerate, don't send the stale one.
4. **Invalidate on change.** Any material state change after pre-staging marks the artifact STALE (never deletes it: fleet never-delete rule) so a stale digest can never fire.

## Why it works

- Context quality at write time >> context quality at trigger time.
- The trigger condition is named at pre-stage time, when you know exactly which event will need the digest — not guessed later.
- Freshness check keeps it honest: pre-staging is an optimization, not a cache of lies.

## Failure modes

- **Stale fire:** trigger fires, digest is old, nobody checks → always pair with step 3.
- **Trigger never named:** pre-staged doc sits forever because no one knows when to use it → the TRIGGER line is mandatory, not optional.
- **Over-pre-staging:** writing digests for events that never happen → only pre-stage for triggers you can actually name.

## Fleet-install notes

Readable as a standalone `.md` pattern in the blackboard bin, or as a skill with one rule: "when you finish a work unit that a scheduled/conditional consumer will need, write the digest now and name its trigger."
