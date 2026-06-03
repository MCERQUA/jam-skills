"""fetch_dnslytics.py — Reverse-analytics: find a brand's HIDDEN site network.

The brand-SERP + Serper lanes find what's PUBLICLY tied to the name. They cannot find a
well-built DBA / leadgen site that targets entirely different keywords and is JS-rendered
(e.g. tampasprayfoaminsulation.com for On The Mark) — nothing on it names the brand in a
way search surfaces. The technique that DOES find those is reverse-analytics: every site an
operator builds tends to share the SAME Google Analytics / GTM / AdSense ID. Find every domain
using that ID and you've mapped their network.

Flow:
  1. Render the primary site headless (Playwright) and capture the tracking IDs from the
     actual googletagmanager / google-analytics / adsense REQUEST URLs (authoritative — the
     page-text regex is noisy). The IDs are JS-injected, so a raw fetch sees nothing.
  2. Reverse each ID via DNSlytics:
       GET https://api.dnslytics.net/v1/reverseganalytics/<gid>?apikey=<key>   (GA: g-…/ua-…)
       GET https://api.dnslytics.net/v1/reverseadsense/<pub>?apikey=<key>      (ca-pub-…)
     → domains[] = {domain, firstseen, lastseen}.
  3. Return connected domains (minus the primary) with the shared ID — high-confidence
     same-operator candidates.

Key: DNSLYTICS_API_KEY in .openclaw-keys.env or env (premium credits, ~6/call). ADDITIVE +
no-key-safe: with no key we skip the (expensive) headless render entirely.
"""

import os
import re
import sys
import json
import urllib.request

_OPENCLAW_KEYS = "/mnt/system/base/.openclaw-keys.env"
_DNS_BASE = "https://api.dnslytics.net/v1"


def _key() -> str:
    k = os.environ.get("DNSLYTICS_API_KEY", "").strip()
    if k:
        return k
    try:
        with open(_OPENCLAW_KEYS) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DNSLYTICS_API_KEY="):
                    return line.partition("=")[2].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


# GA4 = G-<10 alnum>; UA = UA-<digits>-<digits>; GTM = GTM-<alnum>; AdSense = ca-pub-<digits>
_GA4   = re.compile(r'\bG-[A-Z0-9]{10}\b')
_UA    = re.compile(r'\bUA-\d{4,}-\d+\b', re.I)
_GTM   = re.compile(r'\bGTM-[A-Z0-9]{5,8}\b', re.I)
_PUB   = re.compile(r'\bca-pub-\d{10,}\b', re.I)
_ID_IN_URL = re.compile(r'[?&](?:id|tid)=([A-Za-z0-9-]+)')


def extract_tracking_ids(domain: str, timeout_s: int = 35) -> dict:
    """Headless-render the site and return clean tracking IDs from analytics request URLs.

    Returns {"ga": [...], "gtm": [...], "adsense": [...]}. Trusts IDs seen on actual
    googletagmanager/google-analytics/googlesyndication requests (authoritative) plus a
    tightened page-text scan; ignores the G-SERVICES/g-recaptcha-style false hits.
    """
    out = {"ga": set(), "gtm": set(), "adsense": set()}
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print(f"[INFO] dnslytics: Playwright unavailable, can't extract IDs ({e})", file=sys.stderr)
        return {k: [] for k in out}

    def _add(s: str):
        for m in _GA4.findall(s):  out["ga"].add(m.upper())
        for m in _UA.findall(s):   out["ga"].add(m.upper())
        for m in _GTM.findall(s):  out["gtm"].add(m.upper())
        for m in _PUB.findall(s):  out["adsense"].add(m.lower())

    try:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True, args=["--no-sandbox"])
            pg = b.new_page()

            def on_req(r):
                u = r.url
                low = u.lower()
                if any(h in low for h in ("googletagmanager.com", "google-analytics.com",
                                          "analytics.google.com", "googlesyndication.com",
                                          "doubleclick.net")):
                    for cap in _ID_IN_URL.findall(u):
                        _add(cap)
                    _add(u)  # also scan the whole url (tid=, pubid=)

            pg.on("request", on_req)
            try:
                pg.goto(f"https://{domain}", wait_until="networkidle", timeout=timeout_s * 1000)
            except Exception as e:
                print(f"[INFO] dnslytics: render warn for {domain}: {e}", file=sys.stderr)
            # tightened scan of rendered DOM as a backstop
            try:
                _add(pg.content())
            except Exception:
                pass
            b.close()
    except Exception as e:
        print(f"[WARN] dnslytics: headless extraction failed: {e}", file=sys.stderr)

    res = {k: sorted(v) for k, v in out.items()}
    print(f"[INFO] dnslytics: tracking IDs for {domain} → "
          f"GA={res['ga']} GTM={res['gtm']} AdSense={res['adsense']}", file=sys.stderr)
    return res


def _dns_get(path: str, key: str) -> dict:
    url = f"{_DNS_BASE}/{path}?apikey={key}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JamBot-BrandAudit/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[WARN] dnslytics {path}: {e}", file=sys.stderr)
        return {}


def _reverse(kind: str, ident: str, key: str) -> list:
    """kind = 'reverseganalytics' | 'reverseadsense'. Returns [{domain,firstseen,lastseen}]."""
    data = _dns_get(f"{kind}/{ident}", key)
    if (data.get("status") or "").lower() not in ("succeed", "success", "ok"):
        return []
    return (data.get("data") or {}).get("domains") or []


def fetch_connected_via_analytics(domain: str, brand_name: str = "") -> dict:
    """Map the operator's domain network via shared tracking IDs. Never raises.

    Returns:
        {
          "available": bool,            # key present + at least one ID extracted
          "tracking_ids": {"ga","gtm","adsense"},
          "connected": [{domain, via, id, firstseen, lastseen}],  # primary excluded
        }
    """
    out = {"available": False, "tracking_ids": {}, "connected": []}
    key = _key()
    if not key:
        print("[INFO] dnslytics: no DNSLYTICS_API_KEY — reverse-analytics skipped", file=sys.stderr)
        return out

    ids = extract_tracking_ids(domain)
    out["tracking_ids"] = ids
    primary = (domain or "").lower().replace("www.", "")

    seen = {}
    # GA IDs (G-… and UA-…) → DNSlytics uses lowercase; for UA it takes the account form
    for gid in ids.get("ga", []):
        q = gid.lower()
        # UA-15589237-1 → ua-15589237 (DNSlytics keys on the account, not the property)
        m = re.match(r'(ua-\d+)', q)
        if m:
            q = m.group(1)
        for d in _reverse("reverseganalytics", q, key):
            dom = (d.get("domain") or "").lower().replace("www.", "")
            if dom and dom != primary and primary not in dom and dom not in seen:
                seen[dom] = {"domain": dom, "via": "google-analytics", "id": gid,
                             "firstseen": d.get("firstseen", ""), "lastseen": d.get("lastseen", "")}
    for pub in ids.get("adsense", []):
        for d in _reverse("reverseadsense", pub, key):
            dom = (d.get("domain") or "").lower().replace("www.", "")
            if dom and dom != primary and primary not in dom and dom not in seen:
                seen[dom] = {"domain": dom, "via": "adsense", "id": pub,
                             "firstseen": d.get("firstseen", ""), "lastseen": d.get("lastseen", "")}

    out["connected"] = sorted(seen.values(), key=lambda x: x["domain"])[:25]
    out["available"] = bool(ids.get("ga") or ids.get("adsense"))
    print(f"[INFO] dnslytics: {len(out['connected'])} connected domain(s) via shared tracking ID",
          file=sys.stderr)
    return out
