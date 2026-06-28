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

# [300b7ef4] File an OPEN pledge at dispatch so the accountability loop tracks this run.
# Derivations: tenant from repo_path, next_run inferred as +7d (default weekly cadence).
# The pledge_id is stable on (agent, deliverable, deadline) so cron re-runs are idempotent.
_PLEDGE_INDEX="/mnt/agent-mesh/mesh/BLACKBOARD/accountability/pledge-index.jsonl"
_BLOG_TENANT=$(python3 -c "
import json, re, sys
try:
    d = json.load(open('$CFG'))
    rp = d.get('repo_path', '')
    m = re.search(r'/mnt/clients/([^/]+)/', rp)
    print(m.group(1) if m else 'unknown')
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown")
_PLEDGE_AGENT="${_BLOG_TENANT}@mesh"
_PLEDGE_DEADLINE=$(date -u -d '+7 days' +%Y-%m-%d 2>/dev/null || date -u -v +7d +%Y-%m-%d 2>/dev/null || echo "")
_PLEDGE_DELIVERABLE="${SITE_KEY}-blog-post-$(date -u +%Y%m%d)"
_PLEDGE_ID=$(printf '%s:%s:%s' "$_PLEDGE_AGENT" "$_PLEDGE_DELIVERABLE" "$_PLEDGE_DEADLINE" | sha256sum | cut -c1-8)
export BLOG_FACTORY_PLEDGE_ID="$_PLEDGE_ID"
export BLOG_FACTORY_TENANT="$_BLOG_TENANT"

if [ -f "$_PLEDGE_INDEX" ] && grep -qF "\"pledge_id\": \"$_PLEDGE_ID\"" "$_PLEDGE_INDEX" 2>/dev/null; then
  : # already filed — idempotent
else
  mkdir -p "$(dirname "$_PLEDGE_INDEX")"
  python3 -c "
import json, sys
print(json.dumps({
    'pledge_id':   sys.argv[1],
    'agent':       sys.argv[2],
    'deadline':    sys.argv[3],
    'deliverable': sys.argv[4],
    'status':      'OPEN',
    'source':      'blog-scheduler',
    'ts':          sys.argv[5],
    'source_file': sys.argv[6],
}))" "$_PLEDGE_ID" "$_PLEDGE_AGENT" "$_PLEDGE_DEADLINE" \
       "$_PLEDGE_DELIVERABLE" "$(date -u +%FT%TZ)" "$CFG" >> "$_PLEDGE_INDEX" || true
  echo "$(date -u +%FT%TZ) blog-factory-cron: pledge filed pledge_id=$_PLEDGE_ID agent=$_PLEDGE_AGENT"
fi

echo "$(date -u +%FT%TZ) blog-factory-cron: START $SITE_KEY"
if bash "$DIR/blog-factory.sh" "$CFG" "$@"; then
  echo "$(date -u +%FT%TZ) blog-factory-cron: OK $SITE_KEY"
else
  rc=$?
  echo "$(date -u +%FT%TZ) blog-factory-cron: FAIL($rc) $SITE_KEY"
  exit $rc
fi
