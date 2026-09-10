#!/usr/bin/env bash
# Hermes Expert — quick lookup against index.json
# Usage:
#   scripts/lookup.sh <term>                      # fuzzy search across all indexes
#   scripts/lookup.sh --env VAR_NAME              # exact env-var lookup
#   scripts/lookup.sh --cli "hermes config show"  # exact CLI command lookup
#   scripts/lookup.sh --config model.provider     # exact config key lookup
#   scripts/lookup.sh --slash /sessions           # exact slash command lookup
#   scripts/lookup.sh --section <id>              # dump one section JSON file
#   scripts/lookup.sh --list-categories           # list categories + section counts
#
# Output: section ids that match + a one-line summary. Read sections/<id>.json
# for the full structured content, or the section's source URL.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INDEX="$ROOT/index.json"

[[ -f "$INDEX" ]] || { echo "ERROR: $INDEX not found. Run scripts/build-index.py first." >&2; exit 1; }
command -v jq >/dev/null || { echo "ERROR: jq required (apt install jq)" >&2; exit 1; }

show_section_summaries() {
  # Read a list of section ids on stdin, print one line each.
  local id title category summary
  while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    jq -r --arg id "$id" '
      .sections[] | select(.id == $id) |
      "\(.id)\t[\(.category)\(if .subcategory != "" then "/" + .subcategory else "" end)]\t\(.title)\n  → sections/\(.id).json\n  → \(.summary[0:160])"
    ' "$INDEX"
  done
}

cmd="${1:-}"
arg="${2:-}"

case "$cmd" in
  --env)
    [[ -z "$arg" ]] && { echo "Usage: lookup.sh --env VAR_NAME" >&2; exit 2; }
    ids=$(jq -r --arg k "$arg" '.by_env_var[$k] // [] | .[]' "$INDEX")
    if [[ -z "$ids" ]]; then
      # fallback to fuzzy match on key names
      echo "# no exact match for env var '$arg'. Closest keys:"
      jq -r --arg q "$arg" '.by_env_var | to_entries | map(select(.key|ascii_downcase|contains($q|ascii_downcase))) | .[].key' "$INDEX" | head -10
    else
      echo "# env var '$arg' is documented in:"
      printf '%s\n' "$ids" | show_section_summaries
    fi
    ;;
  --cli)
    [[ -z "$arg" ]] && { echo "Usage: lookup.sh --cli '<command>'" >&2; exit 2; }
    ids=$(jq -r --arg k "$arg" '.by_cli_command[$k] // [] | .[]' "$INDEX")
    if [[ -z "$ids" ]]; then
      echo "# no exact match for CLI command. Closest:"
      jq -r --arg q "$arg" '.by_cli_command | to_entries | map(select(.key|ascii_downcase|contains($q|ascii_downcase))) | .[].key' "$INDEX" | head -10
    else
      echo "# CLI command '$arg' documented in:"
      printf '%s\n' "$ids" | show_section_summaries
    fi
    ;;
  --config)
    [[ -z "$arg" ]] && { echo "Usage: lookup.sh --config <dotted.key>" >&2; exit 2; }
    ids=$(jq -r --arg k "$arg" '.by_config_key[$k] // [] | .[]' "$INDEX")
    if [[ -z "$ids" ]]; then
      echo "# no exact match for config key. Closest:"
      jq -r --arg q "$arg" '.by_config_key | to_entries | map(select(.key|ascii_downcase|contains($q|ascii_downcase))) | .[].key' "$INDEX" | head -10
    else
      echo "# config key '$arg' documented in:"
      printf '%s\n' "$ids" | show_section_summaries
    fi
    ;;
  --slash)
    [[ -z "$arg" ]] && { echo "Usage: lookup.sh --slash /command" >&2; exit 2; }
    ids=$(jq -r --arg k "$arg" '.by_slash_command[$k] // [] | .[]' "$INDEX")
    if [[ -z "$ids" ]]; then
      echo "# no exact match for slash command. Closest:"
      jq -r --arg q "$arg" '.by_slash_command | to_entries | map(select(.key|ascii_downcase|contains($q|ascii_downcase))) | .[].key' "$INDEX" | head -10
    else
      echo "# slash command '$arg' documented in:"
      printf '%s\n' "$ids" | show_section_summaries
    fi
    ;;
  --section)
    [[ -z "$arg" ]] && { echo "Usage: lookup.sh --section <id>" >&2; exit 2; }
    f="$ROOT/sections/$arg.json"
    if [[ -f "$f" ]]; then
      cat "$f"
    else
      echo "# section '$arg' not found. Available IDs containing '$arg':"
      jq -r --arg q "$arg" '.sections[] | select(.id|ascii_downcase|contains($q|ascii_downcase)) | .id' "$INDEX" | head -20
    fi
    ;;
  --list-categories)
    jq -r '.categories | to_entries[] | "\(.key)\t\(.value|length) sections"' "$INDEX" | column -t -s $'\t'
    ;;
  ""|--help|-h)
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
    ;;
  *)
    # Fuzzy search: scan section titles, summaries, keywords, env vars, cli, config, slash
    q="$cmd"
    echo "# fuzzy search for: $q"
    echo
    echo "## sections (id / title / summary)"
    jq -r --arg q "$q" '
      .sections[] |
      select(
        (.id|ascii_downcase|contains($q|ascii_downcase)) or
        (.title|ascii_downcase|contains($q|ascii_downcase)) or
        (.summary|ascii_downcase|contains($q|ascii_downcase)) or
        (.keywords|map(ascii_downcase)|any(contains($q|ascii_downcase)))
      ) |
      "  \(.id)  [\(.category)\(if .subcategory != "" then "/" + .subcategory else "" end)]  \(.title)"
    ' "$INDEX" | head -20

    echo
    echo "## env vars matching"
    jq -r --arg q "$q" '.by_env_var | to_entries | map(select(.key|ascii_downcase|contains($q|ascii_downcase))) | .[] | "  \(.key)  →  \(.value | join(", "))"' "$INDEX" | head -10

    echo
    echo "## cli commands matching"
    jq -r --arg q "$q" '.by_cli_command | to_entries | map(select(.key|ascii_downcase|contains($q|ascii_downcase))) | .[] | "  \(.key)  →  \(.value | join(", "))"' "$INDEX" | head -10

    echo
    echo "## config keys matching"
    jq -r --arg q "$q" '.by_config_key | to_entries | map(select(.key|ascii_downcase|contains($q|ascii_downcase))) | .[] | "  \(.key)  →  \(.value | join(", "))"' "$INDEX" | head -10

    echo
    echo "## slash commands matching"
    jq -r --arg q "$q" '.by_slash_command | to_entries | map(select(.key|ascii_downcase|contains($q|ascii_downcase))) | .[] | "  \(.key)  →  \(.value | join(", "))"' "$INDEX" | head -10
    ;;
esac
