#!/usr/bin/env python3
"""
article_io.py — shared parsing helpers for the blog-factory gate scripts.

The gates operate on a WORK DIR that contains a candidate article staged as:
    <work_dir>/article.mdx     # frontmatter (---) + body (markdown)
    <work_dir>/meta.json       # config-derived context (site_url, money_pages, thresholds...)
    <work_dir>/schema.json     # JSON-LD (array of @graph objects or a single object)

These helpers are framework-agnostic: they parse the .mdx the SAME way regardless
of whether the destination site is Next.js content/blog, a [slug] record, or plain
markdown. No LLM, pure stdlib.
"""
import json
import os
import re
import sys

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_frontmatter(raw: str):
    """Return (frontmatter_dict, body_str). Tolerant YAML-subset parser
    (key: "value" / key: value), enough for our flat blog frontmatter."""
    m = FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    fm_block, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_block.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # strip matching quotes
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        fm[key] = val
    return fm, body


def load_article(work_dir):
    path = os.path.join(work_dir, "article.mdx")
    if not os.path.exists(path):
        # also accept article.md
        alt = os.path.join(work_dir, "article.md")
        if os.path.exists(alt):
            path = alt
        else:
            raise FileNotFoundError(f"no article.mdx or article.md in {work_dir}")
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    fm, body = parse_frontmatter(raw)
    return {"path": path, "raw": raw, "frontmatter": fm, "body": body}


def load_meta(work_dir):
    path = os.path.join(work_dir, "meta.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_schema(work_dir):
    path = os.path.join(work_dir, "schema.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --- markdown extraction helpers (used by several gates) ---------------------

# [anchor](url) — captures anchor + url
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+|/[^\s)]*)\)")
# bare html anchors too (in case body has raw <a>)
HTML_LINK_RE = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)


def extract_links(body):
    """Return list of dicts {anchor,url} for markdown + html links in the body."""
    out = []
    for m in MD_LINK_RE.finditer(body):
        out.append({"anchor": m.group(1).strip(), "url": m.group(2).strip()})
    for m in HTML_LINK_RE.finditer(body):
        out.append({"anchor": "", "url": m.group(1).strip()})
    return out


def word_count(body):
    # strip markdown link syntax to anchor text, strip headings markers
    text = MD_LINK_RE.sub(r"\1", body)
    text = re.sub(r"[#*_>`-]", " ", text)
    return len(text.split())


def headings(body):
    """Return list of (level, text) for ATX headings."""
    out = []
    for line in body.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if m:
            out.append((len(m.group(1)), m.group(2).strip()))
    return out


# --- reporting ----------------------------------------------------------------

class Gate:
    """Tiny pass/fail reporter. exit(0) on pass, exit(1) on fail."""

    def __init__(self, name):
        self.name = name
        self.checks = []  # (ok:bool, label:str, detail:str)

    def check(self, ok, label, detail=""):
        self.checks.append((bool(ok), label, detail))
        return ok

    def report_and_exit(self):
        failed = [c for c in self.checks if not c[0]]
        print(f"\n=== GATE: {self.name} ===")
        for ok, label, detail in self.checks:
            mark = "PASS" if ok else "FAIL"
            line = f"  [{mark}] {label}"
            if detail:
                line += f" — {detail}"
            print(line)
        if failed:
            print(f"  >>> {self.name}: FAIL ({len(failed)} failing check(s))")
            sys.exit(1)
        print(f"  >>> {self.name}: PASS")
        sys.exit(0)
