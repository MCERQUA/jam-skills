# Phase 7 — HTML Design (Designed Article, NOT a Document)

**Agent:** html-design-agent (sonnet for the design pass — this is the phase that decides whether the
output looks like a *crafted article* or a *plain document*; do not cheap-out the layout judgment).
**Inputs:** the markdown draft (`article-draft.md`), the visual plan + generated images
(`article-design/`), `internal-links.json`, validated authority links, the brand/theme inputs.
**Output:** `article-final.html` (+ `drafts/article-v1.html`). The markdown draft stays the
content source-of-truth; this phase is a **design transform**, never a content rewrite (content
parity is gated in Phase 8).

---

## 🎯 THE BAR — "real article", not "a document"

A plain markdown→HTML conversion (wall of prose + a couple of `<img>` + default link color) is a
**FAILURE of this phase**, even if the writing is excellent. The output must read like a designed,
modern editorial page: visual rhythm, components woven through the prose, scannable, branded.

**The design richness comes from COMPONENTS, not photos.** Reference pages that set the bar carry
only ~4 real images but **hundreds** of styled elements — gradient stat cards, colored callout
boxes, icon grids, comparison tables, pull-quotes, CTA blocks. That component density is what makes
a page feel "real." Photos are the garnish; **components are the meal.**

**Self-contained, no shared template.** Each article carries its OWN design system inline: one
`<style>` block + inline SVG icons, scoped under a single root class so it renders correctly wherever
it is dropped (a Next.js site, a static host, a canvas preview) with **zero external/build
dependency**. No Tailwind build, no icon-font CDN, no component import. Embedded `<style>` + inline
SVG only.

### Density rule (enforced — Phase 8 checks it)
Across the body, average **at least one non-prose visual element per ~400–500 words** — a callout,
stat grid, card grid, table, **data chart**, infographic/figure, or pull-quote. A 4,000-word article
therefore carries **8–12+** component blocks minimum, never two consecutive screens of unbroken
paragraphs. Lead with the hero, follow within the first screenful with a "Key Takeaways" block, and
close with a CTA. **Include at least one real data visualization** (a chart or a Gemini infographic)
whenever the article contains quantitative content — and most do.

---

## ⚠️ Three concrete markup bugs that passed Phase 8's score but broke on real render (2026-07-12)

A fleet run of 6 articles all scored 8.9-9.3 and "PASSED" Phase 8, then a rendered screenshot check
found 3 of the 6 had live bugs the score never caught. Avoid these when writing the HTML:

1. **Every CSS class that sets a `background`/`background-image` MUST be applied to a real element
   in the body — verify it, don't assume it.** The failure: `.aw-hero{background:linear-gradient(...)}`
   gets defined, but the body only uses sub-parts like `.aw-hero-eyebrow`/`.aw-hero-img` and never
   wraps them in `<div class="aw-hero">...</div>`. Result: the H1/dek/hero-image silently fall back to
   the page's plain background with no gradient, and any `.aw-hero h1{color:#fff}`-style child rule
   never applies (can leave text low-contrast). **Before finishing this phase**, grep every
   background-bearing class name against the body HTML and confirm each one is actually used as a
   `class="..."` value, wrapping all the content it's meant to contain.
2. **Never let a `display:flex` container's direct children include a bare inline tag mixed with
   sibling text.** `<li style="display:flex">icon-svg text <em>word</em> more text</li>` renders
   broken: flexbox treats the `<em>` as its OWN flex item, inserting the container's `gap` around it
   and killing natural text wrap (a word visually floats with dead space on both sides). **Always**
   wrap the ENTIRE text portion of a flex item in one block-level child, e.g.
   `<li><svg>...</svg> <span>text <em>word</em> more text</span></li>` — so the flex container has
   exactly 2 children (icon + text-span) no matter how much inline emphasis is inside the span. This
   applies to every flex-styled list item, callout, badge, or byline — not just `.aw-tldr li`.
3. **Use exactly one relative image-path convention for the whole article and never mix it with
   another.** If you reference generated images as `article-design/images/<file>.jpg`, use that
   EXACT prefix for every single `<img src>` — never drop to a bare `images/<file>.jpg` (missing
   segment) partway through. Downstream integration does a literal find-replace on the documented
   convention; a second undocumented one ships as a silently-broken image path that only a rendered
   screenshot (not a source read) reveals.
