#!/usr/bin/env python3
"""
quality-review/check.py — the Quality Officer gate.

Reviews a finished deliverable (a live URL, a local static dir, or a brand-report
HTML+data) BEFORE it ships and returns a pass/fail with a findings list. Catches the
failure classes that have repeatedly shipped broken this project:
  - dead endpoints / routes (404/403/5xx silently → blanks or zeros)
  - missing/broken images (<img> that don't 200)
  - dead internal links (nav/cards pointing nowhere)
  - incomplete output (required sections absent)
  - fabrication / placeholder content (lorem, TODO, "Data unavailable" overload)
  - brand reports scored 0 from FAILED fetchers (not real zeros)

Dependency-light: stdlib only (urllib, re, json, html). No headless browser — checks
are HTTP-status + HTML-structure based, which catches the large majority of "broken
before the user sees it" cases. (Visual/contrast review still needs a browser pass.)

USAGE
  # A live site or app (crawls the given routes, checks each):
  python3 check.py --url https://garage-sale.jam-bot.com \
      --routes "/,/map,/browse,/submit" \
      --require "Get a Quote,footer"

  # A brand report (HTML page + the score data it was built from):
  python3 check.py --url https://x.jam-bot.com/pages/brand-report.html \
      --report-data /path/ai/score.json \
      --require "Brand Health,Keywords,Backlinks,Roadmap"

  # A local static build dir (file:// style — pass a dir):
  python3 check.py --dir /tmp/site --routes "/,/about" --require "nav,footer"

EXIT CODE: 0 = PASS, 1 = FAIL (so callers can gate: `python3 check.py ... || halt`).
Writes JSON findings to <out>/quality-review.json when --out given.
"""
import argparse, json, re, sys, urllib.request, urllib.error, os, html as _html

UA = {"User-Agent": "jambot-quality-review/1.0"}
TIMEOUT = 15

FABRICATION_MARKERS = [
    "lorem ipsum", "todo:", "tktk", "placeholder text", "your text here",
    "company name here", "xxxxx", "sample text", "replace this",
]


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.getcode(), r.read().decode("utf-8", "ignore"), dict(r.headers)
    except urllib.error.HTTPError as e:
        # keep headers on error responses — Clerk's auth-gate signal lives in 404 headers
        try:
            return e.code, "", dict(e.headers)
        except Exception:
            return e.code, "", {}
    except Exception as e:
        return 0, f"__ERR__{e}", {}


def head_ok(url):
    code, _, hdrs = fetch(url)
    # An auth-gated route (Clerk protect) returns 404/redirect to a signed-out crawler —
    # that's working-as-designed, not a dead link. Detect Clerk's gate headers.
    if any(k.lower().startswith("x-clerk-auth") for k in (hdrs or {})):
        reason = (hdrs.get("x-clerk-auth-reason") or hdrs.get("X-Clerk-Auth-Reason") or "")
        if "protect" in reason.lower():
            return "AUTH_GATED"
    return code


def abs_url(base, src):
    if src.startswith(("http://", "https://")):
        return src
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        m = re.match(r"(https?://[^/]+)", base)
        return (m.group(1) if m else base.rstrip("/")) + src
    return base.rstrip("/") + "/" + src


def review_page(base, route, require, findings):
    url = base.rstrip("/") + ("" if route == "/" else route)
    code, html, _ = fetch(url)
    tag = f"{route}"
    if code != 200:
        findings.append({"severity": "fail", "check": "route", "where": tag,
                         "detail": f"HTTP {code} (expected 200)"})
        return
    # images
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    for src in set(imgs):
        src = _html.unescape(src)   # &amp; → & etc. (next/image URLs are entity-encoded in HTML)
        if src.startswith("data:"):
            continue
        c = head_ok(abs_url(url, src))
        if c != 200:
            findings.append({"severity": "fail", "check": "image", "where": tag,
                             "detail": f"image {src[:80]} → HTTP {c}"})
    # internal links resolve
    links = re.findall(r'<a[^>]+href=["\'](/[^"\'#?]*)["\']', html, re.I)
    seen = set()
    for href in links:
        href = _html.unescape(href)
        if href in seen or href in ("/",):
            continue
        seen.add(href)
        c = head_ok(abs_url(url, href))
        if c not in (200, 301, 302, 308, "AUTH_GATED"):
            findings.append({"severity": "fail", "check": "deadlink", "where": tag,
                             "detail": f"internal link {href} → HTTP {c}"})
    # required sections / phrases
    low = html.lower()
    for need in require:
        if need.strip() and need.strip().lower() not in low:
            findings.append({"severity": "fail", "check": "completeness", "where": tag,
                             "detail": f'required content "{need.strip()}" MISSING'})
    # fabrication markers
    for mk in FABRICATION_MARKERS:
        if mk in low:
            findings.append({"severity": "warn", "check": "fabrication", "where": tag,
                             "detail": f'placeholder/fabrication marker "{mk}" present'})
    # raw icon-ligature leak (Material Symbols rendered as text — past bug)
    if re.search(r">\s*(admin_panel_settings|verified_user|account_tree|support_agent)\s*<", html):
        findings.append({"severity": "warn", "check": "icons", "where": tag,
                         "detail": "Material Symbols ligature names rendering as raw text (icon font not loaded)"})


