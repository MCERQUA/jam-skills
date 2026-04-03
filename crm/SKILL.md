---
name: crm
description: "Manage contacts, companies, deals, notes, and tasks via Twenty CRM. Use when the user mentions CRM, contacts, leads, pipeline, deals, follow-ups, or customer management."
---

# CRM — Twenty CRM Integration

You have a dedicated CRM workspace at **https://crm.jam-bot.com** powered by Twenty CRM. Use it to track contacts, companies, deals, notes, and tasks for your client's business.

## Critical Rules

1. **This is a SHADOW CRM.** It is YOUR dedicated workspace for tracking the client's leads and pipeline. It is NOT the client's own CRM system.
2. **Never ask the client for CRM credentials.** Your API key is already configured.
3. **Never try to sync TO the client's real CRM.** Data flows one-way: FROM their CRM into yours, only if explicitly configured. You never push data outward.
4. **You own all data in your workspace.** Create, update, and organize freely.
5. **Never attempt to access other workspaces or change your API key.** Your key is scoped to your workspace only.

## Authentication

Your API key is in the environment variable `TWENTY_CRM_API_KEY`. Every request must include it as a Bearer token:

```
Authorization: Bearer $TWENTY_CRM_API_KEY
```

## API Reference

**Base URL:** `https://crm.jam-bot.com/rest`

All examples use `exec()` with `curl`. Always include `-s` (silent) and `-f` (fail on HTTP errors) flags.

### Rate Limit

100 requests per minute. Space out bulk operations accordingly.

---

### People (Contacts)

```bash
# List all contacts
exec("curl -sf 'https://crm.jam-bot.com/rest/people?limit=50' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")

# Get a single contact by ID
exec("curl -sf 'https://crm.jam-bot.com/rest/people/{id}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")

# Create a contact
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/people' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"name\": {\"firstName\": \"Jane\", \"lastName\": \"Smith\"},
    \"emails\": {\"primaryEmail\": \"jane@example.com\"},
    \"phones\": {\"primaryPhoneNumber\": \"+16025551234\"},
    \"jobTitle\": \"Owner\",
    \"city\": \"Phoenix\"
  }'")

# Update a contact
exec("curl -sf -X PATCH 'https://crm.jam-bot.com/rest/people/{id}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{\"jobTitle\": \"CEO\"}'")

# Delete a contact (soft delete)
exec("curl -sf -X DELETE 'https://crm.jam-bot.com/rest/people/{id}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")
```

**Person fields:**
| Field | Format | Example |
|-------|--------|---------|
| name | `{firstName, lastName}` | `{"firstName":"Jane","lastName":"Smith"}` |
| emails | `{primaryEmail}` | `{"primaryEmail":"jane@example.com"}` |
| phones | `{primaryPhoneNumber, primaryPhoneCountryCode}` | `{"primaryPhoneNumber":"+16025551234"}` |
| jobTitle | string | `"Owner"` |
| city | string | `"Phoenix"` |
| companyId | UUID | Links person to a company |

---

### Companies

```bash
# List all companies
exec("curl -sf 'https://crm.jam-bot.com/rest/companies?limit=50' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")

# Create a company
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/companies' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"name\": \"Acme Roofing\",
    \"domainName\": {\"primaryLinkUrl\": \"https://acmeroofing.com\"},
    \"employees\": 12,
    \"address\": {
      \"addressStreet1\": \"123 Main St\",
      \"addressCity\": \"Phoenix\",
      \"addressState\": \"AZ\",
      \"addressPostcode\": \"85001\"
    },
    \"idealCustomerProfile\": true
  }'")

# Update a company
exec("curl -sf -X PATCH 'https://crm.jam-bot.com/rest/companies/{id}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{\"employees\": 15}'")
```

**Company fields:**
| Field | Format | Example |
|-------|--------|---------|
| name | string | `"Acme Roofing"` |
| domainName | `{primaryLinkUrl}` | `{"primaryLinkUrl":"https://acmeroofing.com"}` |
| employees | integer | `12` |
| address | `{addressStreet1, addressCity, addressState, addressPostcode}` | See example above |
| idealCustomerProfile | boolean | `true` if this company matches your ideal customer |

