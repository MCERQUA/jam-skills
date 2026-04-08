# Lead Tracker Skill

All website form submissions are stored in a central database. Use this API to view, search, and manage leads — NOT the old `website_leads.json` file.

## API Base URL

```
http://172.17.0.1:6350/api/leads
```

Always include `?tenant=<USER>` (your username, e.g. `src`, `nick`, `josh`).

## List All Leads

```bash
curl -s "http://172.17.0.1:6350/api/leads?tenant=<USER>"
```

Returns: `{ leads: [{ id, name, email, phone, company, address, service_type, message, status, source_site, created_at, ... }] }`

## Filter Leads

```bash
# By status
curl -s "http://172.17.0.1:6350/api/leads?tenant=<USER>&status=new"

# By source site
curl -s "http://172.17.0.1:6350/api/leads?tenant=<USER>&source_site=seattleroofingco"

# Recent only (last N days)
curl -s "http://172.17.0.1:6350/api/leads?tenant=<USER>&days=7"
```

## Update Lead Status

```bash
curl -s -X PATCH "http://172.17.0.1:6350/api/leads/<ID>?tenant=<USER>" \
  -H "Content-Type: application/json" \
  -d '{"status": "contacted"}'
```

Valid statuses: `new`, `contacted`, `qualified`, `proposal`, `won`, `lost`, `spam`

## Add a Lead Manually

```bash
curl -s -X POST "http://172.17.0.1:6350/api/leads/webhook/netlify?tenant=<USER>&site=<site-name>" \
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
