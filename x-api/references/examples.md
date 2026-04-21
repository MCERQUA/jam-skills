# X API — Working Code Examples

All examples assume base URL `https://api.x.com/2`. Replace secrets with env-var reads in real code.

## Python

### 1. App-only: recent search with rate-limit-aware retry

```python
import os, time, requests

BEARER = os.environ["X_BEARER_TOKEN"]

def search_recent(query, max_results=100):
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": "created_at,author_id,public_metrics,lang",
    }
    headers = {"Authorization": f"Bearer {BEARER}"}
    for attempt in range(5):
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 429:
            reset = int(r.headers.get("x-rate-limit-reset", time.time() + 2**attempt))
            time.sleep(max(reset - time.time(), 2))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("rate-limited too many times")

def search_recent_paged(query, max_pages=5):
    url = "https://api.x.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {BEARER}"}
    params = {"query": query, "max_results": 100}
    for _ in range(max_pages):
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        body = r.json()
        for t in body.get("data", []):
            yield t
        nxt = body.get("meta", {}).get("next_token")
        if not nxt: return
        params["next_token"] = nxt
```

### 2. OAuth 2.0 user: post a tweet

```python
import os, requests
USER_TOKEN = os.environ["X_USER_ACCESS_TOKEN"]  # from PKCE flow

def post_tweet(text, reply_to=None, quote_id=None):
    payload = {"text": text}
    if reply_to: payload["reply"] = {"in_reply_to_tweet_id": reply_to}
    if quote_id: payload["quote_tweet_id"] = quote_id
    r = requests.post(
        "https://api.x.com/2/tweets",
        headers={
            "Authorization": f"Bearer {USER_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload, timeout=15,
    )
    r.raise_for_status()
    return r.json()["data"]
```

### 3. Bulk lookup (batched, dedup-friendly)

```python
def bulk_lookup(ids):
    """Fetch up to 100 tweet IDs in one call — 1 quota unit for all of them."""
    assert 1 <= len(ids) <= 100
    r = requests.get(
        "https://api.x.com/2/tweets",
        headers={"Authorization": f"Bearer {BEARER}"},
        params={
            "ids": ",".join(ids),
            "tweet.fields": "public_metrics,author_id,created_at",
        }, timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", [])
```

### 4. Chunked media upload + attach to tweet

```python
import os, requests, math

def upload_video(path, user_token):
    size = os.path.getsize(path)
    h = {"Authorization": f"Bearer {user_token}"}

    # INIT
    init = requests.post(
        "https://api.x.com/2/media/upload/initialize",
        headers=h,
        json={
            "total_bytes": size,
            "media_type": "video/mp4",
            "media_category": "tweet_video",
        }, timeout=15,
    ).json()
    media_id = init["data"]["id"]

    # APPEND (5 MB chunks)
    CHUNK = 5 * 1024 * 1024
    with open(path, "rb") as f:
        seg = 0
        while True:
            buf = f.read(CHUNK)
            if not buf: break
            requests.post(
                f"https://api.x.com/2/media/upload/{media_id}/append",
                headers=h,
                data={"segment_index": seg},
                files={"media": buf},
                timeout=60,
            ).raise_for_status()
            seg += 1

    # FINALIZE
    fin = requests.post(
        f"https://api.x.com/2/media/upload/{media_id}/finalize",
        headers=h, timeout=30,
    ).json()

    # Poll processing_info if present
    info = fin.get("data", {}).get("processing_info")
    while info and info.get("state") in ("pending", "in_progress"):
        import time; time.sleep(info.get("check_after_secs", 5))
        s = requests.get(
            "https://api.x.com/2/media/upload",
            headers=h, params={"media_id": media_id, "command": "STATUS"},
            timeout=15,
        ).json()
        info = s.get("data", {}).get("processing_info")
        if info.get("state") == "failed":
            raise RuntimeError(info.get("error"))

    return media_id

def post_with_media(text, media_ids, user_token):
    r = requests.post(
        "https://api.x.com/2/tweets",
        headers={"Authorization": f"Bearer {user_token}",
                 "Content-Type": "application/json"},
        json={"text": text, "media": {"media_ids": media_ids}},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["data"]
```

### 5. Filtered stream consumer (Pro+)

```python
import requests, json

def stream(rules):
    BEARER = os.environ["X_BEARER_TOKEN"]
    h = {"Authorization": f"Bearer {BEARER}"}

    # 1. Replace existing rules
    existing = requests.get(
        "https://api.x.com/2/tweets/search/stream/rules", headers=h
    ).json().get("data", [])
    if existing:
        requests.post(
            "https://api.x.com/2/tweets/search/stream/rules",
            headers=h,
            json={"delete": {"ids": [r["id"] for r in existing]}},
        )

    # 2. Add new rules
    requests.post(
        "https://api.x.com/2/tweets/search/stream/rules",
        headers=h,
        json={"add": [{"value": v, "tag": t} for t, v in rules.items()]},
    ).raise_for_status()

    # 3. Open stream
    with requests.get(
        "https://api.x.com/2/tweets/search/stream",
        headers=h, stream=True, timeout=(10, None),
        params={"tweet.fields": "author_id,lang,public_metrics"},
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line: continue
            msg = json.loads(line)
            yield msg
```

## TypeScript / Node

### 1. App-only Bearer fetch with retry

