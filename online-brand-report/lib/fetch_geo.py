"""fetch_geo.py — per-service-area search volume for the money-page matrix.

Resolves the nearest service-areas (offline geo) and pulls real per-city search volume
for "[core service] [city]" in one batch DataForSEO call. plan.py reads city_volumes to
populate the service×area matrix. Cheap: one keywords_data call.
"""
import sys
from .config import dfs_post
from . import geo


def fetch_geo(service, city, state, services=None):
    out = {"service_areas": [], "city_volumes": {}}
    if not city:
        return out
    areas = geo.nearest_service_areas(city, state, 5)
    out["service_areas"] = areas
    svc_list = services or [service]
    terms = []
    for svc in svc_list:
        for a in areas:
            terms.append(f"{svc} {a['city']}".lower())
    terms = list(dict.fromkeys(terms))[:200]   # dedupe, API cap-safe
    try:
        r = dfs_post("keywords_data/google_ads/search_volume/live",
                     [{"keywords": terms, "location_code": 2840, "language_code": "en"}])
        items = (r.get("tasks") or [{}])[0].get("result") or []
        for it in items:
            kw = (it.get("keyword") or "").lower()
            if kw:
                out["city_volumes"][kw] = int(it.get("search_volume") or 0)
    except Exception as e:
        print(f"[WARN] geo volume fetch: {e}", file=sys.stderr)
    return out
