# X API v2 — Full Endpoint Catalog

Base URL: `https://api.x.com/2` · All paths below omit the `/2` prefix in column 1.

**Legend:**
- **Auth:** `Bearer` = app-only, `User` = OAuth 2.0 user context (scopes listed), `1.0a` = OAuth 1.0a user context
- **Scopes:** OAuth 2.0 scopes required (OAuth 1.0a uses permission toggle instead)
- **Rate limits** in `(user / app)` per 15-min unless labeled otherwise. `—` = not supported in that context.

## Posts

| Endpoint | Method | Auth | Scopes | Rate limits |
|----------|--------|------|--------|-------------|
| `/tweets` | POST | User | `tweet.read tweet.write users.read` | 100 / 10,000 per 24h |
| `/tweets/:id` | GET | Bearer, User | `tweet.read users.read` | 900 / 450 |
| `/tweets` | GET (bulk lookup, `?ids=`) | Bearer, User | `tweet.read users.read` | 5,000 / 3,500 |
| `/tweets/:id` | DELETE | User | `tweet.read tweet.write users.read` | 50 / — |
| `/tweets/:id/hidden` | PUT | User | `tweet.moderate.write` | — / — |

### Search

| Endpoint | Method | Auth | Scopes | Rate limits |
|----------|--------|------|--------|-------------|
| `/tweets/search/recent` (7d) | GET | Bearer, User | `tweet.read users.read` | 300 / 450 |
| `/tweets/search/all` (archive, **Pro+**) | GET | Bearer | — | 1/sec + 300/24h |
| `/tweets/counts/recent` | GET | Bearer | — | — / 300 |
| `/tweets/counts/all` (Pro+) | GET | Bearer | — | — / 300 |

`query` max length: 512 chars (recent) / 1,024 chars (all). `max_results`: 10–100 (recent), 10–500 (all).

### Timelines

| Endpoint | Method | Auth | Rate limits |
|----------|--------|------|-------------|
| `/users/:id/tweets` | GET | Bearer, User | 900 / 10,000 |
| `/users/:id/mentions` | GET | Bearer, User | 300 / 450 |
| `/users/:id/timelines/reverse_chronological` | GET | User (`tweet.read users.read`) | 180 / — |

Timelines return ≤ 3,200 historical posts per user regardless of tier.

### Engagement

| Endpoint | Method | Auth | Scopes | Rate limits |
|----------|--------|------|--------|-------------|
| `/tweets/:id/liking_users` | GET | Bearer, User | `like.read` | 75 / 75 |
| `/users/:id/liked_tweets` | GET | Bearer, User | `like.read` | 75 / 75 |
| `/users/:id/likes` | POST | User | `like.write` | 50/15m + 1,000/24h |
| `/users/:id/likes/:tweet_id` | DELETE | User | `like.write` | 50/15m + 1,000/24h |
| `/tweets/:id/retweeted_by` | GET | Bearer, User | — | 75 / 75 |
| `/tweets/:id/quote_tweets` | GET | Bearer, User | — | 75 / 75 |
| `/users/:id/retweets` | POST | User | `tweet.write` | 50 / — |
| `/users/:id/retweets/:tweet_id` | DELETE | User | `tweet.write` | 50 / — |
| `/users/:id/bookmarks` | GET | User | `bookmark.read` | — / — |
| `/users/:id/bookmarks` | POST | User | `bookmark.write` | — / — |
| `/users/:id/bookmarks/:tweet_id` | DELETE | User | `bookmark.write` | — / — |

## Users

| Endpoint | Method | Auth | Rate limits |
|----------|--------|------|-------------|
| `/users` | GET (bulk, `?ids=`) | Bearer, User | 900 / 300 |
| `/users/:id` | GET | Bearer, User | 900 / 300 |
| `/users/by` | GET (bulk, `?usernames=`) | Bearer, User | 900 / 300 |
| `/users/by/username/:username` | GET | Bearer, User | 900 / 300 |
| `/users/me` | GET | User (`users.read tweet.read`) | 75 / — |
| `/users/search` | GET | Bearer, User | 900 / 300 |

