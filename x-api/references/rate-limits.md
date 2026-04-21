# X API Rate Limits — Complete Matrix

All windows are **15 minutes** unless marked `/24h` (24 hours, rolling). Enterprise customers negotiate per-endpoint limits — treat the table below as **Basic/Pro baseline**.

## Response headers (every API response)

```
x-rate-limit-limit:      N          # bucket size
x-rate-limit-remaining:  K          # requests left in window
x-rate-limit-reset:      1745174400 # unix timestamp when bucket refills
```

Some endpoints (media, DMs, compliance) additionally return a second family of headers for the 24h bucket:

```
x-24h-rate-limit-limit
x-24h-rate-limit-remaining
x-24h-rate-limit-reset
```

**Always look at BOTH on media/DM/create-post endpoints** — the 24h cap is the one that bites you in production.

## The table

**Columns:** user-context limit / app-context (Bearer) limit.

### Posts

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/tweets` | GET (bulk lookup) | 5,000 | 3,500 |
| `/2/tweets/:id` | GET | 900 | 450 |
| `/2/tweets` | POST | 100 + **10,000/24h** | — |
| `/2/tweets/:id` | DELETE | 50 | — |
| `/2/tweets/search/recent` | GET | 300 | 450 |
| `/2/tweets/search/all` (Pro+) | GET | 1/sec | 1/sec + 300/24h |
| `/2/tweets/counts/recent` | GET | — | 300 |
| `/2/tweets/counts/all` | GET | — | 300 |

### Timelines

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/users/:id/tweets` | GET | 900 | 10,000 |
| `/2/users/:id/mentions` | GET | 300 | 450 |
| `/2/users/:id/timelines/reverse_chronological` | GET | 180 | — |

### Engagement

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/tweets/:id/liking_users` | GET | 75 | 75 |
| `/2/users/:id/liked_tweets` | GET | 75 | 75 |
| `/2/users/:id/likes` | POST | 50 + **1,000/24h** | — |
| `/2/users/:id/likes/:tweet_id` | DELETE | 50 + 1,000/24h | — |
| `/2/tweets/:id/retweeted_by` | GET | 75 | 75 |
| `/2/tweets/:id/quote_tweets` | GET | 75 | 75 |
| `/2/users/:id/retweets` | POST | 50 | — |
| `/2/users/:id/retweets/:tweet_id` | DELETE | 50 | — |

### Users

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/users` | GET (bulk) | 900 | 300 |
| `/2/users/:id` | GET | 900 | 300 |
| `/2/users/by` | GET (bulk) | 900 | 300 |
| `/2/users/by/username/:username` | GET | 900 | 300 |
| `/2/users/me` | GET | 75 | — |
| `/2/users/search` | GET | 900 | 300 |

### Relationships

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/users/:id/following` | GET | 300 | 300 |
| `/2/users/:id/followers` | GET | 300 | 300 |
| `/2/users/:id/following` | POST | 50 | — |
| `/2/users/:src/following/:tgt` | DELETE | 50 | — |
| `/2/users/:id/blocking` | GET | 15 | — |
| `/2/users/:id/muting` | GET | 15 | — |
| `/2/users/:id/muting` | POST | 50 | — |
| `/2/users/:src/muting/:tgt` | DELETE | 50 | — |

### Direct Messages

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/dm_events` | GET | 15 | — |
| `/2/dm_events/:id` | GET | 15 | — |
| `/2/dm_conversations/:id/dm_events` | GET | 15 | — |
| `/2/dm_conversations/with/:pid/dm_events` | GET | 15 | — |
| `/2/dm_conversations` | POST | 15 + **1,440/24h** | 1,440/24h |
| `/2/dm_conversations/with/:pid/messages` | POST | 15 + 1,440/24h | 1,440/24h |
| `/2/dm_conversations/:id/messages` | POST | 15 + 1,440/24h | 1,440/24h |
| `/2/dm_events/:id` | DELETE | 300 + 1,500/24h | 4,000/24h |

### Lists

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/lists/:id` | GET | 75 | 75 |
| `/2/users/:id/owned_lists` | GET | 15 | 15 |
| `/2/lists/:id/tweets` | GET | 900 | 900 |
| `/2/lists/:id/members` | GET | 900 | 900 |
| `/2/users/:id/list_memberships` | GET | 75 | 75 |
| `/2/lists` | POST | 300 | — |
| `/2/lists/:id` | PUT | 300 | — |
| `/2/lists/:id` | DELETE | 300 | — |
| `/2/lists/:id/members` | POST | 300 | — |
| `/2/lists/:id/members/:uid` | DELETE | 300 | — |
| `/2/users/:id/followed_lists` | POST | 50 | — |
| `/2/users/:id/followed_lists/:lid` | DELETE | 50 | — |
| `/2/users/:id/pinned_lists` | GET | 15 | — |
| `/2/users/:id/pinned_lists` | POST | 50 | — |
| `/2/users/:id/pinned_lists/:lid` | DELETE | 50 | — |

### Spaces

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/spaces/:id` | GET | 300 | 300 |
| `/2/spaces` | GET | 300 | 300 |
| `/2/spaces/:id/tweets` | GET | 300 | 300 |
| `/2/spaces/by/creator_ids` | GET | 300 + 1/sec | 300 + 1/sec |
| `/2/spaces/:id/buyers` | GET | 300 | 300 |
| `/2/spaces/search` | GET | 300 | 300 |

