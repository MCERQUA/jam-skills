#!/usr/bin/env python3
"""
prep_context.py — build the generation CONTEXT a cheap model needs to pass the gates:
  - authority.json : a list of PRE-VETTED outbound URLs (HTTP 200 + DR >= threshold),
                     so whatever the model cites is guaranteed high-authority + live.
  - internal.json  : {"money":[{path,label}], "blogs":[{path,title}]} pulled from the
                     config money_pages + the existing posts in the repo blog_dir.

Authority candidates come from (in order): the Tier-2 brain authority-sources.json
(already vetted), plus a built-in insurance authority seed pool. Each candidate is
HTTP-checked live and DR-checked here so the downstream gate is a re-confirmation,
not a coin flip.

Usage: prep_context.py <config.json> <topic_json> <out_dir>
Writes <out_dir>/authority.json and <out_dir>/internal.json. Prints a summary.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

# Built-in high-authority insurance / regulatory seed pool (DR 70+ / gov).
SEED_AUTHORITY = [
    "https://www.iii.org/article/what-is-business-insurance",
    "https://www.iii.org/article/commercial-general-liability-insurance",
    "https://www.sba.gov/business-guide/launch-your-business/get-business-insurance",
    "https://www.osha.gov/businesscase",
    "https://www.cpsc.gov/Business--Manufacturing/Recall-Guidance",
    "https://www.ftc.gov/business-guidance",
    "https://www.naic.org/consumer.htm",
    "https://www.irs.gov/businesses/small-businesses-self-employed",
    "https://consumer.ftc.gov/",
    "https://www.cpsc.gov/Recalls",
    "https://www.iii.org/article/business-liability-insurance",
]
UA = "Mozilla/5.0 (compatible; JamBot-BlogFactory/1.0)"


def http_ok(url, timeout=20):
    try:
        out = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-L", "--max-time", str(timeout),
             "-A", UA, "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=timeout + 5).stdout.strip()
        return out and out[0] in "23"
    except Exception:
        return False


def registrable(host):
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def dr_of(domain, timeout=20):
    url = ("https://api.ahrefs.com/v3/public/domain-rating-free?target="
           + urllib.parse.quote(domain) + "&output=json")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        dr = data.get("domain_rating", {})
        return float(dr.get("domain_rating", 0)) if isinstance(dr, dict) else float(dr or 0)
    except Exception:
        return -1.0


def brain_authority(cfg):
    p = os.path.join(cfg.get("knowledge_base", ""), "authority-sources.json")
    urls = []
    if os.path.isfile(p):
        try:
            data = json.load(open(p))
            items = data if isinstance(data, list) else data.get("sources", [])
            for it in items:
                u = it if isinstance(it, str) else it.get("url")
                if u:
                    urls.append(u)
        except Exception:
            pass
    return urls


def existing_blogs(cfg):
    blog = os.path.join(cfg["repo_path"], cfg.get("blog_dir", "content/blog"))
    prefix = cfg.get("blog_path_prefix", "/blog/")
    out = []
    if os.path.isdir(blog):
        for f in sorted(os.listdir(blog)):
            if f.endswith((".mdx", ".md")):
                slug = re.sub(r"\.(mdx|md)$", "", f)
                title = slug.replace("-", " ").title()
                # try to read real title from frontmatter
                try:
                    raw = open(os.path.join(blog, f), encoding="utf-8").read()
                    m = re.search(r'^title:\s*"?([^"\n]+)"?', raw, re.MULTILINE)
                    if m:
                        title = m.group(1).strip()
                except Exception:
                    pass
                out.append({"path": f"{prefix}{slug}", "title": title})
    return out


def main():
    cfg = json.load(open(sys.argv[1]))
    json.load(open(sys.argv[2]))  # topic (reserved for future topical filtering)
    out_dir = sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    dr_min = cfg.get("gates", {}).get("authority_dr_min", 60)
    need = cfg.get("gates", {}).get("min_outbound", 4)

    # config-supplied seeds (per-niche) take priority, then brain, then built-in pool
    cfg_seeds = cfg.get("authority_seed_urls", [])
    candidates = cfg_seeds + brain_authority(cfg) + SEED_AUTHORITY
    seen, vetted = set(), []
    dr_cache = {}
    for u in candidates:
        if u in seen:
            continue
        seen.add(u)
        host = urllib.parse.urlparse(u).netloc.lower()
        reg = registrable(host)
        # authority by allowlist token or DR
        allow = any(tok in host for tok in
                    cfg.get("gates", {}).get("authority_allowlist", []))
        if not allow:
            if reg not in dr_cache:
                dr_cache[reg] = dr_of(reg)
            if dr_cache[reg] < dr_min:
                continue
        if not http_ok(u):
            continue
        vetted.append(u)
        if len(vetted) >= max(need + 2, 6):  # a couple spare so the model has choices
            break

    internal = {
        "money": [{"path": p, "label": p.strip("/").replace("-", " ").title() or "Home"}
                  for p in cfg.get("money_pages", [])],
        "blogs": existing_blogs(cfg),
    }

    json.dump(vetted, open(os.path.join(out_dir, "authority.json"), "w"), indent=2)
    json.dump(internal, open(os.path.join(out_dir, "internal.json"), "w"), indent=2)
    print(f"prep_context: {len(vetted)} vetted authority URLs, "
          f"{len(internal['money'])} money pages, {len(internal['blogs'])} existing blogs")
    if len(vetted) < need:
        print(f"prep_context: WARNING — only {len(vetted)} vetted < min_outbound {need}",
              file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
