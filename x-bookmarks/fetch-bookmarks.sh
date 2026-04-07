#!/usr/bin/env bash
# Fetch X/Twitter bookmarks via internal GraphQL API
# Usage: bash fetch-bookmarks.sh [count]
# Requires: X_CT0 and X_AUTH_TOKEN env vars
# Output: JSON array of bookmarks to stdout

set -euo pipefail

COUNT="${1:-20}"

if [ -z "${X_CT0:-}" ] || [ -z "${X_AUTH_TOKEN:-}" ]; then
  echo '{"error": "X_CT0 and X_AUTH_TOKEN env vars required"}' >&2
  exit 1
fi

BEARER="AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

VARIABLES="{\"count\":$COUNT}"
FEATURES='{"graphql_timeline_v2_bookmark_timeline":true,"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}'

# URL-encode the params
ENC_VARS=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$VARIABLES'))")
ENC_FEAT=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.stdin.read().strip()))" <<< "$FEATURES")

# Fetch bookmarks
TMPFILE=$(mktemp)
trap "rm -f $TMPFILE" EXIT

curl -s \
  "https://x.com/i/api/graphql/Z9GWmP0kP2dajyckAaDUBw/Bookmarks?variables=$ENC_VARS&features=$ENC_FEAT" \
  -H "Authorization: Bearer $BEARER" \
  -H "x-csrf-token: $X_CT0" \
  -H "x-twitter-auth-type: OAuth2Session" \
  -H "x-twitter-active-user: yes" \
  -H "cookie: ct0=$X_CT0; auth_token=$X_AUTH_TOKEN" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Content-Type: application/json" \
  -o "$TMPFILE"

# Parse and output clean JSON
python3 - "$TMPFILE" << 'PYEOF'
import json, sys

with open(sys.argv[1]) as f:
    data = json.load(f)

bookmarks = []
instructions = data.get("data", {}).get("bookmark_timeline_v2", {}).get("timeline", {}).get("instructions", [])

for inst in instructions:
    if inst.get("type") != "TimelineAddEntries":
        continue
    for entry in inst.get("entries", []):
        if not entry.get("entryId", "").startswith("tweet-"):
            continue
        result = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
        legacy = result.get("legacy", {})
        user = result.get("core", {}).get("user_results", {}).get("result", {})
        user_core = user.get("core", {})
        user_legacy = user.get("legacy", {})

        # Extract links from entities
        links = []
        for url_obj in legacy.get("entities", {}).get("urls", []):
            links.append(url_obj.get("expanded_url", url_obj.get("url", "")))

        # Extract media
        media = []
        for m in legacy.get("entities", {}).get("media", []):
            media.append({"type": m.get("type"), "url": m.get("media_url_https", m.get("url", ""))})
        for m in (legacy.get("extended_entities", {}) or {}).get("media", []):
            if m.get("type") == "video":
                variants = m.get("video_info", {}).get("variants", [])
                mp4s = [v for v in variants if v.get("content_type") == "video/mp4"]
                if mp4s:
                    best = max(mp4s, key=lambda v: v.get("bitrate", 0))
                    media.append({"type": "video", "url": best.get("url", "")})

        bookmark = {
            "id": legacy.get("id_str", entry.get("entryId", "").replace("tweet-", "")),
            "author": user_core.get("screen_name", ""),
            "author_name": user_core.get("name", ""),
            "author_followers": user_legacy.get("followers_count", 0),
            "text": legacy.get("full_text", ""),
            "posted_at": legacy.get("created_at", ""),
            "likes": legacy.get("favorite_count", 0),
            "retweets": legacy.get("retweet_count", 0),
            "replies": legacy.get("reply_count", 0),
            "views": result.get("views", {}).get("count", "0"),
            "links": links,
            "media": media,
        }
        bookmarks.append(bookmark)

print(json.dumps(bookmarks, indent=2))
PYEOF
