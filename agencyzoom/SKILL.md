# AgencyZoom — Insurance CRM Integration

AgencyZoom is the insurance CRM (by Vertafore) connected to AMS360 for policy management.

## Available Tools (via z-code or maxcode)

| Tool | Purpose |
|------|---------|
| `agencyzoom_find_a_lead` | Search leads by name, email, phone, or ID |
| `agencyzoom_find_service_request` | Search service requests by customer, pipeline, stage, date |
| `agencyzoom_create_personal_lead` | Create a personal lines lead |
| `agencyzoom_create_business_lead` | Create a commercial/business lead |
| `agencyzoom_create_a_note` | Add a note to a lead or customer |
| `agencyzoom_create_task` | Create a task in AgencyZoom |
| `agencyzoom_create_service_request` | Open a service request |
| `agencyzoom_update_lead` | Update an existing lead |
| `agencyzoom_update_service_request` | Update a service request |

## How to Use

**Search for a lead:**
```bash
exec("z-code -p 'Use the agencyzoom_find_a_lead tool to search for a lead named Smith. Show me all the details.' --allowedTools 'Bash,Read' 2>&1 | tail -50")
```

**Create a lead:**
```bash
exec("maxcode -p 'Use the agencyzoom_create_business_lead tool to create a lead: company=Smith Contractors LLC, contactName=John Smith, email=john@example.com, phone=555-123-4567, notes=From website contact form' --allowedTools 'Bash,Read' 2>&1 | tail -50")
```

## Critical Rules

- **NEVER write back to AgencyZoom without user confirmation** (same as email rules — show the data, get a "yes")
- **NEVER create test leads** — this is a live production CRM
- **NEVER delete or modify existing leads** without explicit permission
- **AgencyZoom syncs to AMS360 automatically** — changes cascade to the policy management system
- Search is **exact match** (name, email, phone) — not fuzzy/partial
- Josh's agent ID in AgencyZoom is **128603** (Josh Cotner)

## Lead Pipeline

```
Website Form → Netlify → Social Dashboard (Neon DB) → Zapier Webhook → AgencyZoom → AMS360
```

All website leads auto-push to AgencyZoom via Zapier webhook. No manual entry needed. The social dashboard stores all raw data. AgencyZoom syncs to AMS360 for the full policy lifecycle.

## Lead Tracker API

Query leads from the social dashboard (Neon DB — all website leads stored here):

```bash
# Recent leads
curl -s "http://172.17.0.1:6350/api/leads?tenant=josh&limit=10"

# Filter by source site
curl -s "http://172.17.0.1:6350/api/leads?tenant=josh&source_site=fightclubinsurance"

# Lead stats
curl -s "http://172.17.0.1:6350/api/leads/stats?tenant=josh"

# Live feed (SSE stream — real-time new leads)
curl -s "http://172.17.0.1:6350/api/leads/feed?tenant=josh"
```

## Voice Queries

Common things the user might ask:
- "How many new leads do I have?" → Query lead tracker for recent
- "Find the lead from [company]" → `agencyzoom_find_a_lead` by name
- "Create a task to follow up with [name]" → `agencyzoom_create_task`
- "Add a note to [lead name]" → `agencyzoom_create_a_note`
- "What's in my pipeline?" → Lead tracker stats + AgencyZoom search
- "Show me leads from [website]" → Lead tracker filtered by source_site
- "What came in today?" → Lead tracker filtered by today's date

## Webhook Datapoints (for form builders)

74 fields are configured in the Zapier webhook. When building new website forms, use these exact field names so data flows automatically into AgencyZoom.

Full field reference: `docs/WEBHOOK-DATAPOINTS.md`

### Quick Reference — Most Common Fields

**Contact:** `name`, `firstName`, `lastName`, `email`, `phone`, `preferred_contact`
**Business:** `company`, `businessName`, `fein`, `service_type`, `businessEntity`
**Address:** `address`, `city`, `state`, `zip`
**Employment:** `employee_count`, `employee_payroll`, `owner_payroll`
**Financial:** `gross_sales`, `annual_revenue`, `subcontracting_costs`
**Projects:** `project_count`, `largest_job`, `largestJobDescription`, `avg_project`
**Projections:** `next_gross_estimate`, `nextEmployeeCount`, `nextEmployeePayroll`, `estimatedGross`
**Insurance:** `liability_claims`, `no_losses`, `insurance_history`
**Tracking:** `source_site`, `form_type`, `message`, `notes`, `referrer`

### Niche-Specific Fields

**Fight clubs/gyms:** `training_focus`, `membership_count`, `classes_per_week`
**Bars/nightclubs:** `capacity`, `hours_operation`, `num_staff`
**Mobile detailing:** `equipment_value`, `client_base`, `services`
**Mini trucks/vehicles:** `truckYear`, `truckMake`, `truckModel`, `modifications`
**Van life:** `van_type`, `van_value`, `usage`
**Insulation/home:** `home_size`, `built`, `concern`
**Glazing/construction:** `project_type`, `focus`, `structures_built`
**Hood vent cleaning:** `estimatedGross`, `estimatedMaterialCosts`, `exampleUpcomingJobAmount`, `exampleUpcomingJobDescription`