## Relationships

| Endpoint | Method | Auth | Scopes | Rate limits |
|----------|--------|------|--------|-------------|
| `/users/:id/following` | GET | Bearer, User | `follows.read` | 300 / 300 |
| `/users/:id/followers` | GET | Bearer, User | `follows.read` | 300 / 300 |
| `/users/:id/following` | POST | User | `follows.write` | 50 / — |
| `/users/:src/following/:tgt` | DELETE | User | `follows.write` | 50 / — |
| `/users/:id/blocking` | GET | User | `block.read` | 15 / — |
| `/users/:id/muting` | GET | User | `mute.read` | 15 / — |
| `/users/:id/muting` | POST | User | `mute.write` | 50 / — |
| `/users/:src/muting/:tgt` | DELETE | User | `mute.write` | 50 / — |

## Direct Messages

All DM endpoints require OAuth 2.0 user context with `dm.read` and/or `dm.write`. App must also have DM read/write **permission** toggled in the developer portal (scope alone is not enough).

| Endpoint | Method | Scopes | Rate limits |
|----------|--------|--------|-------------|
| `/dm_events` | GET | `dm.read` | 15 / — |
| `/dm_events/:id` | GET | `dm.read` | 15 / — |
| `/dm_conversations/:id/dm_events` | GET | `dm.read` | 15 / — |
| `/dm_conversations/with/:pid/dm_events` | GET | `dm.read` | 15 / — |
| `/dm_conversations` | POST | `dm.write` | 15/15m + 1,440/24h (user) · 1,440/24h (app) |
| `/dm_conversations/with/:pid/messages` | POST | `dm.write` | same as above |
| `/dm_conversations/:id/messages` | POST | `dm.write` | same as above |
| `/dm_events/:id` | DELETE | `dm.write` | 300/15m + 1,500/24h (user) · 4,000/24h (app) |

## Lists

| Endpoint | Method | Auth | Scopes | Rate limits |
|----------|--------|------|--------|-------------|
| `/lists/:id` | GET | Bearer, User | `list.read` | 75 / 75 |
| `/users/:id/owned_lists` | GET | Bearer, User | `list.read` | 15 / 15 |
| `/lists/:id/tweets` | GET | Bearer, User | `list.read tweet.read` | 900 / 900 |
| `/lists/:id/members` | GET | Bearer, User | `list.read users.read` | 900 / 900 |
| `/users/:id/list_memberships` | GET | Bearer, User | `list.read` | 75 / 75 |
| `/lists` | POST | User | `list.write` | 300 / — |
| `/lists/:id` | PUT | User | `list.write` | 300 / — |
| `/lists/:id` | DELETE | User | `list.write` | 300 / — |
| `/lists/:id/members` | POST | User | `list.write` | 300 / — |
| `/lists/:id/members/:uid` | DELETE | User | `list.write` | 300 / — |
| `/users/:id/followed_lists` | POST | User | `list.write follows.write` | 50 / — |
| `/users/:id/followed_lists/:list_id` | DELETE | User | same | 50 / — |
| `/users/:id/pinned_lists` | GET | User | `list.read` | 15 / — |
| `/users/:id/pinned_lists` | POST | User | `list.write` | 50 / — |
| `/users/:id/pinned_lists/:list_id` | DELETE | User | `list.write` | 50 / — |

## Spaces

| Endpoint | Method | Auth | Scopes | Rate limits |
|----------|--------|------|--------|-------------|
| `/spaces/:id` | GET | Bearer, User | `space.read tweet.read users.read` | 300 / 300 |
| `/spaces` | GET (bulk) | Bearer, User | same | 300 / 300 |
| `/spaces/:id/tweets` | GET | Bearer, User | same | 300 / 300 |
| `/spaces/by/creator_ids` | GET | Bearer, User | same | 300 + 1/sec |
| `/spaces/:id/buyers` | GET | Bearer, User | same | 300 / 300 |
| `/spaces/search` | GET | Bearer, User | same | 300 / 300 (max 100 results) |

