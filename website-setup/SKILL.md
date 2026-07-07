---
name: website-setup
description: "Website setup + 4-style generation — conversational secretary mode. Use when the user asks to fill out the website setup form, make/build/create a website, enter business info, or generate homepage style options. Open the website-setup canvas page, POST data to fill fields live, trigger the 4 Stitch style variants, help the client pick one. Never build website code directly."
metadata:
  version: 2.0.0
  openclaw:
    emoji: "🌐"
---

# Website Setup Skill — Agent Secretary Mode + 4-Style Chooser

## When to Use This Skill

Activate when the user says ANYTHING like:
- "make me a website" / "build a website" / "create a website"
- "I need a website for my business"
- "can you design a website" / "start a new website" / "show me website styles"
- Any variation of wanting a new website built

## What You Do (and Don't Do)

**You are the secretary. The form + host pipeline are the builder.**

You open the website setup canvas, ask the user questions conversationally, and POST their answers to the API so the form fields populate live with a green flash. When the essentials are filled, generating "4 Styles" produces four full Stitch homepage designs (dark / light / creative / simple) the client picks from — thumbnails appear right in the page's build-monitor drawer. You do NOT write site code, scaffold projects, or run builds yourself.

## The Pattern

1. Open the form: say something natural and include `[CANVAS:website-setup]`
2. Ask conversationally — start with: business name, industry, location, phone
3. POST partial data immediately as you learn each piece — don't wait until the end
4. Keep asking follow-ups: services, target area, style preferences, domain
5. User watches fields populate and corrects out loud — you update and re-POST
6. When essentials are filled, the user (or you, on their ask) hits **✨ Generate 4 Styles** — four homepage designs generate in ~3-5 minutes and appear as crisp thumbnails in the drawer
7. Help the client compare and **Choose** one (or **↺ Regenerate** any single style they don't like)

**Example opener:**
> "Sure, let me pull up the website setup form. [CANVAS:website-setup] Tell me — what's the business name and what do you do?"

## API — Posting Form Data

**Endpoint:** `POST http://openvoiceui:5001/api/canvas/data/website-creator-cmd.json`
(the page polls this file every ~3s and flashes the fields you filled)

**Shell command (use exec tool):**
```bash
curl -s -X POST http://openvoiceui:5001/api/canvas/data/website-creator-cmd.json \
  -H "Content-Type: application/json" \
  -d '{"_ts":"2026-01-01T12:00:00Z","data":{"basics":{"businessName":"Acme Roofing LLC","industry":"Residential Roofing"}}}'
```

Always replace `_ts` with the current UTC timestamp. The page marks the file `_processed:true` after applying it.

**IMPORTANT — Use `_mode: "replace"` for a NEW company:** wipes all previous data first so a prior client's fields can't bleed through. Omit `_mode` when fixing a single field for the SAME company (default = merge).

```bash
curl -s -X POST http://openvoiceui:5001/api/canvas/data/website-creator-cmd.json \
  -H "Content-Type: application/json" \
  -d '{"_ts":"2026-01-01T12:00:00Z","_mode":"replace","data":{"basics":{"businessName":"Real Steel","industry":"Custom Welding"}}}'
```

> Naming note: the page is `website-setup.html` but its data namespace is `website-creator.json` / `website-creator-cmd.json`. That is intentional — do NOT "fix" it.

## Payload Schema (verified against the live page)

```json
{
  "_ts": "2026-01-01T12:00:00Z",
  "data": {
    "basics": {
      "businessName": "Acme Roofing LLC",
      "industry": "Residential Roofing",
      "description": "Dallas-area residential roofing contractor.",
      "ownerName": "John Smith",
      "yearsInBusiness": "12",
      "license": "TX #12345",
      "phone": "(555) 123-4567",
      "email": "info@acmeroofing.com",
      "address": "123 Main St, Dallas TX 75201",
      "domain": "acmeroofing.com",
      "gbpUrl": "",
      "hours": "",
      "socials": {"facebook":"","instagram":"","youtube":"","linkedin":"","yelp":"","tiktok":"","twitter":"","nextdoor":""}
    },
    "siteConfig": {
      "siteType": "local-service",
      "primaryCTA": "Get a Free Quote",
      "pages": ["home","about","services","contact","blog","faq"],
      "specialFeatures": [],
      "urlStructure": ""
    },
    "branding": { "theme": "hubspot", "tone": "professional" },
    "targetAudience": {
      "idealCustomer": "Homeowners 35-65 needing roof repair or replacement.",
      "geographicScope": "local",
      "services": ["Roof Replacement","Leak Repair","Gutters"],
      "targetMarkets": ["Dallas, TX","Plano, TX"],
      "topics": ["how to spot roof damage","when to replace vs repair"]
    },
    "seo": { "primaryKeywords": ["roofing contractor Dallas TX","roof repair Dallas"] },
    "sellingPoints": ["Licensed & insured","Free estimates","Lifetime warranty"],
    "notes": ""
  }
}
```

## Valid Field Values (verified 2026-07-07)

| Field | Options |
|-------|---------|
| `siteType` | `local-service` `ecommerce` `portfolio` `webapp` |
| `geographicScope` | `local` `regional` `statewide` `nationwide` `worldwide` |
| `theme` | `stripe` `tailwind-indigo` `material-blue` `airbnb` `shopify` `supabase-dark` `hubspot` `tailwind-emerald` `calendly` `navy-gold` `intercom` `slack` (+ custom saved themes) |

## The 4-Styles Flow (what happens after the form is filled)

1. **Generate:** the page's **✨ Generate 4 Styles** button writes `creator-styles-trigger.json`. (You can also trigger it for the user: `POST /api/canvas/data/creator-styles-trigger.json` with `{"requestedAt":"<UTC>","business":"<businessName>","_processed":false}` — requires the form draft to be saved first.)
2. **Host generates:** a host-side watcher (cron, every minute, all tenants) runs 4 parallel Google Stitch generations — variants **dark / light / creative / simple** — with automatic quality retries and an AI visual review.
3. **Watch:** the page polls `creator-styles-status.json` and shows each variant's card go pending → generating → done with a crisp full-page thumbnail (~3-5 min total).
4. **Choose:** the client clicks **Choose** on their favorite (saved as `chosenStyle` in the draft) — or **↺** regenerates one variant (`{"variants":["dark"], ...}` in the trigger regenerates just that one).
5. The full generated pages are viewable at `/pages/creator-style-<variant>.html`.

**Status you can read:** `GET /api/canvas/data/creator-styles-status.json` — per-variant `state` (`pending|generating|done|error`), `page`, `thumb`, `sections`, `reviewPass`.

## What you must NOT do

- Do NOT scaffold, code, or deploy the site yourself — the build handoff after style selection is host-side (under construction; the chosen style becomes the design foundation).
- Do NOT read/follow `WEBSITE-BUILD.md` from this flow — that is the host build pipeline's document, not yours.
- Do NOT edit `creator-styles-status.json` — it is written by the host generator only.
