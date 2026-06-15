"""plan.py — turn the report's raw SEO data into an actionable BUILD PLAN.

The "meat": specific pages to build + specific articles to write, derived from real
keyword data. Output is shown in the report AND written to seo-plan.json (the spec the
website builder's Phase 1 consumes). A #1-ranking site needs BOTH a tight transactional
page set AND topical content clusters — so we always produce both, filling clusters with
real keywords where they exist and sensible generated angles where they don't.
"""
import re
try:
    from . import geo
except Exception:
    import geo  # when run/tested standalone

_STOP_TITLE = {"in", "of", "the", "for", "and", "to", "a", "an", "near", "me", "vs",
               "on", "with", "your", "by", "at"}
_STATE_ABBR = {"az","ca","tx","fl","ny","nv","co","wa","or","ut","nm","ga","nc","sc","va","oh","pa","mi","il","tn","mo","wi","mn","in","ky","al","la","ok","ar","ks","ms","ia","ct","nj","md","ma"}


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:70]


def _clean_kw(kw):
    """Title-case a keyword cleanly: uppercase state abbrevs, drop trailing 'near me',
    and remove ANY duplicate word (keep first) so 'spray foam insulation spray' →
    'Spray Foam Insulation', not 'Spray Foam Insulation Spray'."""
    words = (kw or "").strip().split()
    out, used = [], set()
    for w in words:
        lw = w.lower()
        if lw in used and lw not in _STOP_TITLE:   # drop repeated content words anywhere
            continue
        used.add(lw)
        if lw in _STATE_ABBR:
            out.append(w.upper())
        elif lw in _STOP_TITLE and out:
            out.append(lw)
        else:
            out.append(w.capitalize())
    s = " ".join(out)
    s = re.sub(r"\s+(near me|near you)$", "", s, flags=re.I)
    return s.strip() or (kw or "").title()


def _canon(kw):
    """Strong canonical form for de-duping near-identical keywords. Drops connector
    stopwords, singularizes, and uses the SORTED UNIQUE word SET — so 'spray foam
    insulation spray' / 'spray in foam insulation' / 'foam spray for insulation' all
    collapse to one ('foam insulation spray')."""
    words = re.sub(r"[^a-z0-9 ]", "", (kw or "").lower()).split()
    core = sorted({(w[:-1] if w.endswith("s") and len(w) > 3 else w)
                   for w in words if w not in _STOP_TITLE})
    return " ".join(core)


# intent classifier → ("page"|cluster_name)
def _classify(kw):
    low = (kw or "").lower()
    if re.search(r"\bcost|price|pricing|\$|per (square )?(foot|ft|sq)|calculator|estimate|how much|cheap|afford", low):
        return "Cost & Pricing"
    if re.search(r"\bvs\b|versus|compare|comparison|better|alternative|diy|do it yourself", low):
        return "Comparisons & Decisions"
    if re.search(r"how to|how do|guide|step|process|prepare|maintain|clean|fix|tips", low):
        return "How-To & Guides"
    if re.search(r"what is|what does|why |benefit|worth it|pros|cons|how long|last|safe|\bfaq\b|questions", low):
        return "Education & FAQ"
    return "page"   # transactional service/location term → a PAGE


_ENTITY_SUFFIX = re.compile(r"\b(llc|inc|corp|co|company|ltd|incorporated|enterprises)\b", re.I)

def _is_brand_term(kw: str, competitor_domains: list) -> bool:
    """True if a keyword looks like a business/brand NAME rather than a service term —
    so we don't build a page targeting a competitor's brand ('AZ Wheel Repair LLC',
    'awrs wheel repair'). Catches entity suffixes (LLC/Inc/...) and overlap with a
    competitor domain's brand token."""
    low = (kw or "").lower().strip()
    if not low:
        return False
    if _ENTITY_SUFFIX.search(low):
        return True
    joined = re.sub(r"[^a-z0-9]", "", low)
    for dom in competitor_domains:
        sld = re.sub(r"[^a-z0-9]", "", (dom or "").lower().split(".")[0])
        if len(joined) >= 7 and len(sld) >= 7 and (joined in sld or sld in joined):
            return True
    return False


