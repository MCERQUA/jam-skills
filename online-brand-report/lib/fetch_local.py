"""fetch_local.py — GMB reviews, map pack rankings, GBP Q&A + Posts depth."""

import sys
from .config import dfs_post, dfs_get_items, dfs_get_result0


def _fetch_gbp_qna(brand_name: str, city: str, state: str) -> dict:
    """Fetch GBP Q&A via business_data/google/questions_and_answers/live. Never raises.

    Result paths (confirmed from DFS docs):
      result[0].items[]                    answered questions
      result[0].items_without_answers[]    unanswered questions
      items[].question_text                question body (current, post-edit)
      items[].items[].answer_text          top answer body
      items[].time_ago                     relative post time
      items[].url                          direct Q&A URL on Google

    ASSUMPTION A: keyword is brand-name + city/state; no CID/place_id available here.
    ASSUMPTION B: items_without_answers[] field name — confirmed from docs; flag if absent.
    """
    out = {
        "gbp_questions":      [],
        "gbp_qna_count":      0,
        "gbp_qna_unanswered": 0,
        "gbp_qna_error":      None,
    }
    try:
        result = dfs_post("business_data/google/questions_and_answers/live", [
            {
                "keyword":       f"{brand_name} {city} {state}",
                "location_code": 2840,
                "language_code": "en",
                "depth":         20,
            }
        ])
        r0 = dfs_get_result0(result)
        if not r0:
            task_msg = ""
            try:
                task_msg = result.get("tasks", [{}])[0].get("status_message", "")
            except Exception:
                pass
            out["gbp_qna_error"] = (
                f"no Q&A data (DFS: {task_msg})" if task_msg else "no Q&A data"
            )
            return out

        answered   = r0.get("items") or []
        unanswered = r0.get("items_without_answers") or []

        out["gbp_qna_count"]      = len(answered) + len(unanswered)
        out["gbp_qna_unanswered"] = len(unanswered)

        for item in answered[:5]:
            q_text = (
                item.get("question_text") or item.get("original_question_text") or ""
            ).strip()
            ans_items   = item.get("items") or []
            top_answer  = ""
            answered_by = ""
            if ans_items:
                top_answer  = (ans_items[0].get("answer_text") or "").strip()[:250]
                answered_by = ans_items[0].get("profile_name") or ""
            out["gbp_questions"].append({
                "question":    q_text[:200],
                "top_answer":  top_answer,
                "answered_by": answered_by,
                "date":        item.get("time_ago") or item.get("timestamp") or "",
                "url":         item.get("url") or "",
            })

        if not answered and not unanswered:
            out["gbp_qna_error"] = "no Q&A found on profile"

    except Exception as e:
        print(f"[WARN] GBP Q&A fetch failed: {e}", file=sys.stderr)
        out["gbp_qna_error"] = str(e)

    return out


def _fetch_gbp_posts(brand_name: str, city: str, state: str) -> dict:
    """Fetch GBP posts via business_data/google/my_business_updates/live. Never raises.

    ASSUMPTION C: DFS docs confirm only task_post/task_get (async) for my_business_updates
    — no live endpoint found. Attempting live anyway (mirrors reviews/live graceful-fail
    pattern). Will set gbp_posts_error if unavailable. Host must confirm; if async only,
    task_post + delayed task_get is the fallback (not implemented here — needs polling).

    Result paths (ASSUMPTION D — inferred from reviews/my_business_info patterns):
      result[0].items[]          post objects
      items[].post_text          post body
      items[].post_date          date string: mm/dd/yyyy hh:mm:ss
      items[].timestamp          UTC timestamp
      items[].url                direct URL to post
      items[].type               expected: google_business_post
    """
    out = {
        "gbp_posts":       [],
        "gbp_posts_count": 0,
        "gbp_posts_error": None,
    }
    # Host live-check 2026-06-14: business_data/google/my_business_updates/live returns
    # 404 — the sync/live variant does not exist (DFS only offers task_post/task_get for
    # GBP updates, per the worker's flagged ASSUMPTION C). Short-circuit to "unavailable"
    # so we don't make 3 failed HTTP calls every report run. Q&A (confirmed endpoint) is
    # unaffected. Re-enable here if/when an async posts lane is wired.
    out["gbp_posts_error"] = "posts endpoint unavailable (my_business_updates has no live variant)"
    return out
    try:  # noqa: unreachable — kept for the async re-enable path
        result = dfs_post("business_data/google/my_business_updates/live", [
            {
                "keyword":       f"{brand_name} {city} {state}",
                "location_code": 2840,
                "language_code": "en",
                "depth":         10,
            }
        ])
        items = dfs_get_items(result)
        out["gbp_posts_count"] = len(items)
        for item in items[:5]:
            out["gbp_posts"].append({
                "text": (item.get("post_text") or "").strip()[:300],
                "date": item.get("post_date") or item.get("timestamp") or "",
                "url":  item.get("url") or "",
                "type": item.get("type") or "google_business_post",
            })
        if not items:
            task_msg = ""
            try:
                task_msg = result.get("tasks", [{}])[0].get("status_message", "")
            except Exception:
                pass
            out["gbp_posts_error"] = (
                f"no posts found (DFS: {task_msg})" if task_msg else "no GBP posts found"
            )

    except Exception as e:
        print(f"[WARN] GBP posts fetch failed: {e}", file=sys.stderr)
        out["gbp_posts_error"] = str(e)

    return out

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
        # GBP depth — Q&A + Posts (populated at end of this function)
        "gbp_questions":      [],  # list of {question, top_answer, answered_by, date, url}
        "gbp_qna_count":      0,   # total Q count (answered + unanswered)
        "gbp_qna_unanswered": 0,   # unanswered count
        "gbp_qna_error":      None,
        "gbp_posts":          [],  # list of {text, date, url, type}
        "gbp_posts_count":    0,
        "gbp_posts_error":    None,
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
                    # Real NAP straight from the GMB profile (ica-voice 2026-06-01 wanted these
                    # in the report). Stored as both gmb_* (for the local section) and bare
                    # phone/address (generate.py falls back to these when --phone/--address absent).
                    if item.get("phone"):
                        out["gmb_phone"] = out["phone"] = item["phone"]
                    if item.get("address"):
                        out["gmb_address"] = out["address"] = item["address"]
                    if item.get("category"):
                        out["gmb_category"] = item["category"]
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

    # --- GBP Q&A (business_data/google/questions_and_answers/live) ---
    out.update(_fetch_gbp_qna(brand_name, city, state))

    # --- GBP Posts/Updates (business_data/google/my_business_updates/live) ---
    out.update(_fetch_gbp_posts(brand_name, city, state))

    return out
