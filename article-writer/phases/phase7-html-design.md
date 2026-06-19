# Phase 7 — HTML Design & Conversion

**Agent:** html-design-agent. **Inputs:** markdown draft, visual plan + generated images, internal
links JSON, validated authority links. **Output:** `article-final.html` (+ `drafts/article-v1.html`).

## Requirements
- Semantic HTML5 (`header`/`main`/`article`/`section`/`footer`), proper H1>H2>H3 hierarchy.
- **Embed ALL generated images** from `article-design/images/`:
  `<img src="./article-design/images/01-featured-hero.png" alt="<seo alt>" loading="lazy" style="max-width:100%;height:auto">`
  placed per the visual plan. If `images/` is empty, go back to Phase 6 and generate first.
- All internal links embedded; authority links with appropriate `rel` (e.g. `nofollow noopener`,
  `target="_blank"`).
- Mobile-first responsive; list + table formats where they aid **featured-snippet / AI-Overview**
  targeting (clear, concise answers; comparison tables).
- Schema.org placeholder comment for Phase 9.

## Theme colors (generic, readable — never light-on-light)
If the site has a saved theme file (e.g. `<site_root>/ai/knowledge/blog-theme.json`), use it.
Otherwise neutral readable defaults: background `#ffffff`, text `#1f2937`, headings `#111827`,
links `#2563eb`, accent `#3b82f6`, muted `#6b7280`. Byline uses `site_author` / `brand` inputs —
no hardcoded name. → Phase 8.
