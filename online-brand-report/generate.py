#!/usr/bin/env python3
"""
online-brand-report — generate a fully-populated SEO brand report HTML file.

Usage:
  python generate.py \
    --domain spartancoatingsystems.com \
    --name "Spartan Coating Systems" \
    --owner "Stephen Smith" \
    --city "Lawton" \
    --state "OK" \
    --phone "+1-580-555-0100" \
    --email "info@spartancoatingsystems.com" \
    --service "spray foam insulation" \
    --competitors "competitor1.com,competitor2.com" \
    --output /mnt/clients/test-dev/openvoiceui/canvas-pages/brand-report-spartan.html \
    [--tenant test-dev]
"""

import argparse
import os
import sys
import time
from datetime import datetime
import traceback
from pathlib import Path

# ── Path setup ───────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SKILL_DIR))

from lib import (
    fetch_brand,
    fetch_web,
    fetch_organic,
    fetch_serp,
    fetch_local,
    fetch_backlinks,
    fetch_competitive,
    fetch_content,
    fetch_ai,
    fetch_social,
    fetch_geo,
    score as score_mod,
    roadmap as roadmap_mod,
    render as render_mod,
    plan as plan_mod,
)

TEMPLATE_PATH = "/mnt/clients/test-dev/openvoiceui/canvas-pages/online-brand-report-template.html"

# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Generate an Online Brand Report HTML file.")
    p.add_argument("--domain",      required=True,  help="Target domain (no https://)")
    p.add_argument("--name",        required=True,  help="Business name")
    p.add_argument("--owner",       default="",     help="Owner / contact name")
    p.add_argument("--city",        default="",     help="Primary city")
    p.add_argument("--state",       default="",     help="State abbreviation")
    p.add_argument("--phone",       default="",     help="Phone number")
    p.add_argument("--email",       default="",     help="Email address")
    p.add_argument("--service",     default="",     help="Primary service (drives keyword research, e.g. 'spray foam insulation')")
    p.add_argument("--services",    default="",     help="Comma-separated FULL service list for the service×area money-page matrix "
                                                         "(e.g. 'rim repair,curb rash,bent rim straightening'). If omitted, the "
                                                         "matrix expands only the primary --service across areas.")
    p.add_argument("--competitors", default="",     help="Comma-separated competitor domains")
    p.add_argument("--output",      default="",     help="Full output path for the HTML file")
    p.add_argument("--tenant",      default="test-dev", help="JamBot tenant name (for default output path)")
    p.add_argument("--publish-slug", default="",    help="Company slug for public publication at start.jam-bot.com/<slug>/. "
                                                         "If omitted, derived from --name (kebab-case). "
                                                         "Pass --no-publish to skip public copy.")
    p.add_argument("--no-publish",  action="store_true", help="Skip the start.jam-bot.com publication step")
    p.add_argument("--client-knowledge-path", default="", help="If set, writes brand_report_url and brand_report_generated_at back to this client-knowledge.json (for stager substitution)")
    return p.parse_args()


def slugify(text: str) -> str:
    """company-slug — kebab-case, ASCII-safe, matches nginx vhost regex ^[a-z0-9][a-z0-9-]{0,80}$"""
    import re
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = re.sub(r'-+', '-', s)
    return s[:80] or 'unnamed'


def resolve_output(args) -> str:
    if args.output:
        return args.output
    # Default: canvas-pages for the given tenant
    slug = args.domain.replace("www.", "").replace(".", "-").replace("_", "-").lower()
    return f"/mnt/clients/{args.tenant}/openvoiceui/canvas-pages/brand-report-{slug}.html"


# ── Fetcher runner ────────────────────────────────────────────────────────────

