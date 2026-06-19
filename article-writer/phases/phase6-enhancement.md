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
Plan AND generate 5-8 images into `article-design/images/`.

**Image content rule (generalized):** prefer **infographics, diagrams, data-visualizations,
comparison images, conceptual/abstract graphics**. For any real-world / people / on-location scene,
use **real photos from the site's own gallery** (e.g. `<site_root>/public/gallery/`) rather than
synthesizing them — AI-rendered people/equipment look fake and hurt credibility. (This is a general
rule, not niche-specific.)

For each image: SEO alt text, placement recommendation. Naming: `01-featured-hero.*`,
`02-*-infographic.*`, etc. Generate with the available image tool, 1K (~1024px), then optimize:
≤1200px wide, ~80% quality, **≤300KB each**. Do NOT skip generation — prompts without images are useless.

## 3. authority-link-validator-agent → `authority-link-research/validated-links.md`
Test every external URL: 200 OK, crawlable (no noindex/robots block), still exists and relevant,
DR estimate. Drop dead links, flag redirects. Produce the final approved link list.

## Hand-off
All 3 done → Phase 7 (create HTML). Do not ask.
