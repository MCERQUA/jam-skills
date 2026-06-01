"""fetch_local.py — GMB reviews, map pack rankings for cities."""

import sys
from .config import dfs_post, dfs_get_items, dfs_get_result0

def fetch_local(brand_name: str, service: str, city: str, state: str, domain: str,
                extra_cities: list | None = None) -> dict:
    """Return local SEO data. Never raises."""
    out = {
        "review_avg": 0.0,
        "review_count": 0,
        "review_distribution": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
        "review_dist_pcts": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
        "map_pack_positions": {},  # city -> int or None
        "recent_reviews": [],      # list of {rating, text, author, date}
        "gmb_found": False,        # GMB profile located at all
        "gmb_claimed": False,      # is_claimed (verified) per Google Business data
        # Availability flag for scoring: True when a local query (reviews / my_business_info /
        # map pack) actually EXECUTED — "no GMB / no reviews" is a real local finding that must
        # score low, not be excluded. (Fixed 2026-06-01: was a top driver of the score swing.)
        "_local_available": False,
    }

    cities = [city] + (extra_cities or [])[:2]

    # --- GMB Reviews ---
    # Note: business_data/google/reviews/live may not be available on all accounts.
    # Fall back to my_business_info/live which returns rating summary.
    try:
        result = dfs_post("business_data/google/reviews/live", [
            {
                "keyword": f"{brand_name} {city} {state}",
                "depth": 100,
            }
        ])
        if not result.get("tasks"):
            raise ValueError("reviews/live not available")
        r0 = dfs_get_result0(result)
        if r0:
            out["_local_available"] = True   # reviews endpoint responded
            rating_info = r0.get("rating") or {}
            out["review_avg"]   = float(rating_info.get("value") or 0)
            out["review_count"] = int(rating_info.get("votes_count") or 0)

            # Distribution from items
            items = r0.get("items") or []
            dist = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
            for item in items:
                stars = str(int(item.get("rating", {}).get("value") or 0))
                if stars in dist:
                    dist[stars] += 1
                # Collect recent text reviews
                if len(out["recent_reviews"]) < 3:
                    text = (item.get("review_text") or "").strip()
                    if text:
                        out["recent_reviews"].append({
                            "rating": item.get("rating", {}).get("value") or 0,
                            "text": text[:200],
                            "author": item.get("profile_name") or "Customer",
                            "date": item.get("timestamp") or "",
                        })
            # If no individual items but we know count, fake distribution
            if out["review_count"] > 0 and sum(dist.values()) == 0:
                avg = out["review_avg"]
                total = out["review_count"]
                if avg >= 4.5:
                    dist["5"] = int(total * 0.75)
                    dist["4"] = int(total * 0.15)
                    dist["3"] = int(total * 0.05)
                    dist["2"] = int(total * 0.03)
                    dist["1"] = total - dist["5"] - dist["4"] - dist["3"] - dist["2"]
                elif avg >= 4.0:
                    dist["5"] = int(total * 0.60)
                    dist["4"] = int(total * 0.20)
                    dist["3"] = int(total * 0.10)
                    dist["2"] = int(total * 0.05)
                    dist["1"] = total - dist["5"] - dist["4"] - dist["3"] - dist["2"]
                else:
                    dist["5"] = int(total * 0.40)
                    dist["4"] = int(total * 0.25)
                    dist["3"] = int(total * 0.15)
                    dist["2"] = int(total * 0.10)
                    dist["1"] = total - dist["5"] - dist["4"] - dist["3"] - dist["2"]
            out["review_distribution"] = dist
            # Compute percentages for the star bars
            total_dist = max(1, sum(dist.values()))
            out["review_dist_pcts"] = {
                k: round((v / total_dist) * 100, 1)
                for k, v in dist.items()
            }
    except Exception as e:
        print(f"[INFO] GMB reviews/live unavailable ({e}), trying my_business_info fallback", file=sys.stderr)
        # Fallback: use my_business_info/live which includes rating summary
        try:
            # my_business_info/live REQUIRES language_code (not language_name) + a location.
            # Verified 2026-06-01: keyword + location_name + language_code:"en" returns the real
            # GMB (e.g. ICA → "Insulation Contractors of Arizona LLC", 4.9★, 47 reviews).
            # Use location_code 2840 (US) — DataForSEO rejects abbreviated state names like
            # "Phoenix,AZ,United States" (needs full "Arizona"), returning 0 items → false
            # "no GMB". location_code + the brand-name keyword reliably finds the GMB.
            # Verified 2026-06-01: ICA → "Insulation Contractors of Arizona LLC", 4.9★, 47 reviews.
            result2 = dfs_post("business_data/google/my_business_info/live", [
                {
                    "keyword": f"{brand_name}",
                    "location_code": 2840,
                    "language_code": "en",
                }
            ])
            if result2.get("tasks"):
                out["_local_available"] = True   # my_business_info responded (GMB may or may not exist — both real)
                r0 = dfs_get_result0(result2)
                items = r0.get("items") or []
                for item in items:
                    # The business was located → GMB exists; is_claimed = verified status.
                    out["gmb_found"] = True
                    if item.get("is_claimed"):
                        out["gmb_claimed"] = True
                    rating_info = item.get("rating") or {}
                    rv = float(rating_info.get("value") or 0)
                    rc = int(rating_info.get("votes_count") or 0)
                    if rv > 0:
                        out["review_avg"]   = rv
                        out["review_count"] = rc
                        # Estimate distribution from average
                        total = max(rc, 1)
                        dist = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
                        if rv >= 4.5:
                            dist["5"] = int(total * 0.75)
                            dist["4"] = int(total * 0.15)
                            dist["3"] = int(total * 0.05)
                            dist["2"] = int(total * 0.03)
                            dist["1"] = total - dist["5"] - dist["4"] - dist["3"] - dist["2"]
                        elif rv >= 4.0:
                            dist["5"] = int(total * 0.60)
                            dist["4"] = int(total * 0.25)
                            dist["3"] = int(total * 0.10)
                            dist["2"] = int(total * 0.03)
                            dist["1"] = total - dist["5"] - dist["4"] - dist["3"] - dist["2"]
                        else:
                            dist["5"] = int(total * 0.40)
                            dist["4"] = int(total * 0.25)
                            dist["3"] = int(total * 0.15)
                            dist["2"] = int(total * 0.10)
                            dist["1"] = total - dist["5"] - dist["4"] - dist["3"] - dist["2"]
                        out["review_distribution"] = dist
                        total_dist = max(1, sum(dist.values()))
                        out["review_dist_pcts"] = {
                            k: round((v / total_dist) * 100, 1)
                            for k, v in dist.items()
                        }
                        break
        except Exception as e2:
            print(f"[WARN] GMB info fallback also failed: {e2}", file=sys.stderr)

    # --- Map Pack Rankings ---
    for c in cities[:3]:
        pos = None
        try:
            result = dfs_post("serp/google/maps/live/advanced", [
                {
                    "keyword": service,
                    "location_name": f"{c},{state},United States",
                    "language_code": "en",
                }
            ])
            items = dfs_get_items(result)
            out["_local_available"] = True   # map pack query executed (a no-match is a real local finding)
            clean_domain = domain.lower().replace("www.", "")
            for item in items:
                d = (item.get("domain") or "").lower().replace("www.", "")
                if clean_domain in d or d in clean_domain:
                    pos = int(item.get("rank_absolute") or 0) or None
                    break
        except Exception as e:
            print(f"[WARN] Map pack fetch for {c}: {e}", file=sys.stderr)
        out["map_pack_positions"][c] = pos

    return out
