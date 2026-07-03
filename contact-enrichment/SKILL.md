---
name: contact-enrichment
description: "Contact-enrichment cascade — raw names (person or company) in, progressively enriched rows out: phone, email, website, address, LinkedIn, social profiles via cheap-to-expensive providers, chaining email-finder / dataforseo / headshot-finder / browser-automation. TRIGGER: a CSV of names with no contact info, or any name-to-reachable-contact pipeline."
metadata: {"openclaw": {"emoji": "📇", "requires": {"anyBins": ["python3", "bash"]}}}
---

# Contact Enrichment Cascade

Take a list of names (companies + people, mixed, no other fields) and progressively enrich each row with reachable contact info. Cheap → expensive. Each stage only fills empty fields. Each stage is a plugin so we can swap providers.

**Planning doc / source of truth:** `/home/mike/MIKE-AI/docs/jambot/contact-enrichment-skill.md` (NOT in this skill dir — it's in the project repo and tracks all repo evaluations, scope decisions, and stage-by-stage build status).

**Operating context:** This skill is most useful when run from inside the **residential ubuntu desktop** container — that environment has authenticated browser cookies (LinkedIn, Facebook, X, Instagram) that unlock data sources public scrapers can't reach. The cheap stages (1-5) work fine anywhere.

## When to use

- "Enrich this list of contacts"
- "I have a CSV of names — find emails / phones / websites"
- "Build a directory entry for these companies/people"
- Foam-industry directory ingest for `foambook.jam-bot.com` (sibling consumer)
- Outreach-list preparation (cascade output → email-finder → agentmail)

DO NOT use for:
- One-off "find an email for X" — go straight to `email-finder` skill
- Headshot lookup alone — `headshot-finder` skill
- Lead-scoring / scoring quality of leads — different problem

## Cascade architecture (9 stages)

```
INPUT ROW  (raw name string)
   │
   ├─ STAGE 1: Normalize & classify              ← BUILT (this skill)
   │       classify.sh "<name>"  →  {type: person|company|ambiguous, ...}
   │
   ├─ STAGE 2: Company discovery                 ← planned
   │       Google Maps Places API (key live) → phone, website, address
   │
   ├─ STAGE 3: Website crawl (2 levels)          ← planned
   │       / + /contact + /about + /team → emails + names
   │
   ├─ STAGE 4: DataForSEO Business Data          ← uses `dataforseo` skill
   │       Confirms NAP, pulls social URLs from SERP
   │
   ├─ STAGE 5: Hunter domain search              ← uses `email-finder` skill
   │       `domain-search.sh <domain>` → pattern + ~10 named addresses
   │
   ├─ STAGE 6a: LinkedIn (residential only)      ← planned (wrap joeyism/linkedin_scraper)
   │       Person profile + Company page from authenticated session
   │
   ├─ STAGE 6b: Other social (residential only)  ← planned
   │       Facebook, Instagram, X via screenshot + OCR
   │
   ├─ STAGE 7: Person email lookup               ← uses `email-finder` skill
   │       `find-email.sh "<first>" "<last>" "<domain>"` (Hunter→Snov→Apollo)
   │
   ├─ STAGE 8: Verify                            ← uses `email-finder` skill
   │       `verify-email.sh <email>` → deliverable + score
   │
   └─ STAGE 9: Manual review queue               ← planned
           Anything below confidence threshold → human-review CSV
```

## Helper scripts

All under `/mnt/shared-skills/contact-enrichment/`:

| Script | Purpose | Cost |
|---|---|---|
| `classify.sh "<name>"` | Stage 1 — classifies a raw name string as person, company, or ambiguous. Outputs JSON with normalized form, tokens, and signals. | free |
| `classify.sh --batch <file>` | Stage 1 batch — reads one name per line from `<file>` (or `-` for stdin), outputs JSONL. | free |
| `classify.sh --test` | Self-test against built-in cases. Useful sanity check. | free |

### classify.sh examples

```bash
classify.sh "ACME Insulation LLC"
# → {"input":"ACME Insulation LLC","type":"company","confidence":"high",
#    "normalized":"ACME Insulation LLC","tokens":["ACME","Insulation","LLC"],
#    "signals":["suffix:llc","keyword:insulation"]}

classify.sh "John Smith"
# → {"input":"John Smith","type":"person","confidence":"high",
#    "first":"John","last":"Smith",
#    "tokens":["John","Smith"],"signals":["name-pattern"]}

classify.sh "Bob's Spray Foam"
# → {"input":"Bob's Spray Foam","type":"company","confidence":"medium",
#    "normalized":"Bob's Spray Foam","tokens":["Bob","s","Spray","Foam"],
#    "signals":["keyword:spray","keyword:foam","possessive"]}

# Batch mode — reads stdin if path is "-"
cat names.txt | classify.sh --batch -
# → one JSON object per line, one per input row

# Self-test (built-in cases)
classify.sh --test
```

## Classification signals (Stage 1)

The classifier looks for these signals on each input row:

**HIGH-CONFIDENCE COMPANY**
- `suffix:<token>` — explicit corporate suffix (LLC, Inc, Corp, Ltd, Co, LP, PLC, PC, PA, LC, PLLC, GmbH, AG, SA)

**MEDIUM-CONFIDENCE COMPANY**
- `keyword:<token>` — industry keyword (insulation, foam, spray, contractor, builder, construction, restoration, roofing, HVAC, energy, services, solutions, systems, group, enterprises, supply, products, industries, partners, associates, consulting, management, properties, realty, design — see `classify.py` for full list)
- `possessive` — apostrophe-s in the name (e.g. "Bob's", "Smith's")
- `conjunction` — contains `&` or the word `and` (e.g. "Smith & Sons", "Doe and Associates")

**HIGH-CONFIDENCE PERSON**
- `last-first-format` — comma-separated "Last, First" pattern
- `name-pattern` — 2-3 capitalized tokens, no business signals, no conjunctions

**LOW-CONFIDENCE / AMBIGUOUS**
- `single-token` — only one word, no other signals (e.g. "Acme") — could be a brand or a first name
- `no-signals` — multi-token but nothing tells us either way (e.g. "Smith Brothers" — partnership? brand? family name?)

The classifier never guesses when ambiguous — it returns `type: "ambiguous"` so downstream stages can route to a manual review queue.

## What's NOT built yet

Stages 2, 3, 6a, 6b, 9 need implementation. See the planning doc for the queued tasks and which repos we've evaluated for each stage. **Do not start building those stages without explicit ask from Mike** — the planning doc has a SESSION-RESUME PROTOCOL section at the top that gates this.

## Cost awareness

Stage 1 is free (pure heuristic, no API calls). Downstream stages have provider costs:
- Stage 2 — Google Maps Places API: free quota ~$200/mo of usage, then $0.017/call
- Stage 4 — DataForSEO: see `dataforseo` skill for current credit balance
- Stage 5/7/8 — Hunter/Snov/Apollo: see `email-finder/quota.sh` before batches
- Stage 6a/6b — residential-desktop browser time only (no API spend)

## Failure modes

Stage 1:
- Unicode names with non-Latin scripts → tokens may be empty → classifier returns `ambiguous`
- Names with embedded punctuation (e.g. "X.Y.Z. Holdings, Inc.") → suffix detection still works on lowercased tokens; comma in middle still parses as company if other signals present
- Single-letter "names" (e.g. "M") → ambiguous, low confidence

Downstream stages (not yet built):
- All standard provider failure modes — see each linked skill's SKILL.md
