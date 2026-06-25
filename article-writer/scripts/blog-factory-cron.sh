#!/usr/bin/env bash
# blog-factory-cron.sh — cron wrapper for one client's scheduled blog run.
#
# This makes the pipeline CRON-RUNNABLE. It is intentionally NOT installed fleet-wide
# yet — an operator wires a single crontab line per client when ready (see CADENCE
# in each config's `cadence_cron`). Example crontab entry (weekly Mon 13:00 UTC):
#
#   0 13 * * 1  /mnt/system/base/skills/article-writer/scripts/blog-factory-cron.sh \
#                 manufacturedproductinsurance >> \
#                 /home/mike/MIKE-AI/logs/blog-factory.log 2>&1
#
# It loads the env wrapper (OAuth + platform keys), runs the orchestrator for the named
# config, and appends a one-line result to the log. Topic is auto-picked (brain/plan/
# DataForSEO) unless --topic is passed through.
#
# USAGE: blog-factory-cron.sh <site_key> [extra blog-factory.sh flags...]
set -uo pipefail
SITE_KEY="${1:?usage: blog-factory-cron.sh <site_key> [flags]}"; shift || true
DIR="$(cd "$(dirname "$0")" && pwd)"
CFG="$DIR/config/${SITE_KEY}.json"
[ -f "$CFG" ] || { echo "$(date -u +%FT%TZ) blog-factory-cron: no config $CFG"; exit 2; }

# env: OAuth token + platform keys (idempotent if already set)
if [ -f /home/mike/MIKE-AI/scripts/with-claude-env.sh ]; then
  # shellcheck disable=SC1091
  source /home/mike/MIKE-AI/scripts/with-claude-env.sh 2>/dev/null || true
fi
set -a; source /mnt/system/base/.platform-keys.env 2>/dev/null || true; set +a

echo "$(date -u +%FT%TZ) blog-factory-cron: START $SITE_KEY"
if bash "$DIR/blog-factory.sh" "$CFG" "$@"; then
  echo "$(date -u +%FT%TZ) blog-factory-cron: OK $SITE_KEY"
else
  rc=$?
  echo "$(date -u +%FT%TZ) blog-factory-cron: FAIL($rc) $SITE_KEY"
  exit $rc
fi
