#!/usr/bin/env python3
"""qa_detectors.py — diverse-domain QA harness for the brand-report detectors.

Runs the THREE no-cost detectors (no DataForSEO) against a matrix of real domains
and flags bad output, so "works for any business anywhere" is something we VERIFY
instead of discover in front of a prospect:
  • resolve_location_code  — right country for the domain/location
  • _logo_from_header      — the real header/menu logo (validated it's an image)
  • detect_service         — a clean, non-empty, non-geo-polluted keyword seed

Usage:
  python3 qa_detectors.py                 # run the built-in matrix
  python3 qa_detectors.py d1.com d2.ca …  # run specific domains

Each row prints PASS/WARN/FAIL per signal. Exit 1 if any FAIL.
"""
import sys, urllib.request
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import generate as g
from lib import fetch_brand

# (domain, expected_country_substr_or_None) — real businesses across country/stack/vertical.
MATRIX = [
    ("azrimrepair.com", "United States"),               # US, AZ, rim repair
    ("foamit.ca", "Canada"),                            # CA, insulation, WordPress, www-redirect
    ("printguys.ca", "Canada"),                         # CA, apparel printing, Next.js
    ("insulationcontractorsofarizona.com", "United States"),
]

_BAD_LOGO_HINTS = ("og-image", "og_image", "social", "banner", "hero", "cover",
                   "screenshot", "photo", "-blown-in-", "facebook", "twitter")


def _is_image(url):
    """HEAD the logo URL: is it really an image and not a 404/HTML page?"""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=10)
        return (r.headers.get("Content-Type") or "").lower().startswith("image/")
    except Exception:
        return False


def run(domains):
    rows, fails = [], 0
    for item in domains:
        dom, exp_country = item if isinstance(item, tuple) else (item, None)
        code = g.resolve_location_code("", "", dom)
        country = g.country_name_for(code)
        logo = fetch_brand._logo_from_header(dom)
        service = g.detect_service(dom, {})

        # --- country verdict ---
        c_v = "PASS"
        if exp_country and exp_country.lower() not in country.lower():
            c_v = "FAIL"; fails += 1

        # --- logo verdict ---
        if not logo:
            l_v = "WARN(badge)"                       # acceptable: clean initials badge
        elif any(h in logo.lower() for h in _BAD_LOGO_HINTS):
            l_v = "FAIL(looks like a photo)"; fails += 1
        elif _is_image(logo) is False:
            l_v = "FAIL(not an image)"; fails += 1
        else:
            l_v = "PASS"

        # --- service verdict ---
        s_low = (service or "").lower()
        if not service:
            s_v = "WARN(empty→generic)"
        elif s_low in g._PLACEHOLDER_SERVICES:
            s_v = "FAIL(placeholder)"; fails += 1
        elif any(tok in s_low for tok in (" in ", " serving ", " near ")):
            s_v = "FAIL(geo-polluted)"; fails += 1
        elif len(service) > 45 or len(service.split()) > 5:
            s_v = "WARN(long seed)"
        else:
            s_v = "PASS"

        rows.append((dom, f"{country} [{c_v}]", f"{s_v}: {service!r}", f"{l_v}", logo or "—"))

    w = max(len(r[0]) for r in rows)
    print(f"\n{'DOMAIN':<{w}}  COUNTRY                  SERVICE                              LOGO")
    print("-" * (w + 96))
    for dom, country, service, lv, logo in rows:
        print(f"{dom:<{w}}  {country:<24} {service:<36} {lv}")
        print(f"{'':<{w}}    logo: {logo[:88]}")
    print(f"\n{'FAILURES: ' + str(fails) if fails else 'ALL PASS'} ({len(rows)} domains)")
    return 1 if fails else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(run(args if args else MATRIX))
