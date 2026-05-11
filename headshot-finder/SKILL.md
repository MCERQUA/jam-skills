---
name: headshot-finder
description: "Find a headshot photo for a named person at a known company, WITHOUT touching their Facebook account (zero FB-ban risk). Tries Hunter.io (returns LinkedIn URL), Google Images via DataForSEO (top-ranked headshots), and company-website team pages via a web-research sub-agent. Use when enriching contacts with photos for FoamBook, CRM, outreach, or directory builds."
metadata: {"openclaw": {"emoji": "📸", "requires": {"env": ["HUNTER_API_KEY", "DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"], "anyBins": ["curl", "python3"]}}}
---

# Headshot Finder Skill

Find a headshot photo for a named contact, **never touching Facebook**. FB headshot scraping at scale (1000+ sequential profile fetches) is a textbook scraping fingerprint and risks bans on the operator's personal FB account — see the email-finder skill's risk note for why we route around FB entirely.

## When to Use

Trigger on any of:
- "find a headshot for <person> at <company>"
- "get photos for everyone in FoamBook / our contacts list / this CRM"
- "enrich [contact list] with photos"
- Outreach prep where you want to show the recipient + their photo to the user before sending

DO NOT use this for:
- Facebook profile photo scraping (forbidden — risks FB ban on operator account)
- Public-figure / news-event photos (use generic image search; this skill is targeted at business contacts)

## Provider order (zero-FB-risk stack)

| Order | Source | What it returns | Cost | Risk |
|---|---|---|---|---|
| 1 | Hunter.io `email-finder` | `linkedin_url` field (no photo, but record it for manual visit) | already-paid Hunter search credit OR free if email already known | none |
| 2 | DataForSEO Google Images SERP | Top image results for `"First Last" Company headshot` — filter for LinkedIn-hosted (`media.licdn.com`), then company-domain hosted, then anything else | DataForSEO API call (~$0.0006 per query) | none |
| 3 | Company website team page (sub-agent) | Sub-agent fetches `https://<domain>/about` `/team` `/leadership` `/our-people`, finds entry for `<Name>`, extracts `<img>` URL | Claude sub-agent tokens | none |
| 4 | Mark "no photo found" | — | — | — |

**Never fall to Facebook.** If steps 1-3 miss, the answer is "no photo found" — do not silently use FB.

## Helper Scripts

All under `/mnt/shared-skills/headshot-finder/`:

| Script | Purpose |
|---|---|
| `headshot-finder.sh "<First>" "<Last>" "<Company>" [--domain <X.com>] [--out <path>]` | Single-person orchestrator. Tries providers 1-3 in order, downloads best result to `<path>` (default `/tmp/headshot-<First>-<Last>.jpg`). Prints JSON to stdout. |
| `from-hunter.sh "<First>" "<Last>" "<domain>"` | Hunter `email-finder` lookup — returns `{linkedin_url, twitter, position}` for record-keeping. NO image fetch. |
| `from-google-image.sh "<First>" "<Last>" "<Company>" [--limit N]` | DataForSEO Google Images SERP. Returns ranked image URLs filtered for headshot likelihood (LinkedIn > company-domain > other). |
| `from-company-site.sh "<First>" "<Last>" "<domain>"` | Best-effort: GET `<domain>/{about,team,leadership,our-team,about-us,our-people,staff}`, find `<img>` near person name. Fast HTML parse first; fall through to a sub-agent if heuristic fails. |
| `download-image.sh <url> <output-path>` | Generic downloader with realistic UA, content-type validation, max-size cap (5MB), retries on 503. Returns 0 on success + image saved. |
| `headshot-batch.sh <input.csv> <out-dir>` | Batch runner. CSV columns: `id,first,last,company,domain` (domain optional). Rate-limited to 1 call per 3s by default. Writes `<out-dir>/<id>.jpg` + `<out-dir>/results.csv` (`id,status,source,confidence,url,linkedin_url`). Idempotent — skips IDs whose `<id>.jpg` already exists. |

## Single-person example

```bash
set -a; source /mnt/system/base/.platform-keys.env; set +a
/mnt/shared-skills/headshot-finder/headshot-finder.sh "Joel" "Pressley" "Insulate48" --domain insulate48.com
# → {"id":null,"saved_to":"/tmp/headshot-Joel-Pressley.jpg","source":"google-images","confidence":75,"image_url":"https://media.licdn.com/...","linkedin_url":"https://www.linkedin.com/in/joel-pressley-..."}
```

Exit 0 = image saved, 1 = no photo found, 2 = bad args / missing env.

