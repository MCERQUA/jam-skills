#!/bin/bash
# run.sh — registry-driven CLI coding-agent launcher (runs INSIDE the openclaw container)
#
# Usage:  bash /mnt/shared-skills/cli-coding-agents/run.sh <agent-name> "<prompt>"
#
# mode:"local"  → exec the CLI right here (z-code).
# mode:"remote" → file the task to ~/.openclaw/workspace/.cli-tasks/ and poll for
#                 the result. The HOST dispatcher executes it under the proper
#                 subscription — credentials never enter this container.
#
# Call this from a NATIVE SUB-AGENT (sessions_spawn), never from the main voice
# session — it blocks until the CLI agent finishes.
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT="${1:?usage: run.sh <agent-name> <prompt>}"
export CLI_AGENT_PROMPT="${2:?prompt required}"
REG="$DIR/registry.json"
LOCAL_OVERRIDE="$HOME/.openclaw/workspace/.cli-agents-local.json"
WORKSPACE="$HOME/.openclaw/workspace"

CFG=$(node -e '
const fs = require("fs");
const reg = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
let local = {};
try { local = JSON.parse(fs.readFileSync(process.argv[2], "utf8")); } catch (e) {}
const name = process.argv[3];
if (!reg[name]) { console.log("ERR|unknown-agent"); process.exit(0); }
const e = { ...reg[name], ...(local[name] || {}) };
if (!e.enabled) { console.log("ERR|disabled"); process.exit(0); }
console.log(["OK", e.mode || "local", e.cmd || "", e.host_cmd || "", e.timeout_s || 840].join("|"));
' "$REG" "$LOCAL_OVERRIDE" "$AGENT")

IFS='|' read -r STATUS MODE CMD HOST_CMD TIMEOUT_S <<< "$CFG"
if [ "$STATUS" != "OK" ]; then
  echo "CLI_AGENT_ERROR: agent '$AGENT' is $MODE (check registry.json / .cli-agents-local.json)"
  exit 1
fi

if [ "$MODE" = "local" ]; then
  echo "== cli-agent '$AGENT' (local) starting =="
  timeout "$TIMEOUT_S" bash -c "$CMD" 2>&1
  RC=$?
  [ $RC -eq 124 ] && echo "CLI_AGENT_ERROR: '$AGENT' timed out after ${TIMEOUT_S}s"
  exit $RC
fi

# --- remote: file task, poll for result -----------------------------------
TASKS_DIR="$WORKSPACE/.cli-tasks"
mkdir -p "$TASKS_DIR"
ID="$(date +%s)-$$-$RANDOM"
TMP="$TASKS_DIR/.$ID.tmp"
node -e '
const fs = require("fs");
fs.writeFileSync(process.argv[1], JSON.stringify({
  id: process.argv[2],
  agent: process.argv[3],
  prompt: process.env.CLI_AGENT_PROMPT,
  created: new Date().toISOString(),
}, null, 2));
' "$TMP" "$ID" "$AGENT"
mv "$TMP" "$TASKS_DIR/$ID.json"
echo "== cli-agent '$AGENT' (remote) task filed: $ID — host dispatcher will run it =="

WAITED=0
STATUS_FILE="$TASKS_DIR/$ID.status"
RESULT_FILE="$TASKS_DIR/$ID.result.md"
while [ "$WAITED" -lt "$TIMEOUT_S" ]; do
  if [ -f "$STATUS_FILE" ]; then
    ST=$(cat "$STATUS_FILE")
    if [ "$ST" = "done" ] || [[ "$ST" == error* ]]; then
      echo "== cli-agent '$AGENT' finished: $ST =="
      [ -f "$RESULT_FILE" ] && cat "$RESULT_FILE"
      [ "$ST" = "done" ] && exit 0 || exit 1
    fi
  fi
  sleep 5
  WAITED=$((WAITED + 5))
done
echo "CLI_AGENT_ERROR: '$AGENT' remote task $ID timed out after ${TIMEOUT_S}s (dispatcher down? check host cron)"
exit 1
