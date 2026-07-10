"""fetch_local.py — GMB reviews, map pack rankings, GBP Q&A + Posts depth."""

import sys
from .config import dfs_post, dfs_get_items, dfs_get_result0
import re

# US state abbrev→name, for validating that a matched GMB is actually in the requested
# city/state. Without this, a name search ("<brand> <city> <state>") can return a
# same-named business in another state (e.g. a Houston "EZ Roof" matched for a Sacramento
# query), whose reviews/rating then contaminate the report and inflate the local score.
_US_STATES = {
    "AL":"alabama","AK":"alaska","AZ":"arizona","AR":"arkansas","CA":"california","CO":"colorado",
    "CT":"connecticut","DE":"delaware","FL":"florida","GA":"georgia","HI":"hawaii","ID":"idaho",
    "IL":"illinois","IN":"indiana","IA":"iowa","KS":"kansas","KY":"kentucky","LA":"louisiana",
    "ME":"maine","MD":"maryland","MA":"massachusetts","MI":"michigan","MN":"minnesota","MS":"mississippi",
    "MO":"missouri","MT":"montana","NE":"nebraska","NV":"nevada","NH":"new hampshire","NJ":"new jersey",
    "NM":"new mexico","NY":"new york","NC":"north carolina","ND":"north dakota","OH":"ohio","OK":"oklahoma",
    "OR":"oregon","PA":"pennsylvania","RI":"rhode island","SC":"south carolina","SD":"south dakota",
    "TN":"tennessee","TX":"texas","UT":"utah","VT":"vermont","VA":"virginia","WA":"washington",
    "WV":"west virginia","WI":"wisconsin","WY":"wyoming","DC":"district of columbia",
}

# CA/region full-name → 2-letter abbreviation. Lets a province-GRANULARITY location
# (e.g. city='Ontario Canada', a province, not a city) confirm an in-province listing
# whose address writes 'ON', not 'Ontario'. Purely ADDITIVE to _loc_ok — the strict
# city-substring accept is unchanged, so real-city inputs still reject cross-city
# name-collisions exactly as before. (Added 2026-06-29.)
_PROVINCES = {
    "ontario":"on","quebec":"qc","québec":"qc","british columbia":"bc","alberta":"ab",
    "manitoba":"mb","saskatchewan":"sk","nova scotia":"ns","new brunswick":"nb",
    "newfoundland and labrador":"nl","newfoundland":"nl","prince edward island":"pe",
    "northwest territories":"nt","nunavut":"nu","yukon":"yt",
}
_GEO_FILLER = {"canada","usa","us","united","states","america"}

# state/province 2-letter abbrev → FULL name, for building a valid DataForSEO
# `location_name` ("North York,Ontario,Canada"). DataForSEO REJECTS abbreviated
# regions ("North York,ON,Canada" → 40501 Invalid Field: location_name → 0 items),
# which silently zeroed every Canadian (and abbreviated-US) map-pack lookup. (Added 2026-06-29.)
_REGION_FULL = {
    # Canada
    "on":"Ontario","qc":"Quebec","bc":"British Columbia","ab":"Alberta","mb":"Manitoba",
    "sk":"Saskatchewan","ns":"Nova Scotia","nb":"New Brunswick","nl":"Newfoundland and Labrador",
    "pe":"Prince Edward Island","nt":"Northwest Territories","nu":"Nunavut","yt":"Yukon",
    # United States
    "al":"Alabama","ak":"Alaska","az":"Arizona","ar":"Arkansas","ca":"California","co":"Colorado",
    "ct":"Connecticut","de":"Delaware","fl":"Florida","ga":"Georgia","hi":"Hawaii","id":"Idaho",
    "il":"Illinois","in":"Indiana","ia":"Iowa","ks":"Kansas","ky":"Kentucky","la":"Louisiana",
    "me":"Maine","md":"Maryland","ma":"Massachusetts","mi":"Michigan","mn":"Minnesota","ms":"Mississippi",
    "mo":"Missouri","mt":"Montana","ne":"Nebraska","nv":"Nevada","nh":"New Hampshire","nj":"New Jersey",
    "nm":"New Mexico","ny":"New York","nc":"North Carolina","nd":"North Dakota","oh":"Ohio","ok":"Oklahoma",
    "or":"Oregon","pa":"Pennsylvania","ri":"Rhode Island","sc":"South Carolina","sd":"South Dakota",
    "tn":"Tennessee","tx":"Texas","ut":"Utah","vt":"Vermont","va":"Virginia","wa":"Washington",
    "wv":"West Virginia","wi":"Wisconsin","wy":"Wyoming","dc":"District of Columbia",
}


