#!/usr/bin/env python3
"""
check-components.py — DETERMINISTIC required-components gate (no LLM).

Verifies the staged article has every required structural component:
  title, meta description (length-checked), H1 (from title), H2/H3 hierarchy,
  intro, minimum word count, CTA, author, date, featured image + alt text.

Usage:  check-components.py <work_dir>
Exit:   0 = PASS, 1 = FAIL
Reads:  <work_dir>/article.mdx + <work_dir>/meta.json

meta.json thresholds (all optional, defaults shown):
  min_words            : 1000
  meta_desc_min        : 120
  meta_desc_max        : 165
  title_max            : 65
  min_h2               : 3
  require_featured_image : true
  cta_patterns         : ["get a quote","get quote","contact","call ","request a quote","/quote","/contact","/get-a-quote"]
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from article_io import Gate, load_article, load_meta, word_count, headings  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("usage: check-components.py <work_dir>")
        sys.exit(2)
    work_dir = sys.argv[1]
    art = load_article(work_dir)
    meta = load_meta(work_dir)
    fm = art["frontmatter"]
    body = art["body"]

    min_words = int(meta.get("min_words", 1000))
    md_min = int(meta.get("meta_desc_min", 120))
    md_max = int(meta.get("meta_desc_max", 165))
    title_max = int(meta.get("title_max", 65))
    min_h2 = int(meta.get("min_h2", 3))
    require_img = meta.get("require_featured_image", True)
    cta_patterns = meta.get("cta_patterns", [
        "get a quote", "get quote", "contact", "call ", "request a quote",
        "/quote", "/contact", "/get-a-quote",
    ])

    g = Gate("required-components")

    # Title
    title = fm.get("title", "").strip()
    g.check(bool(title), "title present", repr(title[:60]))
    g.check(len(title) <= title_max, f"title <= {title_max} chars",
            f"len={len(title)}")

    # Meta description (frontmatter key varies by site: description | excerpt)
    desc = (fm.get("description", "") or fm.get("excerpt", "")).strip()
    g.check(bool(desc), "meta description present (description|excerpt)")
    g.check(md_min <= len(desc) <= md_max,
            f"meta description {md_min}-{md_max} chars", f"len={len(desc)}")

    # Date
    date = fm.get("date", "").strip()
    g.check(bool(re.match(r"\d{4}-\d{2}-\d{2}", date)) or bool(date),
            "date present", date)

    # Author / byline — frontmatter author OR meta.site_author injected at deploy
    author = fm.get("author", "").strip() or meta.get("site_author", "").strip()
    g.check(bool(author), "author/byline resolvable", author or "(none)")

    # Slug
    slug = fm.get("slug", "").strip()
    g.check(bool(slug), "slug present", slug)

    # Heading hierarchy
    hs = headings(body)
    h2s = [h for h in hs if h[0] == 2]
    h3s = [h for h in hs if h[0] == 3]
    # H1 in body is discouraged (title renders as H1) — flag if a body H1 exists
    body_h1 = [h for h in hs if h[0] == 1]
    g.check(len(h2s) >= min_h2, f">= {min_h2} H2 sections", f"found {len(h2s)}")
    g.check(len(body_h1) == 0, "no stray H1 in body (title is the H1)",
            f"found {len(body_h1)}")
    # if H3 used, ensure each H3 follows an H2 (no orphan H3 before any H2)
    seen_h2 = False
    orphan_h3 = False
    for level, _ in hs:
        if level == 2:
            seen_h2 = True
        if level == 3 and not seen_h2:
            orphan_h3 = True
    g.check(not orphan_h3, "no orphan H3 before first H2")

    # Intro — first non-heading paragraph before the first H2, >= 40 words
    intro_words = 0
    for para in re.split(r"\n\s*\n", body.strip()):
        p = para.strip()
        if not p:
            continue
        if p.startswith("#"):
            break
        intro_words = len(p.split())
        break
    g.check(intro_words >= 40, "intro paragraph present (>=40 words)",
            f"{intro_words} words")

    # Word count
    wc = word_count(body)
    g.check(wc >= min_words, f"word count >= {min_words}", f"{wc} words")

    # CTA
    low = body.lower()
    has_cta = any(p.lower() in low for p in cta_patterns)
    g.check(has_cta, "CTA present (quote/contact/call link or phrase)")

    # Featured image + alt
    feat_img = fm.get("image", "").strip() or fm.get("featured_image", "").strip()
    if require_img:
        g.check(bool(feat_img), "featured image in frontmatter",
                feat_img or "(none)")
        alt = fm.get("image_alt", "").strip() or fm.get("imageAlt", "").strip()
        g.check(bool(alt), "featured image alt text", alt or "(none)")
    else:
        g.check(True, "featured image not required (config)", "skipped")

    g.report_and_exit()


if __name__ == "__main__":
    main()
