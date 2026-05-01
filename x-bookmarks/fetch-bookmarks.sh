#!/usr/bin/env bash
# Fetch X/Twitter bookmarks via official API v2 (OAuth 1.0a user context)
# Usage: bash fetch-bookmarks.sh [count]
# Requires: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
# Output: JSON array of bookmarks to stdout

set -euo pipefail

COUNT="${1:-20}"

if [ -z "${X_API_KEY:-}" ] || [ -z "${X_API_SECRET:-}" ] || [ -z "${X_ACCESS_TOKEN:-}" ] || [ -z "${X_ACCESS_TOKEN_SECRET:-}" ]; then
  echo '{"error": "X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET required"}' >&2
  exit 1
fi

python3 - "$COUNT" << 'PYEOF'
import sys, json, os, requests
from requests_oauthlib import OAuth1

count = int(sys.argv[1])

auth = OAuth1(
    os.environ["X_API_KEY"],
    os.environ["X_API_SECRET"],
    os.environ["X_ACCESS_TOKEN"],
    os.environ["X_ACCESS_TOKEN_SECRET"],
)

# Get authenticated user's ID
r = requests.get("https://api.x.com/2/users/me", auth=auth)
if r.status_code != 200:
    print(json.dumps({"error": f"users/me HTTP {r.status_code}", "detail": r.text}), file=sys.stderr)
    sys.exit(1)
user_id = r.json()["data"]["id"]

# Fetch bookmarks
params = {
    "max_results": min(count, 100),
    "tweet.fields": "created_at,public_metrics,entities,attachments",
    "expansions": "author_id,attachments.media_keys",
    "user.fields": "username,name,public_metrics",
    "media.fields": "url,preview_image_url,type",
}
r = requests.get(f"https://api.x.com/2/users/{user_id}/bookmarks", auth=auth, params=params)

if r.status_code != 200:
    print(json.dumps({"error": f"bookmarks HTTP {r.status_code}", "detail": r.text}), file=sys.stderr)
    sys.exit(1)

data = r.json()

if "errors" in data and "data" not in data:
    print(json.dumps({"error": data["errors"]}))
    sys.exit(1)

tweets = data.get("data", [])
users  = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
media  = {m["media_key"]: m for m in data.get("includes", {}).get("media", [])}

bookmarks = []
for tweet in tweets:
    author   = users.get(tweet.get("author_id", ""), {})
    entities = tweet.get("entities", {}) or {}
    links    = [u.get("expanded_url", u.get("url", "")) for u in entities.get("urls", [])]
    m_list   = []
    for mk in (tweet.get("attachments", {}) or {}).get("media_keys", []):
        m = media.get(mk, {})
        m_list.append({"type": m.get("type"), "url": m.get("url") or m.get("preview_image_url", "")})

    metrics = tweet.get("public_metrics", {})
    bookmarks.append({
        "id": tweet["id"],
        "author": author.get("username", ""),
        "author_name": author.get("name", ""),
        "author_followers": author.get("public_metrics", {}).get("followers_count", 0),
        "text": tweet["text"],
        "posted_at": tweet.get("created_at", ""),
        "likes": metrics.get("like_count", 0),
        "retweets": metrics.get("retweet_count", 0),
        "replies": metrics.get("reply_count", 0),
        "views": metrics.get("impression_count", 0),
        "links": links,
        "media": m_list,
    })

print(json.dumps(bookmarks, indent=2))
PYEOF