4. **NEVER emit an `@media (prefers-color-scheme: dark)` block.** The article renders inside the
   site's always-light shell — a per-article dark override desynchronizes from the page around it
   and ships dark-purple-on-dark headings and grey-on-light cards to every dark-mode phone (DSF
   incident 2026-07-19, 5 articles affected). One light theme, high contrast, period. Also keep
   every `display:grid` list/column at `grid-template-columns: minmax(0,1fr)` (or wider minmax
   forms) and give the article root `overflow-wrap: break-word; overflow-x: clip` — grid blowout
   and stray wide elements are the standing mobile-overflow classes.

**None of these are caught by reading the HTML source or by a content-completeness score** — they
only show up when the page is actually rendered. See Phase 8's gate for the mandatory
screenshot-based verification step this requires.

---

## The self-contained design system (emit this `<style>` at the top of the fragment)

Scope everything under a root class (default `.aw-article`) so it can't collide with a host site.
Drive all color from **CSS custom properties** resolved from the theme (below), so one variable
change re-themes the whole article.

```html
<style>
.aw-article{
  /* THEME TOKENS — resolved in the "Theme resolution" step below; these are the fallbacks */
  --brand:#3b82f6; --brand-600:#2563eb; --brand-700:#1d4ed8; --brand-50:#eff6ff;
  --ink:#0f172a; --body:#1f2937; --muted:#64748b; --bg:#ffffff; --card:#ffffff;
  --border:#e5e7eb; --tip:#059669; --tip-50:#ecfdf5; --warn:#b45309; --warn-50:#fffbeb;
  --info:#2563eb; --info-50:#eff6ff;
  --radius:16px; --shadow:0 1px 2px rgba(15,23,42,.06),0 8px 24px rgba(15,23,42,.06);
  --maxw:760px;
  color:var(--body); background:var(--bg);
  font:400 1.0625rem/1.7 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.aw-article *{box-sizing:border-box}
.aw-article .aw-wrap{max-width:var(--maxw);margin:0 auto;padding:0 20px}
.aw-article h1,.aw-article h2,.aw-article h3{color:var(--ink);line-height:1.2;letter-spacing:-.01em}
.aw-article h2{font-size:clamp(1.5rem,3.5vw,2rem);margin:2.5em 0 .6em;font-weight:750}
.aw-article h3{font-size:clamp(1.2rem,2.5vw,1.4rem);margin:1.8em 0 .4em;font-weight:700}
.aw-article p{margin:0 0 1.15em}
.aw-article a{color:var(--brand-700);text-decoration:underline;text-underline-offset:2px}
.aw-article a:hover{color:var(--brand-600)}
.aw-article a:focus-visible{outline:3px solid var(--brand-50);outline-offset:2px;border-radius:4px}

/* HERO */
.aw-hero{background:linear-gradient(135deg,var(--brand-700),var(--brand));color:#fff;padding:56px 20px;border-radius:0 0 var(--radius) var(--radius)}
.aw-hero .aw-wrap{max-width:var(--maxw)}
.aw-hero h1{color:#fff;font-size:clamp(2rem,5.5vw,3rem);font-weight:800;margin:0 0 .5em}
.aw-hero .aw-dek{color:#dbeafe;font-size:1.15rem;margin:0 0 1.2em;max-width:60ch}
.aw-meta{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;color:#bfdbfe;font-size:.9rem}
.aw-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.aw-chip{background:rgba(255,255,255,.16);color:#fff;border:1px solid rgba(255,255,255,.25);
  padding:5px 12px;border-radius:999px;font-size:.8rem;font-weight:600}

/* KEY TAKEAWAYS / TL;DR */
.aw-tldr{background:var(--brand-50);border:1px solid var(--border);border-left:5px solid var(--brand);
  border-radius:var(--radius);padding:22px 24px;margin:28px 0}
.aw-tldr h2{margin:0 0 .5em;font-size:1.15rem;color:var(--brand-700);display:flex;gap:10px;align-items:center}
.aw-tldr ul{margin:0;padding-left:0;list-style:none;display:grid;gap:10px}
.aw-tldr li{display:flex;gap:10px;align-items:flex-start}
.aw-tldr li svg{flex:0 0 20px;margin-top:3px;color:var(--brand)}

/* STAT CARDS */
.aw-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:28px 0}
.aw-stat{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  box-shadow:var(--shadow);padding:20px;text-align:center}
.aw-stat .n{font-size:clamp(1.6rem,4vw,2.1rem);font-weight:800;color:var(--brand-700);line-height:1.1}
.aw-stat .l{font-size:.85rem;color:var(--muted);margin-top:6px}

/* CALLOUTS */
.aw-callout{display:flex;gap:14px;border:1px solid var(--border);border-radius:var(--radius);
  padding:18px 20px;margin:24px 0;background:var(--card)}
.aw-callout svg{flex:0 0 22px;margin-top:2px}
.aw-callout .t{font-weight:700;color:var(--ink);margin:0 0 4px}
.aw-callout.is-key{background:var(--brand-50);border-left:5px solid var(--brand)} .aw-callout.is-key svg{color:var(--brand)}
.aw-callout.is-info{background:var(--info-50);border-left:5px solid var(--info)} .aw-callout.is-info svg{color:var(--info)}
.aw-callout.is-tip{background:var(--tip-50);border-left:5px solid var(--tip)} .aw-callout.is-tip svg{color:var(--tip)}
.aw-callout.is-warn{background:var(--warn-50);border-left:5px solid var(--warn)} .aw-callout.is-warn svg{color:var(--warn)}

/* CARD GRID (parallel items: coverage types, steps, benefits) */
.aw-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:28px 0}
.aw-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  box-shadow:var(--shadow);padding:22px}
.aw-card .ic{width:44px;height:44px;display:grid;place-items:center;border-radius:12px;
  background:var(--brand-50);color:var(--brand-700);margin-bottom:12px}
.aw-card h3{margin:.2em 0 .3em;font-size:1.1rem}
.aw-card p{margin:0;color:var(--muted);font-size:.95rem}

/* COMPARISON TABLE */
.aw-tablewrap{overflow-x:auto;margin:26px 0;border:1px solid var(--border);border-radius:var(--radius)}
.aw-table{width:100%;border-collapse:collapse;min-width:480px;font-size:.95rem}
.aw-table th{background:var(--brand-700);color:#fff;text-align:left;padding:13px 16px;font-weight:650}
.aw-table td{padding:12px 16px;border-top:1px solid var(--border)}
.aw-table tr:nth-child(even) td{background:#f8fafc}

/* PROS / CONS */
.aw-pc{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:26px 0}
@media(max-width:560px){.aw-pc{grid-template-columns:1fr}}
.aw-pc .col{border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;background:var(--card)}
.aw-pc .col h3{margin:0 0 .5em;font-size:1.05rem}
.aw-pc li{display:flex;gap:9px;align-items:flex-start;margin:8px 0;list-style:none}
.aw-pc .pros svg{color:var(--tip)} .aw-pc .cons svg{color:#dc2626}
.aw-pc ul{padding:0;margin:0}

/* PULL QUOTE */
.aw-quote{border-left:5px solid var(--brand);background:var(--brand-50);border-radius:0 var(--radius) var(--radius) 0;
  padding:18px 24px;margin:28px 0;font-size:1.2rem;font-weight:600;color:var(--ink)}

/* FIGURE */
.aw-figure{margin:28px 0}
.aw-figure img{width:100%;height:auto;border-radius:var(--radius);border:1px solid var(--border);display:block}
.aw-figure figcaption{color:var(--muted);font-size:.85rem;margin-top:8px;text-align:center}

/* DATA CHART (native inline SVG) */
.aw-chart{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  box-shadow:var(--shadow);padding:22px 20px 14px}
.aw-chart svg{width:100%;height:auto;display:block;overflow:visible}
.aw-chart .axis{stroke:var(--border);stroke-width:1}
.aw-chart .grid{stroke:var(--border);stroke-width:1;stroke-dasharray:3 4;opacity:.7}
.aw-chart .bar{fill:var(--brand)} .aw-chart .bar-alt{fill:var(--brand-700)}
.aw-chart .line{fill:none;stroke:var(--brand);stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
.aw-chart .vlabel{fill:var(--ink);font-size:12px;font-weight:700} .aw-chart .clabel{fill:var(--muted);font-size:11px}
.aw-chart .sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}

/* FAQ ACCORDION */
.aw-faq{margin:28px 0;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.aw-faq details{border-top:1px solid var(--border)} .aw-faq details:first-child{border-top:0}
.aw-faq summary{cursor:pointer;padding:16px 20px;font-weight:650;color:var(--ink);list-style:none;
  display:flex;justify-content:space-between;gap:12px;align-items:center;min-height:44px}
.aw-faq summary::-webkit-details-marker{display:none}
.aw-faq summary .chev{transition:transform .2s} .aw-faq details[open] summary .chev{transform:rotate(180deg)}
.aw-faq .a{padding:0 20px 16px;color:var(--body)}

/* CTA */
.aw-cta{background:linear-gradient(135deg,var(--brand-700),var(--brand));color:#fff;border-radius:var(--radius);
  padding:34px 28px;margin:36px 0;text-align:center}
.aw-cta h2{color:#fff;margin:0 0 .4em} .aw-cta p{color:#dbeafe;margin:0 0 1.2em}
.aw-btn{display:inline-flex;align-items:center;gap:8px;background:#fff;color:var(--brand-700);
  font-weight:700;padding:13px 26px;border-radius:999px;text-decoration:none;min-height:44px}
.aw-btn:hover{color:var(--brand-700);background:#f1f5f9}

@media(prefers-reduced-motion:reduce){.aw-article *{transition:none!important}}
</style>
```

