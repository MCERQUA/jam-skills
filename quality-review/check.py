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
import argparse, json, re, sys, urllib.request, urllib.error, os, html as _html, subprocess

UA = {"User-Agent": "jambot-quality-review/1.0"}
TIMEOUT = 15

FABRICATION_MARKERS = [
    "lorem ipsum", "todo:", "tktk", "placeholder text", "your text here",
    "company name here", "xxxxx", "sample text", "replace this",
]



# ---------------------------------------------------------------------------
# BRAND VOICE + REVERT checks (2026-09-11, meeting standard "agents are everyone's eyes")
#
# Origin: Danielle C's homepage review caught spelling but MISSED "Boutique Digital Marketing &
# Brand Advisory Collective" — corporate jargon on her own banned list — and a previously-fixed
# line silently reverted in a Stitch rebuild. She caught both. Two mechanisms were missing:
#   (a) the banned list lived only inside a brand-kit canvas HTML, so no check could load it;
#   (b) nothing compared the page to its last APPROVED state.
# Fix: a canonical machine-readable file per tenant — business/brand-voice.json — and a git tag
# per approved page in the canvas-pages repo (`approved/<file>`), both consumed here.
# ---------------------------------------------------------------------------

def load_brand_voice(path):
    """Return (banned_words, banned_regex, prose_patterns, brand_names) from business/brand-voice.json.
    Every brand's lists are merged: a tenant with two brands wants BOTH sets enforced on any page
    unless the file says otherwise, and a check that silently picks one is the miss this exists to
    close. A word list is mechanical; `banned_patterns` are prose hints for the human/LLM pass and
    are only ECHOED, never claimed as checked."""
    d = json.load(open(path))
    words, regex, prose, names = [], [], [], []
    for name, b in (d.get("brands") or {}).items():
        names.append(name)
        words += [w for w in (b.get("banned_words") or []) if isinstance(w, str) and w.strip()]
        regex += [r for r in (b.get("banned_regex") or []) if isinstance(r, str) and r.strip()]
        prose += [p for p in (b.get("banned_patterns") or []) if isinstance(p, str) and p.strip()]
    # de-dup, keep order
    seen = set(); words = [w for w in words if not (w.lower() in seen or seen.add(w.lower()))]
    return words, regex, prose, names


def visible_text_lines(html):
    """Strip script/style/comments/tags; return non-empty visible text lines (entities decoded)."""
    t = re.sub(r"(?is)<(script|style|noscript|template)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?s)<!--.*?-->", " ", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|section|article|header|footer)>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    out = []
    for line in t.split("\n"):
        line = re.sub(r"[ \t\r\f\v]+", " ", line).strip()
        if line:
            out.append(line)
    return out


