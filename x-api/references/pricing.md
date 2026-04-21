# X API Pricing — Full Reference

**Pricing source of truth:** https://console.x.com (verify before quoting).
**Last cross-checked:** 2026-04-20.

## The model (what changed 2026-02)

On **6 February 2026** X made **Pay-Per-Use** the default for all new developers and removed the Free tier. Basic and Pro remain **legacy-only** — existing subscribers can stay, but new signups cannot opt in. Enterprise is unchanged.

Existing Free-tier developers who were recently active received a **one-time $10 voucher** to migrate onto pay-per-use.

## Pay-Per-Use (default)

**Purchase credits upfront in the Developer Console.** Credits are deducted per API call with real-time tracking. Unused credits roll forward.

### Per-call prices (USD)

| Operation | Cost | Notes |
|-----------|------|-------|
| **Post read** (any GET returning a Post) | $0.005 | dedup'd within UTC day |
| **Post write** (POST /2/tweets) | $0.01 | |
| **Post delete** | $0.01 | counts as a write |
| **User profile lookup** | $0.01 | dedup'd within UTC day |
| **DM send** | $0.01 – $0.015 | depends on media |
| **DM read** | $0.005 | per event returned |
| **Search (recent, per request)** | priced by posts returned | read price × count |
| **Media upload init/append/finalize** | nominal | bundle billed per finalize |
| **Follow / like / retweet action** | $0.01 | write-class |

### Monthly ceiling

**Pay-per-use caps at 2,000,000 post reads/month.** Above that, you must move to Enterprise. X will throttle you at the cap, not auto-bill past it (spending limits are user-configured).

### Deduplication rule (**important, saves real money**)

> All resources are deduplicated within a 24-hour UTC-day window. Requesting the same Post (or same user, etc.) twice within the same UTC day is charged **once**.

Implications:
- Cache keys that include UTC date align perfectly with dedup windows.
- Resetting your cache at UTC midnight is optimal.
- Polling the same post's metrics every 5 minutes = **1 charge/day**, not 288.

### Spend controls

- **Max spend per billing cycle** — hard cap, requests blocked when hit.
- **Auto-recharge** — top up when balance < threshold, with configurable recharge amount.
- **Per-key budgets** (Enterprise/Pro) — allocate limits across projects.

### Bonus

> Purchase X API credits, earn up to 20% back as **free xAI API credits**.

## Legacy Basic — $200/month

**Closed to new signups.** Existing subscribers may remain.

- ~50,000 post writes/month
- ~10,000–15,000 post reads/month
- 2 apps per project
- No full-archive search
- No streaming
- 7-day recent search: ✓
- Annual discount: $175/mo

Rate-limit sample (per-15min): 3,500/5,000 app/user on post lookup; 450/300 app/user on recent search; 500/day app, 100/day user on user lookup.

## Legacy Pro — $5,000/month

**Closed to new signups.** Existing subscribers may remain.

- ~300,000 post writes/month
- 1,000,000 post reads/month
- 3 apps per project
- **Full-archive search** (`/search/all`): ✓
- **Filtered streaming** (1 connection, 25 rules × 512 char): ✓
- 10,000/month media upload allowance higher than Basic
- Annual discount: $4,500/mo

## Enterprise — $42,000–$50,000+/month (starting)

Contract-negotiated. Typical inclusions:
- 50M+ post reads/month (scales with contract)
- Firehose (100% of public posts) and decahose (10%)
- Unlimited rules, multiple redundant stream connections
- Account Activity webhooks
- Compliance batch jobs
- Dedicated Partner Engineer
- Custom rate limits per endpoint
- SLA

Apply: https://developer.x.com/en/products/x-api/enterprise/enterprise-api-interest-form

## Tier access matrix (which endpoints need which tier)

