"""geo.py — resolve a business's nearest service-area cities for the money-page matrix.

Offline + free: uses the bundled data/us-cities.csv (29k US cities w/ lat-lng) and a
haversine nearest-neighbour search. No API calls. The business's own city is #1, then
the N-1 nearest distinct cities/towns.
"""
import csv, math, os, re

_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "us-cities.csv")
_CITIES = None


def _load():
    global _CITIES
    if _CITIES is None:
        rows = []
        with open(_CSV, newline="") as f:
            for r in csv.DictReader(f):
                try:
                    rows.append((r["CITY"], r["STATE_CODE"], float(r["LATITUDE"]), float(r["LONGITUDE"])))
                except Exception:
                    continue
        _CITIES = rows
    return _CITIES


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def _haversine_mi(a, b, c, d):
    R = 3958.8
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(h))


def nearest_service_areas(city, state, n=5):
    """Return [{city, state, distance_mi}] — business city first, then nearest n-1 distinct.
    state = 2-letter code. Falls back gracefully if the city isn't found."""
    cities = _load()
    cn, sn = _norm(city), (state or "").strip().upper()
    origin = None
    # exact city+state, else city-only
    for c, st, la, ln in cities:
        if _norm(c) == cn and (not sn or st == sn):
            origin = (c, st, la, ln); break
    if origin is None:
        for c, st, la, ln in cities:
            if _norm(c) == cn:
                origin = (c, st, la, ln); break
    if origin is None:
        # unknown city — return just what we were given
        return [{"city": city, "state": sn, "distance_mi": 0.0}]

    oc, ost, ola, oln = origin
    scored = []
    seen = {(_norm(oc), ost)}
    for c, st, la, ln in cities:
        key = (_norm(c), st)
        if key in seen:
            continue
        d = _haversine_mi(ola, oln, la, ln)
        scored.append((d, c, st))
    scored.sort(key=lambda x: x[0])
    out = [{"city": oc, "state": ost, "distance_mi": 0.0}]
    for d, c, st in scored:
        if len(out) >= n:
            break
        if (_norm(c), st) in seen:
            continue
        seen.add((_norm(c), st))
        out.append({"city": c, "state": st, "distance_mi": round(d, 1)})
    return out


def service_area_terms(services, areas):
    """[(service, area_dict, 'service city')] for the service×area matrix."""
    terms = []
    for svc in services:
        for a in areas:
            terms.append((svc, a, f"{svc} {a['city']}".lower()))
    return terms


if __name__ == "__main__":
    import sys, json
    city = sys.argv[1] if len(sys.argv) > 1 else "Tempe"
    state = sys.argv[2] if len(sys.argv) > 2 else "AZ"
    print(json.dumps(nearest_service_areas(city, state, 5), indent=2))
