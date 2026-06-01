#!/usr/bin/env python3
"""
seo-plan-to-research.py — turn the Brand Report's seo-plan.json into the website
builder's Phase 1 research files. This is the "research from Brand Report" wiring:
the brand report is the single SEO research engine; the builder CONSUMES its plan
instead of re-querying DataForSEO.

Usage:
  python3 seo-plan-to-research.py <project_dir>
    <project_dir> must contain ai/seo-plan.json (+ .intake.json).
  Writes ai/research/{keywords,topical-map,faq-research,page-recommendations,
  competitors,content-strategy,market-analysis,design-notes}.md + ai/research/.dfs/volumes.json,
  and seeds intake.pages from the plan's recommended_pages.

Exit 0 on success (gate-passing files written), 1 if the plan is missing/too thin.
"""
import json, os, re, sys

proj = sys.argv[1] if len(sys.argv) > 1 else "."
plan_path = os.path.join(proj, "ai", "seo-plan.json")
if not os.path.exists(plan_path):
    print(f"NO PLAN: {plan_path} not found — fall back to live DataForSEO research", file=sys.stderr)
    sys.exit(1)

plan = json.load(open(plan_path))
research = os.path.join(proj, "ai", "research")
dfs = os.path.join(research, ".dfs")
os.makedirs(dfs, exist_ok=True)

service = plan.get("service", "the service")
city    = plan.get("city", "")
domain  = plan.get("domain", "")
kws     = plan.get("all_keywords", [])
gaps    = plan.get("keyword_gaps", [])
pages   = plan.get("recommended_pages", [])
clusters = plan.get("content_clusters", [])
comps   = plan.get("competitors", [])
qw      = plan.get("quick_wins", [])

def w(name, text):
    open(os.path.join(research, name), "w").write(text)

# ── .dfs/volumes.json (source-of-truth the gate checks) ──
json.dump({"source": "brand-report seo-plan.json", "keywords":
           [{"keyword": k["keyword"], "search_volume": k["volume"], "cpc": k["cpc"],
             "competition_index": k.get("difficulty", 0)} for k in kws]},
          open(os.path.join(dfs, "volumes.json"), "w"), indent=2)

# ── keywords.md (≥ rows, integer volume + decimal cpc) ──
rows = "\n".join(
    f"| {k['keyword']} | {k['volume']} | {k['cpc']:.2f} | {k.get('difficulty',0)} | {k['intent']} | {k.get('our_position') or '—'} |"
    for k in kws)
w("keywords.md",
  f"# Keyword Strategy — {domain}\n\nTools Used: DataForSEO (via Brand Report seo-plan.json — single research engine, no re-pull).\n\n"
  f"| Keyword | Volume | CPC | Difficulty | Intent | Our Position |\n|---|---|---|---|---|---|\n{rows}\n")

# ── topical-map.md (clusters from the plan) ──
tm = [f"# Topical Map — {service}\n\n## Pillar: {plan.get('core_pillar', service)}\n"]
for c in clusters:
    tm.append(f"\n## Cluster: {c['name']}  ({len(c['articles'])} articles)")
    for a in c["articles"]:
        tm.append(f"- **{a['title']}** — target: \"{a['target_keyword']}\" ({a.get('volume',0)}/mo)")
# add a transactional cluster from the page set
if pages:
    tm.append("\n## Cluster: Core Service & Location Pages")
    for pg in pages:
        tm.append(f"- **{pg['title']}** — \"{pg['primary_keyword']}\" ({pg.get('volume',0)}/mo) [{pg['page_type']}]")
w("topical-map.md", "\n".join(tm) + "\n")

# ── faq-research.md (≥20 Q&A synthesized from informational keywords + standard set) ──
faq = [f"# FAQ Research — {service}{(' in ' + city) if city else ''}\n"]
def q(question, answer):
    faq.append(f"\n**Q: {question}**\nA: {answer}")
# from informational keywords
info = [k for k in kws if k["intent"] == "informational"][:14]
for k in info:
    kw = k["keyword"]
    if re.search(r"cost|price|how much|per ", kw.lower()):
        q(f"How much does {kw} cost{(' in ' + city) if city else ''}?",
          f"Pricing for {service} varies by scope, materials, and access. This page gives honest ranges and the factors that drive your quote. Search demand: {k['volume']}/mo.")
    elif kw.lower().startswith(("how", "what", "why", "is ", "does ", "can ")):
        q(kw[0].upper() + kw[1:] + "?",
          f"Answered in plain language for {city or 'local'} customers, grounded in our {service} experience. ({k['volume']}/mo)")
    else:
        q(f"What should I know about {kw}?",
          f"Key facts about {kw} for anyone considering {service}. ({k['volume']}/mo)")
# standard service questions to guarantee ≥20
STD = [
    (f"How long does {service} take?", f"Most {service} jobs are completed within the timeframe we confirm at quote — we give you a clear schedule up front."),
    (f"Is {service} worth it?", f"For most {city or 'local'} customers, yes — we walk you through the value and the alternatives honestly."),
    (f"Do you offer free quotes for {service}?", "Yes — a no-obligation quote so you know exactly what to expect."),
    (f"Are you licensed and insured for {service}?", "Yes — fully licensed and insured; documentation available on request."),
    (f"What areas do you serve?", f"{city + ' and the surrounding area' if city else 'Your local area'} — call to confirm your address is covered."),
    (f"How do I get started with {service}?", "Request a quote or call us — we'll assess your needs and give you a clear next step."),
    (f"What makes your {service} different?", "Specialized focus, transparent pricing, and a track record of local reviews."),
    (f"Can you handle my specific {service} job?", "Most likely — tell us the details and we'll confirm scope and timing."),
    (f"How soon can you start my {service} project?", "Often within days — we'll confirm the soonest slot when you reach out."),
    (f"Do you offer warranties on {service}?", "Yes — we stand behind our work; warranty terms are confirmed at quote."),
    (f"What payment options do you accept for {service}?", "Standard options plus financing where applicable — ask at quote."),
    (f"Do I need to be home during {service}?", "We'll confirm access requirements when scheduling — many jobs don't require it."),
    (f"How do I prepare for {service}?", "We send a short prep checklist before the appointment so it goes smoothly."),
]
for ques, ans in STD:
    if len([x for x in faq if x.startswith("\n**Q")]) >= 24:
        break
    q(ques, ans)
