---
name: x-api
description: Build against the X (Twitter) API v2 — auth flows (OAuth 2.0 PKCE / 1.0a / Bearer), endpoint catalog, pay-per-use & tier pricing, and per-endpoint rate limits. Trigger when code imports twitter/tweepy/twitter-api-v2, hits api.x.com or api.twitter.com, handles tweets/posts/DMs/media/spaces/lists, or the user asks about X API pricing, rate limits, or auth. Last verified 2026-04-20.
---

# X API v2 Reference Skill

Authoritative reference for integrating with the X API v2 (api.x.com). Optimized for avoiding rate-limit and billing surprises.

## When to use this skill

- Writing or reviewing code that calls `api.x.com` / `api.twitter.com`
- Choosing between OAuth 2.0 PKCE, OAuth 1.0a, or App-only Bearer
- Estimating cost before shipping (pay-per-use credits burn fast)
- Sizing a polling loop so it doesn't hit 429
- Deciding which tier to buy (or whether to stay pay-per-use)

## Root facts (memorize these)

- **Base URL:** `https://api.x.com/2` (alias: `api.twitter.com/2`)
- **Docs home:** https://docs.x.com/x-api/introduction
- **OpenAPI:** https://docs.x.com/openapi.json
- **LLM index:** https://docs.x.com/llms.txt (full URL list)
- **Rate-limit headers** on every response: `x-rate-limit-limit`, `x-rate-limit-remaining`, `x-rate-limit-reset` (unix timestamp)
- **429 recovery:** sleep until `x-rate-limit-reset`, then exponential backoff on retries
- **Deduplication:** on pay-per-use, the same resource (same post ID etc.) re-requested inside the same UTC day is **free on the second+ hit**. Cache-friendly designs save real money.

## Pricing at a glance (2026-04)

| Tier | Cost | Who can buy | Monthly cap | Use when |
|------|------|-------------|-------------|----------|
| **Pay-Per-Use** | $0.005/read, $0.01/write | Everyone (default) | 2M reads → Enterprise | Unpredictable / low-volume |
| **Basic** | $200/mo | Legacy only | ~50k writes, ~10–15k reads | Small steady app, pre-2026-02 |
| **Pro** | $5,000/mo | Legacy only | ~300k writes, 1M reads | Full-archive search, streaming |
| **Enterprise** | $42k–$50k+/mo | Contract | 50M+ reads, firehose | Platform-scale data |

Pay-per-use tops out at **2M post reads/month** — above that, Enterprise is required. See `references/pricing.md` for per-endpoint cost.

## Tier → endpoint access

| Feature | PPU | Basic | Pro | Enterprise |
|---------|-----|-------|-----|------------|
| Create/read/delete posts | ✓ | ✓ | ✓ | ✓ |
| 7-day recent search | ✓ | ✓ | ✓ | ✓ |
| Full-archive search (`/search/all`) | ✗ | ✗ | ✓ | ✓ |
| Filtered streaming | ✗ | ✗ | ✓ | ✓ |
| Firehose | ✗ | ✗ | ✗ | ✓ |

## Auth quick pick

| Need to... | Use |
|------------|-----|
| Read public posts only | **App-only Bearer** |
| Post, like, follow, DM as a user | **OAuth 2.0 PKCE** (modern, scoped) |
| Media upload chunked APIs, older integrations | **OAuth 1.0a User Context** |
| Some enterprise firehose endpoints | **HTTP Basic** |

