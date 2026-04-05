---
name: agentmail
description: "AgentMail email API — create inboxes, send/receive emails, manage threads, drafts, labels, and attachments for AI agents. Use when asked to send email, check email, create an inbox, or manage email communications."
metadata: {"openclaw": {"emoji": "📧", "requires": {"env": ["AGENTMAIL_API_KEY"], "anyBins": ["curl"]}}}
---

# AgentMail Skill

## DOUBLE CONFIRMATION REQUIRED — READ TOOLS.md FIRST

**Before sending ANY email, you MUST follow the double-confirmation procedure in TOOLS.md.** No email leaves without TWO explicit "yes" responses from the user. No exceptions. No batch sends. No automatic sends. Drafting is fine — sending requires two keys turned.

Email inbox API for AI agents. Create inboxes, send/receive emails, manage threads and conversations programmatically.

**Base URL:** `https://api.agentmail.to/v0`
**Auth:** Bearer token via `$AGENTMAIL_API_KEY`
**Docs:** https://docs.agentmail.to

## When to Use

Use this skill when the user asks to:
- Send or receive email
- Create an email inbox
- Check for new messages
- Reply to or forward emails
- Manage email threads or conversations
- Create email drafts
- Work with email attachments
- Set up webhooks for email notifications

## Auth Header (All Requests)

```bash
-H "Authorization: Bearer $AGENTMAIL_API_KEY"
-H "Content-Type: application/json"
```

---

## Core Operations

### 1. Create an Inbox

```bash
curl -s -X POST 'https://api.agentmail.to/v0/inboxes' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "my-agent",
    "domain": "agentmail.to",
    "display_name": "My Agent",
    "client_id": "my-agent-inbox"
  }' | jq .
```

**Parameters:**
- `username` (optional) — email prefix, auto-generated if omitted
- `domain` (optional) — defaults to `agentmail.to`
- `display_name` (optional) — friendly name
- `client_id` (optional) — idempotency key (safe to retry)

**Returns:** `{ "inbox_id": "my-agent@agentmail.to", ... }`

### 2. List Inboxes

```bash
curl -s 'https://api.agentmail.to/v0/inboxes?limit=20' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

### 3. Get Inbox Details

```bash
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

### 4. Delete Inbox

```bash
curl -s -X DELETE 'https://api.agentmail.to/v0/inboxes/INBOX_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY"
```

---

## Sending Email

### Send a New Message

**IMPORTANT:** Always send both `text` AND `html` for best deliverability.

```bash
curl -s -X POST 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/send' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["recipient@example.com"],
    "subject": "Hello from AgentMail",
    "text": "Plain text version of the email.",
    "html": "<p>HTML version of the email.</p>",
    "labels": ["outreach"]
  }' | jq .
```

**Parameters:**
- `to` (array) — recipient email addresses
- `cc` (array, optional) — CC recipients
- `bcc` (array, optional) — BCC recipients
- `reply_to` (array, optional) — reply-to addresses
- `subject` (string) — email subject
- `text` (string) — plain text body (ALWAYS include)
- `html` (string) — HTML body (ALWAYS include)
- `labels` (array, optional) — string tags for organization
- `attachments` (array, optional) — see Attachments section

**Returns:** `{ "message_id": "msg_xxx", "thread_id": "thread_xxx" }`

### Reply to a Message

```bash
curl -s -X POST 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/MESSAGE_ID/reply' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["sender@example.com"],
    "text": "Thanks for your email! Here is my reply.",
    "html": "<p>Thanks for your email! Here is my reply.</p>"
  }' | jq .
```

### Reply All

```bash
curl -s -X POST 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/MESSAGE_ID/reply-all' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Reply to everyone.",
    "html": "<p>Reply to everyone.</p>"
  }' | jq .
```

### Forward a Message

```bash
curl -s -X POST 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/MESSAGE_ID/forward' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["forward-to@example.com"],
    "text": "FYI - forwarding this to you.",
    "html": "<p>FYI - forwarding this to you.</p>"
  }' | jq .
```

---

## Reading Email

### List Messages in Inbox

```bash
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages?limit=10' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

**Query params:** `limit`, `page_token`, `labels`, `before`, `after`, `ascending`, `include_spam`, `include_blocked`

### Get a Specific Message

```bash
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/MESSAGE_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

