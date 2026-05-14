#!/usr/bin/env bash
# classify.sh — Stage 1 of the contact-enrichment cascade.
# Thin wrapper around classify.py so the skill exposes a consistent .sh surface
# matching email-finder/dataforseo/etc.
#
# Usage:
#   classify.sh "ACME Insulation LLC"
#   classify.sh --batch names.txt
#   cat names.txt | classify.sh --batch -
#   classify.sh --test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/classify.py" "$@"
