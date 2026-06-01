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
    seo_score   = _clamp((top10_pct * 0.5) + (pos_score * 0.3) + (vol_score * 0.2))

    # ── Web Health (20%) ─────────────────────────────────────────────────────
    lh_perf = data.get("lh_performance", 0)
    lh_seo  = data.get("lh_seo", 0)
    lh_a11y = data.get("lh_accessibility", 0)
    web_score = _clamp((lh_perf * 0.50) + (lh_seo * 0.30) + (lh_a11y * 0.20))

    # ── Local SEO (20%) ──────────────────────────────────────────────────────
    review_count = data.get("review_count", 0)
    review_avg   = data.get("review_avg", 0.0)
    map_positions = data.get("map_pack_positions", {})
    review_vol_score = _clamp(min(100, (review_count / 50) * 100))
    review_star_score = (review_avg / 5.0) * 100 if review_avg > 0 else 0
    map_scores = []
    for city, pos in map_positions.items():
        if pos and pos <= 3:    map_scores.append(100)
        elif pos and pos <= 10: map_scores.append(60)
        elif pos:               map_scores.append(30)
        else:                   map_scores.append(0)
    map_score = (sum(map_scores) / len(map_scores)) if map_scores else 0
    local_score = _clamp((review_vol_score * 0.35) + (review_star_score * 0.35) + (map_score * 0.30))

    # ── Backlinks (15%) ──────────────────────────────────────────────────────
    domain_rank = data.get("domain_rank", 0)
    ref_domains = data.get("referring_domains_total", 0)
    rank_score = _clamp(domain_rank)
    rd_score   = _clamp(min(100, (ref_domains / 100) * 100))
    bl_score   = _clamp((rank_score * 0.6) + (rd_score * 0.4))

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
                           review_count > 0 or review_avg > 0
                           or any(v is not None for v in (map_positions or {}).values())),
        "backlinks": avail("_backlinks_available", domain_rank > 0 or ref_domains > 0),
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

    if total >= 80:   grade, grade_desc = "A", "Strong — Visible and Winning"
    elif total >= 65: grade, grade_desc = "B", "Mixed — Visible But Not Winning"
    elif total >= 50: grade, grade_desc = "C", "Developing — Present But Outranked"
    elif total >= 35: grade, grade_desc = "D", "Weak — Mostly Invisible Online"
    else:             grade, grade_desc = "F", "Critical — Needs Immediate Attention"

    return {
        "total": total,
        "grade": grade,
        "grade_desc": grade_desc,
        "breakdown": {d: (round(scores[d], 1) if available[d] else None) for d in scores},
        "available": available,
        "weights_used": weights_used,
        "coverage": sum(1 for v in available.values() if v),
    }
