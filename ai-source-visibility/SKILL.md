---
name: ai-source-visibility
description: "Intelligence on how ChatGPT (and other AI search systems) pick, fetch, and cite sources. Use when advising clients on content strategy for AI search visibility, building AI-optimized pages, or explaining why a client is/isn't cited in AI answers."
version: 1.0.0
source: https://suganthan.com/blog/how-chatgpt-picks-sources/
---

# AI Source Visibility — How ChatGPT Picks Sources

Research by Suganthan (2026) via browser DevTools traffic analysis of ~1,240 source records across a Pro ChatGPT account.

---

## The Four Source Pipelines

ChatGPT tags every source with a `result_source` field — one of four values:

| Pipeline | Provider | Content type |
|----------|----------|--------------|
| `labrador` | Licensed publishers (Reuters, WSJ, Wikipedia, TechRadar) | Full article extracts (~1,080 chars) |
| `bright` | Bright Data scraper | Shopping, finance, weather queries |
| `oxylabs` | Oxylabs scraper | Regional/local content |
| `serp` | Open web baseline | Mostly news sources |

---

## Query Classification — What Triggers Search

ChatGPT classifies every question into a `turn_use_case` bucket. **Search only fires for certain buckets.**

- **`text`** — answers from training data only. No web fetch. No sources. Even "latest treatment guidelines" can land here.
- **`shopping`** — routes to Bright Data
- **`local`** — routes to Oxylabs, caps at 2 results
- **`instant_search`**, **`thinking`**, **`image_generation`** — each fires a different pipeline

**Critical insight:** wording determines classification, not topic. A question about current medical guidelines got classified as `text` and skipped search entirely. Before optimizing a page for ChatGPT visibility, verify the target query actually fires a search request.

---

## Three Distinct Outcomes

Being "in ChatGPT" is not binary:

| Outcome | What it means |
|---------|---------------|
| **Fetched** | Page entered model context (invisible to reader) |
| **Cited** | Page became a footnote source for a specific claim |
| **Mentioned** | Brand appeared in the answer but was NOT the source |

Reddit was fetched 278 times but cited only 11 times. YouTube was fetched 201 times but cited zero times — video metadata has no extractable text.

**Brand mentions do not equal citations.** Citations require textual content the model can extract and attribute.

---

## What Gets Cited

- **Official pages** → cited for their own facts (pricing, specs)
- **Third-party review sites** (Rtings, TechRadar, G2) → cited for opinions and comparisons
- **Reddit** → most-cited domain overall (despite low cite-to-fetch ratio)
- **Video** → never cited (metadata only, no extractable text)

Results deduplicate by domain — multiple weak pages from the same domain collapse into one entry.

---

## The JavaScript Problem

When the thinking model hit a page with JavaScript-loaded content (pricing tables, dynamic grids), it explicitly noted it couldn't read it and fell back to third-party sources (G2, review sites) for the data.

This is a hard block — not a ranking disadvantage, a complete content failure.

---

## Actionable Optimization Rules

### For getting fetched and cited

1. **All facts in plain HTML** — pricing, specs, dates: never behind JavaScript or in images
2. **Include currency symbols** ($, €) on pricing pages — model pattern-matches on them
3. **Probe your own pages:** `site:yourdomain.com/pricing` must return readable content in ChatGPT search
4. **Build one strong page per claim** — thin pages for every fanout query underperform one authoritative page

### For building citation authority

5. **Earn third-party coverage** on Reddit, review sites (G2, TechRadar, Rtings) — these are the most cited external validators
6. **Text > video** — even for products with demo videos, a text description is what gets cited
7. **Official pages for facts, third-party for opinions** — know which role your pages serve

### For prioritization

8. **Verify search fires** — check that target queries trigger network requests before investing in optimization
9. **Stop treating ChatGPT like Google** — it reads context differently; 278 fetches → 11 cites means raw traffic intuition doesn't apply
10. **Local search caps at 2 results** — for local businesses, the competition is tighter than organic

---

## Limitations of the Research

- Single Pro account, tech/SaaS query bias — frequency data is directional, not absolute
- Server-side ranking logic not visible (only client-side fetch records)
- Personalization from user history affects results
- Shopping data has small sample contradictions
- AI Overviews / Gemini / Perplexity have different pipelines (forthcoming in the research series)

---

## Application to JamBot Clients

When a client asks "why isn't ChatGPT citing us":
1. Test their target queries — does search even fire?
2. Run `site:theirdomain.com` in ChatGPT — does it find their pages?
3. Check if key pages use JS-rendered content (common with React/Next.js storefronts)
4. Check if they have third-party coverage (Reddit threads, review site mentions)
5. Compare fetched vs cited — they may be in context but not textually citable

When building content for AI visibility:
- Static HTML for all factual claims
- Structured text (tables, lists, definitions) — extractable by pattern
- One canonical authoritative page per claim, not a microsite of thin pages
