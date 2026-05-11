#!/usr/bin/env bash
# domain-search.sh — Hunter.io domain-search for ONE credit returns the email
# pattern (e.g. {first}.{last}@example.com) + ~10 crawled named addresses.
#
# This is the EFFICIENT path for batch work: one credit per company, then
# derive person emails from the pattern and verify cheaply (see verify-email.sh).
# Per-person `find-email.sh` (which spends a credit each) only as a fallback for
# domains Hunter has no crawl on.
#
# Usage:
#   domain-search.sh <domain> [limit]
#   domain-search.sh insulate48.com
#   domain-search.sh insulate48.com 25
#
# Output: full Hunter JSON to stdout. Look at data.pattern and data.emails[].

set -uo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: domain-search.sh <domain> [limit]" >&2
    exit 2
fi

DOMAIN="$1"
LIMIT="${2:-10}"

if [[ -z "${HUNTER_API_KEY:-}" ]]; then
    echo "domain-search.sh: HUNTER_API_KEY not set — source the env file first" >&2
    exit 1
fi

curl -sS --max-time 20 \
    "https://api.hunter.io/v2/domain-search?domain=${DOMAIN}&api_key=${HUNTER_API_KEY}&limit=${LIMIT}"
echo
