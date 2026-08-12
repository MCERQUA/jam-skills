"""fetch_interlinks.py — BASELINE of the site's CURRENT internal linking.

WHY THIS EXISTS (Mike, 2026-08-12):
The report printed "Internal Link Silo — 263 internal links planned" with no way to judge
it. Mike: "whats the conclusion to this? is it good is it bad? ... i dont fully understand
if this is good or not because its kinda depends on other factors i dont know."

He was right, and the honest answer was that the number could NOT be judged: 263 is pure
arithmetic (money_pages x linking rules), and the report never measured what the site has
TODAY. A planned figure with no baseline is the same defect as the coverage panel that
scored 0/35 against a universe defined as "not covered" — a number with no reference frame,
presented as a finding.

WHAT IT MEASURES (plain GETs — NO DataForSEO cost):
  internal_links_total   every internal <a href> across the crawled set
  avg_links_per_page     density (spam risk is >100/page; 5-30 is normal)
  orphan_pages           sitemap pages with ZERO internal inbound links → get no authority
  max_depth / deep_pages click distance from the homepage (>=4 is effectively invisible)

RELATIONSHIP TO scripts/seo-review/seo-crawl-audit.py — deliberately NOT reused:
That script is the authoritative DEEP audit (findings + severities, images, redirects,
canonicals, thin pages) and defaults to 400 pages. This needs four numbers inside a report
that must finish in minutes, so it is scoped to PAGE_CAP and computes nothing else. If you
want the full picture, run seo-crawl-audit.py — it is the deeper tool and it already
computes orphans the same way (`link_refs`). Keep the two in agreement: both define an
orphan as "in the sitemap, never internally linked".

Never raises. Returns {} on failure, and callers MUST treat {} as UNKNOWN, never as zero —
"0 internal links" would be a confident false claim of the exact kind this module exists to
replace.
"""
import re
import sys
from collections import defaultdict
from urllib.parse import urljoin, urlparse

import requests

PAGE_CAP = 40          # keep the report fast; the deep crawler handles full sites
TIMEOUT = 6
_HREF_RE = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\']', re.I)
_SKIP_EXT = re.compile(r'\.(jpe?g|png|webp|gif|svg|pdf|css|js|ico|zip|mp4|woff2?)(\?|$)', re.I)


def _norm(u: str) -> str:
    """Canonical form for identity comparison: scheme+host+path, no query/fragment/trailing slash."""
    try:
        p = urlparse(u)
        path = (p.path or "/").rstrip("/") or "/"
        return f"{p.netloc.lower().replace('www.', '')}{path}"
    except Exception:  # noqa: BLE001
        return u


def fetch_interlinks(domain: str, pages: list, session=None) -> dict:
    """`pages` = sitemap URLs already discovered by generate.py (no re-discovery, no cost)."""
    out = {}
    try:
        dom = domain.lower().replace("www.", "")
        home = f"https://{dom}"
        urls, seen = [], set()
        for u in [home] + list(pages or []):
            if _SKIP_EXT.search(u or ""):
                continue
            n = _norm(u)
            if n in seen:
                continue
            seen.add(n)
            urls.append(u)
            if len(urls) >= PAGE_CAP:
                break
        if len(urls) < 2:
            print("[INFO] interlinks: <2 crawlable pages — reporting UNKNOWN, not zero", file=sys.stderr)
            return {}

        sess = session or requests.Session()
        inbound = defaultdict(set)      # norm(target) -> {source pages}
        outbound = {}                   # norm(source) -> count
        graph = defaultdict(set)        # norm(source) -> {norm(target)}
        fetched = 0

        for u in urls:
            try:
                r = sess.get(u, timeout=TIMEOUT, headers={"User-Agent": "JamBot-BrandReport/1.0"})
                if r.status_code != 200 or "html" not in r.headers.get("Content-Type", "").lower():
                    continue
                fetched += 1
                src = _norm(u)
                n_out = 0
                for href in _HREF_RE.findall(r.text):
                    href = href.split("#")[0].strip()
                    if not href or href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                        continue
                    absu = urljoin(u, href)
                    if _SKIP_EXT.search(absu):
                        continue
                    tgt = _norm(absu)
                    if not tgt.startswith(dom):
                        continue          # internal only
                    if tgt == src:
                        continue          # self-links carry no authority
                    n_out += 1
                    inbound[tgt].add(src)
                    graph[src].add(tgt)
                outbound[src] = n_out
            except Exception:  # noqa: BLE001 — one bad page must not zero the whole baseline
                continue

        if fetched < 2:
            print(f"[INFO] interlinks: only {fetched} page(s) fetched — UNKNOWN, not zero", file=sys.stderr)
            return {}

        total_links = sum(outbound.values())
        # Orphans: a crawled sitemap page nothing else links to. Homepage excluded — it is
        # reached directly, so counting it as an orphan would be a guaranteed false positive.
        home_n = _norm(home)
        crawled = set(outbound.keys())
        orphans = sorted(p for p in crawled if p != home_n and not inbound.get(p))

        # Click depth from the homepage (BFS over the discovered graph).
        depth = {home_n: 0}
        frontier = [home_n]
        while frontier:
            nxt = []
            for node in frontier:
                for tgt in graph.get(node, ()):
                    if tgt not in depth:
                        depth[tgt] = depth[node] + 1
                        nxt.append(tgt)
            frontier = nxt
        reachable = {p: d for p, d in depth.items() if p in crawled}
        deep = sorted(p for p, d in reachable.items() if d >= 4)

        out = {
            "il_available":        True,
            "il_pages_crawled":    fetched,
            "il_links_total":      total_links,
            "il_avg_per_page":     round(total_links / fetched, 1) if fetched else 0,
            "il_orphan_count":     len(orphans),
            "il_orphan_examples":  orphans[:5],
            "il_max_depth":        max(reachable.values()) if reachable else 0,
            "il_deep_count":       len(deep),
            "il_unreachable":      sorted(p for p in crawled if p not in depth)[:5],
            "il_capped":           len(urls) >= PAGE_CAP,
        }
        print(f"[OK] interlinks: {fetched} pages · {total_links} internal links · "
              f"{out['il_avg_per_page']}/page · {len(orphans)} orphan · depth<={out['il_max_depth']}",
              file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] interlink baseline failed ({e}) — reporting UNKNOWN", file=sys.stderr)
        return {}
    return out