**Response fields:**
- `message_id` — unique ID
- `thread_id` — conversation thread
- `from_` — sender address
- `to` — recipients
- `subject` — subject line
- `text` — plain text body
- `html` — HTML body
- `extracted_text` — just the new reply (quoted text stripped)
- `extracted_html` — HTML reply without quotes
- `attachments` — array with `attachment_id`, `filename`, `content_type`
- `labels` — array of string tags
- `created_at` — timestamp

---

## Threads (Conversations)

### List Threads for an Inbox

```bash
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID/threads?limit=10' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

### List ALL Threads (Org-Wide)

```bash
curl -s 'https://api.agentmail.to/v0/threads?limit=10' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

### Get Thread with Messages

```bash
curl -s 'https://api.agentmail.to/v0/threads/THREAD_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

---

## Labels (Message Organization)

Labels are string tags for organizing and filtering messages.

### Add Labels When Sending

Include `"labels": ["tag1", "tag2"]` in the send request body.

### Update Labels on Existing Message

```bash
curl -s -X PATCH 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/MESSAGE_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "add_labels": ["replied", "processed"],
    "remove_labels": ["unreplied"]
  }' | jq .
```

### Filter by Label

```bash
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID/threads?labels=unreplied' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

**Label best practices:**
- Use kebab-case: `priority-high`, `status-pending`, `dept-sales`
- State tracking: `unreplied`, `replied`, `needs-review`
- Campaign tracking: `q4-outreach`, `warm-lead`
- Triage: `billing-question`, `bug-report`, `feature-request`

---

## Drafts

### Create a Draft

```bash
curl -s -X POST 'https://api.agentmail.to/v0/inboxes/INBOX_ID/drafts' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["recipient@example.com"],
    "subject": "Draft for review",
    "text": "Draft body text.",
    "html": "<p>Draft body HTML.</p>",
    "labels": ["needs-review"]
  }' | jq .
```

### Send a Draft

```bash
curl -s -X POST 'https://api.agentmail.to/v0/inboxes/INBOX_ID/drafts/DRAFT_ID/send' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "add_labels": ["sent"],
    "remove_labels": ["needs-review"]
  }' | jq .
```

### List / Get / Update / Delete Drafts

```bash
# List
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID/drafts' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .

# Get
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID/drafts/DRAFT_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .

# Update
curl -s -X PATCH 'https://api.agentmail.to/v0/inboxes/INBOX_ID/drafts/DRAFT_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"subject": "Updated subject"}' | jq .

# Delete
curl -s -X DELETE 'https://api.agentmail.to/v0/inboxes/INBOX_ID/drafts/DRAFT_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY"
```

---

## Attachments

### Send with Attachments

Attachments use base64-encoded content:

```bash
# Encode file
ENCODED=$(base64 -w0 /path/to/file.pdf)

curl -s -X POST 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/send' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"to\": [\"recipient@example.com\"],
    \"subject\": \"Report attached\",
    \"text\": \"See attached report.\",
    \"html\": \"<p>See attached report.</p>\",
    \"attachments\": [{
      \"content\": \"$ENCODED\",
      \"filename\": \"report.pdf\",
      \"content_type\": \"application/pdf\"
    }]
  }" | jq .
```

### Download Attachment

```bash
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/MESSAGE_ID/attachments/ATTACHMENT_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -o downloaded_file.pdf
```

---

## Webhooks (Real-Time Notifications)

### Create Webhook

```bash
curl -s -X POST 'https://api.agentmail.to/v0/webhooks' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhooks",
    "event_types": ["message.received"],
    "inbox_ids": ["my-agent@agentmail.to"],
    "client_id": "my-webhook"
  }' | jq .
```

### Available Events

| Event | Trigger |
|-------|---------|
| `message.received` | Email arrives in inbox |
| `message.sent` | Email successfully sent |
| `message.delivered` | Recipient server accepted |
| `message.bounced` | Delivery failed |
| `message.complained` | Marked as spam |
| `message.rejected` | Rejected before sending |
| `domain.verified` | Domain verification complete |

### List / Delete Webhooks

```bash
# List
curl -s 'https://api.agentmail.to/v0/webhooks' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .

# Delete
curl -s -X DELETE 'https://api.agentmail.to/v0/webhooks/WEBHOOK_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY"
```

---

## Lists (Allow/Block)

Filter email by address or domain:

| Direction | Type | Effect |
|-----------|------|--------|
| receive | allow | Only accept from these |
| receive | block | Reject from these |
| send | allow | Only send to these |
| send | block | Prevent sending to these |

