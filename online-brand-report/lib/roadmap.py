"""roadmap.py — Priority-driven recommendations engine."""


def generate_roadmap(data: dict, score_result: dict) -> dict:
    """
    Generate Priority 1 / 2 / 3 action items from audit findings.
    Returns: {
        "p1": [{"title": str, "detail": str, "icon": str}, ...],
        "p2": [...],
        "p3": [...],
    }
    """
    p1: list[dict] = []
    p2: list[dict] = []
    p3: list[dict] = []

    lcp_s       = data.get("lcp_s", 0)
    lcp_display = data.get("lcp_display", "N/A")
    cls         = data.get("cls", 0)
    lh_perf     = data.get("lh_performance", 0)
    lh_seo      = data.get("lh_seo", 0)
    schema      = data.get("schema_present", False)
    llms_txt    = data.get("llms_txt_present", False)
    review_count= data.get("review_count", 0)
    review_avg  = data.get("review_avg", 0.0)
    map_positions = data.get("map_pack_positions", {})
    domain_rank = data.get("domain_rank", 0)
    gap_count   = data.get("gap_count", 0)
    platforms_claimed = data.get("platforms_claimed", 0)
    kw_top3     = data.get("kw_top3", 0)
    kw_total    = data.get("kw_total", 0)
    city        = data.get("city", "your area")
    service     = data.get("service", "your service")
    referring_domains = data.get("referring_domains_total", 0)
    has_knowledge_panel = data.get("has_knowledge_panel", False)

    # ── PRIORITY 1 — Fix first ────────────────────────────────────────────────

    if lcp_s > 4.0:
        p1.append({
            "title": f"Fix critical page speed — LCP at {lcp_display}",
            "detail": "Largest Contentful Paint above 4s is a confirmed Google ranking penalty. Compress hero images, add lazy-loading, and enable server-side caching. Expected ranking lift in 4-8 weeks.",
            "icon": "⚡",
            "tag": "Web Speed",
        })
    elif lcp_s > 2.5:
        p1.append({
            "title": f"Improve page speed — LCP at {lcp_display} (needs work)",
            "detail": "LCP between 2.5-4s is in the 'Needs Improvement' zone. Optimize image delivery and reduce render-blocking JavaScript to push into the 'Good' threshold below 2.5s.",
            "icon": "⚡",
            "tag": "Web Speed",
        })

    if not llms_txt:
        p1.append({
            "title": "Deploy llms.txt for AI search visibility",
            "detail": "ChatGPT, Claude, Perplexity, and Google AI Overview pull from llms.txt. A single file can put your brand in AI-generated recommendations for local service searches. Competitors without it are invisible to AI.",
            "icon": "🤖",
            "tag": "AI Visibility",
        })

    if not schema:
        p1.append({
            "title": "Add LocalBusiness + Service schema markup",
            "detail": "No JSON-LD structured data detected on the homepage. LocalBusiness schema ties your NAP, reviews, and services to the Google Knowledge Graph — required for rich results and map-pack eligibility.",
            "icon": "🏗️",
            "tag": "Technical SEO",
        })

    if review_count < 20:
        p1.append({
            "title": f"Build GMB review base — currently {review_count} review{'s' if review_count != 1 else ''}",
            "detail": "Industry benchmark for local services is 40+ reviews at 4.5★+ for page-1 map pack eligibility. Implement a post-job text-ask flow (request 48h after completion) to hit 40 reviews in 90 days.",
            "icon": "⭐",
            "tag": "Local SEO",
        })
    elif review_avg < 4.0 and review_count > 0:
        p1.append({
            "title": f"Address low review average — {review_avg:.1f}★ average",
            "detail": "Below 4.0★ suppresses map pack visibility. Respond to negative reviews publicly, implement a feedback-first flow to catch unhappy customers before they post, and activate a review request campaign for satisfied clients.",
            "icon": "⭐",
            "tag": "Reputation",
        })

    not_in_map = [c for c, pos in map_positions.items() if not pos]
    if len(not_in_map) >= 2:
        p1.append({
            "title": f"Build city landing pages for {', '.join(not_in_map[:3])}",
            "detail": f"Your domain is not visible in the map pack for {len(not_in_map)} target cities. Dedicated city service pages with local schema, NAP, and city-specific content are the primary ranking lever in local search.",
            "icon": "📍",
            "tag": "Local SEO",
        })

    # If nothing critical triggered, say so plainly instead of a blank section.
    # (Mike 2026-06-01: "if there's nothing critical we should just say congrats you're in
    # good shape, nothing critical.")
    if not p1:
        p1.append({
            "title": "No critical issues — you're in good shape on the fundamentals",
            "detail": "Nice work. The site is fast, the Google Business Profile is solid, and the core technical signals check out — none of the make-or-break items need fixing right now. The opportunities below (Priority 2 & 3) are about pulling ahead of competitors, not patching problems.",
            "icon": "✅",
            "tag": "All Clear",
        })

    # ── PRIORITY 2 — Next 60-90 days ─────────────────────────────────────────

    # Only recommend a backlink campaign if we actually MEASURED low authority. When the
    # Backlinks API isn't active (data unavailable → all zeros), don't treat it as a real
    # gap — that's pending data, not a deficiency. (Fixed 2026-06-01.)
    bl_unavailable = data.get("backlinks_unavailable", False) or (domain_rank == 0 and referring_domains == 0)
    if domain_rank < 20 and not bl_unavailable:
        p2.append({
            "title": f"Backlink building campaign needed — Domain Authority {domain_rank}",
            "detail": "Low domain authority limits how fast new content can rank. Focus on local citations (Chamber of Commerce, trade directories), supplier link exchanges, and 2-3 local press placements in the first 90 days.",
            "icon": "🔗",
            "tag": "Off-Page SEO",
        })

    if gap_count > 10:
        p2.append({
            "title": f"Fill {gap_count} keyword gaps competitors rank for",
            "detail": f"Your top competitor ranks for {gap_count} high-intent keywords where you have no visible position. These represent immediate content opportunities — primarily service variation pages and FAQ content.",
            "icon": "📝",
            "tag": "Content",
        })
    elif gap_count > 0:
        p2.append({
            "title": f"Close {gap_count} content gaps vs top competitor",
            "detail": "Competitor holds positions you're missing. Build targeted service/FAQ pages for these queries to capture the traffic.",
            "icon": "📝",
            "tag": "Content",
        })

    if platforms_claimed < 3:
        p2.append({
            "title": f"Claim and activate social profiles — {platforms_claimed} of 6 claimed",
            "detail": "Social signals contribute to local trust and brand authority. Claim Facebook, Instagram, and LinkedIn at minimum. Even low-frequency posting (2x/month) beats an unclaimed profile.",
            "icon": "📱",
            "tag": "Social",
        })

    if not has_knowledge_panel:
        p2.append({
            "title": "Establish Google Knowledge Panel",
            "detail": "No Knowledge Panel detected for this brand. Complete and verify your Google Business Profile, add Wikidata entity data, and ensure consistent NAP across 20+ citation sources to accelerate Knowledge Graph inclusion.",
            "icon": "🧠",
            "tag": "Brand Authority",
        })

    if lh_seo < 80:
        p2.append({
            "title": f"Fix on-page SEO issues — Lighthouse SEO score {lh_seo}/100",
            "detail": "Lighthouse SEO below 80 indicates technical on-page problems: missing meta descriptions, non-crawlable links, missing canonical tags, or blocked resources. Run a full Lighthouse audit and resolve all 'Failing' items.",
            "icon": "🔍",
            "tag": "Technical SEO",
        })

    # ── PRIORITY 3 — Scale phase ──────────────────────────────────────────────

    p3.append({
        "title": f"Build topical content cluster around {service}",
        "detail": "A topical authority cluster — 8-12 interconnected articles around your core service — signals domain expertise to Google and drives long-tail rankings. Focus on cost, comparison, how-to, and area-specific angles.",
        "icon": "📚",
        "tag": "Content Strategy",
    })

    p3.append({
        "title": "Launch editorial backlink outreach campaign",
        "detail": "Target home improvement publications, energy efficiency blogs, and local news sites for earned media links. One editorial link from a DA 40+ site is worth 20 directory submissions.",
        "icon": "✉️",
        "tag": "Link Building",
    })

    p3.append({
        "title": "Produce YouTube/video content for high-intent queries",
        "detail": "Video results appear in 20-30% of local service SERPs. Short-form 'Before/After' and 'How spray foam works' content ranks quickly and builds trust with homeowner buyers who research heavily before calling.",
        "icon": "🎥",
        "tag": "Content",
    })

    if kw_top3 == 0 and kw_total > 0:
        p3.append({
            "title": "Position optimization for near-page-1 keywords",
            "detail": "Several keywords ranking in positions 11-20 are close to page 1. A targeted page refresh — updating title tags, adding FAQ schema, and earning 3-5 relevant links — can push them above the fold.",
            "icon": "📈",
            "tag": "SEO",
        })

    return {"p1": p1, "p2": p2, "p3": p3}
