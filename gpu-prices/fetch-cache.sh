#!/bin/bash
# Refresh gpu-prices local cache from gputable.dev free JSON feed
# Cron: 0 6 * * * bash /mnt/system/base/skills/gpu-prices/fetch-cache.sh

CACHE_DIR="$(dirname "$0")/cache"
LOGFILE="/mnt/system/base/skills/gpu-prices/cache/fetch.log"

mkdir -p "$CACHE_DIR"

log() { echo "[$(date -Iseconds)] $*" >> "$LOGFILE"; }

log "Fetching data.json..."
if curl -s --max-time 30 "https://gputable.dev/data.json" -o "$CACHE_DIR/data.json.tmp"; then
  # Validate it's valid JSON with a data key
  if python3 -c "import json,sys; d=json.load(open('$CACHE_DIR/data.json.tmp')); assert 'data' in d" 2>/dev/null; then
    mv "$CACHE_DIR/data.json.tmp" "$CACHE_DIR/data.json"
    ROWS=$(python3 -c "import json; d=json.load(open('$CACHE_DIR/data.json')); print(len(d['data']))" 2>/dev/null)
    log "data.json OK — $ROWS rows"
  else
    log "data.json INVALID JSON — keeping old cache"
    rm -f "$CACHE_DIR/data.json.tmp"
  fi
else
  log "data.json fetch FAILED (curl error $?)"
  rm -f "$CACHE_DIR/data.json.tmp"
fi

log "Fetching history.json..."
if curl -s --max-time 30 "https://gputable.dev/history.json" -o "$CACHE_DIR/history.json.tmp"; then
  if python3 -c "import json,sys; json.load(open('$CACHE_DIR/history.json.tmp'))" 2>/dev/null; then
    mv "$CACHE_DIR/history.json.tmp" "$CACHE_DIR/history.json"
    log "history.json OK"
  else
    log "history.json INVALID JSON — keeping old cache"
    rm -f "$CACHE_DIR/history.json.tmp"
  fi
else
  log "history.json fetch FAILED (curl error $?)"
  rm -f "$CACHE_DIR/history.json.tmp"
fi

log "Done"
