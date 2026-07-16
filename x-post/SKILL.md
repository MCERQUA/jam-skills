---
name: x-post
description: How a JamBot character agent posts to and reads X/Twitter SAFELY through the per-tenant x-guard.py wrapper (hard $1/day spend cap). Covers text, images (1–4), uploaded video, GIF, alt-text, replies/quotes/retweets/likes, delete, own-account reads, and the cost of every action. TRIGGER when the agent is asked to post/tweet/reply on X, attach an image or video, check its own X account, or reason about X API spend. Requires the tenant to have X creds in ~/.openclaw/.env + bin/x-guard.py (currently: @kyle_bhb). This is the OPERATIONAL how-to; the generic API reference is the `x-api` skill.
---

# x-post — posting to X/Twitter via x-guard.py

**You have your OWN X/Twitter account.** Every X call MUST go through the wrapper
`~/.openclaw/workspace/bin/x-guard.py`. **NEVER raw-curl `api.x.com`** — the wrapper is the
only thing enforcing the **$1.00/day hard spend cap**, per-action cost tracking, the credit-
balance estimate, and the low-balance alarm. Raw calls bypass all of that and can drain the
account's pay-per-use credits.

## ⚠️ CREDENTIAL ISOLATION — this skill is GLOBAL, credentials are NOT

This is a shared/global skill (the same how-to for every tenant), but **X credentials are
strictly per-tenant and never global.** There is no shared or platform X account:

- `x-guard.py` reads credentials **only** from **your own** `~/.openclaw/.env` file — it never
  reads environment variables, the platform keys file, or any path outside your workspace.
- Your container mounts **only your own** tenant directory as `~/.openclaw`, so you cannot see
  or use any other tenant's `.env`, and they cannot see yours.
- The platform/host X keys are **not** mounted into tenant containers and are **not** the account
  you post from. You post **only** as your own account.
- To give a NEW tenant X access, drop **that tenant's own** X app credentials into **their** own
  `~/.openclaw/.env` — never copy one account's keys to another. One tenant = one X account.

If `~/.openclaw/.env` has no X credentials (OAuth 1.0a user-context for posting/own-account +
Bearer for public reads), this skill simply does not apply to your tenant — there is no fallback
to anyone else's account.

## Commands

```bash
GX="python3 ~/.openclaw/workspace/bin/x-guard.py"

# --- read ---
$GX whoami                                  # confirm the logged-in account (own read, ~$0.001)
$GX search "<query>" [10-100]               # public recent search (post read $0.005 each)
$GX get <tweet_id>                          # read one tweet's text/author/metrics ($0.005)
$GX balance                                 # today's spend, remaining $1 budget, est. balance

# --- post (text + media) ---
$GX post "<text>"                           # standalone tweet ($0.015; $0.20 if it has a URL)
$GX post-image <path> "<text>" [alt]        # tweet with ONE image (+ optional alt-text)
$GX post-images <p1,p2,p3,p4> "<text>"      # up to 4 images in one tweet
$GX post-video <path.mp4> "<text>" [alt]    # UPLOADED video (chunked; H.264 mp4/mov, ≤512MB, 0.5–140s)
$GX post-gif <path.gif> "<text>" [alt]      # animated GIF

# --- engage ---
$GX reply <tweet_id> "<text>"               # threaded reply (it IS a post)
$GX reply-image <tweet_id> <path> "<text>" [alt]
$GX reply-video <tweet_id> <path.mp4> "<text>" [alt]
$GX quote <tweet_id> "<text>"               # quote-tweet
$GX retweet <tweet_id>                      # retweet (no text)
$GX like <tweet_id>                         # like
$GX delete <tweet_id>                       # delete one of YOUR OWN tweets ($0.010)

# --- ops ---
$GX set-balance <dollars>                   # re-seed the credit estimate after Mike tops up
```

`tweet` is an alias for `post`. Commands accept `_` or `-` (`post_video` == `post-video`).

## Media rules (X-enforced)

- **Images:** JPG/PNG/GIF/WEBP ≤ 5 MB. Up to **4 photos** per tweet, OR **1 GIF**, OR **1 video** — never mixed.
- **Video:** H.264 High Profile, mp4/mov, ≤ 512 MB, **0.5–140 s**, 32×32–1280×1024. `post-video` chunk-uploads it and waits for X to finish transcoding before tweeting. If your source is longer than 140 s, trim it first (`ffmpeg -t 140 …`).
- **Always add `alt` text** for accessibility when you can — it's the trailing optional arg on any media command (~$0.005 metadata).
- Media is uploaded from a **local file path** (e.g. under `~/.openclaw/workspace/uploads/`), never a URL. Generated assets are already saved to the server — post them by path.

## Cost of each action (matches live X pay-per-use, verified 2026-07-16)

| Action | Cost | Notes |
|---|---|---|
| post / reply / quote | **$0.015** | **$0.200 if the text contains a URL** — avoid links where you can |
| post-image / -images / -video / -gif | $0.015 (+$0.005 if alt) | media upload itself is bundled into the write |
| retweet | $0.015 | |
| like | $0.005 | |
| delete | $0.010 | |
| whoami (own read) | $0.001 | cheapest |
| search / get (post read) | $0.005 × posts returned | dedup'd within the UTC day |

The `$1.00/day` cap resets at **00:00 UTC**. When a call would exceed it, x-guard refuses with
`BLOCKED — $1.00/day cap`. That is working-as-designed, not an error — wait for reset or ask Mike.

## Doctrine (how to behave on a live public account)

- **URLs are ~13× a normal post.** Only include a link when it genuinely matters.
- **Mentions/replies to you are surfaced for review, not auto-answered.** When you find replies to
  your posts or @-mentions, draft responses and get owner approval before sending; flag noteworthy
  ones to Mike. (Owner-facing doctrine — you serve the business owner, you don't autonomously run
  the public account.)
- **Every generated asset is already on the server** — post by path; don't regenerate to post.
- Check `balance` before a media-heavy session so you don't hit the cap mid-thread.

## Related

- **`x-api`** skill — the generic X API v2 reference (auth flows, full endpoint catalog, rate limits, pricing worksheet). Read it when you need API detail x-guard doesn't expose.
- Platform cost visibility: X spend rolls up per-tenant into the admin cost dashboard (`usage-costs` canvas page) via `scripts/jambot-usage-costs.py`.