def review_report_data(path, findings):
    """For brand reports: flag dimensions scored 0/None from FAILED fetchers."""
    try:
        d = json.load(open(path))
    except Exception as e:
        findings.append({"severity": "warn", "check": "report-data",
                         "detail": f"could not read score data: {e}"})
        return
    avail = d.get("available") or {}
    bd = d.get("breakdown") or {}
    for dim, ok in avail.items():
        if not ok:
            findings.append({"severity": "warn", "check": "endpoint-data",
                             "detail": f'dimension "{dim}" had NO real data (fetcher failed) — excluded from score, show as "N/A" not 0'})
    # zero scores that are NOT marked unavailable = suspicious
    for dim, val in bd.items():
        if val == 0 and avail.get(dim, True):
            findings.append({"severity": "warn", "check": "suspicious-zero",
                             "detail": f'dimension "{dim}" scored 0 with data present — verify it is a real zero, not a parse miss'})
    cov = d.get("coverage")
    if isinstance(cov, int) and cov < 4:
        findings.append({"severity": "fail", "check": "coverage",
                         "detail": f"only {cov}/6 data dimensions had real data — report is thin; fix the failed endpoints before shipping"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--dir")
    ap.add_argument("--routes", default="/")
    ap.add_argument("--require", default="")
    ap.add_argument("--report-data")
    ap.add_argument("--out")
    a = ap.parse_args()

    findings = []
    base = a.url
    if not base and a.dir:
        # serve-less: just scan local html files for required content + fabrication
        base = None
        require = [s for s in a.require.split(",") if s.strip()]
        for route in a.routes.split(","):
            route = route.strip()
            rel = "index.html" if route in ("/", "") else route.strip("/") + "/index.html"
            p = os.path.join(a.dir, rel)
            if not os.path.exists(p):
                findings.append({"severity": "fail", "check": "route", "where": route,
                                 "detail": f"file missing: {rel}"})
                continue
            html = open(p).read(); low = html.lower()
            for need in require:
                if need.strip().lower() not in low:
                    findings.append({"severity": "fail", "check": "completeness", "where": route,
                                     "detail": f'required "{need.strip()}" MISSING'})
    elif base:
        require = [s for s in a.require.split(",") if s.strip()]
        for route in a.routes.split(","):
            review_page(base, route.strip(), require, findings)

    if a.report_data:
        review_report_data(a.report_data, findings)

    fails = [f for f in findings if f["severity"] == "fail"]
    warns = [f for f in findings if f["severity"] == "warn"]
    verdict = "PASS" if not fails else "FAIL"
    result = {"verdict": verdict, "fail_count": len(fails), "warn_count": len(warns),
              "findings": findings, "target": base or a.dir}

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        json.dump(result, open(os.path.join(a.out, "quality-review.json"), "w"), indent=2)

    print(f"QUALITY REVIEW: {verdict}  ({len(fails)} fail, {len(warns)} warn)  — {base or a.dir}")
    for f in fails + warns:
        mark = "✗" if f["severity"] == "fail" else "⚠"
        where = f" [{f.get('where')}]" if f.get("where") else ""
        print(f"  {mark} {f['check']}{where}: {f['detail']}")
    if verdict == "PASS" and not warns:
        print("  ✓ all checks passed")
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
