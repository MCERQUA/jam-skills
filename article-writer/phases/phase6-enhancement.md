# Phase 6 — Enhancement (PARALLEL, 3 agents)

Launch all 3 in parallel; wait for all before Phase 7.

## 1. internal-linking-agent → `internal-link-research/internal-links.json`
Find phrases in the draft that match REAL existing pages. **PRIMARY source = the Tier-2 brain's
`<knowledge_base>/topical-map.json`** — its `articles[]` give every prior article's `slug`/`url`/
`target_keyword` + the interlink graph across ALL the client's sites, so cross-site interlinking is
ready without re-crawling. Fall back to `existing_articles` if provided, else crawl
`<site_root>/<blog_dir>` or the site's sitemap.
Each entry: `anchor_text`, `target_url`, `section`, `reason`. **Only link to pages that exist** —
verify before including. 5-10 links. (These chosen targets feed the Completion write-back, which
records this article's `internal_links_out[]` and back-references each target's `internal_links_in[]`
in `topical-map.json`.)

```json
{ "internal_links": [
  { "anchor_text": "...", "target_url": "/blog/<existing-slug>", "section": "...", "reason": "..." }
]}
```

## 2. article-design-agent → `article-design/visual-plan.md` + generates images
Plan AND generate **6-10** images into `article-design/images/` — bring the article to life.

**Generate freely with Gemini.** Image generation is strong now — use the **`gemini-image`** skill
(`gemini-2.5-flash-image`, or `gemini-3-pro-image-preview` for hero/best quality) for **infographics,
diagrams, cutaways, comparison visuals, conceptual/explainer graphics, and hero art**. Gemini makes
great infographics — lean into it. Use a real photo from the site gallery
(`<site_root>/public/gallery/`) when you genuinely have an on-location shot, but there is **no
restriction** on AI imagery — generate it.

**Split of responsibilities (important):**
- **Gemini infographics / visual graphics** → generated HERE as images (`article-design/images/`).
- **Accurate DATA charts** (bar / line / pie / donut from the article's real numbers) → **NOT generated
  as images.** Image models fabricate chart numbers. Those are built in **Phase 7 as native inline
  SVG** from the real figures. In `visual-plan.md`, flag which quantitative sections should get a
  native chart (and the actual numbers), so Phase 7 renders them — do not try to make Gemini draw them.

For each image: SEO alt text + placement recommendation. Naming: `01-featured-hero.*`,
`02-*-infographic.*`, `03-*-diagram.*`, etc. Generate at ~1K (1024px+), then optimize: ≤1600px wide,
~80% quality, **≤350KB each**. Do NOT skip generation — prompts without images are useless.

## 3. authority-link-validator-agent → `authority-link-research/validated-links.md`
Test every external URL: 200 OK, crawlable (no noindex/robots block), still exists and relevant,
DR estimate. Drop dead links, flag redirects. Produce the final approved link list.

## Hand-off
All 3 done → Phase 7 (create HTML). Do not ask.