---

### Opportunities (Deals / Pipeline)

```bash
# List all deals
exec("curl -sf 'https://crm.jam-bot.com/rest/opportunities?limit=50' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")

# Create a deal
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/opportunities' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"name\": \"Acme Roofing - Full Reroof\",
    \"amount\": 18500,
    \"closeDate\": \"2026-04-15\",
    \"stage\": \"INCOMING\",
    \"companyId\": \"{company-uuid}\"
  }'")

# Update deal stage
exec("curl -sf -X PATCH 'https://crm.jam-bot.com/rest/opportunities/{id}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{\"stage\": \"PROPOSAL\"}'")
```

**Opportunity fields:**
| Field | Format | Values |
|-------|--------|--------|
| name | string | Descriptive deal name |
| amount | number | Dollar value (no cents) |
| closeDate | ISO date string | `"2026-04-15"` |
| stage | enum | `INCOMING`, `MEETING`, `PROPOSAL`, `CLOSED_WON`, `CLOSED_LOST` |
| companyId | UUID | Links deal to a company |

---

### Notes

Notes are standalone objects. Link them to people, companies, or opportunities via **noteTargets**.

```bash
# List notes
exec("curl -sf 'https://crm.jam-bot.com/rest/notes?limit=20' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")

# Create a note
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/notes' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"title\": \"Phone call - initial inquiry\",
    \"body\": \"Called about roof damage from recent storm. Wants inspection this week. Has insurance claim open.\"
  }'")

# Link a note to a person
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/noteTargets' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"noteId\": \"{note-uuid}\",
    \"targetPersonId\": \"{person-uuid}\"
  }'")

# Link a note to a company
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/noteTargets' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"noteId\": \"{note-uuid}\",
    \"targetCompanyId\": \"{company-uuid}\"
  }'")

# Link a note to an opportunity
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/noteTargets' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"noteId\": \"{note-uuid}\",
    \"targetOpportunityId\": \"{opportunity-uuid}\"
  }'")
```

**Note fields:**
| Field | Format |
|-------|--------|
| title | string |
| body | string (plain text or markdown) |

---

### Tasks

Tasks are standalone objects. Link them to people, companies, or opportunities via **taskTargets**.

```bash
# List tasks
exec("curl -sf 'https://crm.jam-bot.com/rest/tasks?limit=20' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")

# Create a task
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/tasks' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"title\": \"Follow up with Jane Smith\",
    \"body\": \"Send proposal for full reroof job. Include financing options.\",
    \"status\": \"OPEN\",
    \"dueAt\": \"2026-04-02T09:00:00Z\"
  }'")

# Update a task (mark done)
exec("curl -sf -X PATCH 'https://crm.jam-bot.com/rest/tasks/{id}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{\"status\": \"DONE\"}'")

# Link a task to a person
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/taskTargets' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"taskId\": \"{task-uuid}\",
    \"targetPersonId\": \"{person-uuid}\"
  }'")

# Link a task to a company
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/taskTargets' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"taskId\": \"{task-uuid}\",
    \"targetCompanyId\": \"{company-uuid}\"
  }'")
```

**Task fields:**
| Field | Format | Values |
|-------|--------|--------|
| title | string | Task description |
| body | string | Additional details |
| status | enum | `OPEN`, `DONE` |
| dueAt | ISO datetime | `"2026-04-02T09:00:00Z"` |

---

## Query Parameters

All list endpoints support filtering, sorting, pagination, and relation loading.

### Pagination

```
?limit=20           # Max records to return (default varies)
?offset=20          # Skip first N records (for pagination)
```

### Sorting

```
?orderBy=createdAt  # Sort by field (ascending)
```

### Filtering

```
?filter={"field":{"op":"value"}}
```

