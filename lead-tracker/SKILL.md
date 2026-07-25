---
name: lead-tracker
description: "Track and manage website form submission leads from the central Social Dashboard database. View, filter by status/site/date range, update lead status, add notes, and log follow-ups via the API at 172.17.0.1:6350/api/leads."
version: 1.0.0
---

> ⚠️ **Host API address:** `172.17.0.1` is the DEFAULT docker bridge and NO tenant
> container is on it — that address hangs or refuses. The awk snippet below reads your
> real default gateway from `/proc/net/route` (no `ip` binary needed, it is not installed).
> Fixed fleet-wide 2026-07-25 after it silently blocked otm-voice and cc-backlinks.

# Lead Tracker Skill

All website form submissions are stored in a central database. Use this API to view, search, and manage leads — NOT the old `website_leads.json` file.

## API Base URL

```
http://$(awk '$2=="00000000"{printf "%d.%d.%d.%d","0x"substr($3,7,2),"0x"substr($3,5,2),"0x"substr($3,3,2),"0x"substr($3,1,2);exit}' /proc/net/route):6350/api/leads
```

Always include `?tenant=<USER>` (your username, e.g. `src`, `nick`, `josh`).

## List All Leads

```bash
curl -s "http://$(awk '$2=="00000000"{printf "%d.%d.%d.%d","0x"substr($3,7,2),"0x"substr($3,5,2),"0x"substr($3,3,2),"0x"substr($3,1,2);exit}' /proc/net/route):6350/api/leads?tenant=<USER>"
```

Returns: `{ leads: [{ id, name, email, phone, company, address, service_type, message, status, source_site, created_at, ... }] }`

## Filter Leads

```bash
# By status
curl -s "http://$(awk '$2=="00000000"{printf "%d.%d.%d.%d","0x"substr($3,7,2),"0x"substr($3,5,2),"0x"substr($3,3,2),"0x"substr($3,1,2);exit}' /proc/net/route):6350/api/leads?tenant=<USER>&status=new"

# By source site
curl -s "http://$(awk '$2=="00000000"{printf "%d.%d.%d.%d","0x"substr($3,7,2),"0x"substr($3,5,2),"0x"substr($3,3,2),"0x"substr($3,1,2);exit}' /proc/net/route):6350/api/leads?tenant=<USER>&source_site=seattleroofingco"

# Recent only (last N days)
curl -s "http://$(awk '$2=="00000000"{printf "%d.%d.%d.%d","0x"substr($3,7,2),"0x"substr($3,5,2),"0x"substr($3,3,2),"0x"substr($3,1,2);exit}' /proc/net/route):6350/api/leads?tenant=<USER>&days=7"
```

## Update Lead Status

```bash
curl -s -X PATCH "http://$(awk '$2=="00000000"{printf "%d.%d.%d.%d","0x"substr($3,7,2),"0x"substr($3,5,2),"0x"substr($3,3,2),"0x"substr($3,1,2);exit}' /proc/net/route):6350/api/leads/<ID>?tenant=<USER>" \
  -H "Content-Type: application/json" \
  -d '{"status": "contacted"}'
```

Valid statuses: `new`, `contacted`, `qualified`, `proposal`, `won`, `lost`, `spam`

## Add a Lead Manually

```bash
curl -s -X POST "http://$(awk '$2=="00000000"{printf "%d.%d.%d.%d","0x"substr($3,7,2),"0x"substr($3,5,2),"0x"substr($3,3,2),"0x"substr($3,1,2);exit}' /proc/net/route):6350/api/leads/webhook/netlify?tenant=<USER>&site=<site-name>" \
  -H "Content-Type: application/json" \
  -d '{"form_name":"manual","site_url":"","data":{"Name":"John Doe","Email":"john@example.com","Phone":"555-1234","Service":"Roof Repair","Address":"123 Main St","Message":"Needs quote"}}'
```

## Lead Data Flow

1. Customer submits form on website (Netlify)
2. Netlify webhook → this DB (automatic)
3. Slack notification (automatic)
4. You query this API to see all leads

## Important

- **DO NOT use `website_leads.json`** — that file is outdated and no longer maintained
- **This API is the single source of truth** for all leads
- New leads arrive automatically via Netlify webhook
- Check this API when the user asks about leads, follow-ups, or new business
