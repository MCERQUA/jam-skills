---
name: lead-boost-page
description: Clone a one-page canvas deliverable for a lead-gen tenant owner/stakeholder in pipeline-panic mode ("no leads", "is the site working?") — held leads with reply drafts, a 7-day $0 action plan, and a short "what I need from you" ask list. Use when a tenant owner needs something concrete in one page instead of a wall of text messages.
---

# Skill: lead-boost-page

> Contributed by ica-voice@mesh, 2026-09-29; installed by host.

**Origin:** mesh meeting 2026-09-29 routed share → ica-voice@mesh. Live exemplar: ICA
`canvas-pages/lead-boost.html` (built 2026-09-28 in response to owner's "no leads this
weekend" panic text).

## When to use
A lead-gen tenant's owner/stakeholder texts (or says) something like **"no leads"** /
"is the website working?" / pipeline panic. You need to answer with something concrete
in one page — not a wall of text messages.

## What it is
ONE canvas page holding:
1. Every **held lead** with a full reply draft + Copy button (drafts only — the owner
   sends; you never contact the lead without approval)
2. A **7-day $0 action plan** — every card has an owner and a time/cost
3. A **"What I need from you"** section — 2–3 one-word answers that unblock everything

Then **text the page link to every stakeholder**.

## How to clone
1. Copy `/mnt/shared-skills/lead-boost-page/lead-boost-template.html` into the tenant's
   `canvas-pages/` (it is the placeholder-token version of the ICA page; search for `{{`).
2. Replace placeholders: business name, brand color, lead panels (one per held lead),
   plan cards, the 2–3 asks.
3. Reply drafts MUST follow the tenant's `business/lead-reply-playbook.md` if it
   exists; otherwise draft only a request for missing details, promise nothing, never
   say the owner "will call" unless the playbook says so.
4. Publish as a canvas page, share the link with stakeholders only (private page —
   lead details stay behind login).
5. Paid options (Angi, Thumbtack, LSA) get one sentence at the end, max.

## Fleet install note
Installed at `/mnt/shared-skills/lead-boost-page/` (this doc + `lead-boost-template.html`) by
host, 2026-10-03. Original tenant-local copies remain at ica's own
`/home/node/.openclaw/workspace/canvas-pages/lead-boost-template.html` and
`skills/lead-boost-page/SKILL.md` — unchanged, not deleted.
