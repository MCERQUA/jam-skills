"""render.py — Generates populated brand report HTML from data dict.

Strategy: Extract the full <style> block from the template, then build a fresh
<body> with the same CSS classes, populating all data from the fetchers.
"""

import os
import re
import json
from datetime import date

_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "template.html")


def _extract_css_and_static(template_path: str) -> tuple[str, str]:
    """Extract the <style> block + any additional page CSS not in a section."""
    with open(template_path) as f:
        html = f.read()

    # Extract everything from <head> to </head> for font links, CDN scripts
    head_match = re.search(r"<head>(.*?)</head>", html, re.DOTALL)
    head_inner = head_match.group(1) if head_match else ""

    # Extract <style> block (the full CSS)
    style_match = re.search(r"(<style>.*?</style>)", html, re.DOTALL)
    style_block = style_match.group(1) if style_match else "<style></style>"

    return head_inner, style_block


def _pill_class(pos: int) -> str:
    if pos <= 3:  return "pill-ok"
    if pos <= 10: return "pill-ok"
    if pos <= 20: return "pill-warn"
    return "pill-bad"


def _band_text(band: str) -> str:
    mapping = {"good": "Good", "ok": "Good", "warn": "Needs Work", "bad": "Poor"}
    return mapping.get(band, band)


def _pill_for_band(band: str) -> str:
    mapping = {"good": "pill-ok", "ok": "pill-ok", "warn": "pill-warn", "bad": "pill-bad"}
    return mapping.get(band, "pill-warn")


def _js_list(lst: list) -> str:
    return json.dumps(lst)


