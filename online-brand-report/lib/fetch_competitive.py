"""fetch_competitive.py — Competitor domains, traffic estimates, keyword overlap."""

import os
import sys
from .config import dfs_post, dfs_get_items, dfs_get_result0
from .fetch_ahrefs import enrich_domains_with_dr, fetch_domain_rating

def fetch_competitive(domain: str, competitors=None, location_code: int = 2840) -> dict:
    """Return competitor data. Never raises.

    competitors: optional caller-supplied competitor seed list (currently informational —
    the competitor set is derived from DataForSEO; kept for call-site compatibility).
    location_code: DataForSEO country code threaded from generate.py (2840 US / 2124 CA)."""
    out = {
        "competitors": [],      # list of {domain, traffic_estimate, keyword_count, overlap_pct}
        "client_traffic": 0,    # estimated monthly visits
        "top_competitor": "",
        # For radar chart: normalized 0-100 values vs top competitor
        "radar_client": [0, 0, 0, 0, 0, 0],
        "radar_competitor": [100, 100, 100, 100, 100, 100],
        "radar_labels": ["Traffic", "Keywords", "Top-10 KW", "Backlinks", "Authority", "Pages"],
        "radar_comp_name": "",
    }

    competitors_raw = []

    # --- Competitors ---
    try:
        result = dfs_post("dataforseo_labs/google/competitors_domain/live", [
            {
                "target": domain,
                # location_name/language_name removed: competitors_domain/live (Labs) rejects them →
                # 404. Labs endpoints take location_code/language_code or nothing (ica-voice 2026-06-01).
                "location_code": location_code,
                "language_code": "en",
                "limit": 25,
            }
        ])
        items = dfs_get_items(result)
        # Filter out the domain ITSELF + generic platforms/directories/social/video sites —
        # those aren't real local competitors (they rank for everything). Keep the first 5
        # genuine competitor domains. (Fixed 2026-06-01 — was showing self + youtube/yelp/angi.)
        _self = domain.lower().lstrip("www.")
        _BLOCK = (
            "youtube.com", "facebook.com", "instagram.com", "linkedin.com", "twitter.com",
            "x.com", "tiktok.com", "pinterest.com", "reddit.com", "yelp.com", "angi.com",
            "angieslist.com", "bbb.org", "homeadvisor.com", "thumbtack.com", "homeguide.com",
            "houzz.com", "nextdoor.com", "mapquest.com", "yellowpages.com", "manta.com",
            "homedepot.com", "lowes.com", "amazon.com", "wikipedia.org", "indeed.com",
            "glassdoor.com", "google.com", "apple.com", "bing.com", "porch.com", "buildzoom.com",
            # 2026-07-26: Q&A / forum / UGC platforms rank for every long-tail question in
            # every trade. quora.com reached a real customer report as a "competitor" to a
            # spray-foam contractor in Mt. Vernon IL at 362,982,615 est. traffic.
            "quora.com", "stackexchange.com", "answers.com", "medium.com", "substack.com",
            "wikihow.com", "ehow.com", "hunker.com", "thespruce.com", "bobvila.com",
            "familyhandyman.com", "thisoldhouse.com", "finehomebuilding.com",
            "greenbuildingadvisor.com", "energy.gov", "epa.gov", "consumerreports.org",
            "forbes.com", "nytimes.com", "usatoday.com", "yahoo.com", "msn.com",
            "walmart.com", "ebay.com", "etsy.com", "menards.com", "acehardware.com",
            "tractorsupply.com", "grainger.com", "alibaba.com",
        )
        # ── SCALE SANITY (2026-07-26, Mike: "if we're pulling stuff like that then we're
        # not actually finding competitors") ────────────────────────────────────────────
        # A static blocklist is whack-a-mole and will always be one domain behind. The
        # structural signal is SCALE: a genuine competitor for a local service business is
        # another local service business. National publishers, manufacturers and UGC
        # platforms rank for the same long-tail queries but are not competing for the same
        # customer, and presenting them as competitors is both useless strategically and
        # damaging to our credibility with the prospect.
        #
        # These domains come from Labs `competitors_domain`, which means "ranks for
        # keywords you rank for" — SERP CO-OCCURRENCE, not competition. This is where that
        # distinction gets enforced.
        #
        # Two filters, applied after traffic is known (see _apply_scale_filter below):
        #   1. absolute ceiling  — above COMPETITOR_TRAFFIC_CEILING est. monthly organic,
        #      it is a publisher/national brand, not a local rival.
        #   2. outlier rejection — drop anything >COMPETITOR_OUTLIER_FACTOR x the median of
        #      the surviving candidates, which catches new giants the ceiling misses.
        # Everything dropped is LOGGED with its reason — a filter that silently shrinks the
        # list would read as "only 2 competitors found" when we actually found 5.
        for item in items:
            dom = (item.get("domain") or "").lower().lstrip("www.")
            if not dom or dom == _self or dom in _BLOCK:
                if dom and dom != _self:
                    print(f"[competitors] DROP {dom}: blocklisted (platform/publisher/retailer)",
                          file=sys.stderr)
                continue
            competitors_raw.append({
                "domain": item.get("domain") or "",
                "keyword_count": int(item.get("avg_position") or 0),  # overwritten with traffic
                "intersections": int(item.get("intersections") or 0),
            })
            # Take MORE than we need — the scale filter below removes some, and stopping at
            # 5 here used to mean a blocked giant cost us a real competitor slot.
            if len(competitors_raw) >= 15:
                break
    except Exception as e:
        print(f"[WARN] Competitors fetch failed: {e}", file=sys.stderr)

    # --- Bulk Traffic Estimation ---
    targets = [domain] + [c["domain"] for c in competitors_raw if c["domain"]]
    traffic_map = {}
    if targets:
        try:
            result = dfs_post("dataforseo_labs/google/bulk_traffic_estimation/live", [
                {"targets": targets[:10], "location_code": location_code, "language_code": "en"}
            ])
            items = dfs_get_items(result)
            for item in items:
                t = item.get("target") or ""
                # ETV lives at metrics.organic.etv (verified 2026-06-01) — the old flat
                # estimated_traffic_per_month/traffic fields don't exist → was always 0.
                m = item.get("metrics") or {}
                est = int((m.get("organic") or {}).get("etv") or 0)
                if not est:
                    est = int((m.get("paid") or {}).get("etv") or 0)
                traffic_map[t] = est
        except Exception as e:
            print(f"[WARN] Traffic estimation failed: {e}", file=sys.stderr)

    out["client_traffic"] = traffic_map.get(domain, 0)

    # Enrich competitor domains with DR via the free Ahrefs public endpoint (no key, $0).
    # fetch_backlinks already called fetch_domain_rating(domain) earlier in the run, so the
    # client's entry is already in _cache — no extra HTTP call there.
    comp_domains = [c["domain"] for c in competitors_raw if c.get("domain")]
    dr_map: dict = {}
    if comp_domains:
        try:
            dr_map = enrich_domains_with_dr(comp_domains)
        except Exception as e:
            print(f"[WARN] Competitor DR enrichment failed: {e}", file=sys.stderr)

    # Build competitors output list
    _cand = []
    for c in competitors_raw:
        dom = c["domain"]
        traffic = traffic_map.get(dom, 0)
        _cand.append({
            "domain": dom,
            "traffic_estimate": traffic,
            "keyword_count": c.get("intersections", 0),
            "overlap_pct": 0,
            "dr": dr_map.get(dom, {}).get("dr", 0),
        })

    # ── SCALE FILTER (2026-07-26) ────────────────────────────────────────────────────
    # See the note at the blocklist. Enforced HERE because it needs traffic, which is only
    # known after bulk_traffic_estimation. Tunable via env for verticals where a bigger
    # competitor really is a competitor (set COMPETITOR_TRAFFIC_CEILING=0 to disable).
    CEILING = int(os.environ.get("COMPETITOR_TRAFFIC_CEILING", "500000"))
    FACTOR  = float(os.environ.get("COMPETITOR_OUTLIER_FACTOR", "20"))

    kept = _cand
    if CEILING > 0:
        over = [c for c in kept if c["traffic_estimate"] > CEILING]
        for c in over:
            print(f"[competitors] DROP {c['domain']}: est. traffic {c['traffic_estimate']:,} "
                  f"> ceiling {CEILING:,} — national publisher/brand, not a local rival",
                  file=sys.stderr)
        kept = [c for c in kept if c["traffic_estimate"] <= CEILING]

    # Outlier pass: catches giants under the ceiling that still dwarf the real field.
    known = sorted(c["traffic_estimate"] for c in kept if c["traffic_estimate"] > 0)
    if len(known) >= 3 and FACTOR > 0:
        median = known[len(known) // 2]
        if median > 0:
            out_lim = median * FACTOR
            for c in [c for c in kept if c["traffic_estimate"] > out_lim]:
                print(f"[competitors] DROP {c['domain']}: {c['traffic_estimate']:,} is "
                      f">{FACTOR:g}x the median of the field ({median:,}) — scale outlier",
                      file=sys.stderr)
            kept = [c for c in kept if c["traffic_estimate"] <= out_lim]

    if len(kept) < len(_cand):
        print(f"[competitors] scale filter: kept {len(kept)} of {len(_cand)} candidates",
              file=sys.stderr)
    # Be honest rather than padding: too few real rivals is a FINDING (the client may have
    # no meaningful local competition online), not something to backfill with publishers.
    if not kept:
        print("[competitors] WARNING: every candidate was a platform/publisher/out-of-scale "
              "domain. Reporting NO competitors rather than inventing them — this usually "
              "means the local field has little organic presence, which is itself the story.",
              file=sys.stderr)

    out["competitors"] = kept[:5]

    if out["competitors"]:
        out["top_competitor"] = out["competitors"][0]["domain"]
        out["radar_comp_name"] = out["top_competitor"]

        # Build radar: client vs top competitor (values relative to competitor max)
        top_traffic = max(1, out["competitors"][0]["traffic_estimate"])
        client_traffic = max(0, out["client_traffic"])
        top_kw   = max(1, out["competitors"][0]["keyword_count"])
        client_kw = 0  # filled in by orchestrator from organic data if available

        def _norm(val, max_val):
            return min(100, round((val / max_val) * 100, 1)) if max_val > 0 else 0

        # Authority radar axis: client DR vs top competitor DR (both from Ahrefs free cache)
        top_dr = out["competitors"][0].get("dr", 0)
        try:
            client_dr = fetch_domain_rating(domain)["dr"]
        except Exception:
            client_dr = 0

        out["radar_client"] = [
            _norm(client_traffic, top_traffic),
            0,   # keywords — filled in by orchestrator
            0,   # top-10 kw — filled in by orchestrator
            0,   # backlinks — filled in by orchestrator
            _norm(client_dr, top_dr),  # authority (DR) — live from Ahrefs; 0 if comp DR unknown
            0,   # pages — filled in by orchestrator
        ]

    return out
