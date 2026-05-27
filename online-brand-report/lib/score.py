"""score.py — Brand Health Score 0-100 calculation."""


def _clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


def calculate_score(data: dict) -> dict:
    """
    Compute the Brand Health Score from the aggregated data dict.
    Returns: {
        "total": int (0-100),
        "grade": str,
        "grade_desc": str,
        "breakdown": {dimension: score, ...}
    }
    """

    # ── SEO Score (25%) ──────────────────────────────────────────────────────
    kw_total = data.get("kw_total", 0)
    kw_top10 = (data.get("kw_top3", 0) + data.get("kw_4_10", 0))
    avg_pos   = data.get("avg_position", 50.0)

    # % in top 10 (0-100)
    top10_pct   = (kw_top10 / max(1, kw_total)) * 100 if kw_total > 0 else 0
    # Position score: 1=100, 50=0
    pos_score   = _clamp(100 - ((avg_pos - 1) / 49) * 100)
    # Volume coverage: 50+ keywords = 100, 0 = 0
    vol_score   = _clamp(min(100, kw_total * 2))
    seo_raw     = (top10_pct * 0.5) + (pos_score * 0.3) + (vol_score * 0.2)
    seo_score   = _clamp(seo_raw)

    # ── Web Health (20%) ─────────────────────────────────────────────────────
    lh_perf = data.get("lh_performance", 0)
    lh_seo  = data.get("lh_seo", 0)
    lh_a11y = data.get("lh_accessibility", 0)
    web_score = _clamp((lh_perf * 0.50) + (lh_seo * 0.30) + (lh_a11y * 0.20))

    # ── Local SEO (20%) ──────────────────────────────────────────────────────
    review_count = data.get("review_count", 0)
    review_avg   = data.get("review_avg", 0.0)
    map_positions = data.get("map_pack_positions", {})

    # Review score: 50+ reviews = 100
    review_vol_score = _clamp(min(100, (review_count / 50) * 100))
    # Star rating: 5★ = 100
    review_star_score = (review_avg / 5.0) * 100 if review_avg > 0 else 0
    # Map pack score: average position score for cities
    map_scores = []
    for city, pos in map_positions.items():
        if pos and pos <= 3:
            map_scores.append(100)
        elif pos and pos <= 10:
            map_scores.append(60)
        elif pos:
            map_scores.append(30)
        else:
            map_scores.append(0)
    map_score = (sum(map_scores) / len(map_scores)) if map_scores else 0

    local_score = _clamp(
        (review_vol_score * 0.35) + (review_star_score * 0.35) + (map_score * 0.30)
    )

    # ── Backlinks (15%) ──────────────────────────────────────────────────────
    domain_rank = data.get("domain_rank", 0)
    ref_domains = data.get("referring_domains_total", 0)
    # Domain rank 0-100 (DataForSEO rank is 0-100)
    rank_score = _clamp(domain_rank)
    # Referring domains: 100+ = 100
    rd_score   = _clamp(min(100, (ref_domains / 100) * 100))
    bl_score   = _clamp((rank_score * 0.6) + (rd_score * 0.4))

    # ── Content (10%) ────────────────────────────────────────────────────────
    kw_suggestions = data.get("kw_suggestions_count", 0)
    gap_count      = data.get("gap_count", 0)
    # More ranking keywords = better; fewer gaps = better
    content_kw_score  = _clamp(min(100, kw_total * 1.5))
    gap_score         = _clamp(max(0, 100 - (gap_count * 5)))  # 20 gaps = 0
    content_score     = _clamp((content_kw_score * 0.6) + (gap_score * 0.4))

    # ── Social (10%) ─────────────────────────────────────────────────────────
    platforms_claimed = data.get("platforms_claimed", 0)
    platforms_total   = data.get("platforms_total", 6)
    social_score      = _clamp((platforms_claimed / max(1, platforms_total)) * 100)

    # ── Weighted Total ────────────────────────────────────────────────────────
    total = (
        seo_score   * 0.25 +
        web_score   * 0.20 +
        local_score * 0.20 +
        bl_score    * 0.15 +
        content_score * 0.10 +
        social_score * 0.10
    )
    total = int(_clamp(total))

    # Grade
    if total >= 80:
        grade = "A"
        grade_desc = "Strong — Visible and Winning"
    elif total >= 65:
        grade = "B"
        grade_desc = "Mixed — Visible But Not Winning"
    elif total >= 50:
        grade = "C"
        grade_desc = "Developing — Present But Outranked"
    elif total >= 35:
        grade = "D"
        grade_desc = "Weak — Mostly Invisible Online"
    else:
        grade = "F"
        grade_desc = "Critical — Needs Immediate Attention"

    return {
        "total": total,
        "grade": grade,
        "grade_desc": grade_desc,
        "breakdown": {
            "seo":     round(seo_score, 1),
            "web":     round(web_score, 1),
            "local":   round(local_score, 1),
            "backlinks": round(bl_score, 1),
            "content": round(content_score, 1),
            "social":  round(social_score, 1),
        }
    }
