#!/usr/bin/env bash
# foambook.sh — thin CLI wrapper around the FoamBook global API
# (https://foambook.jam-bot.com).
#
# Read-only subcommands work without auth. Mutations need $FOAMBOOK_API_KEY
# set in env (sourced from /mnt/system/base/.platform-keys.env or your
# desk secrets).
#
# Usage examples:
#   foambook.sh search "Pressley"
#   foambook.sh contact 66
#   foambook.sh company 38
#   foambook.sh companies --segment manufacturer
#   foambook.sh add-contact "Joel" "Pressley" --company-id 42 --role "Field Supervisor" --email joel@insulate48.com
#   foambook.sh update-contact 66 --phone "(817) 677-1200"
#   foambook.sh add-company "Insulate48" --segment contractor --website insulate48.com
#   foambook.sh set-photo 66 /tmp/joel.jpg

set -uo pipefail

BASE="${FOAMBOOK_BASE_URL:-https://foambook.jam-bot.com}"

die() { echo "foambook.sh: $*" >&2; exit 2; }
need_key() {
    [[ -n "${FOAMBOOK_API_KEY:-}" ]] || die "FOAMBOOK_API_KEY not set — source /mnt/system/base/.platform-keys.env (or your desk secrets) first"
}

# Build JSON body from --field value pairs after a fixed number of positional args
build_json_body() {
    python3 - "$@" <<'PY'
import json, sys
args = sys.argv[1:]
out = {}
i = 0
while i < len(args):
    if args[i].startswith("--"):
        key = args[i][2:].replace("-", "_")
        val = args[i+1] if i+1 < len(args) else ""
        # int coercion for ID-ish fields
        if key.endswith("_id") and val.isdigit():
            out[key] = int(val)
        else:
            out[key] = val
        i += 2
    else:
        i += 1
print(json.dumps(out))
PY
}

cmd_search() {
    local q="${1:?usage: search <query> [--limit N]}"; shift
    local limit=20
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --limit) limit="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    curl -sS --max-time 15 "${BASE}/api/contacts?q=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$q")"
    echo
}

cmd_contact() {
    local id="${1:?usage: contact <id>}"
    curl -sS --max-time 15 "${BASE}/api/contacts/${id}"
    echo
}

cmd_company() {
    local id="${1:?usage: company <id>}"
    curl -sS --max-time 15 "${BASE}/api/companies/${id}"
    echo
}

cmd_companies() {
    local seg="" qq=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --segment) seg="$2"; shift 2 ;;
            --q) qq="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    local query="$BASE/api/companies?"
    [[ -n "$seg" ]] && query="${query}segment=${seg}&"
    [[ -n "$qq" ]] && query="${query}q=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$qq")&"
    curl -sS --max-time 15 "$query"
    echo
}

cmd_add_contact() {
    need_key
    local first="${1:?usage: add-contact <first> <last> [--company-id N] [--field value...]}"; shift
    local last="${1:?usage: add-contact <first> <last> [--field value...]}"; shift
    local body
    body=$(build_json_body --first_name "$first" --last_name "$last" "$@")
    curl -sS --max-time 15 -X POST "$BASE/api/contacts" \
        -H "Authorization: Bearer $FOAMBOOK_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$body"
    echo
}

cmd_update_contact() {
    need_key
    local id="${1:?usage: update-contact <id> [--field value...]}"; shift
    local body
    body=$(build_json_body "$@")
    curl -sS --max-time 15 -X PUT "$BASE/api/contacts/${id}" \
        -H "Authorization: Bearer $FOAMBOOK_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$body"
    echo
}

cmd_delete_contact() {
    need_key
    local id="${1:?usage: delete-contact <id>}"
    curl -sS --max-time 15 -X DELETE "$BASE/api/contacts/${id}" \
        -H "Authorization: Bearer $FOAMBOOK_API_KEY"
    echo
}

cmd_add_company() {
    need_key
    local name="${1:?usage: add-company <name> [--field value...]}"; shift
    local body
    body=$(build_json_body --name "$name" "$@")
    curl -sS --max-time 15 -X POST "$BASE/api/companies" \
        -H "Authorization: Bearer $FOAMBOOK_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$body"
    echo
}

cmd_update_company() {
    need_key
    local id="${1:?usage: update-company <id> [--field value...]}"; shift
    local body
    body=$(build_json_body "$@")
    curl -sS --max-time 15 -X PUT "$BASE/api/companies/${id}" \
        -H "Authorization: Bearer $FOAMBOOK_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$body"
    echo
}

cmd_set_photo() {
    need_key
    local id="${1:?usage: set-photo <contact_id> <local-image-path>}"
    local path="${2:?usage: set-photo <contact_id> <local-image-path>}"
    [[ -f "$path" ]] || die "image not found: $path"
    curl -sS --max-time 30 -X POST "$BASE/api/contacts/${id}/photo" \
        -H "Authorization: Bearer $FOAMBOOK_API_KEY" \
        -F "file=@${path}"
    echo
}

cmd_set_logo() {
    need_key
    local id="${1:?usage: set-logo <company_id> <local-image-path>}"
    local path="${2:?usage: set-logo <company_id> <local-image-path>}"
    [[ -f "$path" ]] || die "image not found: $path"
    curl -sS --max-time 30 -X POST "$BASE/api/companies/${id}/logo" \
        -H "Authorization: Bearer $FOAMBOOK_API_KEY" \
        -F "file=@${path}"
    echo
}

cmd_segments() {
    curl -sS --max-time 10 "${BASE}/api/segments"
    echo
}

cmd_health() {
    local status
    status=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${BASE}/api/segments")
    echo "GET /api/segments → $status"
}

# --- dispatch ----------------------------------------------------------------
sub="${1:-}"; shift || true
case "$sub" in
    search)         cmd_search "$@" ;;
    contact)        cmd_contact "$@" ;;
    company)        cmd_company "$@" ;;
    companies)      cmd_companies "$@" ;;
    add-contact)    cmd_add_contact "$@" ;;
    update-contact) cmd_update_contact "$@" ;;
    delete-contact) cmd_delete_contact "$@" ;;
    add-company)    cmd_add_company "$@" ;;
    update-company) cmd_update_company "$@" ;;
    set-photo)      cmd_set_photo "$@" ;;
    set-logo)       cmd_set_logo "$@" ;;
    segments)       cmd_segments ;;
    health)         cmd_health ;;
    ""|-h|--help|help)
        cat <<EOF
foambook.sh — CLI for the FoamBook global API (${BASE})

Read (no auth):
  search <query>                  - search contacts
  contact <id>                    - get one contact
  company <id>                    - get one company
  companies [--segment X] [--q X] - list companies
  segments                        - list valid segment values
  health                          - quick reachability check

Write (requires \$FOAMBOOK_API_KEY):
  add-contact <first> <last> --company-id N [--field val...]
  update-contact <id> [--field val...]
  delete-contact <id>
  add-company <name> [--field val...]
  update-company <id> [--field val...]
  set-photo <contact_id> <image-path>
  set-logo <company_id> <image-path>

Env:
  FOAMBOOK_API_KEY    bearer key (from .platform-keys.env or desk secrets)
  FOAMBOOK_BASE_URL   override base (default: ${BASE})
EOF
        ;;
    *)
        echo "foambook.sh: unknown subcommand '$sub' (try --help)" >&2
        exit 2
        ;;
esac
