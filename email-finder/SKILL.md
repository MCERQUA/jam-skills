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

## Helper Script (preferred)

`/mnt/shared-skills/email-finder/find-email.sh "<first>" "<last>" "<domain>" [--provider hunter|snov|apollo|all]`

Defaults to `--provider all`, which tries Hunter → Snov → Apollo and prints the highest-confidence hit. Output is JSON to stdout, errors to stderr, exit code 0 only when at least one provider returned an email.

```bash
/mnt/shared-skills/email-finder/find-email.sh "Joel" "Pressley" "insulate48.com"
# → {"email":"joel@insulate48.com","confidence":99,"source":"hunter","name":"Joel Pressley"}
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

1. **If you only have a company name (no domain):** Hunter `domain-search` with `company` param, OR Apollo `organizations/search` to get the domain + LinkedIn first.
2. **If you have name + domain:** Hunter `email-finder` first. If `data.email` is null or score < 50, fall through to Snov `get-emails-from-names`.
3. **If both miss:** report "no high-confidence email found" — do not guess. Suggest the user verify via LinkedIn (Apollo enrichment gives the LinkedIn URL).
4. **Always check the confidence score** before handing the email to a compose form. Below 70% = warn the user.
5. **Never blast** the result into an outbound email without the [APPROVAL NEEDED] double-confirmation rail (see `TOOLS.md` line 17 in any josh-style workspace).

## Cost Awareness

| Provider | Free quota | Cost per lookup |
|---|---|---|
| Hunter.io | 25 searches/month free, paid plans go from there | ~1 search credit per email-finder call |
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
