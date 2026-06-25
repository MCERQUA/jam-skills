#!/usr/bin/env python3
"""
topic-pick.py — pick the NEXT blog topic for a client, deduped against published.

Selection order (first non-empty wins):
  1. Tier-2 brain `topical-map.json` -> next_topics[] / gaps[] (recomputed each run)
  2. A content-plan file `<knowledge_base>/blog-plan.json` (operator-curated list)
  3. DataForSEO keyword_suggestions for the site's seed keyword (live, real demand)
  4. A built-in seed list derived from the site brand (last resort)

Dedup: never re-pick a topic whose slug already exists in the blog_dir OR is marked
published in topical-map.json.

Usage:  topic-pick.py <config.json> [--seed "<seed keyword>"]
Output: prints ONE JSON object: {"topic":..., "target_keyword":..., "slug":..., "source":...}
        exits 0 on success, 3 if nothing left to pick.

NO LLM — pure data selection. (The brain/plan are produced by the pipeline's own
distill/Completion steps and by DataForSEO, all deterministic.)
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def existing_slugs(cfg):
    slugs = set()
    blog = os.path.join(cfg["repo_path"], cfg.get("blog_dir", "content/blog"))
    if os.path.isdir(blog):
        for f in os.listdir(blog):
            if f.endswith((".mdx", ".md")):
                slugs.add(re.sub(r"\.(mdx|md)$", "", f))
    # also slugs already in topical-map
    tm = os.path.join(cfg.get("knowledge_base", ""), "topical-map.json")
    if os.path.isfile(tm):
        try:
            data = json.load(open(tm))
            for a in data.get("articles", []):
                if a.get("slug"):
                    slugs.add(a["slug"])
        except Exception:
            pass
    return slugs


def from_brain(cfg, taken):
    tm = os.path.join(cfg.get("knowledge_base", ""), "topical-map.json")
    if not os.path.isfile(tm):
        return None
    try:
        data = json.load(open(tm))
    except Exception:
        return None
    for key in ("next_topics", "gaps"):
        for t in data.get(key, []):
            kw = t if isinstance(t, str) else t.get("keyword") or t.get("topic")
            if not kw:
                continue
            s = slugify(kw)
            if s not in taken:
                return {"topic": kw, "target_keyword": kw, "slug": s,
                        "source": f"brain:{key}"}
    return None


def from_plan(cfg, taken):
    plan = os.path.join(cfg.get("knowledge_base", ""), "blog-plan.json")
    if not os.path.isfile(plan):
        return None
    try:
        items = json.load(open(plan))
    except Exception:
        return None
    if isinstance(items, dict):
        items = items.get("topics", [])
    for t in items:
        kw = t if isinstance(t, str) else (t.get("target_keyword") or t.get("topic"))
        if not kw:
            continue
        s = slugify(kw)
        if s not in taken:
            topic = t.get("topic", kw) if isinstance(t, dict) else kw
            return {"topic": topic, "target_keyword": kw, "slug": s,
                    "source": "blog-plan.json"}
    return None


def from_dataforseo(cfg, seed, taken):
    if not seed:
        return None
    login = os.environ.get("DATAFORSEO_LOGIN")
    pw = os.environ.get("DATAFORSEO_PASSWORD")
    if not (login and pw):
        return None
    import base64
    auth = base64.b64encode(f"{login}:{pw}".encode()).decode()
    payload = json.dumps([{
        "keyword": seed,
        "location_name": cfg.get("location", "United States"),
        "language_name": "English",
        "limit": 50,
    }])
    try:
        out = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_suggestions/live",
            "-H", f"Authorization: Basic {auth}",
            "-H", "Content-Type: application/json",
            "-d", payload,
        ], capture_output=True, text=True, timeout=60).stdout
        data = json.loads(out)
        items = data["tasks"][0]["result"][0]["items"]
    except Exception:
        return None
    # rank by search volume desc; skip taken
    ranked = []
    for it in items:
        kw = it.get("keyword")
        ki = it.get("keyword_info") or {}
        vol = ki.get("search_volume") or 0
        if kw:
            ranked.append((vol, kw))
    ranked.sort(reverse=True)
    for vol, kw in ranked:
        s = slugify(kw)
        if s not in taken and len(kw.split()) >= 2:
            return {"topic": kw, "target_keyword": kw, "slug": s,
                    "source": f"dataforseo(vol={vol})"}
    return None


def main():
    if len(sys.argv) < 2:
        print("usage: topic-pick.py <config.json> [--seed '<kw>']", file=sys.stderr)
        sys.exit(2)
    cfg = json.load(open(sys.argv[1]))
    seed = ""
    if "--seed" in sys.argv:
        seed = sys.argv[sys.argv.index("--seed") + 1]

    taken = existing_slugs(cfg)

    for picker in (lambda: from_brain(cfg, taken),
                   lambda: from_plan(cfg, taken),
                   lambda: from_dataforseo(cfg, seed, taken)):
        res = picker()
        if res:
            print(json.dumps(res))
            sys.exit(0)

    print(json.dumps({"error": "no topic available — brain/plan empty, "
                      "no DataForSEO seed, all suggestions already published"}),
          file=sys.stderr)
    sys.exit(3)


if __name__ == "__main__":
    main()