Scopes needed for OAuth 2.0 (request only what you'll use — users see them at consent):

```
tweet.read tweet.write tweet.moderate.write
users.read
follows.read follows.write
offline.access        # required to get a refresh_token
like.read like.write
list.read list.write
block.read block.write
mute.read mute.write
space.read
dm.read dm.write
bookmark.read bookmark.write
```

Full flows, code, and refresh logic in `references/auth.md`.

## Endpoint cheat sheet (most-used)

| Purpose | Method + Path | Auth | Limit (user / app, 15m) |
|---------|---------------|------|-------------------------|
| Create post | `POST /2/tweets` | OAuth2 user | **100** / 10k per 24h |
| Delete post | `DELETE /2/tweets/:id` | OAuth2 user | 50 / — |
| Lookup post | `GET /2/tweets/:id` | Bearer or user | 900 / 450 |
| Lookup posts (bulk) | `GET /2/tweets?ids=` | Bearer or user | 5,000 / 3,500 |
| Recent search (7d) | `GET /2/tweets/search/recent` | Bearer or user | 300 / 450 |
| Full-archive search | `GET /2/tweets/search/all` | Bearer (Pro+) | 1/sec / 1/sec + 300/24h |
| Counts (recent) | `GET /2/tweets/counts/recent` | Bearer | — / 300 |
| User timeline | `GET /2/users/:id/tweets` | Bearer or user | 900 / 10,000 |
| Mentions timeline | `GET /2/users/:id/mentions` | Bearer or user | 300 / 450 |
| Home timeline | `GET /2/users/:id/timelines/reverse_chronological` | OAuth2 user | 180 / — |
| Me | `GET /2/users/me` | OAuth2 user | 75 / — |
| Lookup user by username | `GET /2/users/by/username/:username` | Bearer or user | 900 / 300 |
| Like a post | `POST /2/users/:id/likes` | OAuth2 user | 50/15m + 1,000/24h |
| Unlike | `DELETE /2/users/:id/likes/:tweet_id` | OAuth2 user | 50/15m + 1,000/24h |
| Retweet | `POST /2/users/:id/retweets` | OAuth2 user | 50 / — |
| Follow | `POST /2/users/:id/following` | OAuth2 user | 50 / — |
| Send DM | `POST /2/dm_conversations/:id/messages` | OAuth2 user (`dm.write`) | 15/15m + 1,440/24h |
| Media upload (simple) | `POST /2/media/upload` | OAuth2 user or 1.0a | 500 / 50k per 24h |
| Media upload init (chunked) | `POST /2/media/upload/initialize` | same | 1,875 / 180k per 24h |
| Filtered stream | `GET /2/tweets/search/stream` | Bearer (Pro+) | — (connection-based) |
| Trends by location | `GET /2/trends/by/woeid/:id` | Bearer | — / 75 |

Full per-endpoint matrix (likes, lists, spaces, blocks, mutes, bookmarks, compliance, usage, streaming, media subtitles, community notes): see `references/endpoints.md` and `references/rate-limits.md`.

## Rate-limit defense pattern (use this, always)

Every request path hitting X should:

1. **Read the headers** — track `x-rate-limit-remaining`; if ≤ 10%, brake.
2. **Honor reset** — on 429, `sleep(max(reset - now, 1))` then retry once, then exponential backoff (2s, 4s, 8s, cap 60s).
3. **Batch reads** — `GET /2/tweets?ids=a,b,c...` up to 100 IDs per call costs the same 1 request as 1 ID.
4. **Cache within the UTC day** — pay-per-use dedupes; so does your wallet.
5. **Separate app vs user buckets** — public reads go on app Bearer (higher app-context limits), user actions on OAuth 2.0 user.
6. **Never poll faster than the slowest bottleneck** — e.g., a DM-read loop is capped at 15/15m = 1 req/min.

See `references/rate-limits.md` for defensive snippets and a drop-in Python `RateLimitedClient`.

## Cost estimation pattern

Before shipping a feature, ballpark monthly cost:

```
monthly_reads  = users_DAU × reads_per_user_per_day × 30 × (1 - cache_hit_rate)
monthly_writes = users_DAU × writes_per_user_per_day × 30
cost_usd       = monthly_reads * 0.005 + monthly_writes * 0.01
```

If `monthly_reads > 2_000_000`, pay-per-use won't cover it — either add caching, reduce frequency, or upgrade to Pro/Enterprise. 2M reads/month = **~46 reads/min sustained** — a single 1s-polling loop eats this.

Full examples and cost tables in `references/pricing.md`.

## Examples

Working code (Python + Node/TS) for: app-only lookup, OAuth 2.0 PKCE login, posting with media, filtered stream consumer, rate-limited retry wrapper — in `references/examples.md`.

## Gotchas (learned the hard way in the wild)

1. **Pay-per-use has no free tier as of Feb 2026.** New devs get a one-time $10 voucher if they were on legacy Free. Budget from $0.
2. **Query operators differ between `search/recent` and `search/all`** — `search/all` supports historical operators (`has:geo`, `sample:`, etc.) but requires Pro+.
3. **`max_results` defaults to 10.** Paginate or you'll silently miss data.
4. **Timelines return at most 3,200 posts historically** (API-enforced per user) regardless of tier.
5. **Filtered stream rule limits per connection are tier-gated** — Pro: 25 rules × 512 chars; Enterprise: 1,000 rules × 1,024 chars.
6. **DMs require OAuth 2.0 user with `dm.read`/`dm.write` scopes** AND the app must have Direct Messages read/write permission toggled in the portal — scope alone isn't enough.
7. **OAuth 2.0 user-context tokens expire in 2 hours.** Always request `offline.access` and refresh.
8. **`since_id` beats `start_time`** — IDs are cheaper to reason about and immune to clock drift.
9. **Media `media_id` is valid for 24 hours** — upload and tweet in the same job or re-upload.
10. **Deduplication is per-UTC-day**, not a rolling 24h. Cache TTLs that align to UTC midnight save more.

## References

- `references/endpoints.md` — full endpoint catalog with auth, scopes, rate limits
- `references/rate-limits.md` — the complete per-endpoint rate-limit matrix + retry patterns
- `references/pricing.md` — pay-per-use costs, tier caps, cost-estimation worksheet
- `references/auth.md` — OAuth 2.0 PKCE, OAuth 1.0a, Bearer — full flows with code
- `references/examples.md` — copy-paste code (Python + TypeScript)

## Research provenance

Compiled 2026-04-20 from:
- docs.x.com/x-api/introduction + llms.txt index
- docs.x.com/x-api/fundamentals/rate-limits
- docs.x.com official endpoint reference pages
- devcommunity.x.com pay-per-use launch announcement (Feb 2026)
- Third-party pricing analyses (postproxy.dev, elfsight, xpoz) cross-checked against docs

Prices and limits change frequently. Verify at https://console.x.com before quoting to a customer.