> Tune the numbers/spacing per article, but keep the **token-driven** structure and the **scoped
> root class**. Never inline raw hex in component markup — always `var(--…)` so theme resolution works.

---

## Inline SVG icon set (no emoji, no icon-font — paste the paths you need)

Per the platform UI rule (**no emojis**), use inline `<svg>` 24×24 stroke icons. Minimum set:

- **check** `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" width="20" height="20"><path d="M20 6 9 17l-5-5"/></svg>`
- **x** `<path d="M18 6 6 18M6 6l12 12"/>`
- **info** `<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>`
- **alert** `<path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>`
- **bulb/tip** `<path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2Z"/>`
- **shield** `<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>`
- **chevron** (FAQ) `<path d="m6 9 6 6 6-6"/>`
- plus topic-appropriate icons for card grids (truck, document, dollar, etc.).

Give each decorative icon `aria-hidden="true"`; icons that carry meaning get an accessible label.

---

## Markdown → component mapping (how to transform, not rewrite)

Walk the draft and lift structures into components — **without changing the words**:

| In the draft… | Render as |
|---|---|
| Title + meta + intro lede | `.aw-hero` (gradient) with H1, dek, byline/meta, tag chips |
| The 3–6 most important points (synthesize from intro/conclusion) | `.aw-tldr` "Key Takeaways" near the top |
| Any cluster of numbers/figures (costs, %, counts) | `.aw-stats` stat cards |
| A sentence flagged *key/important/note/remember* | `.aw-callout.is-key` |
| A *warning/risk/penalty/avoid* point | `.aw-callout.is-warn` |
| A *tip/pro-tip/save money* point | `.aw-callout.is-tip` |
| A definition/context aside | `.aw-callout.is-info` |
| Parallel items (coverage types, steps, benefits, requirements) | `.aw-cards` icon card grid |
| Side-by-side / "vs" / advantages-and-considerations | `.aw-table` **or** `.aw-pc` pros/cons |
| Comparison data, price ranges, requirement matrices | `.aw-table` **and/or** an `.aw-chart` bar chart |
| **3+ related numbers** (costs by category, %, trends, breakdowns) | `.aw-chart` native SVG **bar / line / pie / donut** from the real values |
| A strong quotable line / stat | `.aw-quote` pull-quote |
| The FAQ section | `.aw-faq` `<details>` accordion |
| Generated images / Gemini infographics from `article-design/images/` | `.aw-figure` with caption + alt |
| Conclusion / next step | `.aw-cta` gradient block with one clear `.aw-btn` |

