---
name: client-workflows
description: "Library of repeatable owner-facing service workflows, one dir per workflow. TRIGGER when a client asks about or accepts a recurring service play — currently: google-review-ask (more Google reviews, never touching their GBP). NOT for one-off tasks or site/article builds."
---

# Client workflows

A workflow here is a **repeatable offering** an agent runs for a tenant's business owner —
the play, its trigger, its hard rules, its done-definition, and an improvement log that gets
better every time it runs. These are owner-facing services, never customer-facing.

This directory was invisible to every agent from 2026-07-05 until 2026-08-20: it held a real
workflow but no `SKILL.md`, so nothing routed to it. That is why the index below exists — a new
workflow is only real once it is listed here.

## Index

| Workflow | File | Runs when |
|---|---|---|
| Google review-ask | `google-review-ask/workflow.md` | Client mentions Google/Facebook reviews, or accepts an offered review-ask |

## How to run one

1. Read that workflow's `workflow.md` in full before acting — the hard rules are not optional.
   (`google-review-ask` carries the system-wide never-touch-GBP rule: agents never log into,
   scrape, or modify a client's Google Business Profile.)
2. Open a matter in the client's office (`office/matters/<workflow>-<date>.md`, status: open).
3. Work the steps; close the matter at the done-definition.
4. **Append to that workflow's improvement log** — what you learned, what to try next run.
   A workflow that never gains a log entry is not being improved.

## Adding a workflow

Create `<workflow-name>/workflow.md` with the same shape (Offering · Trigger · Hard rules ·
Steps · Done-definition · Improvement log), then add a row to the index above. Retire by moving
to `/mnt/system/base/skills-retired/` — never delete.
