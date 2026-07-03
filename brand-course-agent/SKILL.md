---
name: brand-course-agent
description: "Work the Brand Launch Course queue for your client — pull your agent agenda from the course API, execute items one at a time (content, schema, citations, review-engine setup, GBP prep), post completion evidence so the client's checklist lights up. TRIGGER: idle work capacity, a course item names you in ACCOUNT-STATE.md, or the client asks about their Brand Launch Course, brand score, progress, or what's next."
metadata:
  version: 1.2.0
  openclaw:
    emoji: "🧭"
---

# Brand Launch Course — Tenant Agent Playbook

## What the Brand Launch Course is

The Brand Launch Course is your client's guided brand-deployment program AND your live work queue — the same per-tenant state powers both. It walks a local service business through 12 modules (brand canon → website → domain → Google Business Profile → citations → trust signals → reviews → social → content → AI visibility → measurement → the ongoing flywheel), teaching the owner what each piece is and why it matters while OUR systems execute most of it. Every item has an owner (`jambot` = we do it, `client` = the owner does it with our guided micro-lesson, `together` = they decide/provide, we execute) and a verify signal that flips it to done. Your job: work the `agent_actionable` items, post honest evidence, and narrate progress to the client specifically and encouragingly. The client watches the checklist light up in real time at `https://<tenant>.jam-bot.com/pages/brand-course.html` — your completed work IS the product they see.

## API access (agent lane)

The course API lives on the host at port **6350** (the same social-dashboard backend the dataforseo skill proxies through). From inside your container:

```bash
TENANT="${HOSTNAME#openclaw-}"

# Reach the host: derive the Docker gateway (per-tenant networks have DIFFERENT
# gateway IPs — never hardcode one). Fallback: your own domain's /social-api path.
BASE="${COURSE_API_BASE:-}"
if [ -z "$BASE" ]; then
  GWHEX=$(awk '$2=="00000000"{print $3; exit}' /proc/net/route)
  GW=$(printf '%d.%d.%d.%d' "0x${GWHEX:6:2}" "0x${GWHEX:4:2}" "0x${GWHEX:2:2}" "0x${GWHEX:0:2}")
  BASE="http://$GW:6350"
  curl -s -m 3 -o /dev/null "$BASE/health" || BASE="https://${TENANT}.jam-bot.com/social-api"
fi
```

**Auth:** agent-lane endpoints (`/api/course/agenda`, `/api/course/event`) require the shared agent key header — **`X-Agent-Key`** — with the value of the **`SOCIAL_DASHBOARD_API_KEY`** environment variable (same convention as every other agent-auth endpoint on :6350; see `requireAgentAuth` in the server). If that env var is empty in your container, STOP and tell the client's host via mesh that the course key isn't provisioned yet — do not guess or invent a key. (Provisioning status: the key was added to `/mnt/system/base/.openclaw-keys.env` on 2026-07-02 — containers pick it up on their next recreate, so a container started before its cycle may still be missing it.)

Read-only endpoints (`/api/course/state`, `/api/course/next`) need **no key** — same as the browser-facing SEO GETs.

## Working your queue — the loop

**1. Pull your agenda:**

```bash
curl -s "$BASE/api/course/agenda?tenant=$TENANT" -H "X-Agent-Key: $SOCIAL_DASHBOARD_API_KEY"
```

Returns your actionable items (status `queued` or `in_progress`, `agent_actionable: true`), each with its `agent_playbook` (how to execute) and `verify` spec (how it will be checked).

**2. Pick ONE item.** Prefer: anything already `in_progress` (finish what you started) → lowest module number → the item whose playbook you can complete with tools you actually have. One item at a time — never bulk-claim.

**3. Claim it** before you start work:

```bash
curl -s -X POST "$BASE/api/course/event?tenant=$TENANT" \
  -H "X-Agent-Key: $SOCIAL_DASHBOARD_API_KEY" -H "Content-Type: application/json" \
  -d '{"item_id":"<id>","status":"in_progress","source":"agent","note":"starting: <one line of what you will do>"}'
```

**4. Execute per its `agent_playbook`.** The playbook is 1–3 sentences telling you HOW. Use your existing skills (dataforseo, seo-platform, article-writer, canvas-pages, customer-comms, ...) to do the actual work. Real work only — an item is not done because you wrote a plan for it.

**5. Post the result with evidence:**

- `status: "done"` — ONLY when verify.mode allows it and the work is verifiably complete.
- `status: "awaiting_verify"` — when the work is done but an auto-check (`verify.signal`) or the host must confirm it. **When unsure, use `awaiting_verify` — never inflate to done.**