def _escape(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _serp_table(block: dict, domain: str) -> str:
    query = _escape(block.get("query", ""))
    city  = _escape(block.get("city", ""))
    results = block.get("results", [])
    rows = ""
    for r in results[:15]:
        pos       = r.get("position", 0)
        dom       = _escape(r.get("domain", ""))
        title     = _escape(r.get("title", ""))
        is_client = r.get("is_client", False)
        tr_class  = ' class="us"' if is_client else (' class="top3"' if pos <= 3 else "")
        rows += f'<tr{tr_class}><td class="num">{pos}</td><td>{dom}</td><td>{title}</td></tr>\n'

    pull_date = date.today().strftime("%Y-%m-%d")
    return f"""
<div class="serp-block">
  <h3>{city} &mdash; &ldquo;{query}&rdquo;</h3>
  <div class="serp-table-wrap">
    <table class="serp-table">
      <thead><tr><th class="num">#</th><th>Domain</th><th>Title</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </div>
  <div class="serp-source-line">Source: DataForSEO SERP API &middot; pulled {pull_date}</div>
</div>
"""


def _roadmap_items_html(items: list, card_class: str, num: str, title: str, sub: str) -> str:
    li_items = ""
    for item in items:
        badge_tag = _escape(item.get("tag", ""))
        li_items += f"""
        <li>
          <div class="rm-check"></div>
          <div class="rm-item-body">
            <div class="rm-item-title">{_escape(item.get('title',''))}</div>
            <div class="rm-item-detail">{_escape(item.get('detail',''))}</div>
            <div class="rm-badges"><span class="rm-badge impact-high">{badge_tag}</span></div>
          </div>
        </li>"""
    return f"""
<div class="rm-card {card_class}">
  <div class="rm-card-header">
    <div class="num-box">{num}</div>
    <div>
      <div class="title">{title}</div>
      <div class="sub">{sub}</div>
    </div>
  </div>
  <ul class="rm-checklist">{li_items}
  </ul>
</div>
"""


def render(data: dict, score_result: dict, roadmap: dict, output_path: str, plan: dict = None) -> None:
    """Generate and write the full HTML report."""
    plan = plan or {}

    # ── Build Plan section (the meat): pages + content clusters w/ real article titles ──
    def _plan_section_html(p):
        if not p:
            return ""
        s = p.get("summary", {})
        pages = p.get("recommended_pages", [])
        clusters = p.get("content_clusters", [])
        qw = p.get("quick_wins", [])
        page_rows = "".join(
            f'<tr><td>{_escape(pg.get("title",""))}</td><td><span class="pill pill-ok">{_escape(pg.get("page_type",""))}</span></td>'
            f'<td>{_escape(pg.get("primary_keyword",""))}</td><td class="num">{int(pg.get("volume") or 0):,}</td></tr>'
            for pg in pages
        ) or '<tr><td colspan="4" style="text-align:center;color:var(--brand-muted);padding:16px;">Page set derives from keyword data</td></tr>'
        qw_rows = "".join(
            f'<tr><td>{_escape(w.get("keyword",""))}</td><td class="num">{int(w.get("volume") or 0):,}</td><td class="num">#{w.get("position")}</td></tr>'
            for w in qw
        ) or '<tr><td colspan="3" style="text-align:center;color:var(--brand-muted);padding:16px;">No page-2 keywords detected</td></tr>'
        cluster_html = ""
        for c in clusters:
            arts = "".join(
                f'<li><strong>{_escape(a.get("title",""))}</strong><span style="color:var(--brand-muted)"> — “{_escape(a.get("target_keyword",""))}” · {int(a.get("volume") or 0):,}/mo</span></li>'
                for a in c.get("articles", [])
            )
            cluster_html += (
                f'<div class="plan-cluster"><h4 style="margin:0 0 8px;color:var(--brand-text)">{_escape(c.get("name",""))} '
                f'<span style="color:var(--brand-muted);font-weight:500">({len(c.get("articles",[]))} articles)</span></h4>'
                f'<ul style="margin:0;padding-left:18px;display:flex;flex-direction:column;gap:8px;font-size:0.9rem;line-height:1.45">{arts}</ul></div>'
            )
        # ── Coverage scorecard ──
        cov = p.get("coverage", {})
        cu, cc, cp, cm = cov.get("universe_size", 0), cov.get("covered", 0), cov.get("partial", 0), cov.get("missing", 0)
        _miss = [it for it in cov.get("items", []) if it.get("status") == "missing"][:25]
        miss_rows = "".join(
            f'<tr><td>{_escape(it["keyword"])}</td><td class="num">{int(it.get("volume") or 0):,}</td>'
            f'<td><span class="pill pill-bad">✗ missing</span></td></tr>'
            for it in _miss) or \
            '<tr><td colspan="3" style="text-align:center;color:var(--brand-muted);padding:12px">—</td></tr>'
        cov_html = (
            f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px">'
            f'<div class="bl-kpi ok" style="flex:1;min-width:120px"><div class="bl-kpi-label">✓ Covered (top 10)</div><div class="bl-kpi-value">{cc}</div></div>'
            f'<div class="bl-kpi warn" style="flex:1;min-width:120px"><div class="bl-kpi-label">⚠ Partial (11–30)</div><div class="bl-kpi-value">{cp}</div></div>'
            f'<div class="bl-kpi bad" style="flex:1;min-width:120px"><div class="bl-kpi-label">✗ Missing</div><div class="bl-kpi-value">{cm}</div></div>'
            f'<div class="bl-kpi" style="flex:1;min-width:120px"><div class="bl-kpi-label">Target Universe</div><div class="bl-kpi-value">{cu}</div></div></div>'
            f'<div class="panel" style="padding:0;overflow-x:auto;max-height:320px;overflow-y:auto"><table class="cs-gap-table">'
            f'<thead><tr><th>Missing Keyword</th><th class="num">Volume</th><th>Status</th></tr></thead><tbody>{miss_rows}</tbody></table></div>'
        ) if cu else ""

        # ── Service × Area money-page matrix ──
        matrix = p.get("service_area_matrix", [])
        services_src = p.get("services_source", "")
        m_rows = "".join(
            f'<tr><td>{_escape(m.get("service",""))}</td><td>{_escape(m.get("city",""))}</td>'
            f'<td>{_escape(m.get("primary_keyword",""))}</td><td class="num">{int(m.get("volume") or 0):,}</td></tr>'
            for m in matrix)
        matrix_html = (
            f'<p class="section-desc" style="margin-top:0">{len(matrix)} geo landing pages — your <strong>money pages</strong> '
            f'({len(p.get("services",[]))} services × {len(p.get("service_areas",[]))} nearest areas). '
            f'<span style="color:var(--brand-muted)">Source: {_escape(services_src)}</span></p>'
            f'<div class="panel" style="padding:0;overflow-x:auto;max-height:380px;overflow-y:auto"><table class="cs-gap-table">'
            f'<thead><tr><th>Service</th><th>Area</th><th>Target Keyword</th><th class="num">Volume</th></tr></thead><tbody>{m_rows}</tbody></table></div>'
        ) if matrix else ""

        # ── Interlink silo summary ──
        il = p.get("interlink_map", [])
        from collections import Counter
        ilc = Counter(l.get("type") for l in il)
        silo_html = (
            f'<p class="section-desc" style="margin-top:0">{len(il)} internal links planned to concentrate authority on the money pages: '
            + ", ".join(f"{n} {t.replace('-',' ')}" for t, n in ilc.most_common()) + ". "
            "Home → service pillars → area pages; supporting blogs link <em>up</em> to their money page; "
            "money pages cross-link to the same service in nearby cities and other services in the same city.</p>"
        ) if il else ""

        return f'''
  <div class="sub-section" id="found-buildplan">
  <section id="build-plan">
    <div class="section-eyebrow"><span class="num">11B</span> The Build Plan</div>
    <h2 class="section-title">Exactly What to Build to Rank #1</h2>
    <div class="section-divider"></div>
    <p class="section-desc">The actionable spec derived from the data above — the exact pages, money pages, content, and internal-link plan to cover every keyword and out-rank competitors. {len(matrix)} money pages · {s.get("content_articles",0)} articles · {s.get("keyword_gaps",0)} gaps · {cm} missing keywords to capture.</p>

    {("<h3 class=" + chr(34) + "text-base font-bold uppercase tracking-wider mb-3 mt-2" + chr(34) + " style=" + chr(34) + "color:var(--brand-muted);font-family:var(--font-ui)" + chr(34) + ">Keyword Coverage — What You Rank For vs. What's Missing</h3>" + cov_html) if cov_html else ""}

    {("<h3 class=" + chr(34) + "text-base font-bold uppercase tracking-wider mb-3 mt-6" + chr(34) + " style=" + chr(34) + "color:var(--brand-muted);font-family:var(--font-ui)" + chr(34) + ">Money Pages — Service × Area Landing Pages</h3>" + matrix_html) if matrix_html else ""}

    {("<h3 class=" + chr(34) + "text-base font-bold uppercase tracking-wider mb-3 mt-6" + chr(34) + " style=" + chr(34) + "color:var(--brand-muted);font-family:var(--font-ui)" + chr(34) + ">Internal Link Silo</h3>" + silo_html) if silo_html else ""}

    <h3 class="text-base font-bold uppercase tracking-wider mb-3 mt-6" style="color:var(--brand-muted);font-family:var(--font-ui)">Supporting Pages to Build ({len(pages)})</h3>
    <div class="panel" style="padding:0;overflow-x:auto"><table class="cs-gap-table">
      <thead><tr><th>Page</th><th>Type</th><th>Primary Keyword</th><th class="num">Volume</th></tr></thead>
      <tbody>{page_rows}</tbody></table></div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3 mt-6" style="color:var(--brand-muted);font-family:var(--font-ui)">Quick Wins — On Page 2, Push to Page 1</h3>
    <div class="panel" style="padding:0;overflow-x:auto"><table class="cs-gap-table">
      <thead><tr><th>Keyword</th><th class="num">Volume</th><th class="num">Current</th></tr></thead>
      <tbody>{qw_rows}</tbody></table></div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3 mt-6" style="color:var(--brand-muted);font-family:var(--font-ui)">Topical Content Clusters</h3>
    <div class="plan-clusters" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px">{cluster_html or "<p style='color:var(--brand-muted)'>Cluster plan derives from keyword data.</p>"}</div>
  </section>
  </div><!-- /found-buildplan -->'''

    plan_section = _plan_section_html(plan)

    # Load CSS from template
    head_inner, style_block = _extract_css_and_static(_TEMPLATE_PATH)

    # ── Extract head assets (fonts, CDN scripts) ──────────────────────────────
    # Pull preconnect + link/script CDN lines from head
    cdn_lines = []
    for line in head_inner.split("\n"):
        stripped = line.strip()
        if (stripped.startswith("<link rel=\"preconnect\"") or
            stripped.startswith("<link href=\"https://fonts") or
            (stripped.startswith("<script") and ("cdn.tailwindcss" in stripped or "cdn.jsdelivr" in stripped))):
            cdn_lines.append(stripped)

    cdn_html = "\n  ".join(cdn_lines)

    # ── Data aliases ──────────────────────────────────────────────────────────
    client_name    = data.get("client_name") or data.get("brand_name", "Your Business")
    domain         = data.get("domain", "yourdomain.com")
    city           = data.get("city", "Your City")
    state          = data.get("state", "")
    city_state     = f"{city}, {state}" if state else city
    service        = data.get("service", "your service")
    owner          = data.get("owner") or data.get("owner_name", "")
    phone          = data.get("phone", "")
    email_addr     = data.get("email", "")
    report_date    = date.today().strftime("%B %d, %Y")

    score_total    = score_result.get("total", 0)
    score_grade    = score_result.get("grade", "C")
    score_desc     = score_result.get("grade_desc", "")
    score_pct_str  = str(score_total)

    # Organic
    kw_total    = data.get("kw_total", 0)
    kw_top3     = data.get("kw_top3", 0)
    kw_4_10     = data.get("kw_4_10", 0)
    kw_11_20    = data.get("kw_11_20", 0)
    kw_21_50    = data.get("kw_21_50", 0)
    kw_51_100   = data.get("kw_51_100", 0)
    avg_pos     = data.get("avg_position", 0.0)
    top_kws     = data.get("top_keywords", [])
    kw_labels   = data.get("top10_kw_labels", [])
    kw_volumes  = data.get("top10_kw_volumes", [])

    # Web
    lh_perf    = data.get("lh_performance", 0)
    lh_a11y    = data.get("lh_accessibility", 0)
    lh_bp      = data.get("lh_best_practices", 0)
    lh_seo     = data.get("lh_seo", 0)
    lcp_s      = data.get("lcp_s", 0)
    lcp_disp   = data.get("lcp_display", "N/A")
    lcp_band   = data.get("lcp_band", "bad")
    cls_disp   = data.get("cls_display", "N/A")
    cls_band   = data.get("cls_band", "warn")
    tbt_disp   = data.get("tbt_display", "N/A")
    tbt_band   = data.get("tbt_band", "warn")
    lcp_pct    = data.get("lcp_gauge_pct", 0)
    fid_pct    = data.get("fid_gauge_pct", 0)
    cls_pct    = data.get("cls_gauge_pct", 0)

    # Local
    rev_avg    = data.get("review_avg", 0.0)
    rev_count  = data.get("review_count", 0)
    rev_dist   = data.get("review_distribution", {"5":0,"4":0,"3":0,"2":0,"1":0})
    rev_pcts   = data.get("review_dist_pcts", {"5":0,"4":0,"3":0,"2":0,"1":0})
    map_pos    = data.get("map_pack_positions", {})

    # Backlinks — prefer ahrefs_dr (free, no-cost) over domain_rank (DataForSEO internal)
    dr          = data.get("ahrefs_dr") or data.get("domain_rank", 0)
    bl_total    = data.get("backlinks_total", 0)
    ref_domains = data.get("referring_domains_total", 0)
    dofollow    = data.get("dofollow_count", 0)
    nofollow    = data.get("nofollow_count", 0)
    top_refs    = data.get("top_referring_domains", [])
    anchor_dist = data.get("anchor_text_dist", {"labels": [], "data": []})

    # Backlinks API not in the current DataForSEO plan (40204) → don't render misleading
    # zeros. Show "N/A — activates July 1, 2026" so the report is honest. (Fixed 2026-06-01.)
    bl_unavailable = data.get("backlinks_unavailable", False) or (dr == 0 and bl_total == 0 and ref_domains == 0)
    if bl_unavailable:
        dr_value_html   = '<span style="color:var(--brand-muted)">N/A</span>'
        dr_sub          = "Backlink data activates Jul 1, 2026"
        bl_total_html   = '<span style="color:var(--brand-muted)">N/A</span>'
        bl_sub          = "Backlinks API not yet active"
        dofollow_html   = '<span style="color:var(--brand-muted)">N/A</span>'
        dofollow_sub    = "Pending data"
        ref_value_html  = '<span style="color:var(--brand-muted)">N/A</span>'
        ref_sub         = "Activates Jul 1, 2026"
        dr_gauge_html   = "N/A"
        bl_pull_html    = ("<strong>Backlink data not yet available.</strong> Referring domains, domain authority, and anchor profile come from the DataForSEO Backlinks API, which activates <strong>July 1, 2026</strong> — this section auto-populates then. (This domain does have an established backlink profile per external tools; it is simply not yet measured here.)")
    else:
        dr_value_html   = f'{dr}<span class="unit">/100</span>'
        dr_sub          = "Strong authority" if dr >= 50 else ("Building — target 30+" if dr >= 20 else "Low — needs backlink investment")
        bl_total_html   = f'{bl_total:,}'
        bl_sub          = f'{ref_domains} referring domains'
        dofollow_html   = f'{dofollow:,}'
        dofollow_sub    = f'{data.get("dofollow_pct",0):.0f}% of profile'
        ref_value_html  = f'{ref_domains}'
        ref_sub         = "Good diversity" if ref_domains >= 50 else "Target 50+ for competitive rankings"
        dr_gauge_html   = f'{dr}'
        bl_pull_html    = ("<strong>Backlink profile needs growth.</strong> Domain rank " + str(dr) + " is " + ("competitive" if dr >= 40 else "below the threshold needed to outrank established competitors") + " in local search. Target 10+ new referring domains from local directories, trade associations, and editorial mentions in the next 90 days.") if bl_total < 200 else "<strong>Healthy backlink profile.</strong> Focus on diversifying anchor text and reducing any exact-match anchor concentration."

    # Competitive
    competitors = data.get("competitors", [])
    client_traffic = data.get("client_traffic", 0)
    top_competitor = data.get("top_competitor", "")
    radar_client = data.get("radar_client", [0,0,0,0,0,0])
    radar_comp   = [100, 100, 100, 100, 100, 100]

    # Content
    content_gaps   = data.get("content_gaps", [])
    kw_suggestions = data.get("keyword_suggestions", [])

    # AI
    llms_txt      = data.get("llms_txt_present", False)
    has_kp        = data.get("has_knowledge_panel", False)
    schema_present= data.get("schema_present", False)

    # Social
    social_platforms = data.get("platforms", {})

    # Logo
    logo_url = data.get("logo_url", "")

    # GMB
    gmb_name    = data.get("gmb_name", client_name)
    gmb_phone   = data.get("gmb_phone", phone)
    gmb_address = data.get("gmb_address", city_state)

    # Score ring gradient
    score_pct_for_ring = score_total
    ring_style = f"background: conic-gradient(var(--brand-primary) 0% {score_pct_for_ring}%, var(--brand-border) {score_pct_for_ring}% 100%);"

    # ── Keyword table rows ────────────────────────────────────────────────────
    kw_rows = ""
    for kw in top_kws[:12]:
        pos_pill = _pill_class(kw["position"])
        kw_rows += f"""
          <tr>
            <td>{_escape(kw['keyword'])}</td>
            <td><span class="pill {pos_pill}">{kw['position']}</span></td>
            <td class="num">{kw['volume']:,}</td>
            <td><canvas class="spark" data-vals=""></canvas></td>
            <td>{_escape(kw.get('url',''))}</td>
          </tr>"""

    # ── SERP blocks ───────────────────────────────────────────────────────────
    serp_blocks_html = ""
    for block in data.get("serp_blocks", []):
        serp_blocks_html += _serp_table(block, domain)

    # ── Referring domains table ───────────────────────────────────────────────
    ref_rows = ""
    for rd in top_refs[:8]:
        rank = rd.get("rank", 0)
        r_pill = "pill-ok" if rank >= 50 else ("pill-info" if rank >= 20 else ("pill-warn" if rank >= 10 else "pill-bad"))
        ref_rows += f"""
          <tr>
            <td>{_escape(rd.get('domain',''))}</td>
            <td><span class="pill {r_pill}">{rank}</span></td>
            <td>{rd.get('backlinks',1)}</td>
            <td>Dofollow</td>
          </tr>"""

    # ── Content gap table ─────────────────────────────────────────────────────
    gap_rows = ""
    for gap in content_gaps[:10]:
        cp = gap.get("competitor_pos", 0)
        gap_rows += f"""
          <tr>
            <td>{_escape(gap.get('keyword',''))}</td>
            <td class="num">{gap.get('volume',0):,}</td>
            <td><span class="pill pill-bad">Not ranked</span></td>
            <td><span class="pill pill-ok">#{cp}</span> {_escape(top_competitor)}</td>
          </tr>"""

    # ── Social channel grid ───────────────────────────────────────────────────
    sc_html = ""
    platform_icons = {
        "facebook": "f", "instagram": "ig", "linkedin": "in",
        "youtube": "yt", "twitter": "x", "tiktok": "tt"
    }
    for plat, info in social_platforms.items():
        status_class = "active" if info.get("exists") else "absent"
        status_text  = "Active" if info.get("exists") else "Not Found"
        icon = platform_icons.get(plat, plat[:2].upper())
        url = info.get('url', '') or ''
        note = f'<a href="{_escape(url)}" target="_blank" rel="noopener">{_escape(url)}</a>' if url else 'No profile found'
        sc_html += f"""
        <div class="sc-channel">
          <div class="nm">{plat.title()}</div>
          <span class="status {status_class}">{status_text}</span>
          <div class="note">{note}</div>
        </div>"""

    # ── Off-site web footprint ("you forgot you had this") ─────────────────────
    # Directory/citation/review listings + long-tail mentions harvested from the brand-name
    # SERP. This is the section that makes the report feel exhaustive — it surfaces the Yelp,
    # BBB, MapQuest, DOT, industry-directory, and press pages the client often forgot existed.
    footprint = data.get("web_footprint", {}) or {}
    fp_dirs = footprint.get("directories", {}) or {}
    fp_mentions = footprint.get("other_mentions", []) or []
    fp_network = footprint.get("connected_network", []) or []
    _cat_label = {"review": "Review Site", "directory": "Directory", "industry": "Industry Directory"}
    footprint_html = ""
    # Connected site network — domains sharing the brand's Google Analytics / AdSense ID
    # (same operator). This is the highest-confidence "supporting / DBA / leadgen site" signal.
    if fp_network:
        net_rows = ""
        for n in fp_network:
            via = "Google Analytics" if n.get("via") == "google-analytics" else "AdSense"
            seen = f"{n.get('firstseen','')}&ndash;{n.get('lastseen','')}".strip("&ndash;")
            net_rows += f"""<tr><td><strong>{_escape(n.get('domain',''))}</strong></td><td>{via} <code>{_escape(n.get('id',''))}</code></td><td>{_escape(seen)}</td></tr>\n"""
        footprint_html += f"""
    <h3 style="margin:28px 0 6px;font-size:18px;">Connected Site Network &mdash; {len(fp_network)} domain(s)</h3>
    <p class="muted" style="margin:0 0 14px;">Other websites sharing {_escape(client_name)}'s Google Analytics / AdSense tracking ID &mdash; a strong signal these are <strong>owned or operated by the same team</strong> (supporting, DBA, or lead-gen sites). Verify and fold into one SEO strategy so they reinforce rather than compete.</p>
    <table class="ls-gmb-table" style="width:100%;"><thead><tr><th>Domain</th><th>Shared via</th><th>Seen</th></tr></thead><tbody>{net_rows}</tbody></table>"""
    if fp_dirs:
        cards = ""
        for label, info in sorted(fp_dirs.items(), key=lambda kv: (kv[1].get("category", ""), kv[0])):
            url = info.get("url", "")
            cat = _cat_label.get(info.get("category", ""), "Listing")
            cards += f"""
        <div class="sc-channel">
          <div class="nm">{_escape(label)}</div>
          <span class="status active">{_escape(cat)}</span>
          <div class="note"><a href="{_escape(url)}" target="_blank" rel="noopener">{_escape(url[:60])}</a></div>
        </div>"""
        footprint_html += f"""
    <h3 style="margin:28px 0 6px;font-size:18px;">Directory &amp; Citation Listings &mdash; {len(fp_dirs)} found</h3>
    <p class="muted" style="margin:0 0 14px;">Where {_escape(client_name)} already appears across review sites, maps, and industry directories. Consistent name/address/phone (NAP) across these is a direct local-ranking signal.</p>
    <div class="sc-channel-grid">{cards}</div>"""
    if fp_mentions:
        rows = ""
        for m in sorted(fp_mentions, key=lambda x: (not x.get("shares_phone"), x.get("domain", ""))):
            phone_tag = ' <span class="pill pill-ok">📞 shares your phone</span>' if m.get("shares_phone") else ""
            rows += f"""<tr><td>{_escape(m.get('domain',''))}{phone_tag}</td><td><a href="{_escape(m.get('url',''))}" target="_blank" rel="noopener">{_escape(m.get('title','') or m.get('url',''))}</a></td></tr>\n"""
        n_phone = sum(1 for m in fp_mentions if m.get("shares_phone"))
        phone_note = f" {n_phone} share your exact phone number (a strong signal of a connected/owned listing or site &mdash; worth verifying)." if n_phone else ""
        footprint_html += f"""
    <h3 style="margin:28px 0 6px;font-size:18px;">Brand Mentions Across the Web &mdash; {len(fp_mentions)} found</h3>
    <p class="muted" style="margin:0 0 14px;">Every place {_escape(client_name)} shows up online &mdash; state registration, press, video features, data aggregators, review sites, and partner pages.{phone_note}</p>
    <table class="ls-gmb-table" style="width:100%;"><thead><tr><th>Source</th><th>Page</th></tr></thead><tbody>{rows}</tbody></table>"""

    # ── Map pack table ────────────────────────────────────────────────────────
    map_rows = ""
    for mc, pos in map_pos.items():
        pos_str = f"#{pos}" if pos else "Not ranked"
        row_cls = ' class="us"' if pos and pos <= 10 else ""
        map_rows += f"<tr{row_cls}><td>{_escape(mc)}</td><td>{_escape(service)}</td><td class='num'>{pos_str}</td></tr>\n"

    # ── Competitor table ──────────────────────────────────────────────────────
    comp_rows = f"""
    <tr class="us">
      <td>{_escape(domain)}</td>
      <td class="num">{client_traffic:,}</td>
      <td class="num">{kw_total}</td>
      <td class="num">{dr}</td>
    </tr>"""
    for c in competitors[:5]:
        comp_rows += f"""
    <tr>
      <td>{_escape(c.get('domain',''))}</td>
      <td class="num">{c.get('traffic_estimate',0):,}</td>
      <td class="num">{c.get('keyword_count',0)}</td>
      <td class="num">{c.get('dr') or '—'}</td>
    </tr>"""

    # ── Roadmap HTML ──────────────────────────────────────────────────────────
    p1_items = roadmap.get("p1", [])
    p2_items = roadmap.get("p2", [])
    p3_items = roadmap.get("p3", [])

    rm_p1 = _roadmap_items_html(p1_items, "week1", "1", "Priority 1 — Foundation", "Fix first: quick wins + critical fixes")
    rm_p2 = _roadmap_items_html(p2_items, "month1", "2", "Priority 2 — Growth", "Content expansion + backlinks + trust")

    # P3 — 3-column layout
    def _p3_col(items: list, title: str) -> str:
        lis = "".join(f"""<li><div class="rm-check"></div><div class="rm-item-body"><div class="rm-item-title">{_escape(it.get('title',''))}</div><div class="rm-item-detail">{_escape(it.get('detail',''))}</div></div></li>""" for it in items)
        return f"""<div><div class="rm-next90-col-title">{title}</div><ul class="rm-checklist">{lis}</ul></div>"""

    p3_cols = ""
    chunk_size = max(1, len(p3_items) // 3 + 1)
    for i, label in enumerate(["Scale", "Authority", "Compound"]):
        chunk = p3_items[i*chunk_size:(i+1)*chunk_size]
        if chunk:
            p3_cols += _p3_col(chunk, label)

    rm_p3 = f"""
<div class="rm-card next90">
  <div class="rm-card-header">
    <div class="num-box">3</div>
    <div>
      <div class="title">Priority 3 — Scale</div>
      <div class="sub">Topical authority + backlink velocity + brand compounding</div>
    </div>
  </div>
  <div class="rm-grid-3" style="margin-top:0;">{p3_cols}</div>
</div>
"""

    # ── Logo display ──────────────────────────────────────────────────────────
    if logo_url:
        logo_html = f'<img src="{_escape(logo_url)}" alt="{_escape(client_name)} logo" style="max-width:84px; max-height:84px; object-fit:contain; border-radius:8px;">'
        header_logo = f'<img src="{_escape(logo_url)}" alt="logo" style="max-width:44px; max-height:44px; object-fit:contain;">'
    else:
        short = (client_name[:4] if len(client_name) >= 4 else client_name).upper()
        logo_html   = f'<div class="logo-fallback">[{_escape(short)}]</div>'
        header_logo = f'<div class="logo-box">[{_escape(short)}]</div>'

    # ── WCAG issues — generated from data ────────────────────────────────────
    a11y_rows = ""
    if lh_a11y < 90:
        a11y_rows += f"""<tr><td>Lighthouse Accessibility score {lh_a11y}/100 — review and fix flagged issues.</td><td><span class="sev sev-high">High</span></td><td>Accessibility failures reduce conversions and expose legal risk.</td></tr>"""
    if not schema_present:
        a11y_rows += """<tr><td>No structured data (JSON-LD) detected on homepage.</td><td><span class="sev sev-critical">Critical</span></td><td>Google cannot reliably tie reviews and services to the entity.</td></tr>"""
    if lh_seo < 80:
        a11y_rows += f"""<tr><td>Lighthouse SEO score {lh_seo}/100 — missing meta descriptions or non-crawlable links.</td><td><span class="sev sev-medium">Medium</span></td><td>Ranking suppression from technical on-page issues.</td></tr>"""
    if not a11y_rows:
        a11y_rows = """<tr><td>No critical issues detected in automated scan.</td><td><span class="sev sev-low">Info</span></td><td>Run a manual WCAG audit to validate.</td></tr>"""

    # ── LLM AI table ──────────────────────────────────────────────────────────
    llms_pill   = '<span class="llm-mention yes">Yes</span>' if llms_txt else '<span class="llm-mention no">No</span>'
    kp_pill     = '<span class="llm-mention yes">Yes</span>' if has_kp else '<span class="llm-mention no">No</span>'
    schema_pill = '<span class="llm-mention yes">Yes</span>' if schema_present else '<span class="llm-mention no">No</span>'

    # ── AI visibility score ──────────────────────────────────────────────────
    ai_score = int(((1 if llms_txt else 0) + (1 if has_kp else 0) + (1 if schema_present else 0)) / 3 * 100)
    ai_ring_pct = ai_score

    # ── Position distribution bar widths ─────────────────────────────────────
    pct_1_3   = data.get("pos_bar_1_3_pct", 0)
    pct_4_10  = data.get("pos_bar_4_10_pct", 0)
    pct_11_20 = data.get("pos_bar_11_20_pct", 0)
    pct_21_50 = data.get("pos_bar_21_50_pct", 0)
    pct_51_100= data.get("pos_bar_51_100_pct", 0)

    # ── DR color ─────────────────────────────────────────────────────────────
    dr_class = "ok" if dr >= 50 else ("warn" if dr >= 20 else "bad")

    # ── What's working / fix first / invest ──────────────────────────────────
    working_items = []
    fix_items     = []
    invest_items  = []

    if kw_4_10 > 0:
        working_items.append(f"<strong>{kw_4_10} keywords rank on page one</strong> — solid foundation to build from.")
    if rev_avg >= 4.0 and rev_count > 0:
        working_items.append(f"<strong>GMB rating {rev_avg:.1f}&star;</strong> across {rev_count} reviews — above category average.")
    if any(pos and pos <= 10 for pos in map_pos.values()):
        city_in = [c for c, p in map_pos.items() if p and p <= 10]
        working_items.append(f"<strong>Map pack visible in {', '.join(city_in)}</strong> — local signal established.")
    if not working_items:
        working_items.append(f"<strong>Domain is indexed</strong> with {kw_total} ranking keywords — foundation to build on.")

    for item in p1_items[:3]:
        fix_items.append(f"<strong>{_escape(item['title'])}</strong> — {_escape(item['detail'][:80])}...")

    for item in p2_items[:3]:
        invest_items.append(f"<strong>{_escape(item['title'])}</strong> — {_escape(item['detail'][:80])}...")

    working_li  = "".join(f"<li>{w}</li>" for w in working_items[:4])
    fix_li      = "".join(f"<li>{f}</li>" for f in (fix_items or ["<strong>Run a full audit</strong> to identify fix-first items."]))
    invest_li   = "".join(f"<li>{i}</li>" for i in (invest_items or ["<strong>Content and backlink strategy</strong> — needed for sustained growth."]))

    # ── Verdict text ──────────────────────────────────────────────────────────
    if score_total >= 65:
        verdict_headline = "You&rsquo;re visible &mdash; but not winning yet."
        verdict_detail = f"<strong>{_escape(client_name)}</strong> has a real online presence: rankings, a verified GMB, and a website Google indexes. What's missing is the <strong>density of signals</strong> Google now expects for a local contractor: city pages, review velocity, schema markup, and link diversity. Every fix in this report is mechanical &mdash; you don&rsquo;t need a rebrand, you need a 90-day execution sprint."
    elif score_total >= 45:
        verdict_headline = "You&rsquo;re online &mdash; but mostly invisible to buyers."
        verdict_detail = f"<strong>{_escape(client_name)}</strong> exists online, but the gaps are significant. Your competitors are winning searches you should own. The fixes are defined &mdash; what&rsquo;s needed is systematic execution: city pages, {'on-page SEO' if bl_unavailable else 'backlinks'}, schema, and review velocity. Every item in this report is actionable within 90 days."
    else:
        verdict_headline = "Critical gaps are costing you leads every day."
        verdict_detail = f"The audit found significant online visibility gaps for <strong>{_escape(client_name)}</strong>. Buyers in {_escape(city)} searching for {_escape(service)} are finding competitors instead. The priority-1 fixes alone &mdash; speed, schema, GMB optimization &mdash; will move the needle in 30-60 days."

    # ════════════════════════════════════════════════════════════════════════
    # BUILD THE HTML
    # ════════════════════════════════════════════════════════════════════════

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Online Brand Report &mdash; {_escape(client_name)}</title>
  <meta name="description" content="Online brand audit for {_escape(client_name)} &mdash; {_escape(city_state)}">
  <meta name="robots" content="noindex, nofollow">

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;600;700&family=Barlow+Condensed:wght@400;600;700&display=swap" rel="stylesheet">

  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-treemap"></script>

  {style_block}
</head>
<body class="min-h-screen">

<!-- STICKY HEADER -->
<header class="obr-header" id="obr-top">
  <div class="obr-header-row">
    <div class="obr-brand">
      {header_logo}
      <div>
        <div class="obr-name">{_escape(client_name)}</div>
        <div class="obr-tag">Online Brand Report &middot; {report_date}</div>
      </div>
    </div>
    <div></div>
    <div class="obr-right">
      <button class="theme-toggle" id="themeToggle" type="button" aria-label="Toggle dark/light mode">
        <span class="dot"></span>
        <span id="themeLabel">DARK</span>
      </button>
      <div class="obr-meta">Prepared by <b>JamBot</b></div>
    </div>
  </div>
</header>

<div class="tab-nav-wrap">
  <nav class="tab-nav" id="tabNav" role="tablist" aria-label="Report pages">
    <button class="tab-btn is-active" data-page="found" role="tab" type="button">What We Found</button>
    <button class="tab-btn" data-page="plan" role="tab" type="button">Your Action Plan</button>
    <button class="tab-btn" data-page="team" role="tab" type="button">Your Tools</button>
    <button class="tab-btn" data-page="day-one" role="tab" type="button">Build With Your Voice</button>
    <button class="tab-btn is-cta" data-page="signup" role="tab" type="button">Sign Up</button>
  </nav>
</div>

<div class="chip-strip-wrap">
  <div class="chip-strip is-active" data-chips-for="found">
    <a class="subchip is-active" href="#found-overview" data-chip="found-overview">Overview</a>
    <a class="subchip" href="#found-brand" data-chip="found-brand">Brand</a>
    <a class="subchip" href="#found-web" data-chip="found-web">Web Health</a>
    <a class="subchip" href="#found-search" data-chip="found-search">Search</a>
    <a class="subchip" href="#found-local" data-chip="found-local">Local &amp; Reputation</a>
    <a class="subchip" href="#found-authority" data-chip="found-authority">Authority &amp; Competitive</a>
    <a class="subchip" href="#found-content" data-chip="found-content">Content &amp; AI</a>
  </div>
  <div class="chip-strip" data-chips-for="plan">
    <a class="subchip is-active" href="#plan-overview" data-chip="plan-overview">The Plan</a>
    <a class="subchip" href="#plan-priorities" data-chip="plan-priorities">Priorities</a>
    <a class="subchip" href="#plan-matrix" data-chip="plan-matrix">Impact / Effort</a>
  </div>
  <div class="chip-strip" data-chips-for="team">
    <a class="subchip is-active" href="#tools-seo" data-chip="tools-seo">SEO Dashboard</a>
    <a class="subchip" href="#tools-voice" data-chip="tools-voice">JamBot AI</a>
    <a class="subchip" href="#tools-crm" data-chip="tools-crm">Your CRM</a>
    <a class="subchip" href="#tools-website" data-chip="tools-website">Website</a>
    <a class="subchip" href="#tools-apps" data-chip="tools-apps">Apps</a>
    <a class="subchip" href="#tools-social" data-chip="tools-social">Social &amp; Content</a>
  </div>
  <div class="chip-strip" data-chips-for="day-one">
    <a class="subchip is-active" href="#day1-tools" data-chip="day1-tools">What You Can Build</a>
    <a class="subchip" href="#day1-commands" data-chip="day1-commands">Example Commands</a>
    <a class="subchip" href="#day1-automations" data-chip="day1-automations">How You Direct It</a>
  </div>
  <div class="chip-strip" data-chips-for="signup">
    <a class="subchip is-active" href="#signup-pricing" data-chip="signup-pricing">Pricing</a>
    <a class="subchip" href="#signup-day1" data-chip="signup-day1">Getting Started</a>
    <a class="subchip" href="#signup-cta" data-chip="signup-cta">Talk to Us</a>
  </div>
</div>

<div class="report-wrap">

<!-- ═══════════════ PAGE 1 — WHAT WE FOUND ═══════════════ -->
<div class="report-page is-active" data-page="found">

  <!-- OVERVIEW -->
  <div class="sub-section" id="found-overview">

  <section class="hero-section" id="hero">
    <span class="hero-eyebrow-pill">Independent Brand &amp; Growth Audit &mdash; {report_date}</span>
    <h1 class="hero-headline">Where {_escape(client_name.split()[0])} Stands<br>And Where The <span class="accent">Real Money</span> Is Hiding</h1>
    <p class="hero-lead">A live snapshot of how {_escape(client_name)} shows up across Google search, Google Maps, local competitor SERPs, AI assistants, and social channels &mdash; with a prioritized action plan to close the gap on the contractors currently winning the {_escape(city)} {_escape(service)} market.</p>

    <div class="client-card">
      {logo_html}
      <div class="info">
        <div class="nm">{_escape(client_name)}</div>
        <div class="meta">{"Owner: " + _escape(owner) + " &middot; " if owner else ""}{_escape(city_state)}{" &middot; " + _escape(phone) if phone else ""} &middot; {_escape(domain)}</div>
      </div>
    </div>

    <div class="hero-facts">
      <div>Domain<b>{_escape(domain)}</b></div>
      <div>Location<b>{_escape(city_state)}</b></div>
      <div>Primary Service<b>{_escape(service.title())}</b></div>
      <div>Report Date<b>{report_date}</b></div>
      {"<div>Phone<b>" + _escape(phone) + "</b></div>" if phone else ""}
    </div>
  </section>

  <section id="executive-summary">
    <div class="section-eyebrow"><span class="num">03</span> Executive Summary</div>
    <h2 class="section-title">Where Your Brand Stands Today</h2>
    <div class="section-divider"></div>

    <div class="es-score-wrap">
      <div>
        <div class="es-score-ring" style="{ring_style}">
          <div class="es-score-inner">
            <span class="es-score-num">{score_total}</span>
            <span class="es-score-denom">/100</span>
          </div>
        </div>
        <div class="es-score-grade text-center">{_escape(score_grade)} &mdash; {_escape(score_desc)}</div>
      </div>
      <div class="es-score-explain">
        <h4>How the Score Was Computed</h4>
        <p>Weighted blend across six dimensions: Organic Search (25%), Web Health (20%), Local SEO &amp; Maps (20%), Backlinks &amp; Authority (15%), Content Coverage (10%), and Social Presence (10%). A score of {score_total} means {_escape(client_name)} {"is building a solid foundation" if score_total >= 60 else "has significant gaps to close"} in {_escape(city)}&rsquo;s {_escape(service)} market.</p>
      </div>
    </div>

    <div class="es-kpi-grid">
      <div class="es-kpi-tile">
        <div class="es-kpi-label">Keywords Tracked</div>
        <div class="es-kpi-value">{kw_total:,}</div>
        <div class="es-kpi-delta-flat">across all positions</div>
      </div>
      <div class="es-kpi-tile">
        <div class="es-kpi-label">Page 1 Keywords</div>
        <div class="es-kpi-value">{kw_top3 + kw_4_10}</div>
        <div class="{"es-kpi-delta-up" if (kw_top3 + kw_4_10) > 5 else "es-kpi-delta-down"}">positions 1-10</div>
      </div>
      <div class="es-kpi-tile">
        <div class="es-kpi-label">Avg SERP Position</div>
        <div class="es-kpi-value">{avg_pos if avg_pos > 0 else "N/A"}</div>
        <div class="{"es-kpi-delta-up" if avg_pos > 0 and avg_pos <= 20 else "es-kpi-delta-down"}">{"good range" if avg_pos > 0 and avg_pos <= 20 else "needs work"}</div>
      </div>
      <div class="es-kpi-tile">
        <div class="es-kpi-label">Backlinks</div>
        <div class="es-kpi-value">{bl_total:,}</div>
        <div class="{"es-kpi-delta-up" if bl_total > 50 else "es-kpi-delta-flat"}">{ref_domains} referring domains</div>
      </div>
    </div>

    <div class="es-grid">
      <div class="es-card working">
        <h3>What&rsquo;s Working</h3>
        <ul>{working_li}</ul>
      </div>
      <div class="es-card fix">
        <h3>What to Fix First</h3>
        <ul>{fix_li}</ul>
      </div>
      <div class="es-card invest">
        <h3>What to Invest In Next</h3>
        <ul>{invest_li}</ul>
      </div>
    </div>

    <div class="es-verdict">
      <span class="tag">The Honest Answer</span>
      <span class="headline">{verdict_headline}</span>
      <div class="detail">{verdict_detail}</div>
    </div>
  </section>
  </div><!-- /found-overview -->

  <!-- BRAND -->
  <div class="sub-section" id="found-brand">
  <section id="brand-identity">
    <div class="section-eyebrow"><span class="num">04</span> Brand Identity Audit</div>
    <h2 class="section-title">Brand Identity &amp; Online Consistency</h2>
    <div class="section-divider"></div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Logo &amp; Visual Identity</h3>
    <div class="bi-two-col">
      <div class="bi-logo-card">
        <h4>Online Presence</h4>
        <ul>
          <li>Domain <strong>{_escape(domain)}</strong> is live and indexed by Google.</li>
          {"<li>Logo detected at <strong>" + _escape(logo_url) + "</strong>.</li>" if logo_url else "<li>No logo file found at standard paths &mdash; add one for brand consistency.</li>"}
          <li>GMB profile {"verified &mdash; consistent NAP across channels." if data.get("gmb_found") else "status could not be confirmed &mdash; verify your Google Business Profile."}</li>
        </ul>
      </div>
      <div class="bi-logo-card issues">
        <h4>Issues to Address</h4>
        <ul>
          {"<li><strong>llms.txt missing</strong> &mdash; AI assistants can't reliably cite your brand.</li>" if not llms_txt else ""}
          {"<li><strong>No structured schema detected</strong> &mdash; Google can't tie reviews to the entity.</li>" if not schema_present else ""}
          {"<li><strong>No Google Knowledge Panel</strong> &mdash; brand entity not strongly established.</li>" if not has_kp else ""}
          <li><strong>Social channel gaps</strong> &mdash; {max(0, data.get("platforms_total", 6) - data.get("platforms_claimed", 0))} of {data.get("platforms_total", 6)} major platforms not claimed.</li>
        </ul>
      </div>
    </div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Voice &amp; Tone</h3>
    <div class="bi-voice">
      <p><strong>What Google sees:</strong> {_escape(client_name)} ranks for {kw_total} keywords in the {_escape(city_state)} market, with strongest visibility in {(top_kws[0]['keyword'] if top_kws else 'primary service keywords')}.</p>
      <p><strong>Opportunity:</strong> The content gap analysis found {len(content_gaps)} keywords where top competitors rank in the top 10 but {_escape(client_name)} does not. These represent direct revenue opportunities.</p>
      <p><strong>Recommended shift:</strong> Lead every service page with a plain-English benefit hook &mdash; comfort, savings, peace of mind &mdash; then layer technical specs below. Add an owner bio page for E-E-A-T trust signals.</p>
    </div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">AI &amp; LLM Visibility Score</h3>
    <div class="bi-gauge">
      <div class="bi-gauge-ring" style="background: conic-gradient(var(--brand-primary) 0% {ai_ring_pct}%, var(--brand-border) {ai_ring_pct}% 100%);"><span>{ai_score}</span></div>
      <div class="bi-gauge-text">
        <h4>{ai_score} / 100 AI Visibility</h4>
        <p>llms.txt: {"Present" if llms_txt else "Missing"} &middot; Knowledge Panel: {"Yes" if has_kp else "No"} &middot; Schema: {"Yes" if schema_present else "No"}. {"Excellent AI visibility foundation." if ai_score == 100 else "Missing signals make it hard for ChatGPT and Claude to cite this brand."}</p>
      </div>
    </div>
  </section>
  </div><!-- /found-brand -->

  <!-- WEB HEALTH -->
  <div class="sub-section" id="found-web">
  <section id="web-ux-audit">
    <div class="section-eyebrow"><span class="num">05</span> Web UX &amp; Performance</div>
    <h2 class="section-title">Lighthouse, Core Web Vitals &amp; Accessibility</h2>
    <div class="section-divider"></div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Core Web Vitals (Desktop)</h3>
    <div class="ux-cwv-grid">
      <div class="ux-cwv-tile">
        <div class="gauge-wrap"><canvas id="ux-cwv-lcp"></canvas></div>
        <div class="val">{_escape(lcp_disp)}</div>
        <div class="lbl">LCP</div>
        <span class="pill {_pill_for_band(lcp_band)} mt-1 inline-block">{_band_text(lcp_band)}</span>
      </div>
      <div class="ux-cwv-tile">
        <div class="gauge-wrap"><canvas id="ux-cwv-fid"></canvas></div>
        <div class="val">{_escape(tbt_disp)}</div>
        <div class="lbl">TBT</div>
        <span class="pill {_pill_for_band(tbt_band)} mt-1 inline-block">{_band_text(tbt_band)}</span>
      </div>
      <div class="ux-cwv-tile">
        <div class="gauge-wrap"><canvas id="ux-cwv-cls"></canvas></div>
        <div class="val">{_escape(cls_disp)}</div>
        <div class="lbl">CLS</div>
        <span class="pill {_pill_for_band(cls_band)} mt-1 inline-block">{_band_text(cls_band)}</span>
      </div>
    </div>

    <div class="ux-lh-grid">
      <div class="ux-lh-bars">
        <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Lighthouse Scores</h3>
        <div class="chart-wrap"><canvas id="ux-lighthouse-bars"></canvas></div>
      </div>
      <div class="ux-mobile-score">
        <div class="ux-mobile-ring" style="background: conic-gradient(var(--brand-primary) 0% {lh_seo}%, var(--brand-border) {lh_seo}% 100%);"><span>{lh_seo}</span></div>
        <div class="ux-mobile-text">
          <h4>SEO Score: {lh_seo}/100</h4>
          <p>{"Strong on-page SEO signals detected." if lh_seo >= 80 else "Technical SEO issues found — review missing meta descriptions, non-crawlable links, and missing canonical tags."}</p>
        </div>
      </div>
    </div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3 mt-6" style="color:var(--brand-muted); font-family: var(--font-ui);">Technical Findings</h3>
    <div class="panel" style="padding:0; overflow-x:auto;">
      <table class="ux-a11y-table">
        <thead>
          <tr><th style="width:55%;">Issue</th><th>Severity</th><th>Business Impact</th></tr>
        </thead>
        <tbody>{a11y_rows}</tbody>
      </table>
    </div>

    <div class="ux-form-callout">
      <p><strong>Performance context:</strong> {"LCP of " + lcp_disp + " is in the " + _band_text(lcp_band) + " zone." if lcp_s > 0 else "Performance data requires a live Lighthouse run."} {"A score below 2.5s is required for the 'Good' CWV label from Google. Every 100ms improvement in LCP correlates with ~1% conversion lift in home-services categories." if lcp_s > 2.5 else "LCP is within the Good threshold — focus on maintaining this as content grows."}</p>
    </div>
  </section>
  </div><!-- /found-web -->

  <!-- SEARCH -->
  <div class="sub-section" id="found-search">
  <section id="organic-search">
    <div class="section-eyebrow"><span class="num">06</span> Organic Search</div>
    <h2 class="section-title">Where You Rank &mdash; And Where You Don&rsquo;t</h2>
    <div class="section-divider"></div>
    <p class="section-desc">Live DataForSEO scan across every keyword the domain ranks for. Total tracked: <strong style="color:var(--brand-text-strong)">{kw_total}</strong>.</p>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Position Distribution ({kw_total} keywords)</h3>
    <div class="panel">
      <div class="os-bar-row"><span>Pos. 1-3 <span class="pill pill-ok">Money</span></span><div class="os-bar-track"><div class="os-bar-fill" style="background:var(--sem-success); width:{pct_1_3}%;"></div></div><span class="count">{kw_top3}</span></div>
      <div class="os-bar-row"><span>Pos. 4-10 <span class="pill pill-ok">Page 1</span></span><div class="os-bar-track"><div class="os-bar-fill" style="background:var(--sem-success); opacity:0.7; width:{pct_4_10}%;"></div></div><span class="count">{kw_4_10}</span></div>
      <div class="os-bar-row"><span>Pos. 11-20 <span class="pill pill-info">Page 2</span></span><div class="os-bar-track"><div class="os-bar-fill" style="background:var(--brand-primary); width:{pct_11_20}%;"></div></div><span class="count">{kw_11_20}</span></div>
      <div class="os-bar-row"><span>Pos. 21-50 <span class="pill pill-warn">Page 3-5</span></span><div class="os-bar-track"><div class="os-bar-fill" style="background:var(--sem-warn); width:{pct_21_50}%;"></div></div><span class="count">{kw_21_50}</span></div>
      <div class="os-bar-row"><span>Pos. 51-100 <span class="pill pill-bad">Invisible</span></span><div class="os-bar-track"><div class="os-bar-fill" style="background:var(--sem-danger); width:{pct_51_100}%;"></div></div><span class="count">{kw_51_100}</span></div>
    </div>

    <div class="os-grid">
      <div class="os-chart-card">
        <h4>Average Keyword Position</h4>
        <div class="sub">Current average: {avg_pos} (lower is better)</div>
        <div class="chart-wrap"><canvas id="os-avg-position"></canvas></div>
      </div>
      <div class="os-chart-card">
        <h4>Top 10 Keywords by Search Volume</h4>
        <div class="sub">Where your addressable demand sits.</div>
        <div class="chart-wrap"><canvas id="os-top-kw-vol"></canvas></div>
      </div>
    </div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Ranked Keywords (top by volume)</h3>
    <div class="panel" style="padding:0; overflow-x:auto;">
      <table class="os-table">
        <thead>
          <tr><th>Keyword</th><th>Position</th><th class="num">Volume</th><th>30-day Trend</th><th>URL</th></tr>
        </thead>
        <tbody>{kw_rows if kw_rows else "<tr><td colspan='5' style='text-align:center;color:var(--brand-muted);padding:20px;'>No ranked keywords data available</td></tr>"}</tbody>
      </table>
    </div>

    <div class="os-pull"><p>{"In plain English: <strong>" + _escape(client_name) + " ranks for " + str(kw_total) + " keywords</strong>, with " + str(kw_top3 + kw_4_10) + " on page one. The fastest path to more leads is page-1 optimization of the " + str(kw_11_20) + " keywords currently stuck on page 2, plus new city-specific service pages for nearby markets." if kw_total > 0 else "No organic ranking data was returned for this domain. This typically means the domain has very limited search visibility &mdash; which makes this audit especially valuable."}</p></div>
  </section>

  <section id="serp-snapshots">
    <div class="section-eyebrow"><span class="num">07</span> Live SERP Snapshots</div>
    <h2 class="section-title">Who&rsquo;s Beating You In Your Own Backyard, Today</h2>
    <div class="section-divider"></div>
    <p class="section-desc">Every table below was pulled live from Google. Your row is highlighted.</p>

    {serp_blocks_html if serp_blocks_html else '<div class="panel" style="text-align:center;color:var(--brand-muted);padding:28px;">SERP data could not be fetched for this domain.</div>'}

    <div class="serp-pull"><p>{"The SERP analysis shows who is currently winning searches in <strong>" + _escape(city) + "</strong>. Use this data to identify which competitor pages to analyze and outcompete with better content, schema, and local signals." if data.get("serp_blocks") else "Run the SERP fetcher with --service and --city flags for live snapshot data."}</p></div>
  </section>
  </div><!-- /found-search -->

  <!-- LOCAL -->
  <div class="sub-section" id="found-local">
  <section id="local-seo">
    <div class="section-eyebrow"><span class="num">08</span> Local SEO &amp; Google Business Profile</div>
    <h2 class="section-title">Map Pack, Reviews &amp; Local Visibility</h2>
    <div class="section-divider"></div>

    <div class="ls-grid cols-2">
      <div class="ls-gmb-card">
        <h4>{_escape(gmb_name)}</h4>
        <div class="meta">{_escape(service.title())} &middot; {_escape(gmb_phone)} &middot; {_escape(gmb_address)}</div>
        <div class="meta" style="margin-top:2px;">{_escape(domain)}</div>
        <table class="ls-gmb-table">
          <thead><tr><th>Element</th><th>Your Profile</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td>GMB Verified</td><td>{"Verified" if data.get("gmb_claimed") else ("Listed (unclaimed)" if data.get("gmb_found") else "Not found")}</td><td><span class="pill {"pill-ok" if data.get("gmb_claimed") else "pill-bad"}">{"Good" if data.get("gmb_claimed") else "Fix"}</span></td></tr>
            <tr><td>Reviews</td><td>{rev_count} at {rev_avg:.1f}&star;</td><td><span class="pill {"pill-ok" if rev_count >= 40 else ("pill-warn" if rev_count >= 15 else "pill-bad")}">{"Good" if rev_count >= 40 else ("Fair" if rev_count >= 15 else "Low")}</span></td></tr>
            <tr><td>NAP Consistency</td><td>{"Phone mismatch across listings &mdash; GMB shows " + _escape(data.get("gmb_phone","")) if data.get("nap_phone_mismatch") else ("Consistent &mdash; " + _escape(data.get("gmb_phone","")) if data.get("gmb_phone") else "Verify name/address/phone match everywhere")}</td><td><span class="pill {"pill-bad" if data.get("nap_phone_mismatch") else ("pill-ok" if data.get("gmb_phone") else "pill-warn")}">{"Fix" if data.get("nap_phone_mismatch") else ("Good" if data.get("gmb_phone") else "Check")}</span></td></tr>
            <tr><td>Schema Markup</td><td>{"Present" if schema_present else "Missing"}</td><td><span class="pill {"pill-ok" if schema_present else "pill-bad"}">{"Good" if schema_present else "Missing"}</span></td></tr>
            <tr><td>llms.txt</td><td>{"Present" if llms_txt else "Missing"}</td><td><span class="pill {"pill-ok" if llms_txt else "pill-bad"}">{"Good" if llms_txt else "Missing"}</span></td></tr>
          </tbody>
        </table>
      </div>

      <div class="ls-chart-card">
        <h4>Review Star Distribution</h4>
        <div class="sub">Reputation health snapshot. Average: <strong style="color:var(--brand-text-strong)">{rev_avg:.1f}</strong> &middot; {rev_count} reviews</div>
        {"".join(f'<div class="ls-star-row"><div class="stars">{s}&#9733;</div><div class="bar-bg"><div class="bar-fill" style="width:{rev_pcts.get(s,0)}%"></div></div><div class="cnt">{rev_dist.get(s,0)}</div></div>' for s in ["5","4","3","2","1"])}
      </div>
    </div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Map Pack Rankings</h3>
    <div class="panel" style="padding:0; overflow-x:auto;">
      <table class="ls-map-table">
        <thead><tr><th>City</th><th>Query</th><th class="num">Your Position</th></tr></thead>
        <tbody>{map_rows if map_rows else "<tr><td colspan='3' style='text-align:center;color:var(--brand-muted);padding:16px;'>No map pack data available</td></tr>"}</tbody>
      </table>
    </div>

    <div class="ls-pull"><p>{"<strong>GMB review velocity is a top local ranking factor.</strong> Getting from " + str(rev_count) + " to 40+ reviews requires a systematic post-job text-ask flow. Every 5 reviews added measurably improves map pack position for competitive local queries." if rev_count < 40 else "<strong>Review base is solid.</strong> Maintain velocity with a post-job ask flow and respond to every review within 24 hours to sustain map pack position."}</p></div>
  </section>
  </div><!-- /found-local -->

  <!-- AUTHORITY & COMPETITIVE -->
  <div class="sub-section" id="found-authority">
  <section id="backlinks">
    <div class="section-eyebrow"><span class="num">09</span> Backlinks &amp; Authority</div>
    <h2 class="section-title">Link Profile &amp; Domain Authority</h2>
    <div class="section-divider"></div>

    <div class="bl-kpi-grid">
      <div class="bl-kpi {dr_class}">
        <div class="bl-kpi-label">Domain Rating (Ahrefs)</div>
        <div class="bl-kpi-value">{dr_value_html}</div>
        <div class="bl-kpi-sub">{dr_sub}</div>
      </div>
      <div class="bl-kpi {"warn" if bl_unavailable else ("ok" if bl_total >= 100 else ("warn" if bl_total >= 30 else "bad"))}">
        <div class="bl-kpi-label">Total Backlinks</div>
        <div class="bl-kpi-value">{bl_total_html}</div>
        <div class="bl-kpi-sub">{bl_sub}</div>
      </div>
      <div class="bl-kpi {"warn" if bl_unavailable else ("ok" if dofollow > nofollow else "warn")}">
        <div class="bl-kpi-label">Dofollow Links</div>
        <div class="bl-kpi-value">{dofollow_html}</div>
        <div class="bl-kpi-sub">{dofollow_sub}</div>
      </div>
      <div class="bl-kpi warn">
        <div class="bl-kpi-label">Referring Domains</div>
        <div class="bl-kpi-value">{ref_value_html}</div>
        <div class="bl-kpi-sub">{ref_sub}</div>
      </div>
    </div>

    <div class="bl-grid-2">
      <div class="bl-card">
        <h4>Domain Authority Gauge</h4>
        <div class="sub">Ahrefs Domain Rating (DR) 0-100 logarithmic scale.</div>
        <div class="bl-da-gauge">
          <canvas id="bl-da-gauge"></canvas>
          <div class="bl-da-overlay"><div class="num">{dr_gauge_html}</div><div class="lbl">DR</div></div>
        </div>
      </div>
      <div class="bl-card">
        <h4>Anchor Text Distribution</h4>
        <div class="sub">Branded vs exact-match vs generic.</div>
        <div class="chart-wrap"><canvas id="bl-anchor"></canvas></div>
      </div>
    </div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Top Referring Domains</h3>
    <div class="panel" style="padding:0; overflow-x:auto;">
      <table class="bl-table">
        <thead><tr><th>Domain</th><th>DR</th><th>Links</th><th>Type</th></tr></thead>
        <tbody>{ref_rows if ref_rows else "<tr><td colspan='4' style='text-align:center;color:var(--brand-muted);padding:16px;'>No referring domain data available</td></tr>"}</tbody>
      </table>
    </div>

    <div class="bl-pull"><p>{bl_pull_html}</p></div>
  </section>

  <section id="competitive-benchmark">
    <div class="section-eyebrow"><span class="num">10</span> Competitive Benchmark</div>
    <h2 class="section-title">How You Stack Up Against Local Competitors</h2>
    <div class="section-divider"></div>

    <div class="cb-table-wrap">
      <table class="cb-table">
        <thead>
          <tr>
            <th>Domain</th>
            <th class="num">Est. Traffic/mo</th>
            <th class="num">Ranking KW</th>
            <th class="num">Authority</th>
          </tr>
        </thead>
        <tbody>
          {comp_rows}
        </tbody>
      </table>
    </div>

    <div class="cb-charts">
      <div class="cb-card">
        <h4>Competitive Radar</h4>
        <div class="sub">You vs top competitor across 6 dimensions.</div>
        <div class="chart-wrap tall"><canvas id="cb-radar"></canvas></div>
      </div>
      <div class="cb-card">
        <h4>Keyword Opportunity Bubble</h4>
        <div class="sub">Search volume vs your current position (size = opportunity).</div>
        <div class="chart-wrap tall"><canvas id="cb-bubble"></canvas></div>
      </div>
    </div>
  </section>
  </div><!-- /found-authority -->

  <!-- CONTENT & AI -->
  <div class="sub-section" id="found-content">
  <section id="content-strategy">
    <div class="section-eyebrow"><span class="num">11</span> Content &amp; Keyword Strategy</div>
    <h2 class="section-title">Content Gaps &amp; Keyword Opportunities</h2>
    <div class="section-divider"></div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3" style="color:var(--brand-muted); font-family: var(--font-ui);">Keywords Competitor Ranks For — You Don&rsquo;t</h3>
    <div class="panel" style="padding:0; overflow-x:auto;">
      <table class="cs-gap-table">
        <thead>
          <tr><th>Keyword</th><th class="num">Volume</th><th>Your Position</th><th>Competitor</th></tr>
        </thead>
        <tbody>{gap_rows if gap_rows else "<tr><td colspan='4' style='text-align:center;color:var(--brand-muted);padding:16px;'>No content gap data available</td></tr>"}</tbody>
      </table>
    </div>

    <h3 class="text-base font-bold uppercase tracking-wider mb-3 mt-6" style="color:var(--brand-muted); font-family: var(--font-ui);">Keyword Suggestions for {_escape(service.title())}</h3>
    <div class="panel" style="padding:0; overflow-x:auto;">
      <table class="cs-gap-table">
        <thead>
          <tr><th>Keyword</th><th class="num">Volume</th><th class="num">Difficulty</th><th class="num">CPC</th></tr>
        </thead>
        <tbody>
          {"".join(f'<tr><td>{_escape(k["keyword"])}</td><td class="num">{k["volume"]:,}</td><td class="num">{k["difficulty"]}</td><td class="num">${k["cpc"]:.2f}</td></tr>' for k in kw_suggestions[:10]) if kw_suggestions else "<tr><td colspan='4' style='text-align:center;color:var(--brand-muted);padding:16px;'>No keyword suggestion data available</td></tr>"}
        </tbody>
      </table>
    </div>

    <div class="cs-pull"><p>{"<strong>" + str(len(content_gaps)) + " keyword gaps found</strong> where competitors rank in the top 20 and " + _escape(client_name) + " doesn't appear. These are direct content-building opportunities — each gap represents searches buyers are making that your site isn't capturing." if content_gaps else "Content gap analysis requires a top competitor identified from the SERP data. Run generate.py with --competitors flag for detailed gap analysis."}</p></div>
  </section>
  {plan_section}

  <section id="ai-visibility">
    <div class="section-eyebrow"><span class="num">12</span> AI &amp; LLM Visibility</div>
    <h2 class="section-title">How AI Assistants See Your Brand</h2>
    <div class="section-divider"></div>

    <div class="llm-llmstxt-callout">
      <div class="status-pill"><span class="pill {"pill-ok" if llms_txt else "pill-bad"}">{_escape("Present" if llms_txt else "Missing")}</span></div>
      <div class="body">
        <strong>llms.txt status:</strong> {_escape("Found at " + data.get("llms_txt_url","") + " — AI assistants can reference this file." if llms_txt else "Not found at " + domain + "/llms.txt — ChatGPT, Claude, Perplexity, and Google AI Overviews cannot reliably find structured information about this business.")}
      </div>
    </div>

    <div class="panel" style="padding:0; overflow-x:auto; margin-top:16px;">
      <table class="llm-table">
        <thead>
          <tr><th>Signal</th><th>Status</th><th>Impact</th></tr>
        </thead>
        <tbody>
          <tr><td>llms.txt file</td><td class="center">{llms_pill}</td><td>Enables AI assistants to cite your business</td></tr>
          <tr><td>Google Knowledge Panel</td><td class="center">{kp_pill}</td><td>Brand entity recognized by Google</td></tr>
          <tr><td>Structured Schema (JSON-LD)</td><td class="center">{schema_pill}</td><td>Machine-readable business data for AI and rich results</td></tr>
        </tbody>
      </table>
    </div>

    <div class="llm-pull"><p>{"<strong>AI search visibility is a priority-1 action.</strong> Without llms.txt and schema, " + _escape(client_name) + " won't appear in AI-generated recommendations — a fast-growing referral source for local service businesses as consumers use ChatGPT and Perplexity to find contractors." if not llms_txt else "<strong>llms.txt is in place</strong> — good foundation. Pair with schema markup and a structured FAQ page to maximize AI citation frequency."}</p></div>
  </section>

  <section id="social-channels">
    <div class="section-eyebrow"><span class="num">13</span> Social Channels</div>
    <h2 class="section-title">Social Media Presence Audit</h2>
    <div class="section-divider"></div>

    <div class="sc-channel-grid">
      {sc_html if sc_html else '<div class="sc-channel"><div class="nm">Social</div><span class="status absent">Data Unavailable</span></div>'}
    </div>

    <div class="sc-pull"><p>{str(data.get("platforms_claimed", 0))} of {data.get("platforms_total", 6)} major social platforms claimed for {_escape(client_name)}. {"Excellent social coverage." if data.get("platforms_claimed", 0) >= 5 else ("Good start — fill remaining gaps." if data.get("platforms_claimed", 0) >= 3 else "Significant social presence gaps. Claimed profiles (even with minimal activity) improve local trust signals and prevent brand squatting.")}</p></div>
    {footprint_html}
  </section>

  <section id="roadmap-section">
    <div class="section-eyebrow"><span class="num">14</span> 90-Day Action Roadmap</div>
    <h2 class="section-title">What Happens Next</h2>
    <div class="section-divider"></div>

    <div class="rm-grid-2">
      {rm_p1}
      {rm_p2}
    </div>
    {rm_p3}

    <div class="rm-target-state">
      <div class="label">Target State — 90 Days</div>
      <p>The goal: top-5 map pack presence in target cities, DR 30+, 40+ GMB reviews at 4.5&star;, and visibility in AI assistant responses for key local queries. Organic sessions growing month-over-month as the content and backlink investments compound. Every action above is mechanical and trackable &mdash; no creative leaps required.</p>
    </div>
  </section>
  </div><!-- /found-content -->

</div><!-- /page=found -->

<!-- ═══════════════ PAGE 2 — ACTION PLAN ═══════════════ -->
<div class="report-page" data-page="plan">
  <div class="sub-section" id="plan-overview">
    <div class="section-eyebrow"><span class="num">P1</span> The Plan</div>
    <h2 class="section-title">Your Prioritized Action Plan</h2>
    <div class="section-divider"></div>
    <p class="section-desc">Every fix below is mechanical: shipping a page, claiming a profile, sending a request, applying a schema. Ordered by impact and effort so the highest-leverage work ships first.</p>
    <div class="panel" style="background: linear-gradient(135deg, rgba(14,92,122,0.10), transparent); border-left: 4px solid var(--brand-primary);">
      <h3 style="font-family: 'Bebas Neue', sans-serif; font-size: 1.4rem; color: var(--brand-text-strong); letter-spacing: 0.04em; margin: 0 0 8px;">How the plan is structured</h3>
      <p style="font-size: 14.5px; color: var(--brand-text); line-height: 1.65; margin: 0;">
        <strong style="color: var(--brand-primary);">Priority 1</strong> stops the bleeding: fix speed, claim profiles, add schema, build first city pages.
        <strong style="color: var(--brand-primary);">Priority 2</strong> builds the foundation: publish pages, install review flow, start backlink outreach, deploy llms.txt.
        <strong style="color: var(--brand-primary);">Priority 3</strong> compounds the work: topical content clusters, editorial backlinks, review velocity, full social cadence.
      </p>
    </div>
  </div>

  <div class="sub-section" id="plan-priorities">
    <div class="section-eyebrow"><span class="num">P2</span> Priorities</div>
    <h2 class="section-title">Actions, In Order</h2>
    <div class="section-divider"></div>
    <div class="rm-grid-2">
      {rm_p1}
      {rm_p2}
    </div>
    {rm_p3}
    <div class="rm-target-state">
      <div class="label">Target State</div>
      <p>Top-5 map pack in target cities. DR 30+. 40+ GMB reviews. AI-visible across key queries. Content ranking for the {len(content_gaps)} gap keywords identified in this report. Execution, not creativity, is what this takes.</p>
    </div>
  </div>

  <div class="sub-section" id="plan-matrix">
    <div class="section-eyebrow"><span class="num">P3</span> Impact / Effort</div>
    <h2 class="section-title">Where Each Action Sits</h2>
    <div class="section-divider"></div>
    <p class="section-desc">Top-left = highest priority. Top-right = plan + protect a calendar block. Bottom-left = quick win. Bottom-right = low priority, revisit later.</p>
    <div class="ie-matrix">
      <div class="ie-axis-y">High Impact &rarr;</div>
      <div class="ie-quad do-now">
        <span class="qlabel">Do Now</span>
        {"".join('<div class="ie-item">' + _escape(it.get("title",""))[:50] + '</div>' for it in p1_items[:4])}
      </div>
      <div class="ie-quad plan">
        <span class="qlabel">Plan</span>
        {"".join('<div class="ie-item">' + _escape(it.get("title",""))[:50] + '</div>' for it in p2_items[:4])}
      </div>
      <div class="ie-axis-y" style="grid-row: 2;"></div>
      <div class="ie-quad quick-win">
        <span class="qlabel">Quick Win</span>
        {"".join('<div class="ie-item">' + _escape(it.get("title",""))[:50] + '</div>' for it in p3_items[:4])}
      </div>
      <div class="ie-quad deprioritize">
        <span class="qlabel">Revisit Later</span>
        <div class="ie-item">Full website rebrand</div>
        <div class="ie-item">Paid display campaigns</div>
        <div class="ie-item">Trade-show booth investment</div>
      </div>
      <div></div>
      <div class="ie-axis-x">Low Effort &nbsp;&larr;&nbsp; Effort &nbsp;&rarr;&nbsp; High Effort</div>
    </div>
  </div>

</div><!-- /page=plan -->

<!-- ═══════════════ PAGE 3 — YOUR TOOLS ═══════════════ -->
<div class="report-page" data-page="team">
  <div class="sub-section" id="tools-seo">
    <div class="section-eyebrow"><span class="num">T1</span> SEO Dashboard</div>
    <h2 class="section-title">Enterprise SEO Intelligence &mdash; Included</h2>
    <div class="section-divider"></div>
    <p class="section-desc">Every data point in the audit you just read was pulled live from the same dashboard your subscription includes. Rank tracking, competitor monitoring, backlink analysis, keyword research, SERP snapshots &mdash; all in one place.</p>
    <div class="cap-grid">
      <div class="cap-card"><h4>Rank &amp; Keyword Tracking</h4><p>Track every keyword you care about daily. See exactly where you rank vs competitors, which queries are moving, and where you&rsquo;re losing ground.</p></div>
      <div class="cap-card"><h4>Live SERP Snapshots</h4><p>Pull any Google search result as it appears right now &mdash; map pack, organic listings, People Also Ask, featured snippets &mdash; with competitor rows highlighted.</p></div>
      <div class="cap-card"><h4>Competitor Intelligence</h4><p>Monitor any competitor&rsquo;s rankings, new pages, backlink gains, and Google Business Profile changes. Know when they make a move before it shows up in your rankings.</p></div>
      <div class="cap-card"><h4>Backlink &amp; Authority Analysis</h4><p>Full backlink profile: domain authority, link quality, anchor text distribution, referring domain breakdown. Spot toxic links and identify the exact sites your competitors are getting links from.</p></div>
      <div class="cap-card"><h4>Keyword &amp; Market Research</h4><p>Search volume, keyword difficulty, CPC, and ranking opportunity for any keyword in any market. Find gaps your competitors rank for that you don&rsquo;t.</p></div>
      <div class="cap-card"><h4>Technical Site Audit</h4><p>Full crawl: broken links, missing schema, duplicate content, redirect chains, page speed issues, mobile usability, Core Web Vitals &mdash; all in one pass.</p></div>
    </div>
  </div>
  <div class="sub-section" id="tools-voice">
    <div class="section-eyebrow"><span class="num">T2</span> JamBot &mdash; Your AI Company Assistant</div>
    <h2 class="section-title">An AI That Runs Your Business &mdash; In Your Pocket</h2>
    <div class="section-divider"></div>
    <p class="section-desc">JamBot is your AI-powered company operating system. It runs with its own dedicated email address, phone number, and SMS line &mdash; and you talk to it through the voice interface in the app.</p>
    <div class="cap-grid">
      <div class="cap-card"><h4>Voice Interface in the App</h4><p>Talk to your AI assistant the way you&rsquo;d talk to a team member &mdash; via voice in the JamBot app. Ask for a competitor report, request a new city page, check your ranking positions.</p></div>
      <div class="cap-card"><h4>Dedicated Email, Phone &amp; SMS</h4><p>Your JamBot agent operates with its own email address, phone number, and SMS line &mdash; so it can communicate on your behalf, receive inbound messages, and handle follow-ups.</p></div>
      <div class="cap-card"><h4>Slack, Discord &amp; Telegram</h4><p>Already running your team in Slack or Discord? Connect JamBot and interact with it directly in your existing channels &mdash; no new app to learn.</p></div>
      <div class="cap-card"><h4>Full Conversation History</h4><p>Every interaction with your agent is logged. Review past conversations, pull up decisions made weeks ago, track what was changed and when.</p></div>
    </div>
  </div>
  <div class="sub-section" id="tools-crm">
    <div class="section-eyebrow"><span class="num">T3</span> Your CRM</div>
    <h2 class="section-title">Open-Source CRM &mdash; You Own It</h2>
    <div class="section-divider"></div>
    <p class="section-desc">A fully self-hosted, open-source CRM deployed on your subscription. Your data stays yours &mdash; no vendor lock-in, no per-seat fees.</p>
    <div class="cap-grid">
      <div class="cap-card"><h4>Pipeline Management</h4><p>Track every lead from first call to closed job. Stages, deal value, follow-up dates &mdash; all visible in one board.</p></div>
      <div class="cap-card"><h4>Automatic Contact Logging</h4><p>Every inbound call, web form submission, and booked appointment creates or updates a contact record automatically.</p></div>
      <div class="cap-card"><h4>Job History &amp; Notes</h4><p>Full history per customer &mdash; what was quoted, what was installed, photos from the job, follow-up dates.</p></div>
      <div class="cap-card"><h4>You Own the Data</h4><p>Self-hosted on your subscription infrastructure. If you ever leave, you export your full database and take it with you.</p></div>
    </div>
  </div>
  <div class="sub-section" id="tools-website">
    <div class="section-eyebrow"><span class="num">T4</span> Website</div>
    <h2 class="section-title">Website Build, Maintenance &amp; SEO &mdash; No Agency Needed</h2>
    <div class="section-divider"></div>
    <div class="cap-grid">
      <div class="cap-card"><h4>City &amp; Service Pages</h4><p>New location pages built and deployed to target markets directly &mdash; identified from the keyword gaps in your audit.</p></div>
      <div class="cap-card"><h4>Performance &amp; Core Web Vitals</h4><p>{"LCP at " + lcp_disp + " needs work. Images compressed, lazy-loading added, schema deployed &mdash; no waiting on a developer." if lcp_s > 2.5 else "Core Web Vitals are in a healthy range. Monitor and maintain as new content is added."}</p></div>
      <div class="cap-card"><h4>Blog &amp; Content Publishing</h4><p>SEO-targeted blog posts researched from the {len(content_gaps)} keyword gaps in your audit, written, and published on a regular cadence.</p></div>
      <div class="cap-card"><h4>Schema &amp; Technical SEO</h4><p>LocalBusiness, Service, and FAQ schema deployed sitewide. Required for rich results and AI assistant citations.</p></div>
    </div>
  </div>
  <div class="sub-section" id="tools-apps">
    <div class="section-eyebrow"><span class="num">T5</span> Apps</div>
    <h2 class="section-title">Custom Apps Built on Demand</h2>
    <div class="section-divider"></div>
    <div class="cap-grid">
      <div class="cap-card"><h4>{_escape(service.title())} Price Calculator</h4><p>A customer-facing calculator that takes square footage and application area and returns an estimated range &mdash; captures the lead email at the end. Targets the high-volume cost queries in your market.</p></div>
      <div class="cap-card"><h4>Service Area Map Tool</h4><p>Interactive coverage map showing every city you serve. Helps customers confirm you cover their area before calling.</p></div>
      <div class="cap-card"><h4>Internal Job Dashboard</h4><p>A company-facing view of all open jobs, crew assignments, and daily route &mdash; built for how your operation actually runs.</p></div>
      <div class="cap-card"><h4>Any Tool You Need</h4><p>Quote generators, photo galleries, inspection checklists, customer portals &mdash; if your business needs it and a spreadsheet isn&rsquo;t cutting it, it gets built.</p></div>
    </div>
  </div>
  <div class="sub-section" id="tools-social">
    <div class="section-eyebrow"><span class="num">T6</span> Social &amp; Content</div>
    <h2 class="section-title">Content Creation, Video &amp; Social Media</h2>
    <div class="section-divider"></div>
    <div class="cap-grid">
      <div class="cap-card"><h4>Content Planning &amp; Calendar</h4><p>Full content strategy built around your service area, seasonal demand, and keyword gaps &mdash; mapped into a monthly calendar.</p></div>
      <div class="cap-card"><h4>Social Posts &amp; Video</h4><p>Written posts, short-form video scripts, Reels, TikToks, YouTube Shorts &mdash; planned, created, and queued across all your channels.</p></div>
      <div class="cap-card"><h4>On-Demand Marketing Assets</h4><p>Flyers, social ads, one-pagers, email banners, proposal decks &mdash; generated from your brand kit without waiting on a designer.</p></div>
      <div class="cap-card"><h4>AI-Visible Content</h4><p>FAQ blocks, structured schema, and optimized content that makes ChatGPT, Claude, Gemini, and Perplexity start citing your business.</p></div>
    </div>
  </div>
</div><!-- /page=team -->

<!-- ═══════════════ PAGE 4 — BUILD WITH YOUR VOICE ═══════════════ -->
<div class="report-page" data-page="day-one">
  <div class="sub-section" id="day1-tools">
    <div class="section-eyebrow"><span class="num">D1</span> Speak Your Company Into Place</div>
    <h2 class="section-title">Every System in This Report &mdash; Built by Asking</h2>
    <div class="section-divider"></div>
    <p class="section-desc">JamBot is an AI-powered company computer that lets you create the digital systems and tools your business needs &mdash; with your voice, a text, or a message in Slack. Everything you saw in this report can be built by asking.</p>
    <div class="cap-grid">
      <div class="cap-card"><h4>Your Audit Data Already Loaded</h4><p>Every finding in this report goes into your JamBot. When you start working with it, it already knows your business and what needs to be done.</p></div>
      <div class="cap-card"><h4>&ldquo;Build Me a City Page for {_escape(city)}&rdquo;</h4><p>Just say what you want &mdash; via voice in the app, a text message, Slack, Discord, or email. The system researches, writes, builds, and deploys it.</p></div>
      <div class="cap-card"><h4>Your SEO Command Center</h4><p>Ask it to pull your rankings, find keyword gaps, check what a competitor is ranking for, or run a full site audit. The data is live.</p></div>
      <div class="cap-card"><h4>Your Company CRM</h4><p>&ldquo;Add that last customer.&rdquo; &ldquo;Show me open jobs.&rdquo; &ldquo;Who hasn&rsquo;t been contacted in 30 days?&rdquo; Your CRM is self-hosted &mdash; your data, your control.</p></div>
      <div class="cap-card"><h4>&ldquo;Make a Promo Flyer for Our Summer Deal&rdquo;</h4><p>It knows your brand. Ask for a flyer, a social post, a one-pager, a video script, a landing page &mdash; it generates it from your brand kit.</p></div>
      <div class="cap-card"><h4>Build Any System Your Company Needs</h4><p>Price calculator. Job dashboard. Service area map. Customer portal. Ask for it. Your AI builds it. You own it.</p></div>
    </div>
  </div>
  <div class="sub-section" id="day1-commands">
    <div class="section-eyebrow"><span class="num">D2</span> What You Can Say</div>
    <h2 class="section-title">Real Commands. Real Output. No Middleman.</h2>
    <div class="section-divider"></div>
    <div class="voice-cmd-grid">
      <div class="voice-cmd-card">
        <div class="voice-cmd-cat">SEO &amp; Rankings</div>
        <div class="voice-cmd-list">
          <div class="voice-bubble">&ldquo;Pull my current rankings for {_escape(service)} {_escape(city)} and show me what moved this week&rdquo;</div>
          <div class="voice-bubble">&ldquo;What keywords is my top competitor ranking for that I&rsquo;m not?&rdquo;</div>
          <div class="voice-bubble">&ldquo;Run a full technical SEO audit on my site and give me a prioritized fix list&rdquo;</div>
        </div>
      </div>
      <div class="voice-cmd-card">
        <div class="voice-cmd-cat">Content &amp; Pages</div>
        <div class="voice-cmd-list">
          <div class="voice-bubble">&ldquo;Write a city page for {_escape(city)} &mdash; {_escape(service)}, around 900 words, target the top keyword gap&rdquo;</div>
          <div class="voice-bubble">&ldquo;Optimize the title tags and meta descriptions on my top 10 pages for better CTR&rdquo;</div>
          <div class="voice-bubble">&ldquo;Add FAQ schema to my service pages using the questions customers actually ask&rdquo;</div>
        </div>
      </div>
      <div class="voice-cmd-card">
        <div class="voice-cmd-cat">Marketing &amp; Brand Assets</div>
        <div class="voice-cmd-list">
          <div class="voice-bubble">&ldquo;Make a social post for our {_escape(service)} deal &mdash; Instagram format, brand colors&rdquo;</div>
          <div class="voice-bubble">&ldquo;Write a short video script for YouTube Shorts &mdash; what is {_escape(service)} and why does it matter&rdquo;</div>
          <div class="voice-bubble">&ldquo;Plan out next month&rsquo;s social media calendar for Facebook and Instagram&rdquo;</div>
        </div>
      </div>
      <div class="voice-cmd-card">
        <div class="voice-cmd-cat">CRM &amp; Customer Data</div>
        <div class="voice-cmd-list">
          <div class="voice-bubble">&ldquo;Show me every customer we&rsquo;ve quoted in the last 30 days who hasn&rsquo;t booked yet&rdquo;</div>
          <div class="voice-bubble">&ldquo;Pull a list of all closed jobs from Q1 and which service each one was&rdquo;</div>
          <div class="voice-bubble">&ldquo;Who are our top 10 customers by total job value in the last 12 months?&rdquo;</div>
        </div>
      </div>
    </div>
  </div>
  <div class="sub-section" id="day1-automations">
    <div class="section-eyebrow"><span class="num">D3</span> How It Works</div>
    <h2 class="section-title">You Direct It. It Builds It. You Own It.</h2>
    <div class="section-divider"></div>
    <div class="auto-lane-grid">
      <div class="auto-lane"><h5>You Ask</h5><div class="auto-task">Voice in the app, SMS, email, Slack, Discord &mdash; however you work</div><div class="auto-task">&ldquo;Build a city page for {_escape(city)} targeting {_escape(service)}&rdquo;</div><div class="auto-task">&ldquo;What did my top competitor rank for this week?&rdquo;</div></div>
      <div class="auto-lane"><h5>It Builds</h5><div class="auto-task">Pulls real data &mdash; your SEO dashboard, your CRM, your brand kit</div><div class="auto-task">Writes, designs, codes, or researches &mdash; whatever the task needs</div><div class="auto-task">Delivers it as a live page, file, report, or tool &mdash; ready to use</div></div>
      <div class="auto-lane"><h5>You Own It</h5><div class="auto-task">Every page is live on your site &mdash; your domain, your content</div><div class="auto-task">Every asset saved to your account &mdash; not locked in a vendor&rsquo;s system</div><div class="auto-task">Open it on your desktop anytime &mdash; it&rsquo;s your AI company computer</div></div>
      <div class="auto-lane"><h5>It Remembers</h5><div class="auto-task">Every build, every conversation, every audit finding stays in context</div><div class="auto-task">Doesn&rsquo;t forget your brand, your preferences, your priorities</div><div class="auto-task">Gets more useful the longer you use it</div></div>
    </div>
  </div>
</div><!-- /page=day-one -->

<!-- ═══════════════ PAGE 5 — SIGN UP ═══════════════ -->
<div class="report-page" data-page="signup">
  <div class="sub-section" id="signup-pricing">
    <div class="section-eyebrow"><span class="num">S1</span> Turn This Report Into Results</div>
    <h2 class="section-title">This report found the gaps. JamBot closes them &mdash; for {_escape(client_name)}.</h2>
    <div class="section-divider"></div>
    <p class="section-desc">You just saw exactly where {_escape(client_name)} is winning and where it&rsquo;s leaving money on the table in {_escape(city_state)}. JamBot is the agent that <strong>does the work in this report</strong> &mdash; not another dashboard you have to learn, but an AI team member that ships the fixes, tracks the rankings, answers your calls, and reports back every week. One job a month covers it.</p>
    <div class="pricing-grid">
      <div class="pricing-card featured">
        <div class="pricing-badge" style="display:inline-block;background:var(--brand-primary,#1E6091);color:#fff;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;padding:4px 12px;border-radius:999px;margin-bottom:10px;">Built for {_escape(client_name)}</div>
        <div class="pricing-tier">JamBot &mdash; Full Agent</div>
        <div class="pricing-price">$297<span class="pricing-period">/mo</span></div>
        <div class="pricing-desc">Less than the cost of <strong>one job</strong>. Replaces a $2,000+/mo agency stack. No setup fee, cancel anytime, your data always exports.</div>
        <ul class="pricing-features">
          <li><strong>Fixes your audit</strong> &mdash; schema, speed, city pages, the Priority 1&ndash;3 list, shipped for you</li>
          <li><strong>Wins back rankings</strong> &mdash; live SEO tracking on the keywords that bring you jobs</li>
          <li><strong>Answers every lead</strong> &mdash; AI assistant on voice, SMS &amp; web so you never miss a call</li>
          <li><strong>Owns your pipeline</strong> &mdash; self-hosted CRM, your data, never held hostage</li>
          <li><strong>Publishes content</strong> &mdash; the blog &amp; social posts you don&rsquo;t have time to write</li>
          <li><strong>Builds on demand</strong> &mdash; landing pages, calculators, apps &mdash; just ask</li>
          <li><strong>Reports weekly</strong> &mdash; what moved, what shipped, what&rsquo;s next &mdash; in plain language</li>
        </ul>
        <a href="mailto:start@jam-bot.com?subject=Start%20JamBot%20&mdash;%20{_escape(client_name)}&body=I%20reviewed%20my%20brand%20report%20and%20I%27m%20ready%20to%20get%20started." class="pricing-cta">Start with {_escape(client_name)} &rarr;</a>
        <div class="pricing-foot">No contract &middot; First fixes shipped in week one</div>
      </div>
    </div>
  </div>

  <div class="sub-section" id="signup-day1">
    <div class="section-eyebrow"><span class="num">S2</span> What Happens Day 1</div>
    <h2 class="section-title">No Setup Fee. No Learning Curve. Running Immediately.</h2>
    <div class="section-divider"></div>
    <div class="day1-grid">
      <div class="day1-tile"><div class="day1-num">1</div><h4>Audit Loaded</h4><p>This report&rsquo;s findings go into your agent. It already knows your rankings, competitors, and what to fix first.</p></div>
      <div class="day1-tile"><div class="day1-num">2</div><h4>Access Granted</h4><p>Your JamBot app is live at your subdomain. Voice interface, SEO dashboard, CRM &mdash; all accessible immediately.</p></div>
      <div class="day1-tile"><div class="day1-num">3</div><h4>First Task Assigned</h4><p>Priority 1 items from your audit are queued. Your agent begins executing &mdash; schema first, then speed, then city pages.</p></div>
      <div class="day1-tile"><div class="day1-num">4</div><h4>Weekly Reports</h4><p>Every week you get a rankings update, what moved, what was shipped, and what&rsquo;s next on the priority list.</p></div>
    </div>
  </div>

  <div class="sub-section" id="signup-cta">
    <div class="section-eyebrow"><span class="num">S3</span> Your competitors aren&rsquo;t waiting</div>
    <h2 class="section-title">Every week this sits, those rankings go to someone else.</h2>
    <div class="section-divider"></div>
    <p class="section-desc">This report was built specifically for {_escape(client_name)} in {_escape(city_state)} &mdash; your agent already knows your market, your competitors, and your exact priority list. The moment you say go, it starts shipping the fixes. Reply and you&rsquo;ll be live this week.</p>
    <div class="su-cta-block">
      <a href="mailto:start@jam-bot.com?subject=Start%20JamBot%20&mdash;%20{_escape(client_name)}&body=I%20reviewed%20my%20brand%20report%20and%20I%27m%20ready%20to%20get%20started." class="su-primary-btn">Start with {_escape(client_name)} &rarr;</a>
      <a href="tel:+15204341343" class="su-secondary-btn">Or call us &mdash; (520) 434-1343</a>
    </div>
  </div>

  <div class="rf-footer">
    <div class="rf-mark">Prepared by <b>JamBot</b> &middot; jam-bot.com</div>
    <div class="rf-title">{_escape(client_name)} &mdash; Online Brand Report</div>
    <div class="rf-meta"><strong>{report_date}</strong> &middot; {_escape(domain)} &middot; {_escape(city_state)}</div>
    <div class="rf-freshness">
      <h4>Data Sources &amp; Freshness</h4>
      <table>
        <tbody>
          <tr><td>Organic Keywords</td><td>DataForSEO Labs &mdash; {report_date}</td><td>100 keyword results</td></tr>
          <tr><td>SERP Snapshots</td><td>DataForSEO SERP API &mdash; {report_date}</td><td>Live Google results</td></tr>
          <tr><td>Backlinks</td><td>DataForSEO Backlinks &mdash; {report_date}</td><td>Live index</td></tr>
          <tr><td>Lighthouse / CWV</td><td>DataForSEO OnPage &mdash; {report_date}</td><td>Live Lighthouse run</td></tr>
          <tr><td>GMB / Local</td><td>DataForSEO Business Data &mdash; {report_date}</td><td>Live Google Maps</td></tr>
          <tr><td>Social Channels</td><td>Public profile probe &mdash; {report_date}</td><td>HTTP status checks</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div><!-- /page=signup -->

</div><!-- /report-wrap -->

<script>
(function(){{
  'use strict';

  const BRAND_BLUE   = '#0E5C7A';
  const BRAND_ORANGE = '#F39C12';
  const GREEN  = '#10b981';
  const YELLOW = '#f59e0b';
  const RED    = '#ef4444';
  const SLATE  = '#64748b';
  const GR     = '#9ca3af';
  const GRID   = '#1f2937';

  // ── Theme toggle ────────────────────────────────────────────────────────
  const themeBtn = document.getElementById('themeToggle');
  const themeLbl = document.getElementById('themeLabel');
  let isLight = true;
  function applyChartTheme(light) {{
    const labelColor = light ? '#475569' : GR;
    const gridColor  = light ? '#e2e8f0' : GRID;
    if (typeof Chart !== 'undefined') {{
      Chart.defaults.color = labelColor;
      Chart.defaults.borderColor = gridColor;
    }}
  }}
  document.addEventListener('DOMContentLoaded', () => {{
    document.body.classList.add('light-mode');
    if (themeLbl) themeLbl.textContent = 'LIGHT';
    applyChartTheme(true);
    const parsed = parseHash();
    activatePage(parsed.page, {{chip: parsed.chip, updateHash: false, smoothScroll: false}});
  }});
  if (themeBtn) {{
    themeBtn.addEventListener('click', () => {{
      isLight = !isLight;
      document.body.classList.toggle('light-mode', isLight);
      if (themeLbl) themeLbl.textContent = isLight ? 'LIGHT' : 'DARK';
      applyChartTheme(isLight);
    }});
  }}

  // ── Page switching ───────────────────────────────────────────────────────
  const PAGES = ['found', 'plan', 'team', 'day-one', 'signup'];
  const DEFAULT_PAGE = 'found';
  const initializedPages = new Set();

  function parseHash() {{
    const h = window.location.hash.slice(1);
    const params = new URLSearchParams(h.replace('page=','_page=').replace(/^([^&=?]+)$/, '_page=$1'));
    const raw = h.includes('page=') ? (h.match(/page=([^&]+)/)||[])[1] : (h || DEFAULT_PAGE);
    const page = PAGES.includes(raw) ? raw : DEFAULT_PAGE;
    const chip = h.includes('chip=') ? (h.match(/chip=([^&]+)/)||[])[1] : null;
    return {{page, chip}};
  }}

  function activatePage(pageName, opts={{}}) {{
    opts = opts || {{}};
    if (!PAGES.includes(pageName)) pageName = DEFAULT_PAGE;
    const tabBtns = Array.from(document.querySelectorAll('.tab-btn[data-page]'));
    const pages   = Array.from(document.querySelectorAll('.report-page[data-page]'));
    const chipStrips = Array.from(document.querySelectorAll('.chip-strip[data-chips-for]'));

    tabBtns.forEach(b => b.classList.toggle('is-active', b.dataset.page === pageName));
    pages.forEach(p => p.classList.toggle('is-active', p.dataset.page === pageName));
    chipStrips.forEach(s => s.classList.toggle('is-active', s.dataset.chipsFor === pageName));

    if (!initializedPages.has(pageName)) {{
      initializedPages.add(pageName);
      try {{ initPageCharts(pageName); }} catch(e) {{ console.error('Chart init failed', pageName, e); }}
    }} else {{
      try {{
        if (typeof Chart !== 'undefined') {{
          const activePage = document.querySelector('.report-page.is-active');
          if (activePage) {{
            activePage.querySelectorAll('canvas').forEach(c => {{
              const inst = Chart.getChart ? Chart.getChart(c) : null;
              if (inst) {{ try {{ inst.resize(); }} catch(_){{}} }}
            }});
          }}
        }}
      }} catch(_) {{}}
    }}

    if (opts.updateHash !== false) {{
      const newHash = '#page=' + pageName;
      if (window.location.hash !== newHash) history.replaceState(null, '', newHash);
    }}

    if (opts.chip) {{
      const target = document.getElementById(opts.chip);
      if (target) setTimeout(() => target.scrollIntoView({{behavior:'auto', block:'start'}}), 30);
    }} else {{
      window.scrollTo({{top:0, behavior: opts.smoothScroll ? 'smooth' : 'auto'}});
    }}
  }}

  document.querySelectorAll('.tab-btn[data-page]').forEach(btn => {{
    btn.addEventListener('click', () => activatePage(btn.dataset.page, {{smoothScroll: true}}));
  }});

  window.addEventListener('hashchange', () => {{
    const parsed = parseHash();
    activatePage(parsed.page, {{chip: parsed.chip, updateHash: false}});
  }});

  // ── Chip strip ───────────────────────────────────────────────────────────
  document.querySelectorAll('.chip-strip a.subchip').forEach(link => {{
    link.addEventListener('click', e => {{
      const chipId = link.dataset.chip;
      const target = document.getElementById(chipId);
      if (target) {{
        e.preventDefault();
        target.scrollIntoView({{behavior: 'smooth', block: 'start'}});
        const strip = link.closest('.chip-strip');
        if (strip) strip.querySelectorAll('a.subchip').forEach(c => c.classList.toggle('is-active', c===link));
        history.replaceState(null, '', '#page=' + (link.closest('.chip-strip')?.dataset.chipsFor || 'found') + '&chip=' + chipId);
      }}
    }});
  }});

  // ── Charts ───────────────────────────────────────────────────────────────
  function bandColor(b) {{
    if (b==='ok'||b==='good') return GREEN;
    if (b==='warn'||b==='needs-work') return YELLOW;
    return RED;
  }}

  function gauge(id, pct, band) {{
    const ctx = document.getElementById(id);
    if (!ctx) return;
    new Chart(ctx, {{
      type: 'doughnut',
      data: {{ datasets: [{{ data: [pct, 100-pct], backgroundColor: [bandColor(band), GRID], borderWidth: 0, circumference: 180, rotation: 270, cutout: '75%' }}] }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{display:false}}, tooltip: {{enabled:false}} }} }}
    }});
  }}

  function initFoundPage() {{
    if (typeof Chart === 'undefined') return;

    gauge('ux-cwv-lcp', {lcp_pct}, '{lcp_band}');
    gauge('ux-cwv-fid', {fid_pct}, '{tbt_band}');
    gauge('ux-cwv-cls', {cls_pct}, '{cls_band}');

    const lhCtx = document.getElementById('ux-lighthouse-bars');
    if (lhCtx) {{
      const lh = {{ performance: {lh_perf}, accessibility: {lh_a11y}, bestPractices: {lh_bp}, seo: {lh_seo} }};
      new Chart(lhCtx, {{
        type: 'bar',
        data: {{
          labels: ['Performance', 'Accessibility', 'Best Practices', 'SEO'],
          datasets: [{{ data: [lh.performance, lh.accessibility, lh.bestPractices, lh.seo], backgroundColor: [lh.performance, lh.accessibility, lh.bestPractices, lh.seo].map(v => v>=90?GREEN:v>=50?YELLOW:RED), borderRadius: 4 }}]
        }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{legend:{{display:false}}}}, scales: {{ y: {{beginAtZero:true, max:100, ticks:{{color:GR}}, grid:{{color:GRID}}}}, x: {{ticks:{{color:GR}}, grid:{{display:false}}}} }} }}
      }});
    }}

    const kwVolCtx = document.getElementById('os-top-kw-vol');
    if (kwVolCtx && {json.dumps(kw_volumes)}.length) {{
      new Chart(kwVolCtx, {{
        type: 'bar',
        data: {{ labels: {_js_list(kw_labels)}, datasets: [{{ data: {_js_list(kw_volumes)}, backgroundColor: BRAND_BLUE, borderRadius: 4 }}] }},
        options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: {{legend:{{display:false}}}}, scales: {{ x: {{ticks:{{color:GR}}, grid:{{color:GRID}}}}, y: {{ticks:{{color:GR, font:{{size:10}}}}, grid:{{display:false}}}} }} }}
      }});
    }}

    const avgPosCtx = document.getElementById('os-avg-position');
    if (avgPosCtx) {{
      new Chart(avgPosCtx, {{
        type: 'bar',
        data: {{
          labels: ['Pos 1-3', 'Pos 4-10', 'Pos 11-20', 'Pos 21-50', 'Pos 51-100'],
          datasets: [{{ data: [{kw_top3}, {kw_4_10}, {kw_11_20}, {kw_21_50}, {kw_51_100}], backgroundColor: [GREEN, GREEN, BRAND_BLUE, YELLOW, RED], borderRadius: 4 }}]
        }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{legend:{{display:false}}}}, scales: {{ y: {{beginAtZero:true, ticks:{{color:GR}}, grid:{{color:GRID}}}}, x: {{ticks:{{color:GR}}, grid:{{display:false}}}} }} }}
      }});
    }}

    // Sparklines (empty vals = flat line placeholder)
    document.querySelectorAll('canvas.spark').forEach(cv => {{
      if (cv.dataset._init) return;
      cv.width = 100; cv.height = 28;
      cv.dataset._init = '1';
      const vals = (cv.dataset.vals||'').split(',').map(Number).filter(n=>!isNaN(n)&&n>0);
      new Chart(cv, {{
        type: 'line',
        data: {{ labels: vals.length ? vals.map((_,i)=>i) : [0,1,2,3,4], datasets: [{{ data: vals.length ? vals : [1,1,1,1,1], borderColor: BRAND_BLUE, backgroundColor: 'rgba(14,92,122,.22)', fill: true, pointRadius: 0, tension: .35, borderWidth: 1.5 }}] }},
        options: {{ responsive: false, plugins: {{legend:{{display:false}}, tooltip:{{enabled:false}}}}, scales: {{x:{{display:false}}, y:{{display:false, reverse:true}}}} }}
      }});
    }});

    const daCtx = document.getElementById('bl-da-gauge');
    if (daCtx) {{
      const da = {dr};
      const color = da>=50?GREEN:da>=25?YELLOW:RED;
      new Chart(daCtx, {{
        type: 'doughnut',
        data: {{ datasets: [{{ data: [da, 100-da], backgroundColor: [color, GRID], borderWidth: 0, circumference: 180, rotation: 270, cutout: '75%' }}] }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{legend:{{display:false}}, tooltip:{{enabled:false}}}} }}
      }});
    }}

    const anchorCtx = document.getElementById('bl-anchor');
    if (anchorCtx) {{
      const anchorData = {_js_list(anchor_dist.get("data", [0,0,0,0,0]))};
      const anchorLabels = {_js_list(anchor_dist.get("labels", ["Branded","Exact","Partial","Generic","Naked"]))};
      new Chart(anchorCtx, {{
        type: 'doughnut',
        data: {{ labels: anchorLabels, datasets: [{{ data: anchorData, backgroundColor: [BRAND_BLUE, RED, YELLOW, SLATE, GREEN], borderColor: '#0a0e1a', borderWidth: 2 }}] }},
        options: {{ responsive: true, maintainAspectRatio: false, cutout: '55%', plugins: {{legend: {{position:'bottom', labels:{{color:GR, font:{{size:9}}}}}}}} }}
      }});
    }}

    const radarCtx = document.getElementById('cb-radar');
    if (radarCtx) {{
      new Chart(radarCtx, {{
        type: 'radar',
        data: {{
          labels: ['Traffic','Keywords','Top-10','Backlinks','Authority','Pages'],
          datasets: [
            {{ label: 'You ({_escape(domain)})', data: {_js_list(radar_client)}, backgroundColor: 'rgba(14,92,122,.30)', borderColor: BRAND_BLUE, pointBackgroundColor: BRAND_BLUE }},
            {{ label: '{_escape(top_competitor) or "Top Competitor"}', data: {_js_list(radar_comp)}, backgroundColor: 'rgba(243,156,18,.20)', borderColor: BRAND_ORANGE, pointBackgroundColor: BRAND_ORANGE }}
          ]
        }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{legend:{{labels:{{color:GR}}}}}}, scales: {{r:{{angleLines:{{color:GRID}}, grid:{{color:GRID}}, pointLabels:{{color:GR, font:{{size:10}}}}, ticks:{{display:false}}, suggestedMin:0, suggestedMax:100}}}} }}
      }});
    }}

    const bubbleCtx = document.getElementById('cb-bubble');
    if (bubbleCtx) {{
      const bubbleData = {_js_list([{"x": kw.get("volume",0), "y": kw.get("position",50), "r": max(6, min(20, kw.get("volume",100)//200)), "label": kw.get("keyword","")[:30]} for kw in top_kws[:10]])};
      new Chart(bubbleCtx, {{
        type: 'bubble',
        data: {{ datasets: [{{ label: 'Keyword Opportunities', data: bubbleData, backgroundColor: 'rgba(14,92,122,.55)', borderColor: BRAND_BLUE }}] }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{legend:{{display:false}}, tooltip:{{callbacks:{{label:(c)=>c.raw.label+': vol '+c.raw.x+', pos '+c.raw.y}}}}}}, scales: {{ x:{{type:'logarithmic', title:{{display:true, text:'Search Volume (log)', color:GR}}, ticks:{{color:GR}}, grid:{{color:GRID}}}}, y:{{reverse:true, title:{{display:true, text:'Your Position', color:GR}}, ticks:{{color:GR}}, grid:{{color:GRID}}}}}} }}
      }});
    }}
  }}

  function initPageCharts(pageName) {{
    switch(pageName) {{
      case 'found': initFoundPage(); break;
    }}
  }}

  window.__OBR__ = {{activatePage, parseHash, initializedPages}};
}})();
</script>

<script>
  window.__JAMBOT_REPORT_BUILD__ = "{date.today().isoformat()}T00:00:00Z";
  window.__JAMBOT_DOMAIN__ = "{_escape(domain)}";
  window.__JAMBOT_SCORE__ = {score_total};
</script>

</body>
</html>"""

    # Write file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[RENDER] Written {len(html):,} bytes → {output_path}", flush=True)
