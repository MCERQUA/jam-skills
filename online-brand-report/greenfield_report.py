#!/usr/bin/env python3
"""greenfield_report.py — CLI entry for the no-website ("greenfield") brand report.

Called by jambot-brand-report-worker.sh when a prospect has a company NAME but no
domain (and domain discovery found nothing). Builds a real, data-driven "you have
the reputation but no website" report from live Google Places + geo-targeted SERP,
writes the HTML to --out, and (optionally) writes the public URL + metadata back
into client-knowledge.json.

Fail-soft contract: prints a status line and exits 0 on a successful render; exits
non-zero ONLY on a hard failure (no HTML written), so the worker can fall back to
its placeholder heredoc. Generation errors inside build/render are caught and still
produce a sane minimal report (exit 0) rather than crashing the pipeline.

Usage:
  python3 greenfield_report.py \
      --name "Talk of the Town" --city "Bowmanville" --region "Ontario" \
      --gl ca --out /var/www/start-jam-bot/<slug>/index.html \
      [--url https://start.jam-bot.com/<slug>] \
      [--client-knowledge-path /path/to/client-knowledge.json]
"""

import argparse
import datetime
import json
import os
import sys

# Allow running both as a module and as a standalone file.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.greenfield import build_greenfield_report, render_greenfield  # noqa: E402


def _minimal_fallback_html(name, city, region) -> str:
    """Last-resort sane report if build/render both blow up — still better than the
    near-empty placeholder, and the worker contract stays intact (HTML written)."""
    loc = ", ".join(p for p in (city, region) if p)
    n = (name or "Your Business")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{n} — Brand Snapshot</title>
<style>body{{font-family:system-ui,Arial,sans-serif;max-width:640px;margin:48px auto;
padding:0 22px;line-height:1.6;color:#0f172a}}h1{{color:#0b3d2e}}.box{{background:#f1f5f4;
border:1px solid #dbe7e2;border-radius:12px;padding:20px;margin:18px 0}}</style></head>
<body><h1>{n}</h1><p>{loc}</p>
<div class="box"><strong>You have the reputation — not the website.</strong>
<p>{n} has a real local presence, but no website means you can't be found in Google
search the way customers look for you. Your JamBot build will turn that reputation
into a site that ranks and converts.</p></div>
<p>Head back to your text thread to keep going.</p></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--region", default="")
    ap.add_argument("--gl", default="us")
    ap.add_argument("--out", required=True, help="HTML output path")
    ap.add_argument("--url", default="", help="public URL to write back to client-knowledge")
    ap.add_argument("--client-knowledge-path", default="")
    args = ap.parse_args()

    html_out = ""
    verdict = ""
    competitors = []
    try:
        data = build_greenfield_report(args.name, args.city, args.region, gl=args.gl)
        html_out = render_greenfield(data)
        verdict = data.get("verdict", "")
        competitors = [c.get("domain") for c in (data.get("top_competitors") or [])]
    except Exception as e:
        print(f"[WARN] greenfield build/render failed ({e}) — minimal fallback", file=sys.stderr)
        html_out = ""

    if not html_out or "<html" not in html_out.lower():
        html_out = _minimal_fallback_html(args.name, args.city, args.region)

    try:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            f.write(html_out)
    except Exception as e:
        print(f"[ERROR] greenfield: could not write {args.out}: {e}", file=sys.stderr)
        return 1   # hard failure → worker falls back

    # Write-back to client-knowledge.json (best-effort, never fatal).
    if args.client_knowledge_path and args.url:
        try:
            with open(args.client_knowledge_path) as f:
                ck = json.load(f)
            ck["brand_report_url"] = args.url
            ck["brand_report_generated_at"] = datetime.datetime.now(
                datetime.timezone.utc).isoformat()
            ck["brand_report_kind"] = "greenfield-no-domain"
            with open(args.client_knowledge_path, "w") as f:
                json.dump(ck, f, indent=2)
        except Exception as e:
            print(f"[WARN] greenfield: client-knowledge writeback failed: {e}", file=sys.stderr)

    print(f"[OK] greenfield report -> {args.out}")
    if verdict:
        print(f"[VERDICT] {verdict}")
    if competitors:
        print(f"[COMPETITORS] {', '.join(competitors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