```bash
curl -s -X POST "$BASE/api/course/event?tenant=$TENANT" \
  -H "X-Agent-Key: $SOCIAL_DASHBOARD_API_KEY" -H "Content-Type: application/json" \
  -d '{"item_id":"<id>","status":"awaiting_verify","source":"agent",
       "evidence":{"url":"<where the work can be seen>","value":"<the concrete fact>"},
       "note":"<one plain-language line for the activity feed>"}'
```

Evidence is `{url, value, source?}` — `url` is a real **https:// link ONLY** (the client's page renders it as a clickable "See it live" link; anything that isn't a public URL gets dropped by the page). A server file path or internal artifact goes in `source` (audit trail, never rendered) with the measurable fact in `value` ("1,240 words", "5 FAQ blocks with schema", "NAP sheet saved"). Empty evidence on a done/awaiting_verify event is a defect.

## HARD RULES

1. **NEVER mark client-owned items done.** Items with `owner: "client"` (and the client half of `together`) flip via the client's own confirmation or auto-verification — not by you. You may PREPARE materials for them and note that in an event (`status` unchanged, `note` + `evidence` only if the API accepts it, otherwise just prepare and tell the client), but the status flip is theirs.
2. **NEVER touch the big identity platforms: Google Business Profile / Google Maps, Facebook, BBB, Yelp, Apple Maps (Business Connect), Bing Places, Angi/HomeAdvisor.** No account creation, no claiming, no editing, no logins — ever. These platforms suspend businesses that look third-party-operated, and a suspension erases the client from the map for weeks. Those items are client-guided micro-lessons; your role is to PREPARE every material (descriptions, categories from competitor research, photo shortlists, Q&A copy, exact walkthrough steps) so the client's few minutes at the wheel are effortless. Small niche directories (module 4 Tier 3 — chamber pages, trade associations, regional lists, supplier "find an installer" pages) ARE yours to discover and submit.
3. **One message of truth:** if an item's playbook needs a tool, credential, or file you don't have, post an event note saying exactly what's missing and move to the next item. Never fake evidence, never mark done to clear the queue.
4. **Verify before you claim:** re-read the item's `verify.signal` before posting done — if the signal is an on-page check, curl the live page yourself first.
5. **`done` and `not_applicable` are TERMINAL.** The API returns **409** if you post any status change to an item that is already done/not_applicable — that is correct behavior, not an error to work around. Never try to "reset" an item; if you believe a terminal item is genuinely wrong, mesh the host (only `source:"host"` can override).
6. **`locked` items are sequencing-gated** (e.g. every Module 3 GBP setup item is locked behind `m3.gbp.readiness-gate` — the GBP-last strategy). They unlock automatically when their prerequisites complete. Don't post events against locked items and don't tell the client to start them; DO explain, if asked, that Google comes last on purpose.

## NEVER DO (client-protection rules)

Practitioner channels are full of levers that "work" until they erase a client from the map. These 12 came out of the 2026-07 field-intelligence review (`docs/jambot/seo-tips-x-bookmarks-2026-07.md`, cautions C1–C12) and are HARD prohibitions: never execute them, never recommend them, and when the client asks for one (they will — other marketers pitch these constantly), explain the risk plainly and offer the safe alternative.