### Media

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/media/upload` | POST | 500 | 50,000/24h |
| `/2/media/upload` | GET | 1,000 | 100,000/24h |
| `/2/media/upload/initialize` | POST | 1,875 | 180,000/24h |
| `/2/media/upload/:id/append` | POST | 1,875 | 180,000/24h |
| `/2/media/upload/:id/finalize` | POST | 1,875 | 180,000/24h |
| `/2/media/metadata` | POST | 500 | 50,000/24h |
| `/2/media/subtitles` | POST | 100 | 10,000/24h |
| `/2/media/subtitles` | DELETE | 100 | 10,000/24h |

### Trends

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/trends/by/woeid/:id` | GET | — | 75 |
| `/2/users/personalized_trends` | GET | 10 + 100/24h | 200 + 200/24h |

### Compliance & Usage

| Endpoint | Method | User | App |
|---|---|---|---|
| `/2/compliance/jobs` | POST | — | 150 |
| `/2/compliance/jobs` | GET | — | 150 |
| `/2/compliance/jobs/:id` | GET | — | 150 |
| `/2/usage/tweets` | GET | — | 50 |

### Streaming

Streaming endpoints are **connection-count** gated, not RPS gated:

| Endpoint | Pro | Enterprise |
|---|---|---|
| `/2/tweets/search/stream` | 1 connection, 25 rules × 512 chars | multiple connections, 1,000 rules × 1,024 chars, redundant allowed |
| `/2/tweets/sample/stream` (1%) | 1 connection | multiple |
| `/2/tweets/sample10/stream` (10%) | — | ✓ |
| `/2/tweets/compliance/stream` | 1 | multiple |

## Strategy: avoiding 429s

### 1. Pick the right auth context

- Public reads: **use Bearer (app-context)** — `/2/tweets` lookup is 3,500/15m app vs 5,000/15m user *in aggregate across your user base* — with Bearer you share one bucket, with User each user has their own. Small apps: user buckets help. Larger apps: app bucket is a ceiling.
- User actions: obvious — OAuth 2.0 user.

### 2. Watch both windows

Endpoints with `/24h` limits (post create, likes, DMs, media) **will quietly accept 100 requests in 15m then block you for ~20 hours**. Track the 24h header separately.

### 3. Pre-emptive braking

```python
remaining = int(resp.headers["x-rate-limit-remaining"])
limit     = int(resp.headers["x-rate-limit-limit"])
if remaining / limit < 0.1:        # under 10% budget
    reset = int(resp.headers["x-rate-limit-reset"])
    sleep(max(reset - time.time(), 1))
```

### 4. Retry template

```python
for attempt in range(5):
    r = session.get(url, headers=h, params=p, timeout=15)
    if r.status_code == 429:
        reset = int(r.headers.get("x-rate-limit-reset", time.time() + 60))
        time.sleep(max(reset - time.time(), 2 ** attempt))
        continue
    r.raise_for_status()
    return r.json()
raise RuntimeError("exhausted retries")
```

### 5. Batch aggressively

`GET /2/tweets?ids=a,b,c,...` (up to 100 IDs) costs **1 request-quota unit** but returns 100 posts. Turning 100 single-ID calls into 1 batched call is a 100× quota multiplier.

Equivalent batching available on `/2/users` (100 IDs), `/2/users/by` (100 usernames), and most lookup endpoints.

### 6. Prefer `since_id` / `until_id` over time windows

ID-based pagination is resilient to clock skew and avoids re-reading old data on restart.

### 7. Respect Retry-After on 5xx too

On 500/502/503, back off and retry — don't hammer.

## Drop-in rate-limited client (Python)

```python
import time, requests

class RateLimitedClient:
    def __init__(self, bearer, min_remaining_pct=0.1):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {bearer}"
        self.s.headers["User-Agent"] = "my-app/1.0"
        self.brake = min_remaining_pct

    def _sleep_until(self, ts):
        delay = max(int(ts) - time.time(), 1)
        time.sleep(delay)

    def request(self, method, url, **kw):
        for attempt in range(6):
            r = self.s.request(method, url, timeout=15, **kw)
            if r.status_code == 429:
                self._sleep_until(r.headers.get("x-rate-limit-reset", time.time() + 2**attempt))
                continue
            if r.status_code in (500, 502, 503):
                time.sleep(min(2 ** attempt, 30)); continue
            # pre-emptive brake on near-empty bucket
            rem = int(r.headers.get("x-rate-limit-remaining", 999))
            lim = int(r.headers.get("x-rate-limit-limit", 1))
            if lim and rem / lim < self.brake:
                self._sleep_until(r.headers.get("x-rate-limit-reset", time.time() + 60))
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"{method} {url} retries exhausted")
```

Same pattern in TypeScript: see `references/examples.md`.
