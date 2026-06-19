# Phase 2 — Research (PARALLEL, 4 agents) + Distill Bridge

> Model: **haiku / GLM** — API calls + summarizing + the distill merge are mechanical. (Phases 4/5
> and the gates are sonnet; opus never.)

Launch ALL 4 in a single message (4 parallel Task calls). Wait for all, run the **Distill Bridge**,
then go to Phase 3.

## Gap-scoping (anti-waste — read the Phase-0 gap brief FIRST)

Each agent reads `<work_dir>/<slug>/knowledge-load.md` and **researches ONLY the GAPS**. For
"ALREADY KNOWN" items, pull straight from the **Tier-2 brain**
(`<knowledge_base>/keyword-corpus.json`, `authority-sources.json`, `faq-bank.json`) instead of
re-calling DataForSEO/Serper. Cached + freshly-researched items merge into the same Tier-1 report so
Phase 3 sees a complete picture. This is how the corpus pays for itself — we never re-pay for
research we already bought.

## 1. topic-research-agent → `topic-research/topic-research-report.md`
Comprehensive, topic-neutral research: background & context, key concepts/definitions, relevant
standards or regulations (whatever applies to THIS topic), current trends, expert perspectives,
common misconceptions.
**Tooling:** `social-research` (real customer language/pain points), `web_search` then
`serper-search` for facts and current developments.

## 2. keyword-research-agent → `keyword-research/keyword-report.md`
Primary (5-10), LSI (15-25), long-tail (20-40), semantic (10-20), question-based (10-20), local
(only if `location` is meaningful for the topic), and topic clusters.
**Tooling — REAL data, not guesses:**
- `dataforseo` `keywords_data/google_ads/search_volume/live` — batch all candidate keywords in ONE
  call for volume + competition + CPC.
- `dataforseo` `dataforseo_labs/google/keyword_suggestions/live` — expand seeds.
- `dataforseo` `dataforseo_labs/google/bulk_keyword_difficulty/live` — difficulty scores.
- `dataforseo` `dataforseo_labs/google/search_intent/live` — intent per keyword.
- `serper-search` `/autocomplete` + `relatedSearches` — query-expansion seeds.
Record volume + difficulty + intent per keyword so Phase 4 can prioritize.

## 3. authority-link-research-agent → `authority-link-research/authority-sources.md`
10-15 authoritative external sources to cite: full citation, URL, authority estimate (Ahrefs DR
via the `dataforseo` skill's free DR endpoint), recommended placement in the article, anchor-text
suggestion. Prefer high-DR, topically-relevant, non-competitor sources.

## 4. faq-research-agent → `faq-research/faq-report.md`
10-20 People-Also-Ask questions (`serper-search` `.peopleAlsoAsk`, re-query 1-2 levels deep),
forum/customer questions (`social-research`), prioritized by intent + volume, plus a recommended
FAQ section structure. **Every real question is an FAQ entry or a section.**

## Distill Bridge (after all 4 raw agents, before Phase 3 — haiku/GLM, mechanical)

The 4 reports above are the **RAW Tier-1 artifacts** — they STAY in `<work_dir>/<slug>/` inside the
website repo (heavy, provenance). Now **extract the durable/reusable knowledge and MERGE it deduped
into the Tier-2 workspace brain** (`<knowledge_base>/`):

- **new priced keywords** → `keyword-corpus.json` — dedupe on `keyword`; store
  `{keyword, volume, difficulty, intent, source_slug:<this slug>}`.
- **vetted external sources** → `authority-sources.json` — dedupe on `url`; store
  `{url, domain, dr, topic, last_validated}`.
- **distilled customer questions** → `faq-bank.json` — dedupe on `question`; store
  `{question, answer_gist, source, topic}`.
- **durable industry/ops insight** worth reusing everywhere → append/update
  `field-knowledge/<topic>.md` (NOT per-article trivia — cross-site durable knowledge only).

**Per-client isolation:** write ONLY under this tenant's `<knowledge_base>/`. Additive + deduped —
never overwrite the corpus wholesale. Raw stays heavy + local to the site; the brain stays lean +
shared. (Full rules: `phases/phase0-knowledge-load.md`.)

## Hand-off
All 4 raw reports written (Tier 1) + distilled knowledge merged into the brain (Tier 2). Proceed to
Phase 3 (do not ask).
