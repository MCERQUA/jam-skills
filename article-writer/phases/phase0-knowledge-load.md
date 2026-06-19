# Phase 0 — Knowledge Load & Gap-Analysis  (+ Completion: Write Back)

> The anti-waste bookends of the pipeline. Phase 0 reads the client's distilled **Tier-2 brain**
> first so Phase 2 only researches the GAPS; the Completion step (end of this file) writes the
> finished article back into the brain so the next run starts smarter. Model: **haiku / GLM** — this
> is mechanical file IO + diffing, never opus.

---

## The two tiers (orientation — full detail in SKILL.md)

- **TIER 1 — RAW (per-site, in the website repo):** `work_dir` =
  `<site_root>/ai/knowledge/article-research/<slug>/`. The bulky raw artifacts (raw DataForSEO/SERP
  JSON, PAA dumps, candidate-source lists, draft iterations). Provenance — ships with the repo.
- **TIER 2 — PROCESSED (per-client, in the openclaw workspace):** `knowledge_base` =
  `/mnt/clients/<tenant>/openclaw/workspace/knowledge/`, sibling of `business/`. The lean, distilled,
  cross-site **shared brain** the client's voice/SMS/ops agent reads. **Phase 0 reads THIS — never
  the raw repo dumps.**

### Tier-2 brain layout (the corpus)

```
<knowledge_base>/
  topical-map.json        # content graph across ALL the client's sites:
                          #   articles[{slug, site, target_keyword, status, url,
                          #             internal_links_in[], internal_links_out[]}],
                          #   covered_topics[], gaps[] / next_topics[]
  keyword-corpus.json     # [{keyword, volume, difficulty, intent, source_slug}] — never re-pay DataForSEO
  authority-sources.json  # [{url, domain, dr, topic, last_validated}]
  faq-bank.json           # [{question, answer_gist, source, topic}]
  field-knowledge/        # durable industry/ops/domain insight as *.md — used everywhere, cross-site
    <topic>.md
```

---

## 🔒 PER-CLIENT ISOLATION (non-negotiable)

The brain is read AND written **only** under this one tenant's `knowledge_base`
(`/mnt/clients/<tenant>/openclaw/workspace/knowledge/`). NEVER read or write a global
`/mnt/system/base/skills/` dir, NEVER another tenant's workspace, NEVER aggregate up to the jambot
host. **Shared TOOL (this skill), isolated DATA (each client's brain stays in their own
ecosystem).** If `knowledge_base` does not resolve under `/mnt/clients/<tenant>/openclaw/workspace/`,
do NOT build a brain — run Tier-1-only and note it in the report.

## 🤝 Shared-brain note — alongside `business/` + `CLIENT.md`

The corpus is a peer of the tenant's existing `business/` dir and `CLIENT.md` in the SAME workspace
the openclaw agent boots from. Knowledge flows **both ways within this one client's ecosystem**:
seed/cross-reference `field-knowledge/*.md` and `faq-bank.json` from the tenant's `business/` facts
and `CLIENT.md` voice; and the durable insight this pipeline distills becomes knowledge the
voice/SMS agent then uses on calls, texts, and future articles. One brain, many readers — but only
ever **this client's** brain.

---

## Phase 0 — Load & Gap-Analysis

**Inputs:** `knowledge_base`, `topic`, `target_keyword`.

**Steps:**
1. If `<knowledge_base>/` is missing or empty, treat EVERYTHING as a gap (first article for this
   client) — Phase 1 will create the stub corpus files, and the run still seeds the brain at the end.
2. Read the five corpus pieces (NOT the raw repo dumps):
   - `keyword-corpus.json` → which candidate keywords for this topic are **already priced** (volume/
     difficulty/intent present) → Phase 2 must NOT re-call DataForSEO for these.
   - `authority-sources.json` → which authoritative sources for this topic are **already vetted**
     (with DR) → reuse instead of re-discovering.
   - `faq-bank.json` → which customer questions for this topic are **already captured** → reuse.
   - `topical-map.json` → which adjacent published articles exist (slug + url) → interlink targets,
     and what `covered_topics[]` / prior `gaps[]` say about this topic.
   - `field-knowledge/*.md` → durable insight already known for this domain.
3. Diff "what the article needs" against "what the brain already has" → produce the **gap brief**.

**Output:** `<work_dir>/<slug>/knowledge-load.md` — two clear sections:
- **ALREADY KNOWN (reuse — do NOT re-research):** cached keywords (with their cached metrics),
  vetted sources, captured FAQs, adjacent articles for interlinking, relevant field-knowledge.
- **GAPS (Phase 2 MUST research these):** the keywords still needing volume/difficulty/intent, the
  source-discovery still needed, the FAQ mining still needed, the topic angles not yet covered.

**Anti-waste:** this brief is the contract Phase 2 honors — it researches ONLY the gaps and pulls
the rest from the brain. → start Phase 1.

---

## Completion — Write Back to the Brain (runs after Phase 9)

After Phase 9 has shipped the article, update the **Tier-2 brain** so the work compounds. Mechanical
(haiku/GLM). **All merges are deduped + additive — never overwrite the corpus wholesale.**

1. **`topical-map.json`** — add the finished article:
   `{slug, site, target_keyword, status:"published", url, internal_links_in:[], internal_links_out:[<from Phase 6>]}`.
   For each page this article links TO, append this article's url to that page's `internal_links_in[]`
   (back-reference). Refresh `covered_topics[]` with the topics this article now covers.
2. **Recompute `gaps[]` / `next_topics[]`** — given the now-covered topics + `keyword-corpus.json`,
   list the strongest still-uncovered topics so the NEXT run's Phase 0 has a ready agenda.
3. **`keyword-corpus.json` / `authority-sources.json` / `faq-bank.json`** — ensure the final
   validated authority links and the article's FAQ entries are present (deduped — many will already
   be there from the Phase-2 distill bridge).
4. **`field-knowledge/*.md`** — if the article surfaced durable industry/ops insight worth reusing
   everywhere, append/update the relevant `<topic>.md`.

**Surface `next_topics[]` in the final report.** Touch ONLY `<knowledge_base>/` under this one
tenant's workspace.