**Filter operators:**
| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` | Equals | `{"stage":{"eq":"PROPOSAL"}}` |
| `neq` | Not equals | `{"stage":{"neq":"CLOSED_LOST"}}` |
| `like` | Pattern match (case-sensitive) | `{"name":{"like":"%roofing%"}}` |
| `ilike` | Pattern match (case-insensitive) | `{"name":{"ilike":"%roofing%"}}` |
| `gt` | Greater than | `{"amount":{"gt":10000}}` |
| `gte` | Greater than or equal | `{"amount":{"gte":5000}}` |
| `lt` | Less than | `{"amount":{"lt":50000}}` |
| `lte` | Less than or equal | `{"amount":{"lte":25000}}` |
| `in` | In list | `{"stage":{"in":["INCOMING","MEETING"]}}` |
| `is` | Is null/not null | `{"companyId":{"is":"NULL"}}` |

**URL-encode the filter JSON in curl:**

```bash
exec("curl -sf -G 'https://crm.jam-bot.com/rest/opportunities' \
  --data-urlencode 'filter={\"stage\":{\"eq\":\"PROPOSAL\"}}' \
  --data-urlencode 'limit=50' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")
```

### Including Relations

```
?depth=1            # Include first-level relations (e.g., company on a person)
```

---

## Practical Examples

### 1. Add a New Lead (Person + Company + Opportunity)

When someone contacts the business, create the full lead chain:

```bash
# Step 1: Create the company
COMPANY=$(exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/companies' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"name\": \"Desert Sun Homes\",
    \"domainName\": {\"primaryLinkUrl\": \"https://desertsunhomes.com\"},
    \"address\": {
      \"addressCity\": \"Scottsdale\",
      \"addressState\": \"AZ\"
    },
    \"idealCustomerProfile\": true
  }'"))
# Extract companyId from response

# Step 2: Create the contact linked to the company
PERSON=$(exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/people' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"name\": {\"firstName\": \"Maria\", \"lastName\": \"Garcia\"},
    \"emails\": {\"primaryEmail\": \"maria@desertsunhomes.com\"},
    \"phones\": {\"primaryPhoneNumber\": \"+14805551234\"},
    \"jobTitle\": \"Property Manager\",
    \"city\": \"Scottsdale\",
    \"companyId\": \"{company-uuid-from-step-1}\"
  }'"))

# Step 3: Create the opportunity
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/opportunities' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"name\": \"Desert Sun Homes - 5 Unit Reroof\",
    \"amount\": 42000,
    \"closeDate\": \"2026-05-01\",
    \"stage\": \"INCOMING\",
    \"companyId\": \"{company-uuid-from-step-1}\"
  }'")
```

### 2. Log a Call Note Linked to a Person

```bash
# Create the note
NOTE=$(exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/notes' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"title\": \"Call - Scheduling inspection\",
    \"body\": \"Maria confirmed availability Thursday 2-4pm for roof inspection of all 5 units. Wants written estimate same day if possible. Mentioned budget is pre-approved by HOA.\"
  }'"))
# Extract noteId from response

# Link the note to the person
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/noteTargets' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"noteId\": \"{note-uuid}\",
    \"targetPersonId\": \"{person-uuid}\"
  }'")
```

### 3. Search Contacts by Company

```bash
# Find all people at a specific company
exec("curl -sf -G 'https://crm.jam-bot.com/rest/people' \
  --data-urlencode 'filter={\"companyId\":{\"eq\":\"{company-uuid}\"}}' \
  --data-urlencode 'depth=1' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")

# Search contacts by name (case-insensitive)
exec("curl -sf -G 'https://crm.jam-bot.com/rest/people' \
  --data-urlencode 'filter={\"name\":{\"ilike\":\"%garcia%\"}}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY'")
```

### 4. Update Deal Stage

```bash
# Move deal from INCOMING to MEETING
exec("curl -sf -X PATCH 'https://crm.jam-bot.com/rest/opportunities/{opportunity-uuid}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{\"stage\": \"MEETING\"}'")

