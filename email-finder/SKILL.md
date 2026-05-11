---
name: email-finder
description: "Find a person's business email from name + company/domain using Hunter.io (primary), Snov.io (fallback), and Apollo.io (company enrichment). Use when the user has a contact list with names but no email addresses, or asks 'find an email for <name> at <company>'."
metadata: {"openclaw": {"emoji": "🔎", "requires": {"env": ["HUNTER_API_KEY", "SNOV_USER_ID", "SNOV_SECRET", "APOLLO_API_KEY"], "anyBins": ["curl", "bash"]}}}
---

# Email Finder Skill

Find business email addresses for prospects when you only have a name + company. Three providers, tried in order — Hunter.io is the primary; Snov.io and Apollo.io fall in behind for redundancy and company-level enrichment.

## When to Use

Trigger on any of:
- "find email for <person> at <company>"
- "look up <name> at <domain>"
- User has a contacts list / CRM page / outreach list with names but no email
- Email Finder Hub canvas page (`canvas-pages/email-finder-hub.html`) sends a `Use Hunter.io to look up emails for...` instruction
- Cold-outreach or prospect-research workflow that needs a verified contact email

DO NOT use this for:
- Looking up email content (use the `agentmail` skill)
- Sending email (use `agentmail` skill — and remember the double-confirmation rail)

## Helper Scripts (preferred)

All under `/mnt/shared-skills/email-finder/`:

| Script | Purpose | Cost |
|---|---|---|
| `find-email.sh "<first>" "<last>" "<domain>" [--provider hunter\|snov\|apollo\|all]` | Per-person lookup. Tries Hunter → Snov → Apollo, prints highest-confidence hit as JSON, short-circuits on Hunter ≥80%. | 1 Hunter search credit (+1 Snov if Hunter misses) |
| `domain-search.sh <domain> [limit]` | Returns the org's email pattern + ~10 crawled named addresses. **Use this FIRST for batch work** — see Recommended Flow below. | 1 Hunter search credit |
| `verify-email.sh <email>` | Confirms whether an address is deliverable + scores it. Use freely on pattern-derived guesses. | 1 Hunter verification credit (100/mo, separate from searches) |
| `quota.sh [--hunter\|--snov] [--raw]` | Show remaining Hunter searches + verifications + Snov credits. Run before any batch. | free |

```bash
find-email.sh "Joel" "Pressley" "insulate48.com"
# → {"email":"joel@insulate48.com","confidence":99,"source":"hunter","name":"Joel Pressley"}

domain-search.sh insulate48.com
# → {"data":{"pattern":"{first}","emails":[{"value":"joel@insulate48.com","confidence":99,...}]}}

verify-email.sh joel@insulate48.com
# → {"data":{"status":"valid","score":100,"mx_records":true,"smtp_check":true,...}}

quota.sh
# → Hunter (Free, resets 2026-06-04):
#     searches:      28/50 used
#     verifications: 56/100 used
#   Snov:
#     balance:      50.00 credits
#     resets in:    29 days
```

## Provider Reference (when you need to call APIs directly)

### Hunter.io — PRIMARY (highest confidence, broadest coverage)

**Auth:** `?api_key=$HUNTER_API_KEY` query param
**Docs:** https://hunter.io/api-documentation

Email finder by name + domain:
```bash
curl -sS "https://api.hunter.io/v2/email-finder?domain=insulate48.com&first_name=Joel&last_name=Pressley&api_key=$HUNTER_API_KEY"
```
Returns `data.email`, `data.score` (0-100 confidence), `data.sources[]` (where Hunter saw it).

Domain search (all emails on a domain):
```bash
curl -sS "https://api.hunter.io/v2/domain-search?domain=insulate48.com&api_key=$HUNTER_API_KEY"
```

Verify an existing email:
```bash
curl -sS "https://api.hunter.io/v2/email-verifier?email=joel@insulate48.com&api_key=$HUNTER_API_KEY"
```

### Snov.io — FALLBACK (50 free credits / 30-day reset)

**Auth:** OAuth2 client_credentials, get a bearer token first
**Account ID:** 4073278 | **Plan:** free, v1 endpoints only (v2 returns 403)

```bash
TOKEN=$(curl -sS -X POST "https://api.snov.io/v1/oauth/access_token" \
  -d "grant_type=client_credentials&client_id=$SNOV_USER_ID&client_secret=$SNOV_SECRET" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
```

