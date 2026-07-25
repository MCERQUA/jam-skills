#!/usr/bin/env python3
"""
usmap.py — project US geometry + lead points to SVG coordinates at BUILD time.

When to draw our own map instead of using Google Maps:

This was originally written as a CSP workaround — maps.googleapis.com was allowlisted
in NO tenant CSP until it was fixed 2026-07-24. That is no longer the reason to use it.

Use this when the map is DATA VISUALIZATION rather than navigation:
  - plotting many records (leads, clients, coverage) on a national/regional map
  - choropleths, density, per-state rollups
  - the page is or may become PUBLIC (/api/maps/config needs auth, so a Google map
    goes blank for anonymous viewers — this one does not)
  - you want zero external requests, zero API cost, and immunity to CSP tightening

Use real Google Maps (templates 1-5) for directions, places search, live pan/zoom.

Albers Equal Area Conic for the lower 48, with Alaska projected separately and
inset bottom-left (the standard "AlbersUsa" composite treatment).

Albers Equal Area Conic for the lower 48, with Alaska projected separately and
inset bottom-left (the standard "AlbersUsa" composite treatment).
"""
import json
import math
import os

# us-states.geojson ships next to this file inside the skill.
# Override with USMAP_REF=<dir> if you keep the geometry elsewhere.
REF = os.environ.get("USMAP_REF") or os.path.dirname(os.path.abspath(__file__))
W, H = 960.0, 600.0


class Albers:
    """Albers Equal Area Conic. Angles in degrees."""

    def __init__(self, lat0, lon0, lat1, lat2, scale, tx, ty):
        self.lon0 = math.radians(lon0)
        p1, p2 = math.radians(lat1), math.radians(lat2)
        self.n = 0.5 * (math.sin(p1) + math.sin(p2))
        self.C = math.cos(p1) ** 2 + 2 * self.n * math.sin(p1)
        self.rho0 = self._rho(math.radians(lat0))
        self.scale, self.tx, self.ty = scale, tx, ty

    def _rho(self, phi):
        return math.sqrt(max(self.C - 2 * self.n * math.sin(phi), 1e-12)) / self.n

    def __call__(self, lon, lat):
        # Wrap the longitude delta into [-180,180]. Alaska's Aleutians cross the
        # antimeridian (+172E), which without this projects them a whole globe
        # away and wrecks the auto-fit for the entire map.
        d = math.degrees(math.radians(lon) - self.lon0)
        d = (d + 180.0) % 360.0 - 180.0
        theta = self.n * math.radians(d)
        rho = self._rho(math.radians(lat))
        x = rho * math.sin(theta)
        y = self.rho0 - rho * math.cos(theta)
        return (self.tx + x * self.scale, self.ty - y * self.scale)


PAD = 18.0


def _fit(proj, feats, box):
    """Rescale/translate a unit projection so `feats` fill `box` exactly.
    Hand-tuned constants clipped Washington off the top edge — derive them."""
    xs, ys = [], []
    for f in feats:
        for ring in _rings(f["geometry"]):
            for lon, lat in ring:
                x, y = proj(lon, lat)
                xs.append(x)
                ys.append(y)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bx, by, bw, bh = box
    s = min((bw - 2 * PAD) / (x1 - x0), (bh - 2 * PAD) / (y1 - y0))
    proj.scale *= s
    # xs/ys are already SCREEN coords (__call__ flips y), so both translations
    # anchor on the minimum. Anchoring y on the max instead pushed Washington
    # 34px off the top edge.
    proj.tx = bx + PAD - x0 * s
    proj.ty = by + PAD - y0 * s
    return proj


def _load():
    return json.load(open(os.path.join(REF, "us-states.geojson")))["features"]


# Unit projections; fitted below once the geometry is known.
CONUS = Albers(37.5, -96, 29.5, 45.5, scale=1, tx=0, ty=0)
ALASKA = Albers(60, -152, 55, 65, scale=1, tx=0, ty=0)
AK_CLIP = {"Alaska"}
SKIP = {"Hawaii", "Puerto Rico"}   # no leads there; keeps the frame tight
_FITTED = False


def _ensure_fitted():
    global _FITTED
    if _FITTED:
        return
    feats = _load()
    _fit(CONUS, [f for f in feats
                 if f["properties"].get("name") not in SKIP | AK_CLIP],
         (0, 0, W, H))
    # Alaska inset, bottom-left. CONUS reaches y=446 in this left strip
    # (New Mexico), so anchor below that or the inset lands on Arizona.
    _fit(ALASKA, [f for f in feats if f["properties"].get("name") in AK_CLIP],
         (0, H * 0.77, W * 0.22, H * 0.23))
    _FITTED = True


def project(lon, lat, region=None):
    """Region name lets Alaska points land in the inset."""
    _ensure_fitted()
    if (region or "").strip() == "Alaska" or (lat > 51 and lon < -129):
        return ALASKA(lon, lat)
    return CONUS(lon, lat)


def _rings(geom):
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    if geom["type"] == "MultiPolygon":
        return [r for poly in geom["coordinates"] for r in poly]
    return []


def state_paths(simplify_every=1):
    """-> list of {name, d} SVG path strings, already projected."""
    _ensure_fitted()
    out = []
    for f in _load():
        name = f["properties"].get("name", "")
        if name in SKIP:
            continue
        proj = ALASKA if name in AK_CLIP else CONUS
        segs = []
        for ring in _rings(f["geometry"]):
            pts = ring[::simplify_every] if simplify_every > 1 else ring
            if len(pts) < 3:
                continue
            d = []
            for i, (lon, lat) in enumerate(pts):
                x, y = proj(lon, lat)
                d.append(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}")
            segs.append("".join(d) + "Z")
        if segs:
            out.append({"name": name, "d": "".join(segs)})
    return out


if __name__ == "__main__":
    paths = state_paths(2)
    print(f"{len(paths)} states, {sum(len(p['d']) for p in paths)} bytes of path data")
    for city, lon, lat, reg in [("Phoenix", -112.07, 33.45, "Arizona"),
                                ("Houston", -95.37, 29.76, "Texas"),
                                ("Anchorage", -149.9, 61.2, "Alaska")]:
        print(f"  {city:10} -> {tuple(round(v,1) for v in project(lon, lat, reg))}")