Body prose stays in `<p>`/`<ul>` with the typographic styles. Every internal link
(`internal-links.json`) and validated authority link gets embedded in context — authority links
`rel="nofollow noopener" target="_blank"`, internal links plain.

---

## Visuals — bring the article to life (images + REAL data viz)

Modern articles are **visual**. Two distinct kinds of visual, used for different jobs — use BOTH,
generously:

### 1. Generated imagery + infographics (Phase 6, embedded here)
Embed every image from `article-design/images/` via `.aw-figure` (SEO alt + `loading="lazy"`).
Phase 6 produces these via `asset-briefs.json` → the **ChatGPT lane** (mac-claude browser delegate —
excellent infographics, diagrams, and programmatically-plotted charts) with **FLUX-via-HF-router
fallback**. Use real photos from the site gallery when you have a genuine on-location shot, but you
are **not** restricted from AI imagery — generate freely.
If `images/` is empty, return to Phase 6 and generate first. Alt/placement come from the brief —
keep them; cross-check every `<img src>` filename against what actually landed in `images/` (the
ChatGPT lane can deliver a subset — never reference an undelivered file).

### 2. Native inline-SVG data charts (built HERE, from the article's REAL numbers)
For **quantitative** content — costs, percentages, ranges, trends, breakdowns — render an actual
**chart**, not a sentence and not a Gemini picture. **Do NOT ask Gemini/any image model to draw data
charts: it fabricates the numbers.** Build charts as **inline `<svg>`** from the real figures so they
are accurate, self-contained, theme-colored (`var(--brand…)`), crisp at any size, and accessible.

