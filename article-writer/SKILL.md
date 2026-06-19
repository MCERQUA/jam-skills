---
name: article-writer
description: "Fully-autonomous, research-driven long-form article pipeline that COMPOUNDS a per-client knowledge brain. Takes a topic + target keyword and produces a publication-ready 3500-5000 word article — markdown + designed HTML + JSON-LD schema — through phases 0–9 (Knowledge-Load/Gap-Analysis → Setup → parallel Research+Distill → quality gate → Planning → Drafting → parallel Enhancement → HTML Design → final quality gate → Schema → Completion write-back). Uses a two-tier corpus: RAW research stays in the website repo (provenance), DISTILLED knowledge merges into the client's openclaw-workspace brain (shared, per-client-isolated) so research is never re-paid. Research is backed by real data (dataforseo, serper-search, social-research) and both quality gates run through the quality-review skill. Generic: works for ANY website/topic/brand via passed-in inputs — never niche-specific. TRIGGER when the user asks to 'write an article / blog post', 'research and write a post about X', 'create a long-form SEO article', 'add a blog post to <site>', or asks for a fully-researched publish-ready article with images + schema. DO NOT USE for: short social posts (use social-media-designer), building a whole website (use website-builder), or a content *calendar/strategy* with many briefs (that's a planning task, not a single article)."
metadata:
  version: 1.0.0
  tags:
    - content
    - seo
    - article
    - blog
    - longform
    - research
    - schema
    - autonomous
  openclaw:
    emoji: "📝"
---

# Article Writer — Autonomous 10-Phase Research-to-Publish Pipeline (Phases 0–9)