Email finder by name + domain (the workhorse — costs 1 credit per lookup):
```bash
curl -sS -X POST "https://api.snov.io/v1/get-emails-from-names" \
  -d "access_token=$TOKEN&firstName=Joel&lastName=Pressley&domain=insulate48.com"
```
Returns `data.emails[]` array (may be empty if Snov hasn't crawled the prospect — try Hunter first to save credits).

Check domain coverage before spending a credit:
```bash
curl -sS -X POST "https://api.snov.io/v1/get-domain-emails-count" \
  -d "access_token=$TOKEN&domain=insulate48.com"
```

Check remaining balance:
```bash
curl -sS -X GET "https://api.snov.io/v1/get-balance" -H "Authorization: Bearer $TOKEN"
```

### Apollo.io — COMPANY ENRICHMENT ONLY (free plan blocks people endpoints)

**Auth:** `X-Api-Key: $APOLLO_API_KEY` header
**Plan:** free — `people/match` and `mixed_companies/search` return `API_INACCESSIBLE`. Use ONLY for company-level data.

Company enrichment (returns LinkedIn URL, phone, address, employee count):
```bash
curl -sS -X POST "https://api.apollo.io/v1/organizations/search" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q_organization_domains":"insulate48.com"}'
```

Auth check:
```bash
curl -sS "https://api.apollo.io/v1/auth/health" -H "X-Api-Key: $APOLLO_API_KEY"
```

## Recommended Flow

### Single-person lookup (one-off)

1. **If you only have a company name (no domain):** Apollo `organizations/search` to get the domain + LinkedIn first.
2. **If you have name + domain:** `find-email.sh "<first>" "<last>" "<domain>"` — uses Hunter, falls through to Snov on miss.
3. **If both miss:** report "no high-confidence email found" — do not guess. Suggest the user verify via LinkedIn (Apollo enrichment gives the LinkedIn URL).

### Batch / contacts-list lookup — PATTERN-FIRST (preferred for >3 prospects)

This is the credit-efficient path. **Validated 2026-05-11 on FoamBook: ~40 hits off ~26 search credits**, vs. the brute-force per-person path which would have spent ~40 credits. Use this any time you have a list of named prospects against a smaller set of company domains.

1. **Per company:** `domain-search.sh <domain>` — costs **1 Hunter credit** and returns:
   - `data.pattern` — the org's email pattern (e.g. `{first}.{last}`, `{f}{last}`, `{first}`)
   - `data.emails[]` — ~10 already-crawled named addresses with confidence scores
2. **For each known person:** check if they're already in `data.emails[]` (free hit). If not, derive their address from the pattern (e.g. pattern `{first}.{last}` + person `Joel Pressley` + domain `insulate48.com` → `joel.pressley@insulate48.com`).
3. **Verify the derived address:** `verify-email.sh <derived-email>` — costs **1 verification credit** (separate quota: 100/month vs 50 search/month). Look at `data.status == "valid"` + `data.score >= 70`.
4. **Only fall to per-person `find-email.sh`** for people Hunter has zero crawl on (often small/regional contractors). That's where Snov fallback earns its keep.

**Check quota before starting a batch:** `quota.sh` shows Hunter searches+verifications used and Snov credits remaining. If you're below 5 search credits, switch to verify-only / Snov-only modes.

### Always

- **Check the confidence score** before handing the email to a compose form. Below 70% = warn the user.
- **Never blast** the result into an outbound email without the [APPROVAL NEEDED] double-confirmation rail (see `TOOLS.md` line 17 in any josh-style workspace).
- **Never fabricate** when all sources miss — guesses fail SPF/DMARC and damage sender reputation.

## Cost Awareness

| Provider | Free quota | Cost per lookup |
|---|---|---|
| Hunter.io | **50 searches + 100 verifications / month, resets the 4th** (Mike's current Free plan — verified 2026-05-11 by residential-laptop) | 1 search credit per `email-finder` call, 1 verification credit per `email-verifier` call |
| Snov.io | 50 credits / 30-day reset | 1 credit per `get-emails-from-names` call |
| Apollo.io | unlimited org searches on free plan | free for company endpoints; people endpoints LOCKED |

When you batch-find emails for a contacts list, prefer Hunter for the first pass and only spend Snov credits on Hunter misses.

## Stored State (per-tenant)

If working in a tenant that uses the Email Finder Hub canvas page (e.g. josh):
- Page: `canvas-pages/email-finder-hub.html` — has a green Hunter.io lookup panel that posts a `canvas-action` message to the agent
- Memory file: `workspace/memory/2026-04-05.md` documents which prospects already have emails found and CRM opp IDs
- After finding an email, post `{type:'hunter-result', email, name, title, confidence}` back via `window.parent.postMessage` so the canvas panel renders the green result card

## Failure Modes

- `HUNTER_API_KEY` missing or expired → 401 from Hunter; fall through to Snov.
- Snov OAuth returns `{"success":false}` → key regenerated, fetch fresh from `.platform-keys.env` / `.openclaw-keys.env`.
- Snov v2 endpoint returns 403 → expected on free plan; use the v1 endpoints listed above.
- Apollo `people/match` returns `API_INACCESSIBLE` → expected on free plan; do NOT retry.
- All three return empty → tell the user "no email found"; do not fabricate.
