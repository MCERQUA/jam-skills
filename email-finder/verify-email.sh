#!/usr/bin/env bash
# verify-email.sh — Hunter.io email-verifier. Confirms whether an address is
# deliverable + scores it. Verifications are tracked separately from search
# credits (Mike's plan: 100/month, vs 50 search credits). Use freely on
# pattern-derived guesses.
#
# Usage:
#   verify-email.sh <email>
#   verify-email.sh joel@insulate48.com
#
# Output: full Hunter JSON to stdout. Look at data.status (valid|invalid|
# accept_all|webmail|disposable|unknown), data.score (0-100), data.smtp_check.
# data.status="valid" + data.score >= 70 is generally safe to send.

set -uo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: verify-email.sh <email>" >&2
    exit 2
fi

EMAIL="$1"

if [[ -z "${HUNTER_API_KEY:-}" ]]; then
    echo "verify-email.sh: HUNTER_API_KEY not set — source the env file first" >&2
    exit 1
fi

curl -sS --max-time 20 \
    "https://api.hunter.io/v2/email-verifier?email=${EMAIL}&api_key=${HUNTER_API_KEY}"
echo
