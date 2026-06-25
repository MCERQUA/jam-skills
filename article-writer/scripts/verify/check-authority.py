#!/usr/bin/env python3
"""
check-authority.py — DETERMINISTIC outbound-authority gate (no LLM).

Enforces that the article links OUT to high-authority sources:
  1. Minimum count of OUTBOUND links (href to a different domain than site_url).
  2. Each outbound link's host is HIGH AUTHORITY: either on a curated authority
     allowlist (gov/edu/standards bodies, etc.) OR scores Ahrefs free-DR >= threshold.
  3. (HTTP liveness is handled by check-links.sh — this gate is about AUTHORITY.)

Ahrefs free DR endpoint (no key needed, proven working):
  https://api.ahrefs.com/v3/public/domain-rating-free?target=<domain>&output=json

Usage:  check-authority.py <work_dir>
Exit:   0 = PASS, 1 = FAIL
Reads:  <work_dir>/article.mdx + <work_dir>/meta.json

meta.json (optional, defaults shown):
  site_url             : ""        (used to identify which links are "outbound")
  min_outbound         : 4
  authority_dr_min     : 60
  authority_allowlist  : [".gov",".edu","iso.org","ansi.org","nfpa.org","irs.gov",
                          "osha.gov","sba.gov","naic.org","iii.org","consumer.ftc.gov"]
"""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from article_io import Gate, load_article, load_meta, extract_links  # noqa: E402

DEFAULT_ALLOWLIST = [
    ".gov", ".edu", "iso.org", "ansi.org", "nfpa.org", "irs.gov", "osha.gov",
    "sba.gov", "naic.org", "iii.org", "consumer.ftc.gov", "cdc.gov", "nist.gov",
    "who.int", "icc-es.org", "iccsafe.org",
]


def host_of(url):
    try:
        return urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return ""


def registrable(host):
    """crude eTLD+1 for same-domain comparison."""
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def ahrefs_dr(domain, timeout=20):
    url = ("https://api.ahrefs.com/v3/public/domain-rating-free?target="
           + urllib.parse.quote(domain) + "&output=json")
    req = urllib.request.Request(url, headers={"User-Agent": "JamBot-BlogFactory/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        dr = data.get("domain_rating", {})
        if isinstance(dr, dict):
            return float(dr.get("domain_rating", 0) or 0)
        return float(dr or 0)
    except Exception as e:
        return -1.0  # signal "could not fetch"


def main():
    if len(sys.argv) < 2:
        print("usage: check-authority.py <work_dir>")
        sys.exit(2)
    work_dir = sys.argv[1]
    art = load_article(work_dir)
    meta = load_meta(work_dir)

    site_host = registrable(host_of(meta.get("site_url", "")))
    min_outbound = int(meta.get("min_outbound", 4))
    dr_min = float(meta.get("authority_dr_min", 60))
    allowlist = [s.lower() for s in meta.get("authority_allowlist", DEFAULT_ALLOWLIST)]

    g = Gate("outbound-authority")

    # collect distinct outbound hosts
    outbound = []
    seen = set()
    for link in extract_links(art["body"]):
        url = link["url"]
        if not url.startswith("http"):
            continue
        h = host_of(url)
        if not h:
            continue
        if site_host and registrable(h) == site_host:
            continue  # same site → internal, not outbound
        if url in seen:
            continue
        seen.add(url)
        outbound.append((url, h))

    g.check(len(outbound) >= min_outbound,
            f">= {min_outbound} outbound external links",
            f"found {len(outbound)}")

    # authority-score each distinct host
    host_results = {}
    for url, h in outbound:
        if h in host_results:
            continue
        on_allow = any(tok in h for tok in allowlist)
        if on_allow:
            host_results[h] = ("allowlist", None)
        else:
            dr = ahrefs_dr(registrable(h))
            host_results[h] = ("dr", dr)

    low_authority = []
    for h, (kind, dr) in host_results.items():
        if kind == "allowlist":
            g.check(True, f"authority OK (allowlist): {h}")
        else:
            if dr < 0:
                # could not fetch DR → fail closed (cannot prove authority)
                g.check(False, f"authority UNVERIFIED (DR fetch failed): {h}",
                        "fail-closed")
                low_authority.append(h)
            else:
                ok = dr >= dr_min
                g.check(ok, f"authority {'OK' if ok else 'LOW'}: {h}",
                        f"DR={dr:.0f} (min {dr_min:.0f})")
                if not ok:
                    low_authority.append(h)

    g.check(len(low_authority) == 0, "all outbound hosts are high-authority",
            f"low/unverified: {low_authority}" if low_authority else "")

    g.report_and_exit()


if __name__ == "__main__":
    main()