def _full_region(state: str) -> str:
    """Full region name for a DataForSEO location_name. Accepts an abbreviation ('ON') or a
    full name ('Ontario') — returns the full name title-cased. '' if unknown/empty."""
    s = (state or "").strip()
    if not s:
        return ""
    if s.lower() in _REGION_FULL:           # 'ON' / 'on'
        return _REGION_FULL[s.lower()]
    return s                                 # already a full name ('Ontario')


def _map_location_name(city: str, state: str, country: str) -> str:
    """Build a DataForSEO-valid map-pack location_name. Uses the FULL region name (never the
    2-letter abbreviation, which DataForSEO rejects). Drops empty parts so 'City,,Country'
    never happens."""
    parts = [p for p in (city.strip() if city else "", _full_region(state), country) if p]
    return ",".join(parts)


def _domain_matches(item: dict, domain: str) -> bool:
    """True when a GMB listing's own website is the client's domain — the STRONGEST possible
    proof the listing is theirs, independent of city. Fixes the borough/municipality problem:
    a business that markets as 'Toronto' but whose GMB address reads the actual municipality
    ('North York') was wrongly rejected by the city-substring test, zeroing its real reviews.
    A website match is unambiguous, so it overrides the location check. (Added 2026-06-29.)"""
    d = (domain or "").lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/").split("/")[0]
    if not d:
        return False
    for k in ("domain", "url", "website"):
        v = item.get(k)
        if v and d in str(v).lower().replace("www.", ""):
            return True
    return False


def _region_granularity_ok(txt: str, city: str, state: str) -> bool:
    """ADDITIVE accept path for when the caller gave a PROVINCE/REGION as 'city' (no real
    city). Confirms only when the haystack carries that province's name or 2-letter
    abbreviation (as a standalone token). Returns False for a real-city input, so it never
    weakens the strict city check. Never accepts on a bare country word ('Canada')."""
    combo = f"{(city or '').lower()} {(state or '').lower()}"
    for full, ab in _PROVINCES.items():
        if full in combo and (full in txt or re.search(rf'\b{ab}\b', txt)):
            return True
    return False

def _loc_haystack(obj):
    """Lowercased location text from whatever address-ish fields a GMB object carries."""
    parts = []
    for k in ("address", "title", "sub_title", "snippet", "category"):
        v = obj.get(k)
        if isinstance(v, str):
            parts.append(v)
    ai = obj.get("address_info")
    if isinstance(ai, dict):
        for k in ("city", "region", "zip", "address", "borough"):
            v = ai.get(k)
            if isinstance(v, str):
                parts.append(v)
    return " ".join(parts).lower()

def _loc_ok(obj, city, state):
    """True only if the matched GMB positively matches the requested city/state. Rejects
    name-collision profiles from other locations. Conservative: if the object carries no
    location text at all, return False (a bare name match isn't proof it's the right business)."""
    txt = _loc_haystack(obj)
    if not txt.strip():
        return False
    cy = (city or "").strip().lower()
    st = (state or "").strip().upper()
    if cy:
        # City is the strong discriminator. Require it — a generic-named business in a
        # DIFFERENT city, even within the same state (e.g. Monterey Park vs Sacramento),
        # is not them. For a business with no GMB, no twin will be in-city → rejected.
        if cy in txt:
            return True
        # ADDITIVE: when 'city' is actually a province/region (e.g. 'Ontario Canada'),
        # the literal substring never matches a real city address — confirm at region
        # granularity instead so a valid in-province GMB isn't dropped. Real-city inputs
        # don't trigger this (the province check returns False), so cross-city collisions
        # are still rejected exactly as before.
        return _region_granularity_ok(txt, city, state)
    if st:
        full = _US_STATES.get(st, "")
        return bool(re.search(rf'\b{st.lower()}\b', txt) or (full and full in txt))
    return True  # nothing to validate against