```typescript
const BEARER = process.env.X_BEARER_TOKEN!;

async function xFetch<T>(url: string, init: RequestInit = {}): Promise<T> {
  for (let attempt = 0; attempt < 5; attempt++) {
    const r = await fetch(url, {
      ...init,
      headers: { Authorization: `Bearer ${BEARER}`, ...init.headers },
    });
    if (r.status === 429) {
      const reset = Number(r.headers.get("x-rate-limit-reset") ?? 0) * 1000;
      const wait = Math.max(reset - Date.now(), 2 ** attempt * 1000);
      await new Promise(res => setTimeout(res, wait));
      continue;
    }
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
    return r.json() as Promise<T>;
  }
  throw new Error("rate-limited too many times");
}

export async function searchRecent(query: string, max = 100) {
  const u = new URL("https://api.x.com/2/tweets/search/recent");
  u.searchParams.set("query", query);
  u.searchParams.set("max_results", String(max));
  u.searchParams.set("tweet.fields", "created_at,author_id,public_metrics");
  return xFetch<{ data: any[]; meta: any }>(u.toString());
}
```

### 2. OAuth 2.0 PKCE (server + callback)

```typescript
// Express route sketch
import crypto from "crypto";

function pkce() {
  const verifier = crypto.randomBytes(32).toString("base64url");
  const challenge = crypto
    .createHash("sha256").update(verifier).digest("base64url");
  return { verifier, challenge };
}

app.get("/auth/x", (req, res) => {
  const { verifier, challenge } = pkce();
  const state = crypto.randomBytes(16).toString("hex");
  req.session.pkce = verifier;
  req.session.state = state;
  const p = new URLSearchParams({
    response_type: "code",
    client_id: process.env.X_CLIENT_ID!,
    redirect_uri: process.env.X_REDIRECT_URI!,
    scope: "tweet.read tweet.write users.read offline.access",
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });
  res.redirect(`https://x.com/i/oauth2/authorize?${p}`);
});

app.get("/auth/x/callback", async (req, res) => {
  if (req.query.state !== req.session.state) return res.status(400).send("csrf");
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code: String(req.query.code),
    redirect_uri: process.env.X_REDIRECT_URI!,
    code_verifier: req.session.pkce,
    client_id: process.env.X_CLIENT_ID!,
  });
  const basic = Buffer.from(
    `${process.env.X_CLIENT_ID}:${process.env.X_CLIENT_SECRET}`
  ).toString("base64");
  const r = await fetch("https://api.x.com/2/oauth2/token", {
    method: "POST",
    headers: {
      Authorization: `Basic ${basic}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });
  const tok = await r.json();
  // store tok.access_token + tok.refresh_token + (expires_at = now + tok.expires_in)
  res.json(tok);
});
```

### 3. Refresh helper

```typescript
async function refreshX(refreshToken: string) {
  const basic = Buffer.from(
    `${process.env.X_CLIENT_ID}:${process.env.X_CLIENT_SECRET}`
  ).toString("base64");
  const r = await fetch("https://api.x.com/2/oauth2/token", {
    method: "POST",
    headers: {
      Authorization: `Basic ${basic}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken,
    }),
  });
  if (!r.ok) throw new Error(`refresh failed: ${await r.text()}`);
  return r.json();
}
```

## curl snippets (quick shell debugging)

```bash
# App-only: recent search
curl -G "https://api.x.com/2/tweets/search/recent" \
  -H "Authorization: Bearer $BEARER" \
  --data-urlencode 'query=from:anthropicai -is:retweet' \
  --data-urlencode 'max_results=20'

# User: post
curl -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"hello from curl"}'

# User: me
curl "https://api.x.com/2/users/me" -H "Authorization: Bearer $USER_TOKEN"

# Check rate-limit headers
curl -si "https://api.x.com/2/users/me" -H "Authorization: Bearer $USER_TOKEN" | grep -i x-rate-limit
```

## Libraries (maintained as of 2026-04)

| Language | Library | Notes |
|---|---|---|
| Python | **tweepy** (4.14+) | v2 client, handles OAuth 1.0a + 2.0; pick `tweepy.Client` not `API` |
| Python | **x-xdk-python** (official) | Newer, opinionated; partial coverage |
| Node/TS | **twitter-api-v2** (npm) | Most popular; full v2 coverage |
| Node/TS | **@xdevplatform/xdk** (official) | Growing coverage |
| Go | **go-twitter** / **gotwtr** | gotwtr is v2-first |
| Rust | **twitter-v2** | async, typed |
| CLI | **xurl** (official) | Great for testing with built-in auth |

## Query operator cheat sheet (recent + all search)

```
from:user              # posts from a specific user
to:user                # replies to a user
@user                  # mentions user
"exact phrase"
hashtag #xapi
lang:en                # BCP-47 code
is:retweet             # filter on type
is:reply
is:quote
has:media              # has images/video
has:links
has:geo                # (Pro+ on search/all)
place:new_york
point_radius:[lon lat 10km]
url:"docs.x.com"
from:user1 OR from:user2
(claude OR anthropic) -is:retweet
context:10.1234567890  # topic/entity context (Pro+)
```

Full operator list: https://docs.x.com/x-api/posts/search-operators (verify — the path has changed historically).

## Common pitfalls (make-or-break)

1. **Forgetting `users.read` scope** — most `tweet.*` endpoints need it too; otherwise `401`.
2. **Forgetting `offline.access`** — no refresh token, user has to re-auth every 2 hours.
3. **DM scope without DM app permission** — scope parses OK, app permission rejects at call time. Update app perms, re-issue token.
4. **No pagination** — `max_results` defaults to 10 on search; you'll silently miss data.
5. **Not batching** — 100 individual lookups = 100 quota units, vs 1 batch request = 1 unit.
6. **Retry storm on 5xx** — back off, don't hammer.
7. **Clock skew on OAuth 1.0a** — signatures fail if host clock is >5 min off.
8. **Media ID timeout** — 24h after FINALIZE, you must re-upload.
9. **`since_id` wins over `start_time`** — more reliable, avoids duplicate billing across runs.
10. **Setting up in prod without a `max-spend` cap** — pay-per-use will burn you on bugs that retry forever.
