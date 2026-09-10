---
name: foambook
description: "Query and edit the FoamBook — a global directory of the spray foam insulation industry (1,283 companies / 1,103 contacts as of 2026-05-11). API at https://foambook.jam-bot.com. Any agent can read; mutations require the FOAMBOOK_API_KEY bearer. Use when asked about SPF contacts, companies, NAFA/SPFA rosters, 'do you know X at Y', adding a new contact/company, or enriching the directory."
metadata: {"openclaw": {"emoji": "🫧", "requires": {"env": ["FOAMBOOK_API_KEY"], "anyBins": ["curl", "python3"]}}}
---

# FoamBook — global SPF-industry directory

FoamBook is a shared platform service. Every agent on the JamBot mesh can READ for free; any mutation requires the bearer key. Lives at `https://foambook.jam-bot.com`.

## Where things live

- **API + UI:** `https://foambook.jam-bot.com`
- **Data on host:** `/mnt/system/base/foambook/` (foambook.db, photos/, app.py, etc.)
- **Service:** `systemctl status jambot-foambook` (uvicorn at 127.0.0.1:8765, nginx fronts SSL)
- **Auth key:** `$FOAMBOOK_API_KEY` (in `.platform-keys.env`, distributed via mesh secrets)

## When to use

- "Do you know <person>?" / "What do we have on <company>?"
- "Add <person> at <company> with role <X> and email <Y>"
- "Show me everyone at <company>" / "Show me all manufacturers / distributors / NAFA people"
- Any cross-tenant SPF-industry data question
- Enriching contacts (after running email-finder or headshot-finder, PUT the result back to FoamBook)

## When NOT to use

- Per-tenant CRM data (use `crm` skill — Twenty CRM)
- Industry research that's not directly contact/company data (use `social-research` or web-research sub-agents)
- Anything Facebook-related (FB ban risk; FoamBook explicitly avoids FB)

## Helper script (preferred)

`/mnt/shared-skills/foambook/foambook.sh <subcommand> [args...]`

Subcommands:

| sub | args | what it does | auth needed |
|---|---|---|---|
| `search` | `<query>` `[--limit N]` | search contacts (matches first/last/company/notes) | no |
| `contact` | `<id>` | get contact by id | no |
| `company` | `<id>` | get company by id | no |
| `companies` | `[--segment <X>] [--q <q>]` | list companies (filter by segment / search) | no |
| `add-contact` | `<first> <last> --company-id <N> [--role X] [--email X] [--phone X] [--notes X]` | create a new contact | YES |
| `update-contact` | `<id> --field value [--field value...]` | update a contact (any column) | YES |
| `add-company` | `<name> [--segment X] [--website X] [--phone X] [--notes X]` | create a new company | YES |
| `update-company` | `<id> --field value [...]` | update a company | YES |
| `set-photo` | `<contact_id> <local-image-path>` | upload a headshot for a contact | YES |
| `set-logo` | `<company_id> <local-image-path>` | upload a logo for a company | YES |

## Direct curl (when the wrapper is overkill)

Read (no auth):
```bash
curl -sS 'https://foambook.jam-bot.com/api/contacts?q=Pressley'
curl -sS 'https://foambook.jam-bot.com/api/companies?segment=manufacturer'
curl -sS 'https://foambook.jam-bot.com/api/contacts/66'
```

Write (auth required):
```bash
curl -sS -X POST 'https://foambook.jam-bot.com/api/contacts' \
  -H "Authorization: Bearer $FOAMBOOK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Joel","last_name":"Pressley","company_id":42,"role":"Field Supervisor","email":"joel@insulate48.com"}'

curl -sS -X PUT 'https://foambook.jam-bot.com/api/contacts/66' \
  -H "Authorization: Bearer $FOAMBOOK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"phone":"(817) 677-1200","notes":"updated 2026-05-11"}'
```

The header can also be `X-FoamBook-Key: $FOAMBOOK_API_KEY` if Authorization is awkward.

## Endpoint reference (full surface)

| method | path | purpose |
|---|---|---|
| GET | `/api/contacts?q=&level=&company_id=` | search/list contacts |
| GET | `/api/contacts/{id}` | one contact (with children + print_orders) |
| POST | `/api/contacts` | create contact |
| PUT | `/api/contacts/{id}` | update contact |
| DELETE | `/api/contacts/{id}` | delete contact |
| POST | `/api/contacts/{id}/photo` | upload headshot (multipart) |
| GET | `/api/companies?segment=&q=` | search/list companies |
| GET | `/api/companies/{id}` | one company |
| POST | `/api/companies` | create company |
| PUT | `/api/companies/{id}` | update company |
| DELETE | `/api/companies/{id}` | delete company |
| POST | `/api/companies/{id}/logo` | upload logo (multipart) |
| GET | `/api/segments` | list of valid segments (manufacturer/equipment/distributor/contractor/rep/association/media/insurance/training/service/other) |
| GET | `/api/slideshow` | curated showcase contacts |
| GET | `/slideshow` | UI slideshow page |
| GET | `/{anything-else}` | static UI files (the FoamBook web app) |

## Schema gotchas

- `contacts` has `first_name` + `last_name` (NO `name` col)
- `companies` has `website` (NO `domain` col); may contain extra text — strip protocol/path before piping to email/headshot finders
- `contacts.company_id` is the FK; the older `contacts.company` string col is a denormalized cache from before the FK existed. **When you create/update, set BOTH `company_id` AND `company` (the company name string) so the legacy denorm stays consistent.**
- Confidence scores from email/headshot finders go in the `notes` field, not their own column

## Source of new data

Most new contacts/companies arrive via two channels:
1. **`residential-laptop@mesh`** runs the FB browser scraper + web-research sub-agents and POSTs results to this API. It's the dominant write source.
2. **Voice agent on `foambot.jam-bot.com`** — Mike asks foambot to add or correct an entry conversationally, foambot translates to API calls.

Other agents can read freely; before writing, check if residential or foambot already covers your case so you don't create dupes.

## When you spot a data quality issue

- Don't silently fix — Mike + residential have a documented review pattern
- Add a `FLAG <date> (<your-agent>):` line to the contact's `notes` field via PUT
- If it's a dup, flag both records — let foambot decide the merge

## Hard rules

- ❌ Never POST/PUT without the bearer key (server returns 401, costs nothing)
- ❌ Never use Facebook to enrich a FoamBook record (FB ban risk on Mike's account)
- ❌ Never auto-tag a confidence-< 70 enrichment hit as canonical email/photo — put it in notes
- ✅ Always include a `source` string when creating new records ("foambot voice 2026-05-11", "residential dig_log Round 9", "host@mesh email-finder enrichment")
