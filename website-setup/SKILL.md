---
name: website-setup
description: "Website setup form fill — conversational secretary mode. Use when user asks to fill out the website setup form, enter business info, populate form fields, or set up a new website. Open the website-setup canvas page and POST data to the API to populate fields live. Never build websites directly."
metadata:
  version: 1.0.0
  openclaw:
    emoji: "🌐"
---

# Website Setup Skill — Agent Secretary Mode

## When to Use This Skill

Activate when the user says ANYTHING like:
- "make me a website" / "build a website" / "create a website"
- "I need a website for my business"
- "can you design a website" / "start a new website"
- "help me with my website" / "set up a website"
- Any variation of wanting a new website built

## What You Do (and Don't Do)

**You are the secretary. The form is the builder.**

You open the website setup canvas, ask the user questions conversationally, and POST their answers to the API so the form fields populate live with a green flash. When the form is complete, the user clicks "Start Research" and the automated pipeline does the building — you do NOT write code, scaffold projects, or touch WEBSITE-BUILD.md.

## The Pattern

1. Open the form: say something natural and include `[CANVAS:website-setup]`
3. Ask conversationally — start with: business name, industry, location, phone
4. POST partial data immediately as you learn each piece — don't wait until the end
4. Keep asking follow-up questions: services, target area, tone, domain
5. User watches fields populate and corrects out loud — you update and re-POST
6. When essentials are filled, tell them: "The form looks good — hit Start Research when you're ready and it'll build the site automatically."

**Example opener:**
> "Sure, let me pull up the website setup form. [CANVAS:website-setup] Tell me — what's the business name and what do you do?"

## API — Posting Form Data

**Endpoint:** `POST http://openvoiceui:5001/api/canvas/data/website-setup-cmd.json`

**Shell command (use exec tool):**
```bash
curl -s -X POST http://openvoiceui:5001/api/canvas/data/website-setup-cmd.json \
  -H "Content-Type: application/json" \
  -d '{"_ts":"2026-01-01T12:00:00Z","data":{"basics":{"businessName":"Acme Roofing LLC","industry":"Residential Roofing"}}}'
```

Always replace `_ts` with the current UTC timestamp.

**IMPORTANT — Use `_mode: "replace"` to clear old data:**
When filling a form for a NEW company, always include `"_mode":"replace"` in your POST. This wipes all previous data and sets only what you send. Without it, old data from a previous company will persist in fields you don't explicitly set.

```bash
curl -s -X POST http://openvoiceui:5001/api/canvas/data/website-setup-cmd.json \
  -H "Content-Type: application/json" \
  -d '{"_ts":"2026-01-01T12:00:00Z","_mode":"replace","data":{"basics":{"businessName":"Real Steel","industry":"Custom Welding"}}}'
```

For updates to an EXISTING company (fixing a single field), omit `_mode` — the default merge behavior will only change what you send.

## Full Payload Schema

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
      "domain": "acmeroofing.com"
    },
    "siteConfig": {
      "siteType": "local-service",
      "primaryCTA": "Get a Free Quote",
      "pages": ["home","about","services","contact","faq"],
      "urlStructure": ""
    },
    "branding": {
      "theme": "hubspot",
      "tone": "professional"
    },
    "targetAudience": {
      "idealCustomer": "Homeowners 35-65 needing roof repair or replacement.",
      "geographicScope": "local",
      "services": ["Roof Replacement","Leak Repair","Gutters"],
      "targetMarkets": ["Dallas, TX","Plano, TX"],
      "topics": ["how to spot roof damage","when to replace vs repair"]
    },
    "seo": {
      "primaryKeywords": ["roofing contractor Dallas TX","roof repair Dallas"]
    },
    "sellingPoints": ["Licensed & insured","Free estimates","Lifetime warranty"],
    "notes": ""
  }
}
```

## Valid Field Values

| Field | Options |
|-------|---------|
| `siteType` | `local-service` `portfolio` `ecommerce` `landing` `blog` |
| `theme` | `stripe` `hubspot` `navy-gold` `tailwind-indigo` `airbnb` `shopify` `supabase-dark` |
| `tone` | `professional` `friendly` `bold` `minimal` `luxury` |
| `geographicScope` | `local` `regional` `national` |

## `/website-build` Command

When you receive `/website-build <project-name>` (triggered automatically by the canvas page after "Start Research"):
1. Read `WEBSITE-BUILD.md` for the complete build workflow
2. Intake file: `~/Websites/<project-name>/.intake.json`
3. Status file: `~/Websites/<project-name>/.build-status.json`
4. Follow ALL phases in order — update the status file at every transition (canvas polls it)
5. Do NOT ask clarifying questions — all info is in the intake file