> **Value proposition:** consistent, fully-researched + planned + twice-checked, ranking-grade
> content with **zero effort-variance — and every article compounds the client's own knowledge
> brain.** It is delivered *economically*: the right model for each phase (haiku/GLM for the
> mechanical grunt, sonnet for the thinking, opus never) plus a **two-tier raw/processed knowledge
> corpus** that means we never re-pay for research we already bought.
>
> A complete, end-to-end article creation pipeline: from research to final HTML with JSON-LD
> schema markup. It orchestrates specialized review agents across the phases and **runs fully
> autonomously** — no stopping to ask the caller between phases. You hand it a topic and a target
> keyword; it returns a publication-ready article with citations, internal links, images, and
> structured data optimized for featured snippets and AI Overviews.
>
> This skill is **generic by design**. Nothing here assumes an industry, niche, or brand. Every
> business-specific value (site root, blog directory, brand name, author byline, location) is an
> **input the caller passes in** — see [Inputs](#inputs-the-caller-passes-these). A reader can use
> this for a local-bakery blog, a SaaS docs site, a non-profit, or anything else.

---

## 🧠 THE TWO-TIER KNOWLEDGE MODEL (read this before the phases)

Every run reads from and writes back to a **persistent knowledge corpus** so the work compounds
instead of starting from zero. The corpus is split into two tiers with a **distillation bridge**
between them:

**TIER 1 — RAW research lives in the WEBSITE REPO (provenance, per-site, ships with the repo).**
- Location: `<site_root>/ai/knowledge/article-research/<slug>/` — i.e. the per-article `work_dir`
  (see [Inputs](#inputs-the-caller-passes-these) + [Directory Layout](#directory-layout-parameterized--no-hardcoded-client-paths)).
- Contents: the bulky raw artifacts — raw DataForSEO keyword/SERP JSON, PAA dumps, FAQ research,
  authority-link candidate lists, topic research, draft iterations. The **full provenance** of how
  the article was researched. Heavy, local to the site, committed with the repo.

**TIER 2 — PROCESSED knowledge goes to the OPENCLAW WORKSPACE brain (distilled, per-client, shared, lean).**
- Location: the `knowledge_base` input, default `<tenant_workspace>/knowledge/` — i.e.
  `/mnt/clients/<tenant>/openclaw/workspace/knowledge/`, **sibling of the existing `business/`
  dir** the tenant's agent already reads.
- This is the **SHARED BRAIN** the client's own voice/SMS/ops agent reads — NOT a per-article
  silo, NOT the raw dumps. Distilled, curated, durable, cross-site.
- Contents (the corpus schema — see [Tier-2 Corpus Schema](#tier-2-corpus-schema-the-brain)):
  `topical-map.json`, `keyword-corpus.json`, `authority-sources.json`, `faq-bank.json`, and
  `field-knowledge/*.md`.

**THE DISTILLATION BRIDGE (the key new step):** after Phase 2 dumps RAW research into the repo
(Tier 1), a **distill pass EXTRACTS** the durable/reusable knowledge from those raw artifacts and
**MERGES it (deduped) into the workspace brain** (Tier 2). Raw stays heavy + local to the site; the
brain stays lean + shared. Then **Phase 0 of the NEXT article reads the brain first** and researches
ONLY the gaps — that's the anti-waste flywheel.

### 🔒 PER-CLIENT ISOLATION (non-negotiable)

The Tier-2 brain is written **ONLY under that one tenant's workspace** — never a global
`/mnt/system/base/skills/` dir, never another tenant's workspace, never aggregated up to the jambot
host. **Shared TOOL (this skill), isolated DATA (each client's brain stays in their own
ecosystem).** One client's knowledge must NEVER reach another client or the host. The skill is
generic; the corpus it builds is private to a single `knowledge_base` path. If `knowledge_base`
resolves outside `/mnt/clients/<tenant>/openclaw/workspace/`, do not write a brain — fall back to
Tier-1-only and note it.

### 🤝 SHARED-BRAIN NOTE — sits alongside `business/` + `CLIENT.md`

The Tier-2 corpus is a peer of the tenant's existing `business/` dir and `CLIENT.md`, inside the
SAME workspace the openclaw agent boots from. Knowledge flows **both ways within that one client's
ecosystem**: `field-knowledge/*.md` and `faq-bank.json` may be seeded from / cross-reference the
tenant's `business/` facts and `CLIENT.md` voice, and the durable industry/ops insight the article
pipeline distills becomes knowledge the voice/SMS agent uses *everywhere* (calls, texts, future
articles). It is one brain with many readers — but only ever **this client's** brain.

### Tier-2 Corpus Schema (the brain)

Under `<knowledge_base>/`:

```
<knowledge_base>/                      # default /mnt/clients/<tenant>/openclaw/workspace/knowledge/
  topical-map.json        # content graph across ALL the client's sites:
                          #   every article {slug, site, target_keyword, status, url,
                          #   internal_links_in[], internal_links_out[]},
                          #   covered_topics[], and gaps[] / next_topics[] (recomputed each run)
  keyword-corpus.json     # curated keywords [{keyword, volume, difficulty, intent, source_slug}]
                          #   — so we NEVER re-pay DataForSEO for a keyword we already priced
  authority-sources.json  # vetted external sources [{url, domain, dr, topic, last_validated}]
  faq-bank.json           # distilled customer questions [{question, answer_gist, source, topic}]
  field-knowledge/        # durable industry / operations / domain insight as *.md the agent
    <topic>.md            #   uses everywhere — NOT per-article, cross-site durable knowledge
```

All five are **merged, deduped, additive** — never overwritten wholesale (same additive-data rule
as the rest of the platform). A run adds/updates entries; it does not clobber prior knowledge.

---

## 🚨 CRITICAL: AUTONOMOUS OPERATION (this is the core rule — do not break it)

**Complete ALL phases (Phase 0 → Phase 9) automatically without stopping for caller approval.**

1. **DO NOT** ask the caller for review between phases.
2. **DO NOT** wait for "continue".
3. **DO NOT** pause for approval of research quality, drafts, or HTML.
4. **RUN ALL PHASES** sequentially (start at Phase 0) until 100% complete.
5. **USE the quality-review skill + review agents** for all quality gates (not human reviews).
6. **FIX ISSUES AUTOMATICALLY** when a gate fails — re-run the weak step, then re-gate.
7. **COMPLETE TO 100%** — research, draft, images, HTML, schema, everything.
8. **ONLY STOP** when all final deliverables exist and both quality gates PASS.

**FORBIDDEN phrases that break autonomy** — never write any of these:
- ❌ "Would you like me to continue?"
- ❌ "Should I proceed with Phase X?"
- ❌ "Do you want me to run the remaining phases?"
- ❌ A summary-and-stop before Phase 9.
- ❌ "Token budget is running low so I'll stop." (Token budget is NOT a reason to stop.)

**CORRECT behavior:** after a phase, immediately say e.g. "Phase 5 complete. Starting Phase 6…"
and launch the next step WITHOUT asking permission.

> The only time you stop is after Phase 9, when the schema is embedded and both quality gates
> have passed. At that point, present the final deliverables summary.

---

## Inputs (the caller passes these)

The skill is parameterized. Resolve these before Phase 1; fall back to the listed defaults when a
value isn't supplied.

| Input | Required | Meaning | Default if omitted |
|-------|----------|---------|--------------------|
| `topic` | ✅ | The article subject (free text). | — (must be given) |
| `target_keyword` | ✅ | Primary SEO keyword to rank for. | derive from `topic` |
| `site_root` | ✅ | Absolute path to the site this article belongs to. | current site / project dir |
| `blog_dir` | — | Where the published article files live (relative to `site_root`). | `content/blog` |
| `work_dir` | — | **TIER 1 (RAW).** Where the per-article raw research + draft iterations are staged — lives **inside the website repo** and ships with it (provenance). **DISTINCT from `knowledge_base`.** | `<site_root>/ai/knowledge/article-research` |
| `brand` | — | Business/site name (used in copy + schema `publisher`). | `{{brand}}` — must be resolved, never a placeholder in output |
| `site_author` | — | Author byline (schema `author`, draft frontmatter). | `{{brand}}` editorial team |
| `site_url` | — | Public base URL (for internal link resolution + schema `url`). | derive from site config |
| `location` | — | Geo for keyword/SERP/local data (DataForSEO `location_name`). | `United States` |
| `word_target` | — | Target length. | `3500-5000` |
| `existing_articles` | — | List/index of existing blog URLs (for internal linking). | crawl `blog_dir` / sitemap |
| `knowledge_base` | — | **TIER 2 (PROCESSED).** The **persistent per-CLIENT corpus** — the distilled, lean, cross-site **shared brain** the client's own voice/SMS/ops agent reads (NOT the raw dumps, NOT a per-article silo). Loaded in Phase 0, written back via the Phase 2 distill bridge + the Completion step. **DISTINCT from `work_dir`** (Tier-1 raw). PER-CLIENT ISOLATED. | `<tenant_workspace>/knowledge/` — i.e. `/mnt/clients/<tenant>/openclaw/workspace/knowledge/` (sibling of the existing `business/` dir) |

**Slug:** derive a lowercase, hyphenated, SEO-friendly slug from `target_keyword` (preferred) or
`topic`. Example: topic "How to choose a project-management tool" → slug
`how-to-choose-a-project-management-tool`.

> ⚠️ **No placeholders in output.** `{{brand}}`, `{{site_author}}`, etc. are inputs you RESOLVE.
> If a real value is unknown, ask once at the very start (before Phase 1) OR pull it from the
> site's config/`profile.md`. A delivered article that still says `{{brand}}` or "Business Name"
> is a failure (same rule as website-builder's placeholder sweep).

---

## Directory Layout (parameterized — no hardcoded client paths)

> This is **TIER 1 — the RAW research that lives in the website repo** (provenance, per-site).
> The distilled **TIER 2 brain** lives separately under `knowledge_base` — see
> [The Two-Tier Knowledge Model](#-the-two-tier-knowledge-model-read-this-before-the-phases).

Everything stages under `work_dir/<slug>/`. Default `work_dir` is
`<site_root>/ai/knowledge/article-research` (inside the website repo — it gets committed and travels
with the site). The caller can point it anywhere, but the default keeps RAW provenance with the repo.

```
<work_dir>/<slug>/
  topic-research/            # background, definitions, standards, trends, misconceptions
  keyword-research/          # primary/LSI/long-tail/semantic/question/local keywords + volume + difficulty
  authority-link-research/   # high-quality external sources to cite
  internal-link-research/    # opportunities to link to existing pages on THIS site
  faq-research/              # PAA + forum/customer questions, FAQ structure
  article-outline-planner/   # outline, section word-count allocation
  article-design/            # image prompts + visual plan
    images/                  # generated images (5-8, web-optimized)
  schema-markup/             # JSON-LD
  extra-components/          # charts/tables/interactive ideas
  drafts/                    # draft-v1.md, article-v1.html
  research-summary.md        # combined research overview
  article-plan.md            # final article plan
  article-draft.md           # markdown version (working copy)
  article-final.html         # HTML version (with embedded images + schema)
  internal-links.json        # internal/external link map
  schema.json                # final JSON-LD
```

**On completion**, copy the publish-ready pair into the site's `blog_dir`:
`<site_root>/<blog_dir>/<slug>.md` (or `.mdx`/`.html` to match the site's blog format) plus the
schema (inline `<script type="application/ld+json">` in the HTML, and `schema.json` alongside).
Never overwrite an existing published file without confirming format — additive only.

---

## Modernized Tooling Map (what each research step actually calls)

The original pipeline predates the current jambot tooling. This is the wiring — use these, not
ad-hoc web searches or hand-rolled rubrics. (Container mount path is `/mnt/shared-skills/...`;
host path is `/mnt/system/base/skills/...`. Use whichever exists in your environment.)

| Pipeline step | Use this skill/tool | Why |
|---|---|---|
| **Keyword research** (volume, difficulty, intent, suggestions) | **`dataforseo`** skill | Real search volume / keyword-difficulty / search-intent / suggestions. Batch keywords (up to 1,000/call). Auto-saved to the tenant SEO DB — the system of record for any rank/keyword claim. |
| **Live SERP / PAA / local pack / autocomplete** | **`serper-search`** skill | Google-shaped data cheaply: `peopleAlsoAsk` (free FAQ briefs), `knowledgeGraph`, `places`, `autocomplete`, `relatedSearches`. ~$0.001/query. |
| **Topic / FAQ / pain-point mining** | **`social-research`** skill | "Every customer question is a blog post." Reddit public JSON (zero cost) — real questions, complaints, objections, the language customers actually use. Feeds topic-research + faq-research. |
| **General web facts / source discovery** | built-in `web_search` first, then `serper-search` | Brave for general research; Serper when you need Google structure or Brave rate-limits. |
| **Phase 3 + Phase 8 quality gates** | **`quality-review`** skill | The ship/no-ship gate. Runs functional + visual checks on the HTML; we keep the score-8+/9+ auto-proceed behavior but route the decision through quality-review instead of an ad-hoc agent rubric. |
| **AI-visibility / GEO check** (optional) | `dataforseo` `serp/google/ai_mode` + `ai_optimization/llm_mentions` | Is the brand/topic cited in Google AI Mode / LLM answers? Informs angle + schema for snippet/AI-Overview targeting. |
| **Free domain authority** (optional, for picking authority links) | `dataforseo` skill → Ahrefs DR free endpoint | DR 0-100 to qualify which external sources are worth citing. |

**Invocation cheat-sheet** (full detail in each skill's SKILL.md):

```bash
# Keyword volume (DataForSEO — batch many keywords in ONE call)
AUTH=$(echo -n "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" | base64)
curl -s -X POST "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live" \
  -H "Authorization: Basic $AUTH" -H "Content-Type: application/json" \
  -d "[{\"keywords\":[\"$target_keyword\"],\"location_name\":\"$location\",\"language_name\":\"English\"}]"

# Keyword difficulty + suggestions (DataForSEO Labs — cheaper than live SERP)
curl -s -X POST "https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_suggestions/live" \
  -H "Authorization: Basic $AUTH" -H "Content-Type: application/json" \
  -d "[{\"keyword\":\"$target_keyword\",\"location_name\":\"$location\",\"language_name\":\"English\",\"limit\":50}]"

# People Also Ask + related searches (Serper — free FAQ + section ideas)
curl -s -X POST 'https://google.serper.dev/search' \
  -H "X-API-KEY: $SERPER_API_KEY" -H "Content-Type: application/json" \
  -d "{\"q\":\"$target_keyword\"}" | jq '.peopleAlsoAsk, .relatedSearches'

# Real customer questions / pain points (social-research — zero cost)
python3 /mnt/shared-skills/social-research/scripts/search_posts.py "$topic question" --sort top --time year --limit 25

# Quality gate (quality-review — gates Phase 3 and Phase 8; exit 0=PASS, 1=FAIL)
python3 /mnt/shared-skills/quality-review/check.py --dir <work_dir>/<slug> \
  --require "<required sections>" --out /tmp/qr-<slug>
python3 /mnt/shared-skills/quality-review/visual-check.py --url <served-html-url> \
  --viewports 390,1440 --out /tmp/qr-<slug>-visual
```

---

## The Phases (0 → 9)

> Each phase has a companion file in `phases/` with full detail. SKILL.md is self-sufficient as
> the entry point; read a phase file when you want the long form.
>
> **Full phase list:** Phase 0 (Knowledge Load & Gap-Analysis) → 1 (Setup) → 2 (Research +
> Distill) → 3 (Research quality gate) → 4 (Planning) → 5 (Drafting) → 6 (Enhancement) →
> 7 (HTML) → 8 (Final quality gate) → 9 (Schema) → **Completion** (write back to the brain).

### Phase 0 — Knowledge Load & Gap-Analysis  → AUTO-PROCEED
**File:** `phases/phase0-knowledge-load.md`
**Agent(s):** none / haiku (host reads files directly — fast + cheap).
**Inputs:** `knowledge_base` (the Tier-2 brain), `topic`, `target_keyword`.
**Do:** read the **WORKSPACE BRAIN** (Tier-2 distilled corpus — `topical-map.json`,
`keyword-corpus.json`, `authority-sources.json`, `faq-bank.json`, `field-knowledge/*.md`) — **NOT
the raw repo dumps**. Determine what's already known for this topic: which keywords are already
priced (in `keyword-corpus.json`), which authority sources are already vetted, which FAQs already
captured, which adjacent articles exist (for interlinking) and which sub-topics are still gaps.
Write `<work_dir>/<slug>/knowledge-load.md` = a **gap brief**: "ALREADY KNOWN (reuse, do NOT
re-research)" vs "GAPS (Phase 2 must research these)".
**Anti-waste:** this brief is what makes Phase 2 research **ONLY the gaps** — reuse cached
keywords/sources/FAQs instead of re-paying DataForSEO/Serper. If the brain is empty (first article
for this client), everything is a gap and Phase 2 runs full — but it still seeds the brain at the
end. → start Phase 1.

### Phase 1 — Setup  → AUTO-PROCEED
**File:** `phases/phase1-setup.md`
**Agent(s):** none (host does this directly).
**Inputs:** `topic`, `target_keyword`, `site_root`, `work_dir`, `knowledge_base`, brand fields, the
Phase-0 gap brief.
**Do:** resolve inputs + defaults, derive the slug, create the full Tier-1 directory layout under
`<work_dir>/<slug>/`, ensure the Tier-2 `<knowledge_base>/` brain dir exists (create the corpus
stub files if first run — empty `topical-map.json` etc.), seed an empty `research-summary.md`.
**Output:** directory tree + stub summary. → start Phase 2.

### Phase 2 — Research (PARALLEL) + Distill Bridge  → AUTO-PROCEED
**File:** `phases/phase2-research.md`
**Gap-scoped:** each agent reads the Phase-0 gap brief and **researches ONLY the gaps** — for the
"already known" items it pulls from the Tier-2 brain (`keyword-corpus.json`, `authority-sources.json`,
`faq-bank.json`) instead of re-paying DataForSEO/Serper. Cached + freshly-researched merge into the
same Tier-1 report.
**Agents (launch all in ONE message, parallel Task calls):**
1. **topic-research-agent** → `topic-research/topic-research-report.md` — background, key concepts,
   standards/regulations (generic to the topic), current trends, expert perspectives,
   misconceptions. Mines `social-research` + `web_search`/`serper-search`.
2. **keyword-research-agent** → `keyword-research/keyword-report.md` — primary (5-10), LSI (15-25),
   long-tail (20-40), semantic (10-20), question (10-20), local (if `location`-relevant), clusters.
   **Backed by `dataforseo`** (volume + difficulty + intent + suggestions) and `serper-search`
   (autocomplete + related searches).
3. **authority-link-research-agent** → `authority-link-research/authority-sources.md` — 10-15
   authoritative external sources with citations, URLs, an authority estimate (Ahrefs DR via
   dataforseo), where to place them, and anchor-text recommendations.
4. **faq-research-agent** → `faq-research/faq-report.md` — 10-20 PAA questions (from
   `serper-search`), forum/customer questions (from `social-research`), prioritized, with a
   recommended FAQ section structure.

**Wait for all 4 to complete.** All 4 reports are written into the **Tier-1 repo** (`<work_dir>/<slug>/`)
— the heavy raw artifacts (raw DataForSEO/SERP JSON, PAA dumps, candidate-source lists) stay there.

**DISTILL BRIDGE (runs after the 4 raw agents, before Phase 3 — haiku/GLM, mechanical):**
Extract the **durable/reusable** knowledge from the just-written RAW Tier-1 artifacts and **MERGE it
deduped into the Tier-2 workspace brain** (`<knowledge_base>/`):
- new priced keywords → `keyword-corpus.json` (dedupe on keyword; keep volume/difficulty/intent/source_slug)
- vetted external sources → `authority-sources.json` (dedupe on url; keep dr/topic/last_validated)
- distilled customer questions → `faq-bank.json` (dedupe on question; keep answer_gist/source/topic)
- durable industry/ops insight worth reusing everywhere → append/update `field-knowledge/<topic>.md`
Raw stays heavy + local to the site; the brain stays lean + shared. **Per-client isolated** — only
write under this tenant's `knowledge_base`. → Phase 3.

### Phase 3 — Quality Review (gate)  → AUTO-PROCEED
**File:** `phases/phase3-quality-gate.md`
**Tool:** **`quality-review`** skill (research completeness/coverage gate) + a
research-quality-reviewer-agent for the qualitative score.
**Do:** grade each research area for Completeness, Quality, Depth (enough for `word_target`),
Actionability. Score 1-10 per area; identify gaps; write `research-summary.md`.
**Autonomous handling (score-driven, route through quality-review):**
- **8+ →** AUTO-PROCEED to Phase 4.
- **6-7 →** AUTO-FIX: re-run the weak agent(s) with gap-filling prompts, re-gate.
- **<6 →** AUTO-FIX: re-run ALL research agents with detailed instructions, re-gate.
- Loop until PASS (8+). No caller notification.

### Phase 4 — Planning  → AUTO-PROCEED
**File:** `phases/phase4-planning.md`
**Agent:** article-planning-agent.
**Inputs:** all research + the Phase-3 summary.
**Output:** `article-outline-planner/article-outline.md` + root `article-plan.md` — SEO title
(<60 chars), meta description (150-160), intro (200-300w), H2/H3 sections with per-section word
allocation + key points + keywords, FAQ structure (8-12 Qs), conclusion (150-200w), totaling
`word_target`. → immediately start Phase 5.

### Phase 5 — Drafting  → AUTO-PROCEED
**File:** `phases/phase5-drafting.md`
**Agent:** article-draft-agent (or handle directly).
**Output:** `article-draft.md` (+ `drafts/draft-v1.md`) — follows the outline exactly,
`word_target` words, all research woven in, natural keyword integration, FAQ section, citations as
markdown links. Frontmatter uses `site_author`/`brand`/`target_keyword` — **never a hardcoded
name**. → immediately launch Phase 6.

### Phase 6 — Enhancement (PARALLEL)  → AUTO-PROCEED
**File:** `phases/phase6-enhancement.md`
**Agents (3, in parallel):**
1. **internal-linking-agent** → `internal-link-research/internal-links.json` — match phrases in the
   draft to REAL existing pages. **PRIMARY source = the Tier-2 brain's `topical-map.json`** (every
   prior article's slug/url/keyword + interlink graph across ALL the client's sites); fall back to
   `existing_articles` / crawl of `blog_dir` / sitemap. Anchor text, target URL, section, reason.
   **Only link to pages that exist.**
2. **article-design-agent** → `article-design/visual-plan.md` + **generates** 5-8 web-optimized
   images into `article-design/images/`. Prefer infographics / diagrams / data-viz / comparison /
   conceptual imagery. Use real photos from the site's own gallery for any real-world/people scenes
   rather than synthesizing them. Alt text (SEO) for each. Optimize each image (≤300KB, ≤1200px).
3. **authority-link-validator-agent** → `authority-link-research/validated-links.md` — test each
   external URL (200 OK, crawlable, still relevant), drop dead links, flag redirects, final list.

**Wait for all 3**, then Phase 7.

### Phase 7 — HTML Design  → AUTO-PROCEED
**File:** `phases/phase7-html-design.md`
**Agent:** html-design-agent.
**Output:** `article-final.html` (+ `drafts/article-v1.html`) — semantic HTML5, **embed all
generated images** from `article-design/images/` with alt text + responsive sizing, internal links
added, authority links with appropriate `rel`, mobile-first, proper heading hierarchy, list/table
formats for snippet targeting. Use the site's saved theme colors if a theme file exists; otherwise
neutral readable defaults (dark text on white, blue links — never light-on-light). → Phase 8.

### Phase 8 — Final Review (gate)  → AUTO-PROCEED
**File:** `phases/phase8-final-gate.md`
**Tool:** **`quality-review`** skill (`check.py` for routes/images/links/completeness/fabrication;
`visual-check.py` for contrast/overflow/broken-image at 390 + 1440) + an article-final-review-agent
for content parity (markdown ⇄ HTML), word count, keyword integration, FAQ completeness.
**Autonomous handling:**
- **9+ / quality-review PASS →** AUTO-PROCEED to Phase 9.
- **7-8 →** AUTO-FIX the findings (missing links, alt text, structure, contrast), re-gate.
- **<7 →** AUTO-FIX, possibly re-draft, re-gate.
- Loop until PASS. `quality-review` exit 1 = do not ship; fix and re-run.

### Phase 9 — Schema (final)  → COMPLETE
**File:** `phases/phase9-schema.md`
**Agent:** schema-markup-agent.
**Output:** `schema.json` (+ `schema-markup/schema.json`), embedded into `article-final.html` as
`<script type="application/ld+json">`. Implement: **Article** (headline, description, `author` =
`site_author`, datePublished/Modified, image, `publisher` = `brand`), **FAQPage** (from the FAQ
section → targets PAA), **BreadcrumbList**, **ImageObject** (per image), and **HowTo** if the
article is procedural. Optimize answers to 40-60 words for snippet/AI-Overview capture.
→ Completion step.

### Completion — Write Back to the Brain  → COMPLETE
**File:** `phases/phase0-knowledge-load.md` (Completion section — paired with Phase 0).
**Agent(s):** none / haiku (mechanical).
**Do (after Phase 9 ships the article):** update the **Tier-2 brain** (`<knowledge_base>/`) so the
work compounds:
- `topical-map.json` — add the finished article `{slug, site, target_keyword, status:"published",
  url, internal_links_in[], internal_links_out[]}`; update the `internal_links_in[]` of the pages
  this article links TO (back-reference); refresh `covered_topics[]`.
- **Recompute `gaps[]` / `next_topics[]`** — given the now-covered topics + the keyword corpus,
  list the strongest uncovered topics so the next run (its Phase 0) has a ready agenda.
- Ensure the final validated authority links + the article's FAQ entries are reflected in
  `authority-sources.json` / `faq-bank.json` (deduped — they may already be there from the Phase-2
  distill).
**Surface next topics** in the final report.
**Per-client isolated** — only `<knowledge_base>/` under this one tenant's workspace is touched.
**This is the only place the pipeline stops** — present the final deliverables summary (including
the brain updates + the surfaced next-topics).

---

## 💰 Cost Discipline — right model per phase (never weaken a gate)

**Frame:** never skip a phase or soften a gate — just don't *overpay* for the grunt work. The
two-tier corpus already removes re-paid research; model-discipline removes overpaid tokens.

| Phase | Kind of work | Model |
|---|---|---|
| **0 — Knowledge Load / Gap-Analysis** | read brain files, diff | **haiku / GLM** |
| **1 — Setup** | mkdir, stubs | **haiku / GLM** |
| **2 — Research (raw gather)** | API calls + summarize | **haiku / GLM** |
| **2 — Distill bridge** | extract + dedupe-merge into brain | **haiku / GLM** |
| **3 — Research quality gate** | ship/no-ship judgment | **sonnet** (capable enough to truly reject sub-bar research) |
| **4 — Planning** | the article's structure + angle | **sonnet** |
| **5 — Drafting** | the prose itself | **sonnet** |
| **6 — Enhancement (links/images/validate)** | mechanical | **haiku / GLM** |
| **7 — HTML design** | template-mechanical | **haiku / GLM** |
| **8 — Final quality gate** | ship/no-ship judgment | **sonnet** (must be able to reject) |
| **9 — Schema** | structured-data mechanical | **haiku / GLM** |
| **Completion — write back** | merge into brain | **haiku / GLM** |

- **sonnet** for Planning + Drafting (the thinking) and for BOTH quality gates (the gates must be
  capable enough to genuinely reject sub-bar work — a cheap gate that rubber-stamps is worse than
  no gate).
- **haiku / GLM** for every mechanical phase: raw-gather, distill, enhancement, HTML, schema, links,
  write-back.
- **opus NEVER.** It is not justified for any phase here.

Both quality gates and the autonomous-operation rule stay **fully intact** — cost discipline never
means skipping a phase, lowering a threshold, or stopping early.

---

## Success Criteria

- [ ] All phases (0–9 + Completion) completed autonomously (no caller intervention).
- [ ] Research quality gate PASS (8+ all areas) via quality-review.
- [ ] Article hits `word_target`.
- [ ] 5-10 internal links — real existing pages only.
- [ ] 10-15 authority links validated (200 OK) and placed.
- [ ] 5-8 images generated, optimized (≤300KB), embedded with SEO alt text.
- [ ] FAQ section with 8-12 questions.
- [ ] Schema implemented (3+ types) and embedded.
- [ ] Final gate PASS (9+ / quality-review PASS) on BOTH markdown and HTML.
- [ ] **Zero placeholders** — no `{{brand}}`, "Business Name", "example.com", lorem.
- [ ] Optimized for AI Overviews + featured snippets.
- [ ] **Phase 0 ran** — brain loaded, gap brief written, Phase 2 scoped to gaps (cached
      keywords/sources/FAQs reused, not re-paid).
- [ ] **Tier-2 brain updated** — Phase-2 distill merged + Completion wrote the article into
      `topical-map.json`, recomputed gaps/next-topics, deduped into corpus.
- [ ] **Per-client isolation honored** — brain written ONLY under this tenant's `knowledge_base`;
      nothing aggregated to the host or another tenant.

## Final Deliverables (present these, then stop)

**Tier 1 (RAW, in the site repo)** — root of `<work_dir>/<slug>/`: `research-summary.md`,
`article-plan.md`, `article-draft.md`, `article-final.html`, `internal-links.json`, `schema.json`,
`knowledge-load.md` (gap brief) — plus the publish-ready copy in `<site_root>/<blog_dir>/`.

**Tier 2 (PROCESSED, in the client's brain)** — updated `<knowledge_base>/`: `topical-map.json`
(now includes this article + recomputed gaps/next-topics), `keyword-corpus.json`,
`authority-sources.json`, `faq-bank.json`, `field-knowledge/*.md`.

Report: phases completed (0–9 + Completion), quality scores, files created, article stats (word
count, internal/external links, images, schema types), **brain deltas** (keywords/sources/FAQs
added, topics now covered), and **surfaced next-topics**.
