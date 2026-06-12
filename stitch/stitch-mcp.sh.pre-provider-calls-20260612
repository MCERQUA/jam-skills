#!/usr/bin/env bash
# stitch-mcp.sh — Direct HTTP calls to Google Stitch MCP server
# Usage: stitch-mcp.sh <tool_name> [json_arguments]
# Stateless JSON-RPC over HTTP

set -euo pipefail

STITCH_ENDPOINT="https://stitch.googleapis.com/mcp"

# API key from container environment (injected via .platform-keys.env)
if [[ -z "${STITCH_API_KEY:-}" ]]; then
  echo "ERROR: STITCH_API_KEY not set in environment." >&2
  exit 1
fi

# Call an MCP tool
call_tool() {
  local tool_name="$1"
  local arguments="$2"
  local tmpfile
  tmpfile=$(mktemp)
  trap "rm -f '$tmpfile'" EXIT

  cat > "$tmpfile" <<ENDJSON
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"${tool_name}","arguments":${arguments}}}
ENDJSON

  curl -s \
    -H "X-Goog-Api-Key: ${STITCH_API_KEY}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -X POST "$STITCH_ENDPOINT" \
    -d @"$tmpfile" 2>/dev/null
}

# List available tools
list_tools() {
  curl -s \
    -H "X-Goog-Api-Key: ${STITCH_API_KEY}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -X POST "$STITCH_ENDPOINT" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' 2>/dev/null
}

# Main
case "${1:-}" in
  --list-tools)
    list_tools
    ;;
  --help)
    cat <<'USAGE'
Usage: stitch-mcp.sh <tool_name> [json_arguments]
       stitch-mcp.sh --list-tools

Examples:
  stitch-mcp.sh list_projects '{}'
  stitch-mcp.sh create_project '{"title": "My App"}'
  stitch-mcp.sh list_screens '{"projectId": "12345"}'
  stitch-mcp.sh generate_screen_from_text '{"projectId": "123", "prompt": "A login page", "modelId": "GEMINI_3_PRO"}'
  stitch-mcp.sh get_screen '{"name": "projects/123/screens/456", "projectId": "123", "screenId": "456"}'
  stitch-mcp.sh edit_screens '{"projectId": "123", "selectedScreenIds": ["456"], "prompt": "Make the button blue"}'
USAGE
    ;;
  "")
    echo "ERROR: No tool name provided. Use --help for usage." >&2
    exit 1
    ;;
  *)
    EMPTY_OBJ='{}'
    call_tool "$1" "${2:-$EMPTY_OBJ}"
    ;;
esac
