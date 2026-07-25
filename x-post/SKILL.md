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


## ✅ ALWAYS PREFLIGHT FIRST — this is the whole workflow

**Do not attempt a post and see what happens. Check, fix, post once.**

```sh
$GX preflight "<your text>" [media paths...]     # sends nothing, costs nothing
```

It validates auth, remaining daily budget, text length, video duration/size,
image size and attachment count IN ONE CALL, and prints either
`PREFLIGHT PASS — safe to post` or an exact list of what to fix with the fix command.

```
✗ VIDEO clip.mp4: 151.7s > 140s limit. FIX:
      ffmpeg -y -i clip.mp4 -t 139 -c copy clip-140s.mp4
      then post clip-140s.mp4
```

### The rule

1. `preflight` → 2. fix everything it lists → 3. post ONCE.

**If a post fails, run `preflight` to find out why. Do not retry the same thing
unchanged — it will fail identically, every time.**

**NEVER report "X is broken", "the API is down", or "nothing I can do" without
running `preflight` first.** In practice the cause is almost always length, and
length is fixable by you, right now, without asking anyone. Reporting a fixable
problem back to Mike instead of fixing it is the failure — not the original error.

Only escalate when preflight PASSES and the post still fails. That is a genuine
fault worth a human. Anything preflight catches is yours to fix and re-run.


## ⛔ LENGTH LIMITS — the #1 cause of "posting is broken"

**If a post fails, CHECK LENGTH FIRST. It is almost always this.**

| what | hard limit | note |
|---|---|---|
| tweet text | **280 characters** | every URL counts as **23** no matter how long — trimming a link saves nothing |
| video | **140 seconds** | and 0.5s minimum, ≤512 MB, H.264 mp4/mov |
| images | 4 per tweet | ≤5 MB each |

x-guard now checks these BEFORE spending or uploading and tells you the exact
overage plus the fix command. An over-length failure looks like this and is NOT
an API fault:

```
TOO LONG — video is 151.7s, the X limit is 140s. You are 11.7s over.
  THIS IS NOT A BROKEN API and retrying will not help. Trim it first:
    ffmpeg -y -i in.mp4 -t 140 -c copy in-140s.mp4
```

**Do not report "X is broken" or "nothing I can do" on a length failure.** Trim and
retry — that is the whole fix. Retrying the same over-length asset will fail forever.

Trim a video:      `ffmpeg -y -i in.mp4 -t 140 -c copy out-140s.mp4`
Check duration:    `ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 in.mp4`
Count tweet chars: remember URLs = 23 each; if you are near 280, shorten prose, not links.

For a video that MUST stay longer than 140s, X requires a different product tier —
post a trimmed cut plus a link, or split it into a thread of ≤140s clips.


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
