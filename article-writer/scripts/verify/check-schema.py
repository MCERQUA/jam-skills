#!/usr/bin/env python3
"""
check-schema.py — DETERMINISTIC JSON-LD schema gate (no LLM).

Validates the staged schema.json:
  - parses as JSON (object, @graph object, or array of nodes)
  - contains a BlogPosting (or Article) node with: headline, description,
    datePublished, author, publisher, mainEntityOfPage/url
  - contains a BreadcrumbList node
  - IF the article body has an FAQ section (## FAQ / "Frequently Asked"), a
    FAQPage node with >=1 Question/acceptedAnswer is REQUIRED; otherwise FAQPage
    is optional but validated if present.

Usage:  check-schema.py <work_dir>
Exit:   0 = PASS, 1 = FAIL
Reads:  <work_dir>/schema.json + <work_dir>/article.mdx
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from article_io import Gate, load_article, load_schema  # noqa: E402


def collect_nodes(schema):
    """Flatten schema into a list of dict nodes regardless of shape."""
    nodes = []
    if schema is None:
        return nodes
    if isinstance(schema, list):
        for item in schema:
            nodes.extend(collect_nodes(item))
        return nodes
    if isinstance(schema, dict):
        if "@graph" in schema and isinstance(schema["@graph"], list):
            for item in schema["@graph"]:
                nodes.extend(collect_nodes(item))
        else:
            nodes.append(schema)
    return nodes


def type_of(node):
    t = node.get("@type", "")
    if isinstance(t, list):
        return [str(x) for x in t]
    return [str(t)]


def find(nodes, *types):
    out = []
    for n in nodes:
        if set(type_of(n)) & set(types):
            out.append(n)
    return out


def main():
    if len(sys.argv) < 2:
        print("usage: check-schema.py <work_dir>")
        sys.exit(2)
    work_dir = sys.argv[1]
    schema = load_schema(work_dir)
    art = load_article(work_dir)
    body = art["body"]

    g = Gate("schema-jsonld")

    g.check(schema is not None, "schema.json present + parses as JSON")
    if schema is None:
        g.report_and_exit()
        return

    nodes = collect_nodes(schema)
    g.check(len(nodes) > 0, "schema has at least one node", f"{len(nodes)} nodes")

    # BlogPosting / Article
    posts = find(nodes, "BlogPosting", "Article", "NewsArticle")
    g.check(len(posts) >= 1, "BlogPosting/Article node present")
    if posts:
        p = posts[0]
        for field in ("headline", "description", "datePublished", "author",
                      "publisher"):
            g.check(bool(p.get(field)), f"BlogPosting.{field} present",
                    "" if p.get(field) else "missing")
        has_url = bool(p.get("mainEntityOfPage") or p.get("url"))
        g.check(has_url, "BlogPosting.mainEntityOfPage/url present")

    # BreadcrumbList
    crumbs = find(nodes, "BreadcrumbList")
    g.check(len(crumbs) >= 1, "BreadcrumbList node present")
    if crumbs:
        items = crumbs[0].get("itemListElement", [])
        g.check(isinstance(items, list) and len(items) >= 2,
                "breadcrumb has >=2 items", f"{len(items) if isinstance(items, list) else 0}")

    # FAQ — required only if the body has an FAQ section
    has_faq_section = bool(re.search(r"^#{2,3}\s+.*(faq|frequently asked)",
                                     body, re.IGNORECASE | re.MULTILINE))
    faq_nodes = find(nodes, "FAQPage")
    if has_faq_section:
        g.check(len(faq_nodes) >= 1, "FAQPage node present (body has FAQ section)")
        if faq_nodes:
            qs = faq_nodes[0].get("mainEntity", [])
            valid_q = isinstance(qs, list) and len(qs) >= 1 and all(
                isinstance(q, dict) and q.get("acceptedAnswer") for q in qs)
            g.check(valid_q, ">=1 Question with acceptedAnswer",
                    f"{len(qs) if isinstance(qs, list) else 0} questions")
    else:
        if faq_nodes:
            qs = faq_nodes[0].get("mainEntity", [])
            g.check(isinstance(qs, list) and len(qs) >= 1,
                    "FAQPage (optional) well-formed")
        else:
            g.check(True, "FAQPage not required (no FAQ section in body)", "skipped")

    g.report_and_exit()


if __name__ == "__main__":
    main()