def review_brand_voice(html, tag, bv, findings):
    words, regex, prose, names = bv
    lines = visible_text_lines(html)
    for w in words:
        pat = re.compile(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", re.I)
        for ln in lines:
            if pat.search(ln):
                findings.append({"severity": "fail", "check": "brand-voice", "where": tag,
                                 "detail": f'banned word "{w}" in: "{ln[:140]}"'})
    for rx in regex:
        try:
            pat = re.compile(rx, re.I)
        except re.error as e:
            findings.append({"severity": "warn", "check": "brand-voice", "where": tag,
                             "detail": f'banned_regex {rx!r} does not compile ({e}) — NOT checked'})
            continue
        for ln in lines:
            if pat.search(ln):
                findings.append({"severity": "fail", "check": "brand-voice", "where": tag,
                                 "detail": f'banned pattern /{rx}/ in: "{ln[:140]}"'})
    if prose:
        findings.append({"severity": "info", "check": "brand-voice-manual", "where": tag,
                         "detail": f"{len(prose)} prose pattern(s) need a human/LLM read against every line "
                                   f"(not mechanically checked): " + " | ".join(prose)})
    findings.append({"severity": "info", "check": "brand-voice", "where": tag,
                     "detail": f"{len(lines)} visible line(s) scanned vs {len(words)} banned word(s), "
                               f"{len(regex)} regex — brands: {', '.join(names)}"})


def review_revert(path, tag_prefix, findings):
    """Compare a page to its last APPROVED state (git tag `<prefix><basename>` in the page's repo).
    Removed visible-text lines are candidate reverts — the class that a rebuild produces silently.
    No tag => CANNOT-TELL, said so, never PASS."""
    d = os.path.dirname(os.path.abspath(path)); base = os.path.basename(path)
    def git(*args):
        r = subprocess.run(["git", "-C", d, *args], capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout, r.stderr
    rc, top, _ = git("rev-parse", "--show-toplevel")
    if rc != 0:
        findings.append({"severity": "info", "check": "revert", "where": base,
                         "detail": "not in a git repo — revert check CANNOT-TELL"})
        return
    tagname = f"{tag_prefix}{base}"
    rc, _, _ = git("rev-parse", "-q", "--verify", f"refs/tags/{tagname}")
    if rc != 0:
        findings.append({"severity": "info", "check": "revert", "where": base,
                         "detail": f"no approved ref — revert check CANNOT-TELL. After a review is approved run: "
                                   f"git -C {d} tag -f {tagname}"})
        return
    rc, approved, err = git("show", f"{tagname}:{os.path.relpath(os.path.abspath(path), top.strip())}")
    if rc != 0:
        findings.append({"severity": "warn", "check": "revert", "where": base,
                         "detail": f"tag {tagname} exists but the file is not in it ({err.strip()[:80]}) — CANNOT-TELL"})
        return
    now = open(path, encoding="utf-8", errors="ignore").read()
    before = set(visible_text_lines(approved)); after = set(visible_text_lines(now))
    removed = [ln for ln in visible_text_lines(approved) if ln not in after]
    for ln in removed:
        findings.append({"severity": "warn", "check": "revert", "where": base,
                         "detail": f'approved text no longer on page: "{ln[:140]}"'})
    findings.append({"severity": "info", "check": "revert", "where": base,
                     "detail": f"vs {tagname}: {len(removed)} approved line(s) gone, "
                               f"{len(after - before)} new line(s)"})


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
    ap.add_argument("--files", default="",
                    help="comma-separated local HTML files (canvas pages) to scan — brand-voice + revert + fabrication")
    ap.add_argument("--brand-voice", default="",
                    help="path to business/brand-voice.json; with --files, auto-found at <workspace>/business/brand-voice.json "
                         "when a file lives under <workspace>/canvas-pages/")
    ap.add_argument("--approved-tag-prefix", default="approved/",
                    help="git tag prefix marking a page's last approved state (tag = <prefix><basename>)")
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

    if a.files:
        files = [f.strip() for f in a.files.split(",") if f.strip()]
        bv_path = a.brand_voice
        for p in files:
            if not os.path.exists(p):
                findings.append({"severity": "fail", "check": "route", "where": p, "detail": "file missing"})
                continue
            html = open(p, encoding="utf-8", errors="ignore").read(); low = html.lower()
            tag = os.path.basename(p)
            for mk in FABRICATION_MARKERS:
                if mk in low:
                    findings.append({"severity": "warn", "check": "fabrication", "where": tag,
                                     "detail": f'placeholder/fabrication marker "{mk}" present'})
            if not bv_path:
                # canvas page inside a tenant workspace => the canonical file is one dir up
                # (container: ~/.openclaw/workspace/{canvas-pages,business}). On the HOST the two
                # live under different parents: /mnt/clients/<t>/openvoiceui/canvas-pages vs
                # /mnt/clients/<t>/openclaw/workspace/business — try that layout second.
                ap_ = os.path.abspath(p)
                cands = [os.path.join(os.path.dirname(os.path.dirname(ap_)), "business", "brand-voice.json")]
                m = re.match(r"^(/mnt/clients/[^/]+)/openvoiceui/canvas-pages/", ap_)
                if m:
                    cands.append(os.path.join(m.group(1), "openclaw", "workspace", "business", "brand-voice.json"))
                bv_path = next((c for c in cands if os.path.exists(c)), "")
            if bv_path:
                review_brand_voice(html, tag, load_brand_voice(bv_path), findings)
            else:
                findings.append({"severity": "info", "check": "brand-voice", "where": tag,
                                 "detail": "no business/brand-voice.json found — brand-voice check CANNOT-TELL "
                                           "(pass --brand-voice, or create the canonical file)"})
            review_revert(p, a.approved_tag_prefix, findings)
    elif a.brand_voice and base:
        bv = load_brand_voice(a.brand_voice)
        for route in a.routes.split(","):
            url = base.rstrip("/") + ("" if route.strip() == "/" else route.strip())
            code, html, _ = fetch(url)
            if code == 200:
                review_brand_voice(html, route.strip(), bv, findings)

    if a.report_data:
        review_report_data(a.report_data, findings)

    fails = [f for f in findings if f["severity"] == "fail"]
    warns = [f for f in findings if f["severity"] == "warn"]
    infos = [f for f in findings if f["severity"] == "info"]
    verdict = "PASS" if not fails else "FAIL"
    result = {"verdict": verdict, "fail_count": len(fails), "warn_count": len(warns),
              "info_count": len(infos), "findings": findings, "target": base or a.dir or a.files}

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        json.dump(result, open(os.path.join(a.out, "quality-review.json"), "w"), indent=2)

    print(f"QUALITY REVIEW: {verdict}  ({len(fails)} fail, {len(warns)} warn, {len(infos)} info)  — {base or a.dir or a.files}")
    for f in fails + warns + infos:
        mark = {"fail": "✗", "warn": "⚠"}.get(f["severity"], "ℹ")
        where = f" [{f.get('where')}]" if f.get("where") else ""
        print(f"  {mark} {f['check']}{where}: {f['detail']}")
    if verdict == "PASS" and not warns:
        print("  ✓ all checks passed")
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
