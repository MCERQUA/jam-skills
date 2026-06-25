#!/usr/bin/env python3
"""
build_gen_prompt.py — assemble the deterministic generation prompt + context for the
bulk body writer (GLM/haiku). Emits a single prompt on stdout.

The prompt is engineered so the cheap model produces an article that PASSES the
deterministic gates on the first or second try:
  - frontmatter with title (<=65), description (120-165), date, slug
  - >= min_h2 H2 sections, a >=40-word intro, CTA to a money page
  - >= min_internal_total internal links (>=1 money page, >=1 other blog) using
    the EXACT slugs/paths we pass in (so they resolve live)
  - >= min_outbound outbound links to the EXACT high-authority URLs we pass in
    (pre-vetted host list → guarantees the authority gate passes)
  - a FAQ section (## Frequently Asked Questions) with >=3 Q/A

Usage: build_gen_prompt.py <config.json> <topic_json> <authority_json> <internal_json>
  topic_json     : {"topic","target_keyword","slug"}
  authority_json : ["https://...","https://..."]   (pre-vetted, live, high-DR)
  internal_json  : {"money":[{"path","label"}...], "blogs":[{"path","title"}...]}
"""
import json
import sys


def main():
    cfg = json.load(open(sys.argv[1]))
    topic = json.load(open(sys.argv[2]))
    authority = json.load(open(sys.argv[3]))
    internal = json.load(open(sys.argv[4]))
    g = cfg.get("gates", {})

    min_h2 = g.get("min_h2", 4)
    min_words = g.get("min_words", 1000)
    md_min = g.get("meta_desc_min", 120)
    md_max = g.get("meta_desc_max", 165)
    min_out = g.get("min_outbound", 4)

    desc_key = cfg.get("frontmatter_desc_key", "description")
    title_max = g.get("title_max", 65)
    auth_lines = "\n".join(f"  - {u}" for u in authority)
    money_lines = "\n".join(f"  - [{m['label']}]({m['path']})" for m in internal["money"])
    blog_lines = "\n".join(f"  - [{b['title']}]({b['path']})" for b in internal["blogs"])
    extra_fm = ""
    if desc_key == "excerpt":
        # this site's renderer also reads author/category/coverImage from frontmatter
        extra_fm = (f'author: "{cfg.get("site_author", cfg["brand"])}"\n'
                    f'category: "Insurance Guide"\n')

    prompt = f"""You are writing ONE publication-ready blog article for {cfg['brand']}
({cfg['site_url']}), an insurance agency site. Write for business owners researching
coverage — clear, authoritative, specific, no fluff, no hype, no emoji.

TOPIC: {topic['topic']}
PRIMARY KEYWORD: {topic['target_keyword']}
SLUG (use exactly): {topic['slug']}

OUTPUT FORMAT — emit a single Markdown (.mdx) document and NOTHING ELSE. Start with
YAML frontmatter delimited by --- lines, then the body. Frontmatter MUST be:
---
title: "<compelling title, <= {title_max} characters, includes the keyword naturally>"
{desc_key}: "<meta description, BETWEEN {md_min} AND {md_max} characters>"
date: "{topic.get('date','')}"
slug: "{topic['slug']}"
{extra_fm}---

BODY REQUIREMENTS (all are hard requirements — the article is auto-rejected if any fail):
1. At least {min_words} words.
2. An intro paragraph of at least 40 words BEFORE the first ## heading.
3. At least {min_h2} second-level (##) section headings. Use ### sub-headings where useful.
4. A clear call-to-action linking to a money page (use one of the internal money-page
   links below, e.g. "[get a free quote](/quote)").
5. Weave in AT LEAST these INTERNAL links (use the exact paths, descriptive anchor text):
   Money pages (link at least one):
{money_lines}
   Other blog posts on this site (link at least one):
{blog_lines}
6. Weave in AT LEAST {min_out} OUTBOUND links to these PRE-VETTED high-authority sources.
   Use EXACTLY these URLs (do not invent others), each inline where it backs a specific
   claim/stat/regulation, with descriptive anchor text (never "click here"):
{auth_lines}
7. End with a section titled "## Frequently Asked Questions" containing AT LEAST 3
   question/answer pairs. Format each question as a "### <question>" sub-heading
   followed by a 40-60 word answer paragraph (optimized for featured snippets).

STYLE: markdown only — ## / ### headings, **bold**, - bullet lists, and
[anchor](url) links. Do NOT output HTML, do NOT output JSON-LD (schema is added
separately), do NOT add a code fence around the document. Begin with the --- frontmatter
line immediately."""
    print(prompt)


if __name__ == "__main__":
    main()