## Media

All media endpoints accept OAuth 2.0 user or OAuth 1.0a. Chunked upload for > 5 MB or videos.

| Endpoint | Method | Rate limits | Notes |
|----------|--------|-------------|-------|
| `/media/upload` | POST (simple) | 500 / 50,000 per 24h | Images up to 5 MB |
| `/media/upload` | GET (status) | 1,000 / 100,000 per 24h | Poll async processing |
| `/media/upload/initialize` | POST | 1,875 / 180,000 per 24h | Start chunked upload |
| `/media/upload/:id/append` | POST | 1,875 / 180,000 per 24h | Each chunk ≤ 5 MB |
| `/media/upload/:id/finalize` | POST | 1,875 / 180,000 per 24h | Returns processing state |
| `/media/metadata` | POST | 500 / 50,000 per 24h | Alt-text, tagged users |
| `/media/subtitles` | POST | 100 / 10,000 per 24h | WebVTT |
| `/media/subtitles` | DELETE | 100 / 10,000 per 24h | |

**Constraints:** JPG/PNG/GIF/WEBP ≤ 5 MB (GIF ≤ 15 MB chunked). Video: H.264 HP, 30–60 FPS, 32×32 to 1280×1024, ≤ 512 MB, 0.5–140s, YUV 4:2:0. GIFs: ≤ 1280×1080, ≤ 350 frames, ≤ 300M pixels. `media_id` valid 24h.

Post attaches ≤ 4 photos, OR 1 GIF, OR 1 video.

## Streaming (Pro+)

| Endpoint | Method | Auth | Rate limits |
|----------|--------|------|-------------|
| `/tweets/search/stream` | GET | Bearer | Connection-based |
| `/tweets/search/stream/rules` | GET | Bearer | — |
| `/tweets/search/stream/rules` | POST | Bearer | — |
| `/tweets/sample/stream` | GET (1% sample) | Bearer | Connection-based |
| `/tweets/sample10/stream` (10%) | GET | Bearer (Enterprise) | Connection-based |
| `/tweets/compliance/stream` | GET | Bearer | Connection-based |

Rule/connection limits per tier:
- **Pro:** 1 connection, 25 rules × 512 chars
- **Enterprise:** multiple connections, 1,000 rules × 1,024 chars, redundant connections allowed

## Trends

| Endpoint | Method | Auth | Scopes | Rate limits |
|----------|--------|------|--------|-------------|
| `/trends/by/woeid/:id` | GET | Bearer | — | 75 / — |
| `/users/personalized_trends` | GET | User | `users.read tweet.read` | 10/15m + 100/24h (user) · 200/15m + 200/24h (app) |

## Communities & Community Notes

| Endpoint | Method | Auth |
|----------|--------|------|
| `/communities/search` | GET | Bearer |
| `/communities/:id` | GET | Bearer |
| `/communities/:id/members` | GET | Bearer |
| `/notes/search/posts_eligible_for_notes` | GET | Bearer |
| `/notes/search/notes_written` | GET | Bearer |
| `/notes` | POST | User (Community Notes Writer required) |

Limits not published — low-volume, conservative polling recommended.

## Compliance & Usage

| Endpoint | Method | Auth | Rate limits |
|----------|--------|------|-------------|
| `/compliance/jobs` | POST | Bearer | — / 150 |
| `/compliance/jobs` | GET | Bearer | — / 150 |
| `/compliance/jobs/:job_id` | GET | Bearer | — / 150 |
| `/usage/tweets` | GET | Bearer | — / 50 |

Compliance batch jobs upload a list of IDs and return a redacted manifest (deleted/suspended/private). Required for apps storing X data long-term.

## Endpoints NOT in this catalog (rare, consult docs directly)

- Ads API (`/11/...`) — separate product, OAuth 1.0a only
- Account Activity API (webhooks) — enterprise, legacy v1.1 shape
- News search — limited rollout
- Labs / experimental endpoints