```bash
# Add to receive allowlist
curl -s -X POST 'https://api.agentmail.to/v0/lists/receive/allow' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"entry": "partner@example.com"}'

# Block a domain
curl -s -X POST 'https://api.agentmail.to/v0/lists/receive/block' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"entry": "spammer.com", "reason": "spam domain"}'

# List entries
curl -s 'https://api.agentmail.to/v0/lists/receive/allow?limit=20' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .

# Remove entry
curl -s -X DELETE 'https://api.agentmail.to/v0/lists/receive/allow/partner@example.com' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY"
```

---

## Conversational Email Pattern

Standard workflow for managing email conversations:

### Step 1: Find Unreplied Threads
```bash
curl -s 'https://api.agentmail.to/v0/inboxes/INBOX_ID/threads?labels=unreplied' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .
```

### Step 2: Get Last Message in Thread
```bash
curl -s 'https://api.agentmail.to/v0/threads/THREAD_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq '.messages[-1]'
```

### Step 3: Reply & Update Labels
```bash
# Reply
curl -s -X POST 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/MESSAGE_ID/reply' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["sender@example.com"],
    "text": "Thanks for reaching out!",
    "html": "<p>Thanks for reaching out!</p>"
  }'

# Update labels
curl -s -X PATCH 'https://api.agentmail.to/v0/inboxes/INBOX_ID/messages/MESSAGE_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"add_labels": ["replied"], "remove_labels": ["unreplied"]}'
```

---

## Idempotency

Use `client_id` on create operations to prevent duplicates on retry:

```bash
# Safe to call multiple times — only creates one inbox
curl -s -X POST 'https://api.agentmail.to/v0/inboxes' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username": "my-agent", "client_id": "my-agent-inbox"}'
```

Rules:
- **Deterministic:** Same resource → same `client_id` (e.g., `inbox-for-user-123`)
- **Unique:** Never reuse across resource types
- Supported on: inboxes, webhooks, pods, domains, drafts

---

## API Keys

```bash
# List keys
curl -s 'https://api.agentmail.to/v0/api-keys' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" | jq .

# Create new key
curl -s -X POST 'https://api.agentmail.to/v0/api-keys' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "production-key"}' | jq .

# Delete key
curl -s -X DELETE 'https://api.agentmail.to/v0/api-keys/KEY_ID' \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY"
```

---

## Deliverability Tips

1. **Always send both `text` AND `html`** — HTML-only emails are flagged as spam
2. **Use custom domains** for production (dramatically improves deliverability)
3. **Warm up sending** — start with 10 emails/day per inbox, gradually increase
4. **Distribute across inboxes** — 100 emails from 100 inboxes > 10,000 from 1
5. **Personalize content** — use recipient name, avoid "free", "buy now", ALL CAPS
6. **No images in first contact** — add links/images only after recipient replies
7. **No tracking pixels** — encoded images harm deliverability
8. **Use `client_id`** for idempotent retries

---

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request (check params) |
| 401 | Invalid API key |
| 404 | Resource not found |
| 429 | Rate limited (check `Retry-After` header) |
| 5xx | Server error (safe to retry) |

---

## Quick Reference

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create inbox | POST | `/v0/inboxes` |
| List inboxes | GET | `/v0/inboxes` |
| Send message | POST | `/v0/inboxes/{id}/messages/send` |
| Reply | POST | `/v0/inboxes/{id}/messages/{mid}/reply` |
| Reply all | POST | `/v0/inboxes/{id}/messages/{mid}/reply-all` |
| Forward | POST | `/v0/inboxes/{id}/messages/{mid}/forward` |
| List messages | GET | `/v0/inboxes/{id}/messages` |
| Get message | GET | `/v0/inboxes/{id}/messages/{mid}` |
| Update labels | PATCH | `/v0/inboxes/{id}/messages/{mid}` |
| List threads | GET | `/v0/inboxes/{id}/threads` |
| Get thread | GET | `/v0/threads/{tid}` |
| Create draft | POST | `/v0/inboxes/{id}/drafts` |
| Send draft | POST | `/v0/inboxes/{id}/drafts/{did}/send` |
| Create webhook | POST | `/v0/webhooks` |
| Get attachment | GET | `/v0/inboxes/{id}/messages/{mid}/attachments/{aid}` |
| Allow/block list | POST | `/v0/lists/{direction}/{type}` |