1. **Keyword-stuffed GBP business name / the DBA-rename trick** ("file a DBA for 'Best Cheap Foam Pros Tampa' and make it your Google name"). It does rank today — and it fragments the brand canon across every citation, invites a suspension review, and is exactly the edit-later volatility Module 3 exists to prevent. *Instead:* GBP name = canon exactly (3.2). If the client genuinely wants service words in their name, that's a real Module-0 rebrand decision, never a Google-only edit.
2. **Fake 24/7 hours to catch late-night searches.** Showing "open" while nobody answers produces missed calls, one-star reviews, and destroys the trust the course builds. *Instead:* accurate hours (3.7); extended hours ONLY if the phone is genuinely answered (a real after-hours answering setup).
3. **Multiple GBP locations / a second profile per trade / virtual offices to beat the proximity radius.** Paper locations violate Google policy outright — the single biggest suspension magnet — and touching GBP is outside your boundary anyway. *Instead:* one honest profile; coverage comes from the 0.4 city list, city pages, and the citation web.
4. **Per-review bounties for techs** ($25–50 per review collected). Bounties quietly incentivize gating and fakes — adjacent to everything 6.9 prohibits. *Instead:* keep the same-day ask workflow (that part is validated); reward asks made or team-level milestones, never the review itself.
5. **Renting a physical address so a service-area business gets a map pin.** Policy violation, suspension magnet, and a lie machines eventually catch. *Instead:* the honest SAB declaration (0.2, 3.6). A real office is a business decision, not an SEO hack.
6. **Geotagging photos for "near me" rankings.** Placebo — Google strips EXIF data on upload. Harmless, but selling it to a client as a lever is selling snake oil. *Instead:* real job photos on a steady cadence (3.12, 7.7) — that's the part that actually works.
7. **Parasite SEO / daily web2 blasting / press-wire volume** ("post daily to 10 socials + 6 web2 blogs, guaranteed traffic in two weeks"). Churn work with platform-ban exposure that burns the client's trust and your time. *Instead:* the M4/M7 owned-profile coverage of the brand SERP — already in the course, quality over volume.
8. **Selling schema as an AI-ranking guarantee.** Structured data correlates with AI citation; it *ensures* nothing, and anyone promising it is overselling. *Instead:* frame schema as one signal among many (9.2) and let the mention-tracking numbers (9.5) do the talking.
9. **Chasing word counts — or gutting content because "E-E-A-T isn't real."** Word count is a coverage proxy, not a ranking factor; but author/expertise signals demonstrably drive AI citations. *Instead:* the 8.7 quality bar — real answers, answer-first openings, a named author with real credentials.
10. **Agent-driven Reddit marketing.** Single operators posting promotionally get banned, and astroturf poisons the brand. Reddit belongs to the identity-platform no-touch family for you. *Instead:* genuine owner-voice participation only, suggested to the client as a micro-lesson at most — never agent-executed.
11. **Forced-indexing services for citations.** Gray-hat, low value, adds a footprint risk. *Instead:* the quarterly citation audit (4.14) verifies listings are live and consistent — that's the whole job.
12. **Promising a Google Knowledge Panel from entity wiring (9.11).** Person schema + Wikidata + consistent bios are cheap and additive, but a panel also needs real name-search demand — it's Google's call. *Instead:* deliver the wiring, report what exists, promise nothing.

## Improvement Sprints (Era 2 — the growth loop)

Once deployment is done, the monthly **needle check** (host-run `course-needle-check.sh`) verdicts each growth dimension — `visibility, reputation, authority, ai_presence, leads, brand_score` — as improving / flat / declining from the tenant's real metrics. A flat or declining dimension produces an **Improvement Sprint**: 3-5 dynamic course items with ids `dyn.<yyyymm>.<focus>.<n>` that land in YOUR agenda exactly like curriculum items (they appear FIRST — the month's game plan outranks the backlog). Work them through the same loop above: claim `in_progress`, execute the playbook, post evidence, respect the terminal rule.

### Authoring a sprint (when the host queues generation to you)

The host may mesh you a sprint-generation task instead of composing it headlessly (you know the client best). You'll get the needle report, course state, and seo-plan. Produce ONE JSON sprint and POST it:

```bash
curl -s -X POST "$BASE/api/course/sprint?tenant=$TENANT" \
  -H "X-Agent-Key: $SOCIAL_DASHBOARD_API_KEY" -H "Content-Type: application/json" \
  -d @sprint.json
```

The API schema-validates hard (400 with the exact errors; duplicate sprint id = 409). What a GOOD sprint looks like:

1. **3-5 plays, never more.** A sprint is a month's focused push, not a backlog dump. Each item is one executable play ("publish 2 supporting pages for the 3 keywords stuck at position 11-15"), not a theme ("improve content").
2. **The id convention is law:** sprint `dyn.<yyyymm>.<focus-slug>` (e.g. `dyn.202607.visibility`; underscores in the dimension become dashes in the slug), items `<sprint-id>.1` … `<sprint-id>.N` sequential. Ids are permanent.
3. **NEVER invent dimensions or metrics.** `focus_dimension` must be one of the six needle dimensions above; `target.metric` must be a real `metrics_history` key from the needle report (ranked_keywords, reviews_count, reviews_rating, llm_mentions, referring_domains, brand_score, money_terms_avg_position, ga4_conversions, gmb_photos).
4. **Targets must be measurable and honest:** `{"metric":"ranked_keywords","from":42,"to":60,"by":"2026-08-01"}` — from = the current number in the report, to = realistic (modest beats heroic; a missed target escalates to the host), by ≈ one month out.
5. **Every play carries a verify signal from the contract vocabulary** (same enums as curriculum items — onpage:/dataforseo:/file:/cadence:/client_confirm; `host_confirm`+`manual` only when nothing fits) and every `agent_actionable` play carries an `agent_playbook` you could hand a stranger.
6. **Canonical play #1 for stuck visibility:** the AI fan-out coverage sprint — enumerate the sub-queries AI systems generate around a keyword the client already ranks 11-15 for, then optimize/create supporting pages for the important ones.
7. **All HARD RULES and NEVER-DO prohibitions apply inside sprints** — no GBP-touching plays, no review bounties, no parasite posting. A sprint is never an excuse to reach for a gray-hat lever.