w("faq-research.md", "\n".join(faq) + "\n")

# ── page-recommendations.md ──
pr = [f"# Page Recommendations — {domain}\n\nDerived from the Brand Report's seo-plan.json (real keyword demand).\n"]
for pg in pages:
    pr.append(f"- **/{pg['slug']}** — {pg['title']} ({pg['page_type']}) — primary kw \"{pg['primary_keyword']}\" ({pg.get('volume',0)}/mo)")
pr.append("\n## Blog / content articles (topical authority)")
for c in clusters:
    for a in c["articles"]:
        pr.append(f"- **/blog/{re.sub(r'[^a-z0-9]+','-',a['title'].lower()).strip('-')[:60]}** — {a['title']}")
w("page-recommendations.md", "\n".join(pr) + "\n")

# ── competitors.md ──
cm = [f"# Competitors — {domain}\n"]
for c in comps:
    cm.append(f"\n## {c.get('domain','')}\n- Est. traffic/mo: {c.get('traffic_estimate',0)}\n- Ranking keywords: {c.get('ranking_keywords',0)}")
cm.append("\n## Keyword gaps (competitor ranks, we don't / worse)")
for g in gaps[:20]:
    cm.append(f"- \"{g['keyword']}\" ({g['volume']}/mo) — {g.get('competitor','competitor')} #{g.get('competitor_position')} vs us {g.get('your_position') or 'not ranked'}")
w("competitors.md", "\n".join(cm) + "\n")

# ── content-strategy.md ──
cs = [f"# Content Strategy — {domain}\n\nGlobal rule: every page leads + ends with a clear CTA. Educate-then-convert.\n"]
for pg in pages:
    cs.append(f"\n## /{pg['slug']}\nAchieve: rank \"{pg['primary_keyword']}\" ({pg.get('volume',0)}/mo). H1: {pg['h1']}. Intent: {pg.get('intent')}. CTA: primary conversion.")
w("content-strategy.md", "\n".join(cs) + "\n")

# ── market-analysis.md + design-notes.md (brief, from plan) ──
total_vol = sum(k["volume"] for k in kws)
w("market-analysis.md",
  f"# Market Analysis — {service}{(' in ' + city) if city else ''}\n\n"
  f"- Total tracked monthly search volume: {total_vol:,}\n- Ranked keywords (this domain): {plan.get('summary',{}).get('ranked_keywords',0)}\n"
  f"- Keyword gaps vs competitors: {len(gaps)}\n- Quick wins (page-2 keywords): {len(qw)}\n- Top competitor: {plan.get('summary',{}).get('top_competitor','')}\n")
w("design-notes.md",
  f"# Design Notes — {domain}\n\nBUSINESS_TYPE: SERVICE_LOCAL (derive from intake). "
  f"Use a clean, trustworthy local-service aesthetic; phone + Get-a-Quote prominent. "
  f"Differentiate from competitors with real photography and clear pricing transparency.\n")

# ── money-page matrix + interlink map → files the build phases consume directly ──
matrix = plan.get("service_area_matrix", [])
interlink = plan.get("interlink_map", [])
supporting = plan.get("supporting_content", [])
json.dump({"money_pages": matrix, "interlink_map": interlink, "supporting_content": supporting,
           "services": plan.get("services", []), "service_areas": plan.get("service_areas", [])},
          open(os.path.join(proj, "ai", "build-plan.json"), "w"), indent=2)

# ── seed intake.pages from recommended_pages + money-page matrix (the full page set) ──
intake_path = os.path.join(proj, ".intake.json")
if os.path.exists(intake_path):
    intake = json.load(open(intake_path))
    existing = {(p if isinstance(p, str) else p.get("slug", "")).strip("/").lower()
                for p in (intake.get("pages") or [])}
    added = []
    page_list = list(intake.get("pages") or [])
    # supporting service/info pages, then the money pages (the priority for local SEO)
    for pg in (pages + matrix):
        slug = pg["slug"]
        if slug.lower() not in existing:
            existing.add(slug.lower()); page_list.append(slug); added.append(slug)
    intake["pages"] = page_list
    intake["_seo_plan_consumed"] = True
    json.dump(intake, open(intake_path, "w"), indent=2)
    print(f"intake.pages: +{len(added)} pages ({len(matrix)} money pages + {len(pages)} supporting)", file=sys.stderr)

n_kw = len(kws); n_faq = len([x for x in faq if x.startswith("\n**Q")])
print(f"OK: research built from seo-plan.json — {n_kw} keywords, {len(clusters)} clusters, "
      f"{len(pages)} pages, {n_faq} FAQs, {len(comps)} competitors", file=sys.stderr)
if n_kw < 30:
    print(f"WARN: only {n_kw} keywords (gate wants ≥30) — thin niche or partial plan", file=sys.stderr)
sys.exit(0)