| Capability | PPU | Basic | Pro | Ent |
|---|---|---|---|---|
| Post CRUD | ✓ | ✓ | ✓ | ✓ |
| User lookup / search | ✓ | ✓ | ✓ | ✓ |
| Timelines | ✓ | ✓ | ✓ | ✓ |
| Likes / RT / follow / bookmarks | ✓ | ✓ | ✓ | ✓ |
| DMs | ✓ | ✓ | ✓ | ✓ |
| Lists, Spaces, Trends | ✓ | ✓ | ✓ | ✓ |
| Media upload (simple + chunked) | ✓ | ✓ | ✓ | ✓ |
| Recent search (7d) | ✓ | ✓ | ✓ | ✓ |
| **Full-archive search** | ✗ | ✗ | ✓ | ✓ |
| Post counts (all) | ✗ | ✗ | ✓ | ✓ |
| **Filtered stream** | ✗ | ✗ | ✓ (25 rules) | ✓ (1,000 rules) |
| Sample stream (1%) | ✗ | ✗ | ✓ | ✓ |
| Decahose (10%) | ✗ | ✗ | ✗ | ✓ |
| **Firehose** (100%) | ✗ | ✗ | ✗ | ✓ |
| Compliance batch jobs | limited | ✓ | ✓ | ✓ |
| Account Activity webhooks | ✗ | ✗ | ✗ | ✓ |

## Cost-estimation worksheet

### Quick formula

```
monthly_reads  = DAU × reads_per_user_per_day × 30 × (1 - cache_hit_rate)
monthly_writes = DAU × writes_per_user_per_day × 30
monthly_cost   = monthly_reads × 0.005 + monthly_writes × 0.01
```

### Worked examples (pay-per-use)

**Example 1: indie hacker, 1k DAU social dashboard.**
- Each user views 10 posts/day (fresh reads — after cache = 3 fresh).
- 1,000 × 3 × 30 = 90,000 reads/mo → **$450/mo**.
- Below Basic's 10–15k read cap, so PPU is cheaper than Basic's $200 + overage (Basic only suits if you're posting thousands of writes/mo).

**Example 2: auto-poster, 1 write/5min.**
- 288 writes/day × 30 = 8,640 writes/mo → **$86.40/mo**.
- PPU wins unless you also do heavy reads.

**Example 3: brand-mention monitor, polls recent search every minute.**
- 60 × 24 × 30 = 43,200 search requests/mo. Each returns ~30 posts.
- Posts counted: ~1.3M reads/mo → **$6,500/mo**. Search-request rate limit of 450/15m = 1,800/hr exceeds 60 — you're fine on rate, but $$$ is brutal.
- Fix: switch to `since_id`, reduce to every 5 min → ~$1,300/mo, still expensive. **Better:** use filtered stream (requires Pro $5k flat — break-even at ~$5k PPU).

**Example 4: analytics product, 100k DAU.**
- 100k × 50 reads/day × 30 × (1 - 0.8 cache) = 30M reads/mo.
- **30M × $0.005 = $150,000/mo → must negotiate Enterprise.**

### When to upgrade

| Your projected monthly reads | Cheapest option |
|---|---|
| < 40,000 | PPU (<$200) |
| 40,000 – 200,000 | PPU ($200 – $1,000) |
| 200,000 – 1,000,000 | PPU ($1k – $5k) — consider Pro if you also need streaming or archive |
| 1,000,000 – 2,000,000 | **Pro $5k/mo** usually cheaper if reads > 1M |
| > 2,000,000 | **Enterprise** (PPU is capped) |

### When to upgrade (writes)

| Monthly post writes | Cheapest option |
|---|---|
| < 20,000 | PPU ($200 or less) |
| 20,000 – 50,000 | PPU ~ Basic parity — pick Basic if you want predictable monthly |
| 50,000 – 300,000 | Pro ($5k) likely wins for heavy posting + reads |
| > 300,000 | Enterprise |

## Cost-control checklist

- [ ] Cache reads keyed by post ID + UTC date.
- [ ] Use bulk-lookup (`?ids=a,b,c`) — same dedup but fewer HTTP calls.
- [ ] Set a max-spend cap in Developer Console before first deploy.
- [ ] Log `x-rate-limit-remaining` AND estimated credit spend per endpoint.
- [ ] Use filtered stream for anything polling-like at scale.
- [ ] Honor `since_id`/`until_id` to avoid re-pulling posts you already have.
- [ ] Degrade gracefully on 429 — don't retry-spam and burn credits on failures.
