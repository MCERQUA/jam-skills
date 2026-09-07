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

## 2. article-design-agent → `article-design/visual-plan.md` + `asset-briefs.json` + generates images
Plan AND deliver **6-10** images into `article-design/images/` — bring the article to life.

**STEP A — Write the asset brief list FIRST: `article-design/asset-briefs.json`.** This is the
contract every generation lane consumes (and the audit trail of what was asked for):

```json
{ "slug": "<article-slug>", "delivery_dir": "<abs path to article-design/images/>",
  "brand": { "name": "...", "colors": ["#..."], "logo": "<path-or-url>" },
  "assets": [
    { "id": "01", "filename": "01-featured-hero.png", "type": "hero",
      "aspect": "16:9", "prompt": "<full generation prompt incl. brand colors/style>",
      "alt": "<SEO alt text>", "placement": "<section>" },
    { "id": "04", "filename": "04-rvalue-comparison-chart.png", "type": "data-chart",
      "aspect": "4:3", "chart_kind": "grouped-bar",
      "data": { "labels": ["Open-cell","Closed-cell","Fiberglass"], "series": [{"name":"R per inch","values":[3.7,6.5,3.2]}] },
      "prompt": "Plot this data PROGRAMMATICALLY (code interpreter / matplotlib) — exact values as given, never freehand-draw. Style: clean, brand colors, large labels.",
      "alt": "...", "placement": "..." }
  ] }
```

Asset types: `hero`, `infographic`, `diagram`, `comparison`, `photo-treatment`, `data-chart`.

**STEP B — Generate, in this lane order:**
1. **ChatGPT (preferred for infographics, diagrams, and graphs).** ChatGPT's image + code-interpreter
   combo produces excellent infographics AND *accurate* charts. Route by node:
   - Agent **with a desktop browser** (mac nodes): drive the on-screen ChatGPT browser directly
     (method: `social-media-designer` skill / node memory `branded-social-images-drive-chatgpt-browser`).
   - Agent **without a browser** (VPS/container — the normal case): **mesh-delegate to `mac-claude@mesh`**:
     `mesh-send --to mac-claude@mesh --kind delegate --subject "article assets: <slug>"` with the body
     pointing at `asset-briefs.json` + the `delivery_dir` (both on the shared mesh-visible filesystem;
     copy the briefs file under `/mnt/agent-mesh/` handoff space if the work_dir isn't mesh-readable).
     mac-claude generates each asset in ChatGPT and writes files to `delivery_dir` named exactly per
     `filename`. **Poll `delivery_dir` up to 30 min**; integrate whatever lands.
2. **Fallback / top-up — FLUX via the HF router** for any asset not delivered in time (as of
   2026-07-17 the Gemini/OpenAI/FAL image keys are dead; if `gemini-image` works again it's also fine
   for conceptual art). **Working recipe (verified 2026-07-19):** HF router with provider
   `fal-ai`, model `flux/schnell` (`fal-ai/fal-ai/flux/schnell`), HF_TOKEN from
   `/mnt/system/base/.platform-keys.env`, and send a real browser `User-Agent` header (default UA
   hits a Cloudflare 1010 bot-block). The `hf-inference` provider's FLUX endpoints are
   deprecated/410 — don't retry them. Never ship with an empty `article-design/images/` — prompts without images
   are useless.
3. Use a real photo from the site gallery (`<site_root>/public/gallery/` or `public/images/`) when you
   genuinely have an on-location shot — real job photos beat AI art for trust content.

**DATA-ACCURACY rule (unchanged in spirit):** no image model may *freehand-draw* numbers. A
`data-chart` brief is allowed ONLY because it embeds the exact figures and instructs programmatic
plotting (ChatGPT code interpreter). Default for quantitative sections remains **Phase 7 native
inline SVG** from the real figures — in `visual-plan.md`, flag which sections get a native chart
(with the actual numbers). Use `data-chart` briefs for the richer styled/annotated chart moments.

For each image: SEO alt text + placement recommendation. Naming: `01-featured-hero.*`,
`02-*-infographic.*`, `03-*-diagram.*`, etc. Target ~1K (1024px+), then optimize: ≤1600px wide,
~80% quality, **≤350KB each**. Record in `visual-plan.md` which lane produced each delivered file.

## 3. authority-link-validator-agent → `authority-link-research/validated-links.md`
Test every external URL: 200 OK, crawlable (no noindex/robots block), still exists and relevant,
DR estimate. Drop dead links, flag redirects. Produce the final approved link list.

## Hand-off
All 3 done → Phase 7 (create HTML). Do not ask.
