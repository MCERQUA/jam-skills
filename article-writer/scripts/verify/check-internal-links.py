#!/usr/bin/env python3
"""
check-internal-links.py — DETERMINISTIC internal-linking gate (no LLM).

Enforces a MINIMUM number of internal links:
  - to MONEY pages (from meta.money_pages — derived from seo-plan.json when present,
    else listed explicitly in the per-client config), AND
  - to OTHER blog posts on the same site.

Internal links are hrefs that are site-relative ("/...") or point at the site's own
registrable domain. Links to the article's OWN slug do not count.

Usage:  check-internal-links.py <work_dir>
Exit:   0 = PASS, 1 = FAIL
Reads:  <work_dir>/article.mdx + <work_dir>/meta.json

meta.json (optional, defaults shown):
  site_url           : ""
  money_pages        : []          (list of path strings, e.g. ["/quote","/services"])
  blog_path_prefix   : "/blog/"
  min_money_links    : 1
  min_blog_links     : 1
  min_internal_total : 2
"""
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from article_io import Gate, load_article, load_meta, extract_links  # noqa: E402


def registrable(host):
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def to_path(url, site_host):
    """Return the site-relative path for an internal link, else None."""
    if url.startswith("/"):
        return url.split("#")[0].split("?")[0]
    if url.startswith("http"):
        p = urllib.parse.urlparse(url)
        if site_host and registrable(p.netloc.lower()) == site_host:
            return (p.path or "/").split("#")[0].split("?")[0]
    return None


def main():
    if len(sys.argv) < 2:
        print("usage: check-internal-links.py <work_dir>")
        sys.exit(2)
    work_dir = sys.argv[1]
    art = load_article(work_dir)
    meta = load_meta(work_dir)
    fm = art["frontmatter"]

    site_host = ""
    if meta.get("site_url"):
        site_host = registrable(urllib.parse.urlparse(meta["site_url"]).netloc.lower())
    money_pages = [m.rstrip("/") for m in meta.get("money_pages", [])]
    blog_prefix = meta.get("blog_path_prefix", "/blog/")
    min_money = int(meta.get("min_money_links", 1))
    min_blog = int(meta.get("min_blog_links", 1))
    min_total = int(meta.get("min_internal_total", 2))
    this_slug = fm.get("slug", "").strip()

    g = Gate("internal-links")

    internal_paths = []
    for link in extract_links(art["body"]):
        p = to_path(link["url"], site_host)
        if p:
            internal_paths.append(p)

    # money-page links
    money_hits = []
    for p in internal_paths:
        pn = p.rstrip("/")
        if any(pn == mp or pn.startswith(mp + "/") for mp in money_pages):
            money_hits.append(p)

    # blog links (other posts, not self)
    blog_hits = []
    for p in internal_paths:
        if p.startswith(blog_prefix):
            slug = p[len(blog_prefix):].strip("/")
            if slug and slug != this_slug:
                blog_hits.append(p)

    total_internal = len(set(internal_paths) - {f"{blog_prefix}{this_slug}"})

    g.check(len(set(money_hits)) >= min_money,
            f">= {min_money} link(s) to money pages",
            f"hits={sorted(set(money_hits))}")
    g.check(len(set(blog_hits)) >= min_blog,
            f">= {min_blog} link(s) to other blog posts",
            f"hits={sorted(set(blog_hits))}")
    g.check(total_internal >= min_total,
            f">= {min_total} internal links total",
            f"found {total_internal}")

    if not money_pages:
        g.check(False, "money_pages configured", "EMPTY — config must list money pages")

    g.report_and_exit()


if __name__ == "__main__":
    main()
