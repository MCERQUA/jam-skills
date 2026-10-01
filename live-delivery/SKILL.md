---
name: live-delivery
description: Give a reviewer ONE URL that fills in as a multi-item job renders, instead of a batch delivered at the end. TRIGGER when a job produces several artifacts over time (a shot list, a voice-casting pass, a multi-clip render batch) and someone needs to watch it assemble rather than wait for the last one; when you are about to build a one-off "status page" or "progress page" for a render job. DO NOT TRIGGER for a single-artifact delivery (just deliver it) or for a job whose full output is known and ready at once (that is a normal delivery, not a live one).
---

# Live delivery — one URL, seeded before the first render, updated per item

**The rule in one line:** *seed every slot as a placeholder BEFORE anything renders, update ONE
slot the moment its artifact lands, and let the page re-poll itself — so an empty slot reads as a
missing BEAT, never as "nothing happening".*

Needs: a served `uploads/` path (data) and a served, gated `pages/` path (the page) on the
tenant's own domain — no API keys, no database. Never a Claude artifact (client-output rule).

## Why not just deliver the batch at the end

- **A clip that exists but is not on the page is invisible to the reviewer**, and "invisible"
  looks identical to "not rendered yet" from their side. Updating per item as it lands is the
  entire value of the pattern; batching the manifest writes at the end silently turns this back
  into an ordinary batch delivery with extra steps.
- **A stuck render and a slow one look the same without a visible clock.** A placeholder that
  never resolves must be distinguishable from one still cooking (last-updated stamp + a `failed`
  status you actually set, not a `rendering` left forever).
- **The reviewer's job is to watch the STORY assemble**, not to review N unrelated files — so
  slots are seeded from the job's own shot/beat list, in order, before slot 1 finishes.

## The two files (never more, never hand-edited)

| Thing | Lives at | Served at | Written by |
|---|---|---|---|
| **Manifest** (data) | `<tenant>/openvoiceui/uploads/<job>.json` | `https://<tenant>.jam-bot.com/uploads/<job>.json` — 200, no login | the CLI, only |
| **Page** (shell) | `<tenant>/openvoiceui/canvas-pages/<job>.html` | `https://<tenant>.jam-bot.com/pages/<job>.html` — Clerk-gated | `--publish-page`, once |

The page carries **no data** — it derives its manifest path from its own filename and re-polls
every 30s. So a new clip needs no HTML rebuild, a new job is a new manifest (never an edited
template), and a stale page file can never make the data stale.

## Manifest schema `live-delivery/1` (the load-bearing fields)

```json
{
  "schema": "live-delivery/1", "job": "…", "tenant": "…", "updated": "ISO-8601",
  "title": "…", "finding": "the one line worth reading first",
  "clips": [
    {"n": 1, "beat": "cold-open", "shows": "what this slot IS, shown while empty",
     "status": "queued|rendering|ready|failed|skipped",
     "file": "x.mp4", "url": "/uploads/x.mp4", "measurements": {"any": "number or string"},
     "alternates": [], "superseded": []}
  ]
}
```

- `n` is contiguous from 1 — the page orders by it, and a reviewer who replies with a single
  digit is replying to a POSITION, so a gap in numbering breaks the only affordance the page has.
- `shows` is written at seed time — it is the only thing on screen while a slot is empty, and is
  what makes an empty grey box read as "this is where the diner scene goes" instead of nothing.
- `status` is a CLOSED list. An unlisted status must be refused, not rendered — an unknown status
  falling through to an empty gap is the one thing a pending slot must never become.
- `superseded[]` records what a slot USED to carry when a later take replaces it — the displaced
  file is never deleted from uploads (a reviewer may already have a link to it), so without this
  list a coverage checker sees an orphaned file no manifest names.

## The CLI (reference implementation — generic, tenant is a parameter)

`~/showrunner/bin/live_delivery.py` on mac-claude@mesh (the node that built and runs this
pattern daily). Full contract, failure-mode table and the gating write-up: `~/showrunner/LIVE-DELIVERY.md`
on that node — read it before a first adoption, it has the two production incidents (a gated page
answers a bare `Unauthorized` with no sign-in redirect; `/uploads/` serves HTML as a download, so
it can host the DATA but never the PAGE) and how each was fixed.

```bash
# seed every slot BEFORE the first render — from a plain count or an existing shot/beat list
live_delivery.py --job <slug> --tenant <slug> --seed <beats.json|N> [--title "…"]
live_delivery.py --job <slug> --tenant <slug> --publish-page          # once per job

# ONE call per artifact, the moment it lands
live_delivery.py --job <slug> --set <n> --status ready --file <name.mp4> [--measure k=v]
live_delivery.py --job <slug> --set <n> --status failed --note "why"    # a roll that died

live_delivery.py --job <slug> --show [--json]                          # read it back
```

Exit codes are a third answer, not collapsed: **0** written · **1** REFUSED (rule named) ·
**2** CANNOT-TELL (remote unreadable/unwritable — nothing changed). Refusals worth knowing:
`ready-without-file`, `file-not-delivered` (deliver first, mark ready second), `unknown-slot`,
`manifest-exists` without `--force` (protects a live manifest from an accidental re-seed).

## The page's non-negotiables (a rewrite that drops one is a regression)

1. Number order always, never arrival order.
2. A pending slot holds its place and says what it's FOR — never an empty gap, never a broken player.
3. Honest degradation: a failed manifest fetch SAYS so; it must never render as "nothing to show".
4. A visible last-updated stamp, so live and stuck are distinguishable from across a room.
5. Phone-first, ≥44px tap targets.
6. A poll never tears down a clip currently being played — only changed slots re-render.

## Gating — say which URL you sent

Canvas pages are Clerk-gated by default (client-output rule: never auto-public). **When you text
the page link, also send one direct `/uploads/` asset URL as a fallback that needs no login** —
measured live: a gated page answers a bare `Unauthorized` with **no sign-in redirect**, so a
reviewer with no open session has nothing on screen to act on. `/uploads/` is 200-with-no-login
fleet-wide but serves `.html` as a forced download (`Content-Disposition: attachment`), so it can
host the manifest but can NEVER host the page itself — don't "fix" the gating problem by moving
the page there.

## When NOT to use it

- A single deliverable — just deliver it through the normal two destinations (uploads + Dropzone
  video doctrine, or the tenant's normal upload flow).
- A job whose full output already exists and is ready to send at once — that's an ordinary
  delivery, not one that benefits from being watched live.

## Adopt target

Reference implementation + template live on **mac-claude@mesh**: `~/showrunner/bin/live_delivery.py`,
`~/showrunner/pages/live-delivery-page.html`, full contract `~/showrunner/LIVE-DELIVERY.md`. An
adopting agent can call the CLI over the mesh (it is a stdlib-only Python script, no external
deps) or copy it — the schema above is the actual adopt target, the script is one correct writer
of it. Live instance to point at as a working example: `cortez-voice-tests` (tenant `danielle`,
8 slots, first job built on this pattern, 2026-09-11).

Still open (named so this doesn't read as all-clear): no formal self-test suite exists for the
CLI yet (unlike `retire-dont-delete`'s `self-test.sh`) — the refusal table above is enforced in
code but not yet pinned by an independent test file.
