"""score.py — Brand Health Score 0-100 calculation.

GRACEFUL DEGRADATION (fixed 2026-06-01): when a DataForSEO source is unavailable
(404 / 403 subscription / empty response), that dimension is EXCLUDED from the
weighted total and its weight is redistributed across the dimensions that DID get
real data — instead of scoring it 0, which falsely tanked healthy sites (ICA scored
20/100 F with 4 of 6 dimensions zeroed by failed endpoints, when it's a real,
ranking site). Unavailable dimensions are returned as None so the report can show
"Data unavailable" rather than a misleading 0.
"""


def _clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


def calculate_score(data: dict) -> dict:
    """
    Compute the Brand Health Score from the aggregated data dict.
    Returns: {
        "total": int (0-100),         # over AVAILABLE dimensions only
        "grade": str, "grade_desc": str,
        "breakdown": {dimension: score|None, ...},   # None = data unavailable
        "available": {dimension: bool, ...},
        "weights_used": {dimension: float, ...},      # renormalized over available
        "coverage": int,              # how many of 6 dimensions had real data
    }
    """

    # ── SEO Score (25%) ──────────────────────────────────────────────────────
    kw_total = data.get("kw_total", 0)
    kw_top10 = (data.get("kw_top3", 0) + data.get("kw_4_10", 0))
    avg_pos   = data.get("avg_position", 50.0)
    top10_pct   = (kw_top10 / max(1, kw_total)) * 100 if kw_total > 0 else 0
    pos_score   = _clamp(100 - ((avg_pos - 1) / 49) * 100)
    vol_score   = _clamp(min(100, kw_total * 2))
    # BUYER-INTENT LIVE WINS: a business can rank page-8 for huge generic informational
    # terms (which dominate the periodic crawl and drag avg_position toward 80+) yet rank
    # PAGE ONE for its actual buyer-intent service terms ("spray foam insulation contractor
    # near me"). The crawl-based components above are blind to that; the live SERP check
    # (live_first_page_count) catches it. Credit real first-page live wins so a business
    # that is visible WHERE IT COUNTS isn't scored as invisible. When no live data exists
    # (e.g. greenfield/no-domain), live_fp=0 and we fall back to the ORIGINAL formula, so
    # pre-existing reports score identically.
    live_fp = data.get("live_first_page_count", 0) or 0
    if live_fp > 0:
        buyer_intent_score = _clamp(min(100, live_fp * 25))   # 4+ first-page wins → 100
        seo_score = _clamp((top10_pct * 0.40) + (pos_score * 0.20)
                           + (vol_score * 0.15) + (buyer_intent_score * 0.25))
    else:
        seo_score = _clamp((top10_pct * 0.5) + (pos_score * 0.3) + (vol_score * 0.2))

    # ── Web Health (20%) ─────────────────────────────────────────────────────
    # Only score sub-components that were ACTUALLY measured. When the live Lighthouse
    # run times out (DataForSEO is intermittent here), perf/a11y stay at 0 and only a
    # heuristic SEO score survives via the instant_pages fallback. Counting the unmeasured
    # 0s falsely tanked the web dimension (e.g. perf*0.5 + seo80*0.3 + a11y*0.2 = 24) and
    # dragged the whole grade down a band. Renormalize over measured components only.
    # Flags default True so pre-2026-06-16 data (no flags) behaves exactly as before.
    lh_perf = data.get("lh_performance", 0)
    lh_seo  = data.get("lh_seo", 0)
    lh_a11y = data.get("lh_accessibility", 0)
    _web_subs = []
    if data.get("_lh_perf_measured", True): _web_subs.append((lh_perf, 0.50))
    if data.get("_lh_seo_measured",  True): _web_subs.append((lh_seo,  0.30))
    if data.get("_lh_a11y_measured", True): _web_subs.append((lh_a11y, 0.20))
    _web_subw = sum(w for _, w in _web_subs)
    web_score = _clamp(sum(v * w for v, w in _web_subs) / _web_subw) if _web_subw > 0 else 0.0

    # ── Local SEO (20%) ──────────────────────────────────────────────────────
    review_count = data.get("review_count", 0)
    review_avg   = data.get("review_avg", 0.0)
    map_positions = data.get("map_pack_positions", {})
    # A VERIFIED Google listing (real NAP — name + address) is itself a local-SEO asset,
    # even with zero reviews. Without this floor an established, addressed business whose
    # Google Business Profile is unclaimed/unreviewed scored a flat 0 local (e.g. Allstate
    # Spray Foam: 20-yr contractor, verified Visalia listing, no Google reviews → local 0
    # → 'Mostly Invisible' D). Credit the verified listing; reviews/stars/map still drive
    # the bulk, and the report still recommends 'claim + get Google reviews'.
    has_listing = bool(
        data.get("gmb_address") or data.get("address")
        or data.get("gmb_found") or data.get("gmb_categories")
    )
    listing_floor = 25.0 if has_listing else 0.0
    review_vol_score = _clamp(min(100, (review_count / 50) * 100))
    review_star_score = (review_avg / 5.0) * 100 if review_avg > 0 else 0
    map_scores = []
    for city, pos in map_positions.items():
        if pos and pos <= 3:    map_scores.append(100)
        elif pos and pos <= 10: map_scores.append(60)
        elif pos:               map_scores.append(30)
        else:                   map_scores.append(0)
    map_score = (sum(map_scores) / len(map_scores)) if map_scores else 0
    local_core = (review_vol_score * 0.35) + (review_star_score * 0.35) + (map_score * 0.30)
    local_score = _clamp(max(local_core, listing_floor))

    # ── Backlinks (15%) ──────────────────────────────────────────────────────
    domain_rank = data.get("domain_rank", 0)
    ahrefs_dr   = data.get("ahrefs_dr", 0)
    ref_domains = data.get("referring_domains_total", 0)
    # Ahrefs DR is a better authority signal than DataForSEO's internal rank.
    # Use DR when available; fall back to DataForSEO rank (also 0-100 scale).
    authority_score = _clamp(ahrefs_dr if ahrefs_dr > 0 else domain_rank)
    rd_score   = _clamp(min(100, (ref_domains / 100) * 100))
    bl_score   = _clamp((authority_score * 0.6) + (rd_score * 0.4))

    # ── Content (10%) ────────────────────────────────────────────────────────
    gap_count      = data.get("gap_count", 0)
    content_kw_score  = _clamp(min(100, kw_total * 1.5))
    gap_score         = _clamp(max(0, 100 - (gap_count * 5)))
    content_score     = _clamp((content_kw_score * 0.6) + (gap_score * 0.4))

    # ── Social (10%) ─────────────────────────────────────────────────────────
    platforms_claimed = data.get("platforms_claimed", 0)
    platforms_total   = data.get("platforms_total", 6)
    social_score      = _clamp((platforms_claimed / max(1, platforms_total)) * 100)

    # ── Availability inference ───────────────────────────────────────────────
    # A dimension is "available" only if its underlying source returned real data.
    # Prefer explicit flags from fetchers (data['_<dim>_available']) when present,
    # else infer: a 0 from a failed API (404/403/empty) is NOT a real score.
    def avail(flag_key, inferred):
        v = data.get(flag_key)
        return bool(v) if v is not None else inferred

    available = {
        # SEO/content reliably return data when the domain ranks at all.
        "seo":       avail("_seo_available", kw_total > 0),
        "content":   avail("_content_available", kw_total > 0 or gap_count > 0),
        # These three are the ones that 404/403 and falsely zeroed the score:
        "web":       avail("_web_available", (lh_perf or lh_seo or lh_a11y) > 0),
        # map_positions can hold keys with all-None values (cities queried, none ranked) — that's
        # NOT real local data, so require at least one non-None position (ica-voice 2026-06-01).
        "local":     avail("_local_available",
                           review_count > 0 or review_avg > 0 or has_listing
                           or any(v is not None for v in (map_positions or {}).values())),
        "backlinks": avail("_backlinks_available", domain_rank > 0 or ref_domains > 0 or ahrefs_dr > 0),
        # platforms_total defaults to 6 so it's always truthy — useless as a signal. Available only
        # if at least one platform was actually found/claimed (ica-voice 2026-06-01).
        "social":    avail("_social_available", platforms_claimed > 0),
    }

    scores = {
        "seo": seo_score, "web": web_score, "local": local_score,
        "backlinks": bl_score, "content": content_score, "social": social_score,
    }
    base_weights = {"seo": 0.25, "web": 0.20, "local": 0.20, "backlinks": 0.15, "content": 0.10, "social": 0.10}

    # Redistribute weight across available dimensions (renormalize to 1.0).
    avail_weight = sum(w for d, w in base_weights.items() if available[d])
    if avail_weight <= 0:
        # Nothing available — fall back to SEO only if we somehow have it, else 0.
        available = {**{k: False for k in available}, "seo": kw_total > 0}
        avail_weight = base_weights["seo"] if available["seo"] else 0

    weights_used, total = {}, 0.0
    for d in scores:
        if available[d] and avail_weight > 0:
            w = base_weights[d] / avail_weight
            weights_used[d] = round(w, 3)
            total += scores[d] * w
        else:
            weights_used[d] = 0.0
    total = int(_clamp(total))

    # Grade labels describe a MIX honestly. The old D/F wording ("Mostly Invisible
    # Online" / "Critical") mislabeled established businesses that rank page-one for
    # their buyer-intent terms but are buried on high-volume generics with few reviews —
    # they are NOT invisible, they have real gaps to close. Wording is accurate to what
    # a sub-band score actually means; bands themselves are unchanged.
    if total >= 80:   grade, grade_desc = "A", "Strong — Visible and Winning"
    elif total >= 65: grade, grade_desc = "B", "Solid — Competitive, With Room to Grow"
    elif total >= 50: grade, grade_desc = "C", "Developing — Present But Outranked"
    elif total >= 35: grade, grade_desc = "D", "Underbuilt — Ranking in Pockets, Real Gaps to Close"
    else:             grade, grade_desc = "F", "Early — Limited Online Visibility So Far"

    return {
        "total": total,
        "grade": grade,
        "grade_desc": grade_desc,
        "breakdown": {d: (round(scores[d], 1) if available[d] else None) for d in scores},
        "available": available,
        "weights_used": weights_used,
        "coverage": sum(1 for v in available.values() if v),
    }