## Batch example (FoamBook 1,103 contacts)

1. Export the contacts to CSV (run on residential — note the FoamBook schema specifics):
```bash
cd /config/foambook
# Schema: contacts has first_name+last_name (no `name` col); companies has `website` (no `domain`).
# `website` may contain a full URL or extra text — strip protocol/www/path to a bare domain.
sqlite3 -header -csv foambook.db "
  SELECT c.id, c.first_name AS first, c.last_name AS last, co.name AS company,
         lower(
           ltrim(
             substr(
               trim(coalesce(co.website,'')),
               instr(trim(coalesce(co.website,''))||'/', '//')+2
             ),
             'wW'
           )
         ) AS rawdomain_dirty
  FROM contacts c JOIN companies co ON c.company_id = co.id
  WHERE (c.photo_path IS NULL OR c.photo_path = '')
    AND c.first_name IS NOT NULL AND c.last_name IS NOT NULL
    AND co.website IS NOT NULL AND co.website != ''
  ORDER BY c.id;
" | python3 -c "
import csv, sys, re
r = csv.reader(sys.stdin); w = csv.writer(sys.stdout)
header = next(r); w.writerow(['id','first','last','company','domain'])
for row in r:
    raw = row[4].strip().lower()
    raw = re.sub(r'^https?://', '', raw)
    raw = re.sub(r'^www\.', '', raw)
    raw = re.split(r'[/?\s,;(]', raw, 1)[0]   # strip path / params / extra notes
    w.writerow(row[:4] + [raw])
" > headshots-todo.csv
```

Note: only contacts whose company has a `website` value get a row. As of 2026-05-11, ~95/1283 FoamBook companies have a website set — the rest need company-website enrichment first (use Apollo `organizations/search` via the email-finder skill to backfill).

2. Run the batch (host-side, since it talks to Hunter + DataForSEO):
```bash
set -a; source /mnt/system/base/.platform-keys.env; set +a
/mnt/shared-skills/headshot-finder/headshot-batch.sh headshots-todo.csv /tmp/foambook-headshots/
```

3. Sync results back to FoamBook:
```bash
# rsync /tmp/foambook-headshots/*.jpg → residential's /config/foambook/photos/people/
# UPDATE contacts SET photo_path='photos/people/<id>.jpg' WHERE id=<id> for each id in results.csv where status='ok'
```

## Cost awareness

| Provider | Per-call cost | Quota |
|---|---|---|
| Hunter `email-finder` | 1 search credit | 50/mo (50 - 28 used today = 22 remaining as of 2026-05-11) |
| DataForSEO Google Images | ~$0.0006 | pay-as-you-go (no monthly cap) |
| Sub-agent (company team page) | Claude tokens (~3-10K per page) | budget-aware |

For a 1,103-contact batch, **skip Hunter entirely if you already have the email** (the LinkedIn URL is nice-to-have, not load-bearing). DataForSEO + sub-agent is the cost-controlled path. Estimated batch cost: ~$0.66 DataForSEO + sub-agent tokens.

## LinkedIn URLs — record but DON'T auto-fetch

When Hunter returns a `linkedin_url`, store it in the contact record but **do not automate fetching it**. LinkedIn aggressively blocks scrapers and a 1,103-profile-fetch loop on one IP / one account is the same scraping-fingerprint risk as FB. Per-person manual visits in a real browser at human pace are fine.

## Failure modes

| Symptom | Cause | Action |
|---|---|---|
| `headshot-finder.sh: HUNTER_API_KEY not set` | Forgot to source env | `set -a; source /mnt/system/base/.platform-keys.env; set +a` |
| Google Images returns no results | Person too obscure / DataForSEO returned 0 hits | Fall through to company team page automatically |
| Image downloads but is wrong person | Common name + small company → SERP picked wrong photo | Confidence will be low; flag for human review; do NOT auto-tag |
| Company team page misses | Site uses JS-rendered team page or no team page at all | Sub-agent fallback handles common cases (Squarespace/Wix/WordPress patterns); marks as not-found if all fail |
| Image file is < 1KB or HTML-disguised-as-jpg | Bot challenge page or 404 with image MIME | Downloader validates content-type + min-size; rejects + retries with different referer |

## What NEVER happens here

- ❌ Sequential FB profile fetches (the 1,103-headshot scraping fingerprint)
- ❌ FB.com or m.facebook.com or mbasic.facebook.com calls of any kind
- ❌ LinkedIn batch scraping (one-off manual visits only)
- ❌ Auto-tag a low-confidence image as the person without human review