Render whichever fits the data:
- **Bar / column** — comparisons across categories (premium by trade, cost by coverage type).
- **Line** — trends over time (rates by year, growth).
- **Pie / donut** — parts of a whole (where the premium dollar goes, market share).
- **Horizontal bar / progress** — rankings, "X of Y", score-style metrics.

Pattern (themeable, accessible — give every chart `role="img"` + `aria-label`, and a `<figcaption>`;
for complex charts add a visually-hidden `<table>` fallback so the data is machine + screen-reader
readable). Bars/slices use `var(--brand)`, `var(--brand-700)`, `var(--tip)`, `var(--warn)` etc.:

```html
<figure class="aw-figure aw-chart">
  <svg viewBox="0 0 480 260" role="img" aria-label="Average annual premium by trade: electrical $4,200; HVAC $3,800; plumbing $3,500">
    <!-- axis lines, then one <rect> per bar at computed x/height, fill="var(--brand)",
         value labels in <text fill="var(--ink)">, category labels in <text fill="var(--muted)"> -->
  </svg>
  <figcaption>Average annual GL premium by trade (2025)</figcaption>
</figure>
```

Compute geometry from the data (don't hardcode a screenshot): map each value to a bar height/slice
angle, label axes, add gridlines. Keep ≤ ~8 series so it stays legible on mobile.

**Rule of thumb:** any section that states 3+ related numbers earns a chart. If a slot has neither a
real photo, a credible infographic, nor chartable data, use a styled component (stat grid / card /
callout) — never ship a weak or fake-looking filler image.

---

## Theme resolution (drives every `var(--…)`)

1. If `<site_root>/ai/knowledge/blog-theme.json` (or a theme passed by the caller) exists, map its
   palette onto the tokens (`--brand`, `--brand-700`, `--brand-50`, `--ink`, …).
2. Else derive `--brand` from the site/brand (e.g. the brand's primary color if known); default to
   the platform blue family already in the fallbacks.
3. **Never purple** (platform rule). **Never light-on-light** — enforce AA contrast: body text ≥
   4.5:1 on its background, hero/CTA text on the gradient ≥ 4.5:1. White or near-white text on the
   brand gradient; dark `--ink` on light surfaces.
4. Byline = `site_author` / `brand` inputs — never a hardcoded name, never a leftover `{{brand}}`.

---

## Output structure

`article-final.html` is a self-contained fragment (drop-in safe) in this order:

1. `<style>` block (scoped `.aw-article`)
2. `<article class="aw-article">`
   - `<header class="aw-hero">` (H1, dek, meta, chips)
   - `<div class="aw-wrap">` … all body sections, components woven through per the mapping …
     - Key Takeaways → stat grid → sectioned content with callouts/cards/tables/figures/quotes
     - FAQ accordion
     - CTA block
   - (Phase 9 injects the JSON-LD `<script>`; leave the `<!-- schema: injected in Phase 9 -->`
     marker where it goes — do not hand-write schema here.)
3. `</article>`

Also write `drafts/article-v1.html`. Keep `article-draft.md` as the content source-of-truth (Phase 8
diffs HTML⇄markdown for parity — the design transform must not add or drop content, only style it).

→ Phase 8 (final gate now ALSO verifies: density rule met, ≥4 distinct component types used, hero +
Key-Takeaways + CTA present, AA contrast, no emoji, no `{{…}}` placeholder, images embedded with alt).