def _fetch_gbp_qna(brand_name: str, city: str, state: str, location_code: int = 2840) -> dict:
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
                "location_code": location_code,
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


def _fetch_gbp_posts(brand_name: str, city: str, state: str, location_code: int = 2840) -> dict:
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
                "location_code": location_code,
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

def _fetch_reviews_async(brand_name: str, city: str, state: str, domain: str,
                         location_code: int = 2840, place_id: str = "") -> dict:
    """Recent review TEXT + the real star distribution via the ASYNC reviews task
    (business_data/google/reviews/task_post → task_get). The /live variant returns 404
    (does not exist) — but task_post/task_get IS subscribed and returns full review text,
    author, rating, and a votes/rating summary. Bounded poll; never raises. Returns
    {recent_reviews, review_avg, review_count, rating_distribution, _reviews_text_ok}."""
    import time as _t
    import requests as _rq
    from .config import dfs_auth_header
    out = {"recent_reviews": [], "review_avg": 0.0, "review_count": 0,
           "rating_distribution": None, "_reviews_text_ok": False}
    try:
        # Proven-working form: keyword + location_code (NOT place_id — that field is
        # rejected on this endpoint/plan with a misleading 40501). The brand+city+state
        # keyword reliably resolves to the right listing for review text.
        task = {"keyword": f"{brand_name} {city} {state}".strip(),
                "location_code": location_code, "language_code": "en", "depth": 30}
        rp = dfs_post("business_data/google/reviews/task_post", [task])
        t0 = (rp.get("tasks") or [{}])[0]
        tid = t0.get("id")
        if not tid or t0.get("status_code") not in (20100, 20000):
            print(f"[INFO] reviews task_post unavailable: {t0.get('status_code')} "
                  f"{t0.get('status_message')}", file=sys.stderr)
            return out
        # Poll task_get (GET) until ready — usually one ~8s cycle.
        url = f"https://api.dataforseo.com/v3/business_data/google/reviews/task_get/{tid}"
        hdrs = {"Authorization": dfs_auth_header()}
        res = {}
        for _ in range(8):
            _t.sleep(8)
            try:
                g = _rq.get(url, headers=hdrs, timeout=30).json()
            except Exception as _ge:
                print(f"[WARN] reviews task_get poll: {_ge}", file=sys.stderr)
                continue
            gt = (g.get("tasks") or [{}])[0]
            if gt.get("status_code") == 20000:
                res = (gt.get("result") or [{}])[0] or {}
                break
            if gt.get("status_code") not in (40601, 40602):  # 'task in queue/handed' codes → keep polling
                # any other terminal non-OK code → stop
                if gt.get("status_code") and gt.get("status_code") >= 40000 and gt.get("status_code") not in (40601, 40602):
                    print(f"[INFO] reviews task_get: {gt.get('status_code')} {gt.get('status_message')}", file=sys.stderr)
                    break
        if not res:
            return out
        ri = res.get("rating") or {}
        out["review_avg"]   = float(ri.get("value") or 0)
        out["review_count"] = int(ri.get("votes_count") or 0)
        items = res.get("items") or []
        dist = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
        for it in items:
            stars = str(int((it.get("rating") or {}).get("value") or 0))
            if stars in dist:
                dist[stars] += 1
            text = (it.get("review_text") or "").strip()
            if text and len(out["recent_reviews"]) < 3:
                out["recent_reviews"].append({
                    "rating": (it.get("rating") or {}).get("value") or 0,
                    "text":   text[:240],
                    "author": it.get("profile_name") or "Customer",
                    "date":   it.get("timestamp") or it.get("time_ago") or "",
                })
        if sum(dist.values()) > 0:
            out["rating_distribution"] = dist  # sampled distribution (real, from fetched items)
        out["_reviews_text_ok"] = bool(out["recent_reviews"])
        print(f"[INFO] reviews task: {out['review_avg']}★ ({out['review_count']}) "
              f"+ {len(out['recent_reviews'])} text snippets", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] reviews async fetch failed: {e}", file=sys.stderr)
    return out