When the client asks about a sprint, frame it forward (the course page does the same): never "your numbers are declining" — always "here's this month's game plan, N plays already in motion", with the real numbers shown plainly.

## When the client asks "where are we at"

Answer from the course state — never from memory or vibes:

```bash
curl -s "$BASE/api/course/next?tenant=$TENANT"
```

This returns `{client_actions, recent_events, progress}`. Answer **specifically and encouragingly**: name the current module, the overall %, the most recent 1–2 concrete wins from `recent_events`, and (if `client_actions` is non-empty) the ONE thing waiting on them with a plain-language why and how long it takes. Example shape: *"You're in Module 4 — the citation web. Your Nextdoor listing went live yesterday and we published your cost guide for attic insulation. Overall you're 61% deployed. The one thing waiting on you is the Yelp claim — about 10 minutes, and I've already written everything you'll paste. Want the steps?"* No jargon, no raw signal names, no hype — real numbers and real names of real pages.

---

## Worked examples

### Example 1 — a content item (you execute end-to-end)

Agenda returns:

```json
{ "id": "m8.content.cost-guide-spray-foam", "title": "Cost guide: spray foam insulation",
  "owner": "jambot", "agent_actionable": true,
  "agent_playbook": "Write an 800+ word cost guide for the tenant's primary service and region using real search phrasing from seo-plan.json; include an FAQ block with FAQPage schema, internal links to the service page, and the client's real photos.",
  "verify": { "mode": "auto", "signal": "onpage:schema:FAQPage" } }
```

You: POST `in_progress` ("starting: drafting spray foam cost guide for Barrie region") → pull keywords from the seo plan / dataforseo skill → write the page through the website content pipeline → confirm the page is live and curl it to see the FAQPage schema block yourself → POST:

```json
{ "item_id": "m8.content.cost-guide-spray-foam", "status": "awaiting_verify", "source": "agent",
  "evidence": { "url": "https://client-domain.com/spray-foam-insulation-cost", "value": "1,340 words, 6-question FAQ block with FAQPage schema, 4 internal links, 3 client job photos" },
  "note": "Your spray foam cost guide is live — the exact page people find when they search what it costs." }
```

(`awaiting_verify`, not `done` — the signal is `onpage:...`, so course-sync's own curl check flips it.)

### Example 2 — a prepare-GBP-materials item (client drives; you build the pit-crew kit)

Agenda returns:

```json
{ "id": "m3.gbp.description", "title": "Business description written and pasted into GBP",
  "owner": "together", "agent_actionable": true,
  "agent_playbook": "Write the full 750-character GBP business description from the brand canon (natural mention of primary services + priority cities, zero keyword stuffing). Save it to the workspace and hand the client exact paste instructions. Do NOT log into or edit the profile.",
  "verify": { "mode": "auto", "signal": "dataforseo:gmb-name-match" } }
```

You: POST `in_progress` → write the 750-char description from the brand canon in `business/` → save it to `canvas-pages/_data/brand-course/prepared/m3.gbp.description.md` (so it's linkable and never lost) → tell the client where it is and the exact 3 clicks to paste it → POST:

```json
{ "item_id": "m3.gbp.description", "status": "awaiting_verify", "source": "agent",
  "evidence": { "url": "/pages/_data/brand-course/prepared/m3.gbp.description.md", "value": "748-char description prepared, paste instructions delivered to client" },
  "note": "Your Google description is written and ready — paste it in whenever you have 2 minutes." }
```

You did NOT touch Google. The item completes when the client pastes it and the DataForSEO check sees it. If they haven't done it in a few days, the drip system nudges them — not you spamming.

### Example 3 — evidence format reference

Good evidence is checkable by someone who isn't you:

```json
"evidence": { "url": "https://client-domain.com/service-areas/innisfil", "value": "unique 900-word city page: 2 local jobs referenced, drive-time honesty section, LocalBusiness schema" }
"evidence": { "url": "/pages/_data/brand-course/prepared/nap-one-pager.md",  "value": "canonical NAP sheet generated from brand canon — name/address/phone/hours/description, copy-paste ready" }
"evidence": { "url": "https://www.saskchamber.com/members/acme-foam",        "value": "Tier-3 niche directory listing live, NAP matches canon exactly" }
```

Bad evidence (never post these): `{"url":"","value":"done"}` · `{"url":"n/a","value":"completed as requested"}` · a URL you never fetched.
