"""fetch_web.py — Lighthouse scores + Core Web Vitals via DataForSEO OnPage."""

import sys
from .config import dfs_post, dfs_get_result0

def _band_lcp(lcp_s: float) -> str:
    if lcp_s <= 2.5:  return "good"
    if lcp_s <= 4.0:  return "warn"
    return "bad"

def _band_cls(cls: float) -> str:
    if cls <= 0.1:   return "good"
    if cls <= 0.25:  return "warn"
    return "bad"

def _band_tbt(tbt_ms: float) -> str:
    if tbt_ms <= 200:  return "good"
    if tbt_ms <= 600:  return "warn"
    return "bad"

def _lh_color(score: int) -> str:
    if score >= 90: return "good"
    if score >= 50: return "warn"
    return "bad"

def fetch_web(domain: str) -> dict:
    """Return Lighthouse + CWV data. Never raises."""
    out = {
        "lh_performance": 0,
        "lh_accessibility": 0,
        "lh_best_practices": 0,
        "lh_seo": 0,
        "lcp_s": 0.0,
        "lcp_display": "N/A",
        "lcp_band": "bad",
        "cls": 0.0,
        "cls_display": "N/A",
        "cls_band": "bad",
        "tbt_ms": 0.0,
        "tbt_display": "N/A",
        "tbt_band": "bad",
        # gauge percentages 0-100 for chart.js doughnut
        "lcp_gauge_pct": 0,
        "fid_gauge_pct": 0,
        "cls_gauge_pct": 0,
        # Availability flag for scoring — True when Lighthouse (or the instant_pages fallback)
        # actually returned data. (Fixed 2026-06-01: stops the score swinging on flaky endpoints.)
        "_web_available": False,
        # Per-component "was this actually measured?" flags (added 2026-06-16). A failed
        # live Lighthouse run leaves perf/a11y/best-practices/CWV at 0 — those zeros are
        # NOT real scores. The instant_pages fallback recovers ONLY a heuristic SEO score.
        # score.py renormalizes the web dimension over measured components; render.py shows
        # "Not measured" instead of fabricating 0/100 bars + "Poor" CWV + a fake a11y finding.
        "_lh_perf_measured": False,
        "_lh_a11y_measured": False,
        "_lh_bp_measured":   False,
        "_lh_seo_measured":  False,
        "_lh_cwv_measured":  False,
    }

    try:
        # Correct endpoint is /live/json — the old /live path 404'd, leaving the web
        # section empty. /live/json returns 20000 with real Lighthouse data. (Fixed 2026-06-01.)
        result = dfs_post("on_page/lighthouse/live/json", [
            {"url": f"https://{domain}", "for_mobile": False}
        ])
        # dfs_post returns {} on error (no raise) — check for valid response
        if not result.get("tasks"):
            raise ValueError("Lighthouse endpoint unavailable or not subscribed")
        r0 = dfs_get_result0(result)
        categories = r0.get("categories") or {}
        audits     = r0.get("audits") or {}
        out["_web_available"] = True   # Lighthouse responded
        # Real live Lighthouse run — every component is genuinely measured.
        out["_lh_perf_measured"] = True
        out["_lh_a11y_measured"] = True
        out["_lh_bp_measured"]   = True
        out["_lh_seo_measured"]  = True
        out["_lh_cwv_measured"]  = True

        def _score(cat: str) -> int:
            s = (categories.get(cat) or {}).get("score")
            if s is None: return 0
            return int(float(s) * 100)

        out["lh_performance"]   = _score("performance")
        out["lh_accessibility"] = _score("accessibility")
        out["lh_best_practices"]= _score("best-practices")
        out["lh_seo"]           = _score("seo")

        # LCP
        lcp_audit = audits.get("largest-contentful-paint") or {}
        lcp_ms = (lcp_audit.get("numericValue") or 0)
        lcp_s  = round(lcp_ms / 1000, 2)
        out["lcp_s"]        = lcp_s
        out["lcp_display"]  = f"{lcp_s}s"
        out["lcp_band"]     = _band_lcp(lcp_s)
        # Map to 0-100 for gauge (invert: 0s=100, 4s+=0)
        out["lcp_gauge_pct"] = max(0, int(100 - (lcp_s / 4.0) * 100))

        # CLS
        cls_audit = audits.get("cumulative-layout-shift") or {}
        cls = round(float(cls_audit.get("numericValue") or 0), 3)
        out["cls"]          = cls
        out["cls_display"]  = str(cls)
        out["cls_band"]     = _band_cls(cls)
        out["cls_gauge_pct"]= max(0, int(100 - (cls / 0.25) * 100))

        # TBT
        tbt_audit = audits.get("total-blocking-time") or {}
        tbt_ms = float(tbt_audit.get("numericValue") or 0)
        out["tbt_ms"]       = tbt_ms
        out["tbt_display"]  = f"{int(tbt_ms)}ms"
        out["tbt_band"]     = _band_tbt(tbt_ms)
        out["fid_gauge_pct"]= max(0, int(100 - (tbt_ms / 600) * 100))

    except Exception as e:
        print(f"[INFO] Lighthouse unavailable ({e}), trying instant_pages fallback", file=sys.stderr)
        # Fallback: on_page/instant_pages — gives us SEO metadata to at least partially score
        try:
            result2 = dfs_post("on_page/instant_pages", [
                {
                    "url": f"https://{domain}",
                    "load_resources": False,
                    "enable_javascript": False,
                }
            ])
            from .config import dfs_get_items as _get_items
            items = _get_items(result2)
            if items:
                meta = (items[0].get("meta") or {})
                # Use heuristic scores based on what we find
                has_title       = bool(meta.get("title"))
                has_description = bool(meta.get("description"))
                has_canonical   = bool(meta.get("canonical"))
                has_schema      = bool(meta.get("structured_data"))
                seo_score = sum([
                    has_title * 30,
                    has_description * 30,
                    has_canonical * 20,
                    has_schema * 20,
                ])
                out["lh_seo"] = seo_score
                # Flag that web data is partial
                out["lh_data_source"] = "instant_pages_fallback"
                out["_web_available"] = True   # partial web data still beats excluding the dimension
                # ONLY the SEO heuristic is real here. Performance / Accessibility /
                # Best-Practices / Core Web Vitals were NOT measured — leave their
                # measured-flags False so score.py and render.py don't treat the 0s as real.
                out["_lh_seo_measured"] = True
        except Exception as e2:
            print(f"[WARN] instant_pages fallback also failed: {e2}", file=sys.stderr)

    return out
