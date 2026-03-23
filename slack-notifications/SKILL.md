# Slack Notifications Skill

Send messages and updates to the client's Slack workspace. Use this skill when the user asks you to post to Slack, send updates, notify their team, or share results.

## Environment Variables

These are pre-configured in your container — use them directly:

| Variable | Purpose |
|----------|---------|
| `SLACK_BOT_TOKEN` | Bot auth token (xoxb-...) |
| `SLACK_CHANNEL_AI_UPDATES` | Channel ID for AI status updates |
| `SLACK_CHANNEL_LEADS` | Channel ID for lead notifications |

## Sending Messages

### Simple Text Message

```bash
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL_AI_UPDATES\",
    \"text\": \"Your message here\"
  }"
```

### Rich Formatted Message (Block Kit)

Use blocks for structured updates — status reports, task completions, summaries:

```bash
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL_AI_UPDATES\",
    \"text\": \"Fallback text for notifications\",
    \"blocks\": [
      {
        \"type\": \"header\",
        \"text\": { \"type\": \"plain_text\", \"text\": \"Title Here\" }
      },
      {
        \"type\": \"section\",
        \"text\": { \"type\": \"mrkdwn\", \"text\": \"*Bold text* and _italic_ and \`code\`\" }
      },
      {
        \"type\": \"divider\"
      },
      {
        \"type\": \"section\",
        \"fields\": [
          { \"type\": \"mrkdwn\", \"text\": \"*Status:*\\nComplete\" },
          { \"type\": \"mrkdwn\", \"text\": \"*Priority:*\\nHigh\" }
        ]
      }
    ]
  }"
```

### Lead Notification (to #leads channel)

For new customer inquiries, contact form submissions, or lead events:

```bash
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL_LEADS\",
    \"text\": \"New lead: Customer Name\",
    \"blocks\": [
      {
        \"type\": \"header\",
        \"text\": { \"type\": \"plain_text\", \"text\": \"New Lead\" }
      },
      {
        \"type\": \"section\",
        \"fields\": [
          { \"type\": \"mrkdwn\", \"text\": \"*Name:*\\nCustomer Name\" },
          { \"type\": \"mrkdwn\", \"text\": \"*Phone:*\\n(555) 123-4567\" },
          { \"type\": \"mrkdwn\", \"text\": \"*Email:*\\ncustomer@email.com\" },
          { \"type\": \"mrkdwn\", \"text\": \"*Service:*\\nService type\" }
        ]
      },
      {
        \"type\": \"section\",
        \"text\": { \"type\": \"mrkdwn\", \"text\": \"*Message:*\\nCustomer's message here\" }
      }
    ]
  }"
```

## Helper Script

Use the helper script at `/mnt/shared-skills/slack-notifications/slack-send.sh` for quick sends:

```bash
# Simple message to default channel (ai-updates)
bash /mnt/shared-skills/slack-notifications/slack-send.sh "Your message here"

# Message to a specific channel
bash /mnt/shared-skills/slack-notifications/slack-send.sh "Lead from John Smith" "$SLACK_CHANNEL_LEADS"

# Message with custom channel name for logging
bash /mnt/shared-skills/slack-notifications/slack-send.sh "Update text" "$SLACK_CHANNEL_AI_UPDATES"
```

## Channel Routing Rules

| Content | Channel | Variable |
|---------|---------|----------|
| AI task completions, status updates, daily summaries | #ai-updates | `$SLACK_CHANNEL_AI_UPDATES` |
| New leads, customer inquiries, contact form data | #leads | `$SLACK_CHANNEL_LEADS` |
| General messages (when user doesn't specify) | #ai-updates | `$SLACK_CHANNEL_AI_UPDATES` |

## When to Send Slack Messages

**ALWAYS send to Slack when:**
- User explicitly asks: "send this to slack", "post an update", "notify the team"
- A research task or report completes (post summary to #ai-updates)
- A lead or customer inquiry comes in (post to #leads)
- User asks to "share" or "send" results somewhere

**NEVER send without being asked:**
- Don't auto-post every task completion
- Don't spam the channels with routine updates
- Only post when the user requests it or when a specific workflow triggers it

## Slack Markdown (mrkdwn)

Slack uses its own markdown variant in blocks:
- Bold: `*text*`
- Italic: `_text_`
- Code: `` `text` ``
- Code block: ` ```text``` `
- Link: `<https://url.com|Display Text>`
- User mention: `<@USER_ID>`
- Channel link: `<#CHANNEL_ID>`
- Bullet list: Use `\n• item` (no native list syntax)

## Checking Response

The API returns JSON. Check `"ok": true` for success:
```json
{"ok": true, "channel": "C0A8A3BQVCH", "ts": "1234567890.123456"}
```

If `"ok": false`, the `"error"` field explains why (e.g., `"channel_not_found"`, `"not_in_channel"`, `"invalid_auth"`).

## Upload a File

To share a file (image, document, etc.) to a channel:

```bash
curl -s -X POST https://slack.com/api/files.upload \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -F "channels=$SLACK_CHANNEL_AI_UPDATES" \
  -F "file=@/path/to/file.png" \
  -F "title=File Title" \
  -F "initial_comment=Here's the file"
```
