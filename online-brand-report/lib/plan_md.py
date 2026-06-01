"""plan_md.py — render the build plan as a human-readable Markdown document.

Companion to plan.py: plan.py emits the machine spec (seo-plan.json) the website
builder's Phase 1 consumes; this renders the SAME plan dict as website-plan.md — the
gold-standard-style background document a human (Mike / the client) reads. Modeled on
docs/clients/seattle-siding/website-plan.md.

Pure function of the already-computed plan + score + roadmap + identity. No network.
"""
from datetime import datetime


def _fmt_vol(v):
    try:
        v = int(v or 0)
    except Exception:
        return "—"
    if v <= 0:
        return "—"
    return f"{v:,}/mo"


def _h(s):
    """Escape pipe chars so values don't break markdown tables."""
    return str(s if s is not None else "").replace("|", "\\|").strip()


def render_plan_md(plan: dict, identity: dict, score_result: dict, roadmap: dict,
                   generated_at: str = "") -> str:
    name   = identity.get("name") or identity.get("brand_name") or plan.get("domain", "")
    domain = plan.get("domain", "")
    city   = plan.get("city", "")
    state  = identity.get("state", "")
    owner  = identity.get("owner", "")
    phone  = identity.get("phone", "")
    service = plan.get("service", "")
    loc    = ", ".join([x for x in [city, state] if x])

    score = score_result or {}
    total = score.get("total", "—")
    grade = score.get("grade", "")
    gdesc = score.get("grade_desc", "")

    matrix      = plan.get("service_area_matrix", []) or []
    rec_pages   = plan.get("recommended_pages", []) or []
    clusters    = plan.get("content_clusters", []) or []
    support     = plan.get("supporting_content", []) or []
    links       = plan.get("interlink_map", []) or []
    coverage    = plan.get("coverage", {}) or {}
    gaps        = plan.get("keyword_gaps", []) or []
    wins        = plan.get("quick_wins", []) or []
    comps       = plan.get("competitors", []) or []
    services    = plan.get("services", []) or []
    svc_source  = plan.get("services_source", "")
    areas       = plan.get("service_areas", []) or []
    top_comp    = (plan.get("summary", {}) or {}).get("top_competitor", "")

    gen = generated_at or datetime.utcnow().strftime("%Y-%m-%d")
    L = []
    w = L.append

    # ── Header ──────────────────────────────────────────────────────────────
    w(f"# Website Build Plan — {name}")
    w("")
    w(f"> **Background build document.** This is the plan the website builder executes and "
      f"the rationale behind it. The machine-readable spec the builder's Phase 1 consumes is "
      f"`seo-plan.json` in this same folder; this `.md` is the human-readable companion.")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| **Business** | {_h(name)} |")
    if owner: w(f"| **Owner** | {_h(owner)} |")
    w(f"| **Domain** | {_h(domain)} |")
    if loc:   w(f"| **Location** | {_h(loc)} |")
    if phone: w(f"| **Phone** | {_h(phone)} |")
    w(f"| **Primary service** | {_h(service)} |")
    w(f"| **Brand Health Score** | {total}/100 ({grade} — {gdesc}) |")
    w(f"| **Generated** | {gen} (real DataForSEO data) |")
    w("")

    # ── 1. Executive summary ────────────────────────────────────────────────
    w("## 1. The Situation")
    w("")
    n_money = len(matrix)
    n_pages = len(rec_pages)
    n_art   = sum(len(c.get("articles", [])) for c in clusters)
    cov_u   = coverage.get("universe_size", 0)
    cov_c   = coverage.get("covered", 0)
    if top_comp:
        comp_line = (f"The market is led by **{top_comp}**"
                     + (f" (~{comps[0].get('traffic_estimate',0):,} est. monthly visits, "
                        f"{comps[0].get('ranking_keywords',0)} ranking keywords)" if comps else "")
                     + ".")
    else:
        comp_line = "Competitor data was limited for this run."
    w(f"{name} scores **{total}/100 ({grade})** on online visibility today. "
      f"Of **{cov_u}** tracked keywords in this market, the site meaningfully ranks for **{cov_c}**. "
      f"{comp_line}")
    w("")
    w(f"**The build closes that gap with a real topical structure:** "
      f"**{n_money}** service×area money pages, **{n_pages}** core/service pages, and "
      f"**{n_art}** supporting articles across **{len(clusters)}** content clusters — "
      f"all wired together with an internal-link silo ({len(links)} planned links). "
      f"Every page below targets demand measured in DataForSEO, not guessed.")
    w("")

    # ── 2. Competitive landscape ────────────────────────────────────────────
    if comps:
        w("## 2. Competitive Landscape")
        w("")
        w("| Competitor | Est. monthly traffic | Ranking keywords |")
        w("|---|---:|---:|")
        for c in comps:
            w(f"| {_h(c.get('domain'))} | {int(c.get('traffic_estimate',0)):,} | "
              f"{int(c.get('ranking_keywords',0)):,} |")
        w("")
        w("These are the sites to out-structure. The page set and clusters below are built to "
          "take share from them on the keywords they currently own (next section).")
        w("")

    # ── 3. Keyword opportunity (gaps) ───────────────────────────────────────
    if gaps:
        w("## 3. Keyword Gaps — Demand Competitors Capture and You Don't")
        w("")
        w("| Keyword | Volume | Competitor rank | Your rank |")
        w("|---|---:|---:|---:|")
        for g in gaps[:25]:
            yr = g.get("your_position")
            yr = str(yr) if yr else "—"
            cp = g.get("competitor_position")
            cp = str(cp) if cp else "—"
            w(f"| {_h(g.get('keyword'))} | {_fmt_vol(g.get('volume'))} | {cp} | {yr} |")
        w("")

    # ── 4. Site architecture: pages to build ────────────────────────────────
    w("## 4. Site Architecture — Pages to Build")
    w("")
    if services:
        w(f"**Services covered:** {', '.join(_h(s) for s in services)}  ")
        if svc_source and "intake" not in svc_source:
            w(f"_Service list source: {_h(svc_source)}. Provide the confirmed service list at "
              f"onboarding to expand the full service×area grid._")
        w("")
    if areas:
        w(f"**Service areas:** {', '.join(_h(a.get('city')) for a in areas)}")
        w("")

    # 4a service/core pages
    svc_pages = [p for p in rec_pages if p.get("page_type") == "service"]
    loc_pages = [p for p in rec_pages if p.get("page_type") == "location"]
    if svc_pages:
        w("### 4a. Core service pages")
        w("")
        w("Near-duplicate keyword variations are consolidated onto one page (\"Also targets\") "
          "rather than spun into separate thin pages.")
        w("")
        w("| Page | URL slug | Primary keyword | Volume | Also targets |")
        w("|---|---|---|---:|---|")
        for p in svc_pages:
            sec = ", ".join(s.get("keyword", "") for s in (p.get("secondary_keywords") or [])) or "—"
            w(f"| {_h(p.get('title'))} | `/{_h(p.get('slug'))}` | {_h(p.get('primary_keyword'))} | "
              f"{_fmt_vol(p.get('volume'))} | {_h(sec)} |")
        w("")

    # 4b service x area matrix (money pages)
    if matrix:
        w("### 4b. Service × Area money pages")
        w("")
        w("The local-SEO grid — one page per service per city. These are the highest-intent, "
          "highest-converting pages.")
        w("")
        w("| Page | URL slug | Primary keyword | Volume | Distance |")
        w("|---|---|---|---:|---:|")
        for m in matrix:
            d = m.get("distance_mi", 0)
            dist = f"{d:.0f} mi" if d else "—"
            w(f"| {_h(m.get('title'))} | `/{_h(m.get('slug'))}` | {_h(m.get('primary_keyword'))} | "
              f"{_fmt_vol(m.get('volume'))} | {dist} |")
        w("")

    # 4c location pages
    if loc_pages:
        w("### 4c. Location pages")
        w("")
        w("| Page | URL slug | Primary keyword | Volume |")
        w("|---|---|---|---:|")
        for p in loc_pages:
            w(f"| {_h(p.get('title'))} | `/{_h(p.get('slug'))}` | {_h(p.get('primary_keyword'))} | "
              f"{_fmt_vol(p.get('volume'))} |")
        w("")

    # ── 5. Topical authority: content clusters ──────────────────────────────
    if clusters:
        w("## 5. Topical Authority — Content Clusters")
        w("")
        w("Supporting blog content that builds topical authority and feeds links up to the money "
          "pages. Articles backed by a real measured keyword show a volume; generated angles "
          "(volume —) round out each cluster so the silo is complete.")
        w("")
        for c in clusters:
            arts = c.get("articles", [])
            w(f"### {_h(c.get('name'))}  _(pillar: {_h(c.get('pillar'))}, {len(arts)} articles)_")
            w("")
            w("| Article | Target keyword | Volume |")
            w("|---|---|---:|")
            for a in arts:
                w(f"| {_h(a.get('title'))} | {_h(a.get('target_keyword'))} | {_fmt_vol(a.get('volume'))} |")
            w("")

    # ── 6. Internal linking / silo map ──────────────────────────────────────
    if links:
        from collections import Counter
        tc = Counter(x.get("type") for x in links)
        w("## 6. Internal Linking — Silo Map")
        w("")
        w("The link architecture that makes the above rank as a system rather than isolated pages:")
        w("")
        labels = {
            "pillar-down": "Pillar → city/money pages (topical authority flows down)",
            "pillar-up":   "City/money pages → pillar (consolidate relevance up)",
            "sibling-city": "City ↔ adjacent city, same service (local relevance web)",
            "cross-service-same-city": "Service ↔ service, same city (cross-sell + crawl depth)",
            "blog-up":     "Blog article → money page it supports (pass equity to converters)",
        }
        for t, n in tc.most_common():
            w(f"- **{n}× {labels.get(t, t)}**")
        w("")
        w("<details><summary>Full link list ({} links)</summary>".format(len(links)))
        w("")
        w("| From | → To | Anchor | Type |")
        w("|---|---|---|---|")
        for x in links:
            w(f"| `{_h(x.get('from'))}` | `{_h(x.get('to'))}` | {_h(x.get('anchor'))} | {_h(x.get('type'))} |")
        w("")
        w("</details>")
        w("")

    # ── 7. Coverage scorecard ───────────────────────────────────────────────
    if coverage:
        w("## 7. Coverage Scorecard")
        w("")
        u = coverage.get("universe_size", 0)
        cc = coverage.get("covered", 0); pp = coverage.get("partial", 0); mm = coverage.get("missing", 0)
        w(f"- **Universe:** {u} tracked keywords")
        w(f"- ✅ **Covered** (pos 1–10): {cc}")
        w(f"- ⚠️ **Partial** (pos 11–30): {pp}")
        w(f"- ❌ **Missing** (pos 31+ / unranked): {mm}")
        w("")
        w("This is the before-state. Re-run `/brand-report` after the build ships to measure movement.")
        w("")

    # ── 8. 90-day roadmap ───────────────────────────────────────────────────
    if roadmap:
        w("## 8. 90-Day Priority Roadmap")
        w("")
        for tier, head in (("p1", "Priority 1 — Do first (highest impact / fixes invisibility)"),
                           ("p2", "Priority 2 — Build authority"),
                           ("p3", "Priority 3 — Scale & dominate")):
            items = roadmap.get(tier, []) or []
            if not items:
                continue
            w(f"### {head}")
            w("")
            for it in items:
                detail = it.get("detail", "")
                w(f"- **{_h(it.get('title'))}** — {_h(detail)}")
            w("")

    # ── 9. Per-page briefs ──────────────────────────────────────────────────
    brief_pages = (matrix + svc_pages)
    if brief_pages:
        # index links by source slug for in/out lookups
        out_by = {}
        in_by = {}
        for x in links:
            out_by.setdefault(x.get("from"), []).append(x)
            in_by.setdefault(x.get("to"), []).append(x)
        w("## 9. Per-Page Briefs")
        w("")
        w("What each money/service page must contain. The builder uses these as the content spec.")
        w("")
        for p in brief_pages:
            slug = p.get("slug")
            title = p.get("title")
            pk = p.get("primary_keyword")
            h1 = p.get("h1") or title
            w(f"### `/{_h(slug)}` — {_h(title)}")
            w(f"- **H1:** {_h(h1)}")
            w(f"- **Primary keyword:** {_h(pk)} ({_fmt_vol(p.get('volume'))})")
            sec = p.get("secondary_keywords") or []
            if sec:
                w(f"- **Secondary keywords:** " + ", ".join(_h(s.get("keyword")) for s in sec))
            w(f"- **Intent:** {_h(p.get('intent') or ('transactional / local' if p.get('page_type')=='money' else 'transactional'))}")
            outs = out_by.get(slug, [])
            ins = in_by.get(slug, [])
            if outs:
                w(f"- **Links to:** " + ", ".join(f"`/{_h(o.get('to'))}`" for o in outs[:8]))
            if ins:
                srcs = [i.get("from") for i in ins[:8]]
                w(f"- **Linked from:** " + ", ".join(f"`{_h(s)}`" for s in srcs))
            w(f"- **Must include:** local NAP, service description, trust signals (reviews/credentials), "
              f"clear CTA, FAQ targeting related long-tail.")
            w("")

    w("---")
    w(f"_Generated by the JamBot SEO engine (`online-brand-report`). "
      f"Customer-facing report: `brand-report-*.html`. Builder spec: `seo-plan.json`._")
    w("")
    return "\n".join(L)