_PAGE_MODIFIERS = {"auto", "car", "cars", "vehicle", "vehicles", "shop", "shops", "store", "stores",
                   "service", "services", "company", "best", "top", "professional", "affordable",
                   "cheap", "mobile", "local", "quality", "expert", "experts", "specialist",
                   "specialists", "pro", "pros", "get", "find"}

def _page_canon(kw: str) -> str:
    """Looser canonical for CONSOLIDATING near-duplicate transactional pages: drop generic
    modifiers (auto/car/shop/service/best/...) and pluralization, keep the meaningful core — so
    'wheel rims repair' / 'repair a rim' / 'auto rim repair' / 'rim repair shop' collapse onto ONE
    page (the doorway-page fix). Distinct cores ('alloy rim repair', 'cracked rim repair') stay
    separate."""
    words = re.sub(r"[^a-z0-9 ]", "", (kw or "").lower()).split()
    core = sorted({(w[:-1] if w.endswith("s") and len(w) > 3 else w)
                   for w in words if w not in _STOP_TITLE and w not in _PAGE_MODIFIERS})
    return " ".join(core)


def build_plan(data: dict) -> dict:
    service = (data.get("service") or "your service").strip()
    city    = (data.get("city") or "").strip()
    domain  = data.get("domain") or ""
    svc_t   = _clean_kw(service)

    suggestions = data.get("keyword_suggestions") or []
    gaps        = data.get("content_gaps") or []
    ranked      = data.get("top_kws") or []
    competitors = data.get("competitors") or []
    top_competitor = (data.get("top_competitor")
                      or (competitors[0]["domain"] if competitors and competitors[0].get("domain") else ""))

    # ── Keyword gaps (competitor ranks, we don't / worse) ──
    keyword_gaps = sorted(
        [{"keyword": g.get("keyword", ""), "volume": int(g.get("volume") or 0),
          "competitor": top_competitor, "competitor_position": g.get("competitor_pos"),
          "your_position": g.get("your_pos")} for g in gaps],
        key=lambda x: x["volume"], reverse=True)

    # ── Quick wins: our keywords ranking 11-20 ──
    quick_wins = sorted(
        [{"keyword": k.get("keyword", ""), "volume": int(k.get("volume") or 0), "position": int(k.get("position") or 0)}
         for k in ranked if 11 <= int(k.get("position") or 0) <= 20],
        key=lambda x: x["volume"], reverse=True)

    # ── Candidate pool (deduped, volume-ranked) ──
    pool, seen = [], set()
    for src in (gaps, suggestions, ranked):
        for k in src:
            kw = (k.get("keyword") or "").strip()
            c = _canon(kw)
            if not kw or c in seen:
                continue
            seen.add(c)
            pool.append({"keyword": kw, "volume": int(k.get("volume") or 0)})
    pool.sort(key=lambda x: x["volume"], reverse=True)

    # ── Split into PAGES (transactional) vs cluster ARTICLES (informational) ──
    PAGE_CAP = 14
    pages, page_by_canon = [], {}
    cluster_kw = {}   # cluster_name -> [ {keyword, volume} ]
    _comp_domains = [c.get("domain", "") for c in competitors]
    for k in pool:   # pool is volume-sorted desc → first hit per canon is the highest-volume primary
        if _is_brand_term(k["keyword"], _comp_domains):
            continue   # competitor brand name / business entity — never a page or article
        kind = _classify(k["keyword"])
        if kind == "page":
            pcanon = _page_canon(k["keyword"]) or _canon(k["keyword"])
            existing = page_by_canon.get(pcanon)
            if existing is not None:
                # near-duplicate variation → fold in as a secondary keyword, not a new page
                if (k["keyword"].lower() != existing["primary_keyword"].lower()
                        and len(existing["secondary_keywords"]) < 8):
                    existing["secondary_keywords"].append({"keyword": k["keyword"], "volume": k["volume"]})
                continue
            if len(pages) >= PAGE_CAP:
                continue
            title = _clean_kw(k["keyword"])
            is_local = bool(re.search(r"near me|near you|\b" + re.escape(city.lower()) + r"\b|local|area|county", k["keyword"].lower())) if city else bool(re.search(r"near me|near you|local|area|county", k["keyword"].lower()))
            pg = {
                "slug": _slug(k["keyword"]),
                "title": (f"{title} in {city}" if is_local and city and city.lower() not in title.lower() else title),
                "page_type": "location" if is_local else "service",
                "primary_keyword": k["keyword"],
                "volume": k["volume"],
                "secondary_keywords": [],   # near-dup variations consolidated onto this page
                "h1": title,
                "intent": "transactional",
            }
            pages.append(pg)
            page_by_canon[pcanon] = pg
        else:
            cluster_kw.setdefault(kind, []).append(k)

    # ── Build content clusters: real keywords first, then top up with generated angles ──
    where = f" in {city}" if city else ""
    BASE_ANGLES = {
        "Cost & Pricing": [
            f"How Much Does {svc_t} Cost{where}? (2026 Price Guide)",
            f"What Drives the Price of {svc_t}: 6 Factors Explained",
            f"Is {svc_t} Worth the Cost? An Honest Breakdown",
        ],
        "How-To & Guides": [
            f"{svc_t}: What to Expect, Step by Step",
            f"How to Choose a {svc_t} Provider{where}",
            f"Preparing for Your {svc_t} Appointment: A Checklist",
        ],
        "Comparisons & Decisions": [
            f"DIY vs. Professional {svc_t}: Which Is Right for You?",
            f"How to Compare {svc_t} Quotes (Without Getting Burned)",
        ],
        "Education & FAQ": [
            f"{svc_t}{where}: Your Top Questions Answered",
            f"How Long Does {svc_t} Last? What to Know",
            f"Common {svc_t} Myths — and the Truth",
        ],
    }

    def _article_title(kw, cluster):
        kc = _clean_kw(kw)
        low = kw.lower()
        if cluster == "Cost & Pricing":
            # don't double "cost" when the keyword already says cost/price/calculator/etc.
            if re.search(r"cost|price|calculator|estimat|per (square )?(foot|ft|sq)|cheap|afford", low):
                return f"{kc}: The {city} Pricing Guide" if city else f"{kc}: A Complete Pricing Guide"
            return f"How Much Does {kc} Cost{where}? (Price Guide)"
        if cluster == "Comparisons & Decisions":
            return f"{kc}: An Honest Comparison"
        if cluster == "How-To & Guides":
            if re.search(r"how to|guide|step", low):
                return kc if kc.lower().startswith("how") else f"{kc}: A Step-by-Step Guide"
            return f"{kc}: A Step-by-Step Guide"
        if cluster == "Education & FAQ":
            if low.startswith(("what", "why", "is ", "how long", "does ", "can ")):
                return kc + ("?" if not kc.endswith("?") else "")
            return f"{kc} — What You Should Know"
        return kc

    content_clusters = []
    for cname, angles in BASE_ANGLES.items():
        arts, seen_t = [], set()
        # real-keyword-backed articles first (best — they target measured demand)
        for k in sorted(cluster_kw.get(cname, []), key=lambda x: x["volume"], reverse=True)[:5]:
            t = _article_title(k["keyword"], cname)
            if t.lower() in seen_t:
                continue
            seen_t.add(t.lower())
            arts.append({"title": t, "target_keyword": k["keyword"], "volume": k["volume"]})
        # top up to >=3 with generated angles so every cluster is actionable
        for a in angles:
            if len(arts) >= 4:
                break
            if a.lower() in seen_t:
                continue
            seen_t.add(a.lower())
            arts.append({"title": a, "target_keyword": f"{service} ({cname.split(' ')[0].lower()})", "volume": 0})
        content_clusters.append({"name": cname, "pillar": cname, "articles": arts})

    # ── Full keyword set (for the builder's keywords.md / volumes.json) ──
    all_keywords, akseen = [], set()
    for src, kind in ((ranked, "ranked"), (gaps, "gap"), (suggestions, "suggestion")):
        for k in src:
            kw = (k.get("keyword") or "").strip()
            if not kw or kw.lower() in akseen:
                continue
            akseen.add(kw.lower())
            all_keywords.append({
                "keyword": kw,
                "volume": int(k.get("volume") or 0),
                "cpc": round(float(k.get("cpc") or 0), 2),
                "difficulty": int(k.get("difficulty") or 0),
                "our_position": k.get("position") or k.get("your_pos"),
                "intent": "informational" if _classify(kw) != "page" else "transactional",
                "source": kind,
            })
    all_keywords.sort(key=lambda x: x["volume"], reverse=True)

    # ── Services (intake + derived) — top 5 DISTINCT services for the matrix ──
    # A candidate is distinct only if it doesn't substantially overlap an already-chosen
    # service's words (so "spray foam insulation spray" + "insulation foam spray kit" don't
    # both get in as separate "services" — they're the same offering). Real builds supply
    # clean intake.services; this keeps the standalone report sane.
    def _wordset(s):
        return {w for w in _canon(s).split() if len(w) > 2}
    services, chosen_sets = [], []
    def _try_add(s):
        s = (s or "").strip()
        if not s or len(services) >= 5:
            return
        ws = _wordset(s)
        if not ws:
            return
        for cs in chosen_sets:
            inter = len(ws & cs)
            if inter and inter >= min(len(ws), len(cs)):   # subset/variation of an existing service
                return
        chosen_sets.append(ws); services.append(s)

    intake_services = [s for s in (data.get("services") or []) if (s or "").strip()]
    if intake_services:
        # Onboarding/intake gives the REAL distinct service list — trust it.
        for s in intake_services:
            _try_add(_clean_kw(s))
        services_source = "intake"
    else:
        # No intake list. Deriving distinct *services* from keyword data is unreliable —
        # it returns competitor brand names + business-type terms ("AZ Wheel Repair LLC").
        # So expand only the CORE service across areas; the full 5×N matrix populates at
        # build time once intake.services exists. (Honest > fabricated.)
        _try_add(_clean_kw(service))
        services_source = "core-only (intake.services not provided — full matrix needs onboarding service list)"
    if not services:
        services = [_clean_kw(service)]

    # ── Service × Area money-page matrix ──
    state = (data.get("state") or "").strip()
    areas = geo.nearest_service_areas(city, state, 5) if city else []
    city_vol = data.get("city_volumes") or {}     # {"service city": volume} (optional enrichment)
    service_area_matrix = []
    for svc in services:
        svc_t = _clean_kw(svc)
        for a in areas:
            term = f"{svc} {a['city']}".lower()
            service_area_matrix.append({
                "service": svc, "city": f"{a['city']}, {a['state']}",
                "slug": _slug(f"{svc}-{a['city']}"),
                "title": f"{svc_t} in {a['city']}, {a['state']}",
                "primary_keyword": term,
                "volume": int(city_vol.get(term, 0)),
                "distance_mi": a.get("distance_mi", 0),
                "page_type": "money", "h1": f"{svc_t} in {a['city']}",
            })

    # ── Supporting content: map each cluster article to a money page (link UP) ──
    supporting_content = []
    money_by_service = {}
    for m in service_area_matrix:
        money_by_service.setdefault(_canon(m["service"]), m["slug"])
    for c in content_clusters:
        for art in c["articles"]:
            # attach to the closest money page by service match, else the first
            supports = service_area_matrix[0]["slug"] if service_area_matrix else None
            for svc in services:
                if any(w in art["target_keyword"].lower() for w in _canon(svc).split()):
                    supports = money_by_service.get(_canon(svc), supports); break
            supporting_content.append({
                "article_title": art["title"], "target_keyword": art["target_keyword"],
                "volume": art.get("volume", 0), "cluster": c["name"], "supports_money_page": supports,
            })

    # ── Interlink / silo map ──
    interlink_map = []
    # pillar per service → its city pages (down) + city pages → pillar (up)
    by_service = {}
    for m in service_area_matrix:
        by_service.setdefault(_canon(m["service"]), []).append(m)
    for skey, ms in by_service.items():
        pillar_slug = _slug(ms[0]["service"])
        for m in ms:
            interlink_map.append({"from": pillar_slug, "to": m["slug"], "anchor": m["primary_keyword"], "type": "pillar-down"})
            interlink_map.append({"from": m["slug"], "to": pillar_slug, "anchor": _clean_kw(ms[0]["service"]), "type": "pillar-up"})
        # same-service adjacent cities cross-link
        for i, m in enumerate(ms):
            for other in ms[:i] + ms[i+1:]:
                interlink_map.append({"from": m["slug"], "to": other["slug"], "anchor": other["primary_keyword"], "type": "sibling-city"})
    # same-city other-services cross-link
    by_city = {}
    for m in service_area_matrix:
        by_city.setdefault(m["city"], []).append(m)
    for cty, ms in by_city.items():
        for i, m in enumerate(ms):
            for other in ms[:i] + ms[i+1:]:
                interlink_map.append({"from": m["slug"], "to": other["slug"], "anchor": other["primary_keyword"], "type": "cross-service-same-city"})
    # blogs link up to their money page
    for sc in supporting_content:
        if sc["supports_money_page"]:
            interlink_map.append({"from": "blog/" + _slug(sc["article_title"]), "to": sc["supports_money_page"],
                                  "anchor": sc["target_keyword"], "type": "blog-up"})

    # ── Coverage checklist: universe → ✓ covered / ⚠ partial / ✗ missing ──
    cov_items, covered = [], 0; partial = 0; missing = 0
    for k in all_keywords:
        pos = k.get("our_position")
        try: pos = int(pos) if pos else 0
        except Exception: pos = 0
        if 1 <= pos <= 10: status = "covered"; covered += 1
        elif 11 <= pos <= 30: status = "partial"; partial += 1
        else: status = "missing"; missing += 1
        cov_items.append({"keyword": k["keyword"], "volume": k["volume"], "status": status, "our_position": pos or None})
    coverage = {"universe_size": len(all_keywords), "covered": covered, "partial": partial,
                "missing": missing, "items": cov_items[:60]}

    return {
        "domain": domain, "service": service, "city": city,
        "service_area_matrix": service_area_matrix,
        "supporting_content": supporting_content,
        "interlink_map": interlink_map,
        "coverage": coverage,
        "services": services,
        "services_source": services_source,
        "service_areas": areas,
        "generated_for": "website-builder Phase 1 (consume instead of re-researching)",
        "all_keywords": all_keywords,
        "summary": {
            "ranked_keywords": data.get("kw_total", 0),
            "keyword_gaps": len(keyword_gaps),
            "quick_wins": len(quick_wins),
            "recommended_pages": len(pages),
            "content_articles": sum(len(c["articles"]) for c in content_clusters),
            "top_competitor": top_competitor,
            # LIVE SERP rank check — terms the domain ACTUALLY ranks for right now
            # (DataForSEO Labs under-reports small/new/non-US domains; see fetch_live_rankings).
            "live_ranked_keywords": data.get("live_ranked_count", 0),
            "live_first_page_keywords": data.get("live_first_page_count", 0),
        },
        # Raw live rankings (keyword / position / page / volume / url) folded into the report.
        "live_rankings": data.get("live_rankings", []),
        "live_first_page_count": data.get("live_first_page_count", 0),
        "live_ranked_count": data.get("live_ranked_count", 0),
        "keyword_gaps": keyword_gaps[:25],
        "quick_wins": quick_wins[:15],
        "recommended_pages": pages,
        "content_clusters": content_clusters,
        "core_pillar": f"{svc_t} (Pillar Page)",
        "competitors": [{"domain": c.get("domain"), "traffic_estimate": c.get("traffic_estimate", 0),
                         "ranking_keywords": c.get("keyword_count", 0)} for c in competitors[:6]],
    }