def _run(label: str, fn, *a, **kw) -> dict:
    """Run a fetcher, catch exceptions, return empty dict on failure."""
    t0 = time.time()
    try:
        result = fn(*a, **kw)
        elapsed = time.time() - t0
        print(f"  [OK]  {label:<30} {elapsed:.1f}s", file=sys.stderr)
        return result
    except Exception:
        elapsed = time.time() - t0
        print(f"  [ERR] {label:<30} {elapsed:.1f}s", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    domain    = args.domain.replace("https://", "").replace("http://", "").rstrip("/")
    name      = args.name
    owner     = args.owner
    city      = args.city
    state     = args.state
    phone     = args.phone
    email     = args.email
    service   = args.service
    tenant    = args.tenant
    output    = resolve_output(args)

    competitors_raw = [c.strip() for c in args.competitors.split(",") if c.strip()]

    print(f"\n=== Online Brand Report: {name} ({domain}) ===", file=sys.stderr)
    print(f"    Output: {output}", file=sys.stderr)
    print(f"    Tenant: {tenant}", file=sys.stderr)
    print(f"\n--- Fetching data ---", file=sys.stderr)

    t_start = time.time()

    # ── Run all fetchers ──────────────────────────────────────────────────────
    brand_data      = _run("brand/GMB",         fetch_brand.fetch_brand,       domain, name, city, state)
    web_data        = _run("web/Lighthouse",    fetch_web.fetch_web,           domain)
    organic_data    = _run("organic/keywords",  fetch_organic.fetch_organic,   domain)
    serp_data       = _run("serp/results",      fetch_serp.fetch_serp,         domain, service, city, state)
    local_data      = _run("local/reviews+map", fetch_local.fetch_local,       name, service, city, state, domain)
    backlink_data   = _run("backlinks",         fetch_backlinks.fetch_backlinks, domain)
    comp_data       = _run("competitive",       fetch_competitive.fetch_competitive, domain, competitors_raw)
    content_data    = _run("content/gaps",      fetch_content.fetch_content,   domain, service, city,
                                                                                comp_data.get("top_competitor", ""))
    ai_data         = _run("AI/llms.txt",       fetch_ai.fetch_ai,             domain, name)
    social_data     = _run("social",            fetch_social.fetch_social,     domain, name)
    geo_data        = _run("geo/city-volumes",  fetch_geo.fetch_geo,           service, city, state)

    t_fetch = time.time() - t_start
    print(f"\n    Total fetch time: {t_fetch:.1f}s", file=sys.stderr)

    # ── Merge into single data dict ───────────────────────────────────────────
    data: dict = {}
    for d in (brand_data, web_data, organic_data, serp_data, local_data,
              backlink_data, comp_data, content_data, ai_data, social_data, geo_data):
        data.update(d)

    # If fetch_local couldn't get reviews, fall back to GMB data from fetch_brand
    if data.get("review_avg", 0) == 0 and data.get("gmb_rating", 0) > 0:
        data["review_avg"]   = data["gmb_rating"]
        data["review_count"] = data.get("gmb_review_count", 0)
        print(f"    [INFO] Using GMB rating as review fallback: {data['review_avg']}★ ({data['review_count']} reviews)", file=sys.stderr)

    # Inject CLI-supplied identity fields (override if fetchers set them)
    data.update({
        "domain":       domain,
        "brand_name":   name,
        "owner_name":   owner,
        "city":         city,
        "state":        state,
        "service":      service,
        "tenant":       tenant,
    })
    # phone / email: CLI WINS when supplied, else keep what the GMB fetcher found
    # (fetch_local sets data["phone"]/["address"] from my_business_info). Non-clobbering
    # so a report still shows the real NAP when the caller didn't pass --phone. (ica-voice 2026-06-01)
    if phone:
        data["phone"] = phone
    if email:
        data["email"] = email

    # Full service list → drives the service×area money-page matrix (plan.py reads data["services"]).
    # Without it the matrix expands only the single primary service across areas (core-only).
    services_list = [s.strip() for s in args.services.split(",") if s.strip()]
    if services_list:
        data["services"] = services_list
        print(f"    [INFO] Service matrix from {len(services_list)} services: {', '.join(services_list)}", file=sys.stderr)

    # ── Score + Roadmap ───────────────────────────────────────────────────────
    print("\n--- Scoring ---", file=sys.stderr)
    score_result = score_mod.calculate_score(data)
    print(f"    Brand Health Score: {score_result['total']}/100  Grade: {score_result['grade']}  ({score_result['grade_desc']})", file=sys.stderr)
    print(f"    Breakdown: {score_result['breakdown']}", file=sys.stderr)

    print("\n--- Roadmap ---", file=sys.stderr)
    roadmap = roadmap_mod.generate_roadmap(data, score_result)
    print(f"    P1 items: {len(roadmap['p1'])}   P2: {len(roadmap['p2'])}   P3: {len(roadmap['p3'])}", file=sys.stderr)

    # ── Build plan (the meat) — machine-readable spec for the website builder ──
    print("\n--- Build Plan ---", file=sys.stderr)
    plan = plan_mod.build_plan(data)
    s = plan["summary"]
    print(f"    {s['keyword_gaps']} gaps · {s['quick_wins']} quick-wins · "
          f"{s['recommended_pages']} pages · {s['content_articles']} articles", file=sys.stderr)

    # ── Render ────────────────────────────────────────────────────────────────
    print("\n--- Rendering HTML ---", file=sys.stderr)

    # Ensure output directory exists
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the machine-readable plan next to the HTML report (builder consumes this).
    import json as _json2
    plan_path = out_path.with_name("seo-plan.json")
    plan_path.write_text(_json2.dumps(plan, indent=2))
    print(f"    seo-plan.json → {plan_path}", file=sys.stderr)

    # Write the human-readable background plan (gold-standard style) alongside it.
    try:
        from lib import plan_md as plan_md_mod
        identity = {"name": name, "owner": owner, "city": city, "state": state,
                    "phone": phone, "email": email, "brand_name": name}
        md = plan_md_mod.render_plan_md(plan, identity, score_result, roadmap,
                                        generated_at=datetime.utcnow().strftime("%Y-%m-%d"))
        md_path = out_path.with_name("website-plan.md")
        md_path.write_text(md)
        print(f"    website-plan.md → {md_path}", file=sys.stderr)
    except Exception as _md_e:
        print(f"    website-plan.md FAILED: {_md_e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    render_mod.render(
        data=data,
        score_result=score_result,
        roadmap=roadmap,
        output_path=str(out_path),
        plan=plan,
    )

    t_total = time.time() - t_start
    file_kb = out_path.stat().st_size // 1024

    # ── Publish to start.jam-bot.com/<slug>/ ─────────────────────────────────
    public_url = ""
    if not args.no_publish:
        publish_slug = args.publish_slug or slugify(name)
        public_dir = Path("/var/www/start-jam-bot") / publish_slug
        try:
            public_dir.mkdir(parents=True, exist_ok=True)
            # Copy as index.html so nginx pretty-URL /<slug>/ serves it
            import shutil
            shutil.copyfile(str(out_path), str(public_dir / "index.html"))
            public_url = f"https://start.jam-bot.com/{publish_slug}/"
            print(f"    Published:   {public_url}", file=sys.stderr)
            # Writeback to client-knowledge.json so stager can substitute {brand_report_url}
            if args.client_knowledge_path and public_url:
                try:
                    import json as _json
                    ckp = Path(args.client_knowledge_path)
                    ck = _json.loads(ckp.read_text()) if ckp.exists() else {}
                    ck["brand_report_url"] = public_url
                    ck["brand_report_generated_at"] = datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%dT%H:%M:%SZ")
                    ckp.write_text(_json.dumps(ck, indent=2))
                    print(f"    Wrote brand_report_url to {ckp}", file=sys.stderr)
                except Exception as _wb_e:
                    print(f"    Writeback FAILED: {_wb_e}", file=sys.stderr)
        except Exception as e:
            print(f"    Publish FAILED: {e}", file=sys.stderr)

    print(f"\n=== DONE ===", file=sys.stderr)
    print(f"    File:        {output}  ({file_kb}KB)", file=sys.stderr)
    print(f"    Total time:  {t_total:.1f}s", file=sys.stderr)
    print(f"    Score:       {score_result['total']}/100  {score_result['grade']} — {score_result['grade_desc']}", file=sys.stderr)
    print(f"    Roadmap:     {len(roadmap['p1'])} P1 / {len(roadmap['p2'])} P2 / {len(roadmap['p3'])} P3 items", file=sys.stderr)

    # Stdout: machine-readable result for openclaw skill invocation
    print(f"Report generated: {output}")
    print(f"Score: {score_result['total']}/100 ({score_result['grade']} — {score_result['grade_desc']})")
    print(f"Roadmap: {len(roadmap['p1'])} P1 / {len(roadmap['p2'])} P2 / {len(roadmap['p3'])} P3 action items")
    print(f"Canvas URL: /canvas/{out_path.name}")
    if public_url:
        print(f"Public URL: {public_url}")


if __name__ == "__main__":
    main()
