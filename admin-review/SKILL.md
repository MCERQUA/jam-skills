---
name: admin-review
description: "Hold consequential agent actions for Mike's email approval before executing. Generalizes the existing [APPROVAL NEEDED] email-send rail to a broader trigger surface: destructive operations, big jobs, vague requests, cross-tenant changes, identity/auth changes. Use BEFORE doing anything that matches the 5 trigger categories — this skill files the request, emails Mike, and tells the user to wait."
metadata: {"openclaw": {"emoji": "🚧", "requires": {"env": ["AGENTMAIL_API_KEY"], "anyBins": ["curl", "python3"]}}}
---

# Admin Review Rail

A user request triggered one of the 5 review categories below. Do **not** execute it. File a review request via this skill; tell the user you're waiting on Mike. Mike replies to the email; the cron resolves the request; you check status when the user asks again.

## The 5 trigger categories — be paranoid, not optimistic

If you're unsure, file the review. Mike approves cheap, recovery from a bad action is expensive.

| # | Category | Examples — file review for any of these |
|---|---|---|
| 1 | **Destructive** | DELETE on FoamBook (any agent, any record), contact merges, bulk UPDATEs (>10 rows), workspace file deletions, container restarts, cron schedule changes, mesh secret rotations |
| 2 | **Big jobs (cost/time)** | Anything that consumes >$5 paid API budget (DataForSEO, Hunter, Suno, Meshy, etc.), runs >5 min compute, touches >50 records, creates >10 new files, deploys nginx/SSL/systemd changes |
| 3 | **Vague / incomplete** | Anything you can't restate in 1 sentence with concrete subject + verb + object. "Update everyone's emails" / "fix the thing" / "send messages to all" / "clean up the data" — file review and ask for specifics in the body |
| 4 | **Cross-tenant** | Anything affecting >1 tenant's data; changes to global skills / templates / shared platform code / `/mnt/system/base/` |
| 5 | **Identity / auth** | Adding to `identity-registry.json`, rotating API keys, modifying Clerk allowlists, granting mesh access to a new agent |

The existing email-send double-confirmation rail (TOOLS.md ⛔ section) is an INSTANCE of this — outbound emails are always category 1 (destructive: irreversible, public). If you're already going through the email rail for an outbound email, you don't need to also file an admin-review for the same action.

## Usage

```bash
/mnt/shared-skills/admin-review/admin-review.sh request \
    "<tenant>" \
    "<one-line-summary>" \
    "<full-details-multiline>"
```

What it does:
1. Generates a request ID (`AR-<YYYYMMDD>-<short-uuid>`)
2. Writes pending file at `/mnt/agent-mesh/admin-review/pending/<id>.md`
3. Sends an AgentMail to `mikecerqua@gmail.com`:
   - Subject: `[ADMIN REVIEW] <tenant>: <summary>`
   - Body: full details + request ID + how Mike approves/rejects
4. Prints the request ID to stdout

The agent then tells the user (in their own words):
> "Holding this for Mike's review (request <id>). I'll proceed when he approves."

## Checking status (when user asks again)

```bash
/mnt/shared-skills/admin-review/admin-review.sh status <request-id>
```

Returns one of:
- `pending` — Mike hasn't replied; show the user "still waiting on Mike."
- `approved` — execute the action now; tell the user "Mike approved, doing it."
- `rejected` — do NOT execute; relay Mike's note to the user.
- `unknown` — the request ID doesn't exist; check your typing.

## What goes in `<full-details-multiline>` — required fields

The body MUST give Mike enough to decide without back-and-forth. Include:

- **Who asked:** the user's exact phrasing (quote it)
- **What you'd do:** the exact command/API call/file edit you would execute, fully specified
- **Why this triggered review:** which of the 5 categories applies
- **Reversibility:** is this action reversible? if so how? if not, say so
- **Blast radius:** which records / tenants / files are affected, how many
- **Cost:** estimated $ cost if applicable

A good admin-review body lets Mike type `APPROVE <id>` or `REJECT <id> <reason>` in 30 seconds. A bad one makes him ask follow-up questions and that's wasted time on both sides.

## Mike's response flow (for context — you don't drive this)

1. Mike receives the email at `mikecerqua@gmail.com`
2. Mike replies with `APPROVE <request-id>` or `REJECT <request-id> <reason>` in the first line of the body
3. A host cron (`scripts/admin-review-poll-replies.sh`) polls AgentMail every 5 minutes, finds replies, moves the request from `pending/` to `resolved/<id>.md` with the disposition + Mike's note
4. Re-ping cron (`scripts/admin-review-reping.sh`) runs hourly, re-emails Mike for any request still pending after 4 hours (records each re-ping in `repinged/<id>.md` so it doesn't double-fire within the window)

## Hard rules

- ❌ Never execute a triggered action while waiting — the whole point is the gate
- ❌ Never bypass with a "just this once" — every triggered action goes through; consistency is the contract
- ❌ Never email Mike directly with the request — go through the helper so it's recorded in the queue
- ❌ Never tell the user "Mike said yes" without checking the status — Mike's silence is NOT approval
- ✅ When in doubt, file. Mike approves cheap.
- ✅ Be SPECIFIC in the body so Mike can decide without follow-up
- ✅ When the user re-asks, check status first, don't re-file
