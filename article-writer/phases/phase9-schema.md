# Phase 9 — Schema Markup (final phase)

**Agent:** schema-markup-agent. **Inputs:** final HTML, article metadata, FAQ section.
**Output:** `schema.json` (+ `schema-markup/schema.json`), embedded into `article-final.html`.

## Schema types
1. **Article** — `headline`, `description`, `author` = `site_author` (resolved input),
   `datePublished`, `dateModified`, `image`, `publisher` = `brand` (resolved input).
2. **FAQPage** — each Q&A from the FAQ section → targets PAA boxes.
3. **HowTo** — only if the article is procedural (step-by-step).
4. **BreadcrumbList** — navigation path (use `site_url` + `blog_dir`).
5. **ImageObject** — for each embedded image.

> `author`/`publisher` come from inputs — never a hardcoded business name.

## Optimization
- Concise 40-60-word answers for snippet / AI-Overview capture.
- Structured data for every Q&A pair. Valid JSON-LD (`@context`, `@type`).
- Embed as `<script type="application/ld+json">…</script>` in `article-final.html`.

## Completion (the ONLY stop point)
Copy the publish-ready pair into `<site_root>/<blog_dir>/<slug>.*` (match the site's blog format).
Then present the final summary: 9 phases done, quality scores, files created, article stats
(word count, internal/external links, images, schema types). This is the only place the pipeline stops.
