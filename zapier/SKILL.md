---
name: zapier
description: "Trigger Zapier automations — send emails, create calendar events, update spreadsheets, post to social media, and more through the client's own Zapier account. Use when the user mentions Zapier, automations, sending emails, scheduling events, or integrating with third-party apps via Zapier."
---

# Zapier Integration

You can trigger Zapier automations on behalf of your client through pre-configured webhooks. Each client has their own Zapier account with Zaps they've set up. You fire webhooks through the social-dashboard proxy — you never need API keys or webhook URLs directly.

## Critical Rules

1. **Never ask the client for Zapier credentials or webhook URLs.** Everything is pre-configured server-side.
2. **Always check status first** before attempting to fire webhooks. If not configured, tell the user their admin needs to set up Zapier.
3. **Every webhook fire costs the client 1 Zapier task** from their plan. Don't fire test webhooks unless explicitly asked.
4. **Never attempt to configure webhooks yourself.** Configuration is admin-only.
5. **Confirm before firing** — always confirm the action details with the user before executing (e.g., "I'll send an email to john@example.com with subject 'Your estimate is ready'. Go ahead?").

## API Reference

**Base URL:** `http://172.17.0.1:6350`
**Auth:** `X-Tenant` header (your tenant ID)

All examples use `exec()` with `curl -sf`.

---

### Check Zapier Status

```bash
exec("curl -sf http://172.17.0.1:6350/api/zapier/status -H 'X-Tenant: $TENANT'")
```

Response:
```json
{
  "ok": true,
  "configured": true,
  "webhookCount": 3,
  "aiActionsEnabled": false,
  "webhooks": ["send_email", "create_event", "update_sheet"]
}
```

If `configured: false` → tell user "Zapier isn't set up yet. Your admin can configure it."

---

### List Available Actions

```bash
exec("curl -sf http://172.17.0.1:6350/api/zapier/actions -H 'X-Tenant: $TENANT'")
```

Response:
```json
{
  "ok": true,
  "webhooks": {
    "send_email": { "description": "Send email via Gmail" },
    "create_event": { "description": "Create Google Calendar event" }
  }
}
```

---

### Fire a Webhook

```bash
exec("curl -sf -X POST http://172.17.0.1:6350/api/zapier/webhook \
  -H 'X-Tenant: $TENANT' \
  -H 'Content-Type: application/json' \
  -d '{
    \"action\": \"send_email\",
    \"data\": {
      \"to\": \"jane@example.com\",
      \"subject\": \"Your appointment is confirmed\",
      \"body\": \"Hi Jane, your appointment is confirmed for Thursday at 2pm. See you then!\"
    }
  }'")
```

Response:
```json
{"ok": true, "action": "send_email", "type": "webhook", "status": 200, "success": true}
```

---

### View Execution Log

```bash
exec("curl -sf 'http://172.17.0.1:6350/api/zapier/log?limit=10' -H 'X-Tenant: $TENANT'")
```

---

## Common Actions & Expected Data Fields

| Action | Description | Data Fields |
|--------|-------------|-------------|
| `send_email` | Send email via Gmail/Outlook | `to`, `subject`, `body`, `cc` (optional) |
| `create_event` | Create Google Calendar event | `title`, `start_time` (ISO), `end_time` (ISO), `description`, `location` |
| `update_sheet` | Add row to Google Sheets | Key-value pairs matching column headers |
| `post_social` | Post to social media | `platform`, `message`, `image_url` (optional) |
| `send_sms` | Send SMS via Twilio | `phone`, `message` |
| `slack_message` | Post to Slack channel | `channel`, `message` |
| `create_task` | Create task in project management | `title`, `description`, `due_date` |

**Note:** Each client's actual actions may differ. Always call `/api/zapier/actions` first to see what's configured.

---

## Usage Examples

### Send an email
User: "Send John an email about his estimate being ready"
```bash
exec("curl -sf -X POST http://172.17.0.1:6350/api/zapier/webhook \
  -H 'X-Tenant: $TENANT' -H 'Content-Type: application/json' \
  -d '{\"action\":\"send_email\",\"data\":{\"to\":\"john@example.com\",\"subject\":\"Your Estimate is Ready\",\"body\":\"Hi John, your estimate for the roof repair is ready. The total comes to $4,500. Please review and let us know if you have any questions.\"}}'")
```

### Schedule a calendar event
User: "Add a roof inspection to my calendar for Friday at 10am"
```bash
exec("curl -sf -X POST http://172.17.0.1:6350/api/zapier/webhook \
  -H 'X-Tenant: $TENANT' -H 'Content-Type: application/json' \
  -d '{\"action\":\"create_event\",\"data\":{\"title\":\"Roof Inspection - Smith Residence\",\"start_time\":\"2026-04-10T10:00:00-07:00\",\"end_time\":\"2026-04-10T12:00:00-07:00\",\"location\":\"123 Main St, Phoenix AZ\",\"description\":\"Annual roof inspection\"}}'")
```

### Log to a spreadsheet
User: "Add today's lead count to the tracking sheet"
```bash
exec("curl -sf -X POST http://172.17.0.1:6350/api/zapier/webhook \
  -H 'X-Tenant: $TENANT' -H 'Content-Type: application/json' \
  -d '{\"action\":\"update_sheet\",\"data\":{\"date\":\"2026-04-08\",\"new_leads\":5,\"calls_made\":12,\"appointments_set\":3}}'")
```

---

## Decision Guide

| User says... | Action to fire |
|-------------|---------------|
| "Send an email to..." / "Email John about..." | `send_email` |
| "Schedule a meeting" / "Add to calendar" / "Book an appointment" | `create_event` |
| "Log this in the spreadsheet" / "Update the tracker" | `update_sheet` |
| "Post this on social media" / "Share on Facebook" | `post_social` |
| "Text the customer" / "Send a text to..." | `send_sms` |
| "Send a Slack message" / "Notify the team on Slack" | `slack_message` |

---

## Integration with CRM

When you create a new CRM lead AND the client has `send_email` configured, proactively offer:
- "I've added the lead to your CRM. Want me to also send them a welcome email via Zapier?"

When a deal closes in CRM AND `send_email` is configured:
- "Congratulations on closing the deal! Want me to send a thank-you email or a review request?"

---

## Error Handling

| Error | Meaning | What to do |
|-------|---------|------------|
| `configured: false` | No Zapier webhooks set up | Tell user to contact admin |
| `No webhook configured for action: X` | That specific action doesn't exist | List available actions, suggest the right one |
| `HTTP 410` | Zap was deleted or turned off in Zapier | Tell user to check their Zapier dashboard |
| `HTTP 000` / connection failed | Zapier is unreachable | Try again in a moment, suggest checking Zapier status |