# Close a deal as won with final amount
exec("curl -sf -X PATCH 'https://crm.jam-bot.com/rest/opportunities/{opportunity-uuid}' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{\"stage\": \"CLOSED_WON\", \"amount\": 45000}'")
```

### 5. Create a Follow-Up Task Linked to a Person

```bash
# Create the task
TASK=$(exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/tasks' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"title\": \"Send proposal to Maria Garcia\",
    \"body\": \"Include 5-unit reroof scope, financing options, and 10-year warranty details. She needs it before Friday HOA meeting.\",
    \"status\": \"OPEN\",
    \"dueAt\": \"2026-04-03T14:00:00Z\"
  }'"))
# Extract taskId from response

# Link the task to the person
exec("curl -sf -X POST 'https://crm.jam-bot.com/rest/taskTargets' \
  -H 'Authorization: Bearer $TWENTY_CRM_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    \"taskId\": \"{task-uuid}\",
    \"targetPersonId\": \"{person-uuid}\"
  }'")
```

---

## Error Handling

Always check for errors in API responses. Common issues:

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 200 | Success | Parse response JSON |
| 201 | Created | Parse response for new record ID |
| 400 | Bad request | Check field names and formats |
| 401 | Unauthorized | `TWENTY_CRM_API_KEY` is missing or invalid |
| 404 | Not found | Record ID does not exist |
| 429 | Rate limited | Wait 60 seconds and retry |

**When a curl call fails:**
- Check that `$TWENTY_CRM_API_KEY` is set: `exec("echo $TWENTY_CRM_API_KEY | head -c 8")`
- If empty, the environment variable was not injected. Report to the admin.
- If you get 401, the API key may have been rotated. Report to the admin.
- Never attempt to generate, guess, or modify the API key.

**When creating linked records (note/task targets):**
- Always capture the ID from the creation response before linking.
- If the create succeeds but the link fails, retry the link — the record still exists.

---

## CRM Navigation — Deep-Link to Specific Views

Open the CRM UI directly to a specific page using `[CANVAS_URL:...]`. The base URL is `https://<user>.crm.jam-bot.com`.

**Object list pages:**
| View | URL Path |
|------|----------|
| All contacts | `/objects/people` |
| All companies | `/objects/companies` |
| All deals/pipeline | `/objects/opportunities` |
| All notes | `/objects/notes` |
| All tasks | `/objects/tasks` |
| Single record | `/object/<type>/<uuid>` (e.g. `/object/person/abc-123`) |

**Examples:**

```
# "Show me my deals"
[CANVAS_URL:https://src.crm.jam-bot.com/objects/opportunities]

# "Open the contact list"
[CANVAS_URL:https://src.crm.jam-bot.com/objects/people]

# "Show me Jowynna's record"
[CANVAS_URL:https://src.crm.jam-bot.com/object/person/{person-uuid}]

# "Open the CRM homepage"
[CANVAS_URL:https://src.crm.jam-bot.com]
```

**When the user says "open my CRM" or "show my pipeline" or "go to contacts":**
1. Map their request to the correct URL path
2. Use `[CANVAS_URL:...]` with the full URL
3. Include a brief spoken intro: "Here's your pipeline." `[CANVAS_URL:https://src.crm.jam-bot.com/objects/opportunities]`

---

## Best Practices

1. **Log everything.** When the client mentions a call, meeting, or conversation with a lead, create a note immediately. Context is perishable.
2. **Move deals through stages.** When the client reports progress (scheduled a meeting, sent a proposal, closed a deal), update the opportunity stage right away.
3. **Create tasks for follow-ups.** If the client says "I need to call them back Thursday," create a task with a due date.
4. **Link records.** Always link notes and tasks to the relevant person, company, or opportunity. Unlinked records are hard to find later.
5. **Use `depth=1` when displaying.** Include relations so you can show company names alongside contacts, not just UUIDs.
6. **Keep data clean.** Before creating a new company or person, search first to avoid duplicates. Use `ilike` filter on name.
7. **Report pipeline status.** When the client asks "how's my pipeline," query opportunities grouped by stage and summarize totals.
8. **Navigate the CRM UI.** When the client asks to "see" or "open" something in the CRM, use `[CANVAS_URL:...]` to deep-link directly to the right page. Don't just describe the data — show them the actual CRM view.