def fetch_local(brand_name: str, service: str, city: str, state: str, domain: str,
                extra_cities: list | None = None, location_code: int = 2840) -> dict:
    """Return local SEO data. Never raises.

    location_code: DataForSEO country code threaded from generate.py (2840 US / 2124 CA) so
    GMB/Q&A/map-pack lookups target the right country for non-US businesses."""
    # Map the country code to the location_name suffix used by the map-pack endpoint
    # (which takes a location_name string, not a code). Defaults to US.
    _country_name = "Canada" if location_code == 2124 else "United States"
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
            # Reject a name-collision match (e.g. a same-named business in another state).
            # If the returned profile's location can't be confirmed as the requested city/
            # state, fall through to the location-scoped my_business_info fallback below.
            if not _loc_ok(r0, city, state):
                print(f"[INFO] reviews/live match '{r0.get('title','?')}' not confirmed in "
                      f"{city} {state} — rejecting name-collision, trying scoped fallback",
                      file=sys.stderr)
                raise ValueError("reviews/live location mismatch")
            rating_info = r0.get("rating") or {}
            out["review_avg"]   = float(rating_info.get("value") or 0)
            out["review_count"] = int(rating_info.get("votes_count") or 0)
            out["gmb_found"]    = True   # confirmed-local GMB with reviews

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
                    "location_code": location_code,
                    "language_code": "en",
                }
            ])
            if result2.get("tasks"):
                out["_local_available"] = True   # my_business_info responded (GMB may or may not exist — both real)
                r0 = dfs_get_result0(result2)
                items = r0.get("items") or []
                for item in items:
                    # Accept the listing when EITHER (a) its own website is the client domain
                    # — unambiguous proof it's theirs, overrides any city mismatch (fixes the
                    # 'markets as Toronto, GMB address says North York' borough problem), OR
                    # (b) the location text confirms the requested city/state. Otherwise reject
                    # the name-collision: a business with genuinely no GMB must score local ≈ 0,
                    # never inherit a same-named out-of-area profile's rating.
                    _dom_ok = _domain_matches(item, domain)
                    if not (_dom_ok or _loc_ok(item, city, state)):
                        print(f"[INFO] my_business_info match '{item.get('title', item.get('address','?'))}' "
                              f"not in {city} {state} and no domain match — skipping name-collision", file=sys.stderr)
                        continue
                    # The business was located → GMB exists; is_claimed = verified status.
                    out["gmb_found"] = True
                    if _dom_ok:
                        # Authoritative: the report's GMB confirmation gate must NOT zero a
                        # domain-verified listing even if the input city != the GMB municipality.
                        out["gmb_domain_verified"] = True
                    if item.get("place_id"):
                        out["gmb_place_id"] = item["place_id"]
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
                        # REAL star distribution straight from the GMB profile when present
                        # ({"1":1,"2":0,"3":1,"4":0,"5":27}) — no more faked estimates. Falls
                        # back to an average-based estimate only if Google didn't return one.
                        rdist = item.get("rating_distribution")
                        dist = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
                        if isinstance(rdist, dict) and any((rdist.get(k) or 0) for k in ("1","2","3","4","5")):
                            for k in ("1","2","3","4","5"):
                                dist[k] = int(rdist.get(k) or 0)
                            out["_review_dist_real"] = True
                        else:
                            total = max(rc, 1)
                            if rv >= 4.5:
                                dist["5"] = int(total * 0.75); dist["4"] = int(total * 0.15)
                                dist["3"] = int(total * 0.05); dist["2"] = int(total * 0.03)
                            elif rv >= 4.0:
                                dist["5"] = int(total * 0.60); dist["4"] = int(total * 0.25)
                                dist["3"] = int(total * 0.10); dist["2"] = int(total * 0.03)
                            else:
                                dist["5"] = int(total * 0.40); dist["4"] = int(total * 0.25)
                                dist["3"] = int(total * 0.15); dist["2"] = int(total * 0.10)
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
    # Two fixes (2026-06-29):
    #  1) location_name MUST use the full region name — '<City>,ON,Canada' returns
    #     40501 Invalid Field → 0 items → every Canadian/abbrev-US map-pack falsely
    #     read "not ranked". _map_location_name() expands 'ON'→'Ontario'.
    #  2) query a small VERTICAL keyword set, not just the single (often too-generic)
    #     detected service. We keep the BEST position per city and record which keyword
    #     earned it, so the real ranking shows.
    # Fix (2026-07-09): use service-intent modifiers (contractor/company/commercial/near me)
    #     instead of equipment/supplies/parts — those are irrelevant to service businesses
    #     and show up as displayed wins which confuses clients.
    base = (service or "").strip()
    _kw_candidates = []
    if base:
        _kw_candidates.append(base)
        low = base.lower()
        for mod in ("contractor", "company", "commercial", "near me"):
            if mod not in low:
                _kw_candidates.append(f"{base} {mod}")
    _kw_candidates = _kw_candidates[:4]
    clean_domain = domain.lower().replace("www.", "")
    map_rows = []
    for ci, c in enumerate(cities[:3]):
        loc_name = _map_location_name(c, state, _country_name)
        # primary city: try all candidate keywords; extra cities: base service only (cost-bounded)
        kws = _kw_candidates if ci == 0 else _kw_candidates[:1]
        best_pos, best_kw = None, base
        for kw in (kws or [base]):
            if not kw:
                continue
            pos = None
            try:
                result = dfs_post("serp/google/maps/live/advanced", [
                    {"keyword": kw, "location_name": loc_name, "language_code": "en"}
                ])
                t0 = (result.get("tasks") or [{}])[0]
                if t0.get("status_code") not in (20000, None):
                    print(f"[INFO] map-pack '{kw}' @ '{loc_name}': {t0.get('status_code')} "
                          f"{t0.get('status_message')}", file=sys.stderr)
                items = dfs_get_items(result)
                out["_local_available"] = True   # map pack query executed (a no-match is a real finding)
                for item in items:
                    d = (item.get("domain") or "").lower().replace("www.", "")
                    if d and (clean_domain in d or d in clean_domain):
                        pos = int(item.get("rank_absolute") or 0) or None
                        break
            except Exception as e:
                print(f"[WARN] Map pack fetch '{kw}' for {c}: {e}", file=sys.stderr)
            if pos is not None:
                map_rows.append({"city": c, "keyword": kw, "position": pos})
                if best_pos is None or pos < best_pos:
                    best_pos, best_kw = pos, kw
        # back-compat: city → best position found across the keyword set
        out["map_pack_positions"][c] = best_pos
        # ensure every city shows at least one row (even when unranked) so render isn't blank
        if not any(r["city"] == c for r in map_rows):
            map_rows.append({"city": c, "keyword": best_kw, "position": None})
    # Sort rows: ranked first (best position), then unranked.
    map_rows.sort(key=lambda r: (r["position"] is None, r["position"] or 0))
    out["map_pack_rows"] = map_rows

    # --- Recent review TEXT + real sampled distribution (async reviews task) ---
    # The dedicated reviews/live endpoint is 404 (does not exist); the async
    # task_post/task_get IS subscribed and returns full review text. Only worth the
    # ~10-30s poll when we actually located the GMB.
    if out.get("gmb_found"):
        rev = _fetch_reviews_async(brand_name, city, state, domain, location_code,
                                   place_id=out.get("gmb_place_id", ""))
        if rev.get("recent_reviews"):
            out["recent_reviews"] = rev["recent_reviews"]
        # Fill rating/count if my_business_info somehow didn't (defensive).
        if out.get("review_avg", 0) == 0 and rev.get("review_avg", 0) > 0:
            out["review_avg"]   = rev["review_avg"]
            out["review_count"] = rev["review_count"]
        # Prefer the REAL profile distribution (my_business_info rating_distribution); only
        # use the async sampled distribution when we don't already have a real one.
        if not out.get("_review_dist_real") and rev.get("rating_distribution"):
            dist = rev["rating_distribution"]
            out["review_distribution"] = dist
            total_dist = max(1, sum(dist.values()))
            out["review_dist_pcts"] = {k: round((v / total_dist) * 100, 1) for k, v in dist.items()}

    # --- GBP Q&A (business_data/google/questions_and_answers/live) ---
    out.update(_fetch_gbp_qna(brand_name, city, state, location_code))

    # --- GBP Posts/Updates (business_data/google/my_business_updates/live) ---
    out.update(_fetch_gbp_posts(brand_name, city, state, location_code))

    return out
