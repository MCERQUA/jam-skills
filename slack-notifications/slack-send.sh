#!/bin/bash
# Slack message sender — used by openclaw agents
# Usage: bash slack-send.sh "message text" [channel_id]
#
# Requires: SLACK_BOT_TOKEN env var
# Defaults to SLACK_CHANNEL_AI_UPDATES if no channel specified

set -euo pipefail

MESSAGE="${1:?Usage: slack-send.sh \"message\" [channel_id]}"
CHANNEL="${2:-$SLACK_CHANNEL_AI_UPDATES}"

if [ -z "${SLACK_BOT_TOKEN:-}" ]; then
  echo '{"ok":false,"error":"SLACK_BOT_TOKEN not set"}'
  exit 1
fi

if [ -z "${CHANNEL:-}" ]; then
  echo '{"ok":false,"error":"No channel specified and SLACK_CHANNEL_AI_UPDATES not set"}'
  exit 1
fi

# Escape JSON special characters in message
ESCAPED=$(echo "$MESSAGE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")

curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"channel\": \"$CHANNEL\", \"text\": $ESCAPED}"
