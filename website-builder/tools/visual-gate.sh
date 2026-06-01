#!/usr/bin/env bash
# visual-gate.sh — host-side Quality Officer VISUAL gate for the website builder.
#
# WHY HOST-SIDE: Playwright + headless Chromium live on the HOST, not inside the
# openclaw build container. So — exactly like the Phase 7 `pnpm build` / URL-curl
# steps and the githubPush step — the in-container agent can't run this itself. It
# flags `visualGate.status="requested"` in .build-status.json and the host
# build-watchdog calls THIS script against the serving site.
#
# WHAT IT DOES: renders every route at mobile+desktop in headless Chromium and runs
# programmatic checks (WCAG contrast / mobile overflow / broken images / clipped /
# empty sections) — catching the light-on-light, dark-on-dark, squished-on-mobile,
# missing-image failures that HTTP checks miss. Writes a report + screenshots, and
# stamps the result back into .build-status.json.
#
# USAGE:
#   visual-gate.sh <project_dir> [url] [routes] [viewports]
#     project_dir : host path to ~/Websites/<project> (holds .build-status.json)
#     url         : site URL (default: .build-status.json .devUrl)
#     routes      : comma list (default: from .quality-gate/urls.txt, else app glob)
#     viewports   : comma list (default: 390,1440  = mobile + desktop)
# EXIT: 0 = PASS, 1 = FAIL (gate). Also writes visualGate.status pass|fail back.

set -uo pipefail

VISUAL_CHECK="/mnt/system/base/skills/quality-review/visual-check.py"

PROJECT_DIR="${1:-}"
URL_ARG="${2:-}"
ROUTES_ARG="${3:-}"
VIEWPORTS="${4:-390,1440}"

if [[ -z "$PROJECT_DIR" || ! -d "$PROJECT_DIR" ]]; then
    echo "ERROR: usage: visual-gate.sh <project_dir> [url] [routes] [viewports]" >&2
    exit 2
fi

STATUS_FILE="$PROJECT_DIR/.build-status.json"
OUT_DIR="$PROJECT_DIR/.quality-gate/visual"
mkdir -p "$OUT_DIR"

# --- Resolve URL (arg > status devUrl) ---------------------------------------
URL="$URL_ARG"
if [[ -z "$URL" && -f "$STATUS_FILE" ]]; then
    URL=$(python3 -c "
import json
try: print(json.load(open('$STATUS_FILE')).get('devUrl','') or '')
except: print('')
" 2>/dev/null)
fi
if [[ -z "$URL" ]]; then
    echo "ERROR: no URL (pass one, or set .devUrl in $STATUS_FILE)" >&2
    exit 2
fi

# --- Resolve routes (arg > urls.txt > app/page.tsx glob > '/') ---------------
ROUTES="$ROUTES_ARG"
if [[ -z "$ROUTES" ]]; then
    URLS_TXT="$PROJECT_DIR/.quality-gate/urls.txt"
    if [[ -s "$URLS_TXT" ]]; then
        ROUTES=$(paste -sd, "$URLS_TXT")
    elif [[ -d "$PROJECT_DIR/src/app" ]]; then
        ROUTES=$(find "$PROJECT_DIR/src/app" -name 'page.tsx' -not -path '*/api/*' \
            | sed -E "s|$PROJECT_DIR/src/app||; s|/page.tsx||; s|^$|/|" | sort -u | paste -sd,)
    fi
    [[ -z "$ROUTES" ]] && ROUTES="/"
fi
# Bound runtime: at most 8 routes through the visual gate
ROUTES=$(echo "$ROUTES" | tr ',' '\n' | grep -v '^$' | head -8 | paste -sd,)

echo "[visual-gate] url=$URL"
echo "[visual-gate] routes=$ROUTES  viewports=$VIEWPORTS"
echo "[visual-gate] out=$OUT_DIR"

# --- Run the visual gate ------------------------------------------------------
python3 "$VISUAL_CHECK" --url "$URL" --routes "$ROUTES" --viewports "$VIEWPORTS" --out "$OUT_DIR"
GATE_RC=$?

# --- Stamp the result back into .build-status.json ----------------------------
if [[ -f "$STATUS_FILE" ]]; then
    python3 -c "
import json, sys
sf='$STATUS_FILE'; rc=$GATE_RC; rep='$OUT_DIR/visual-review.json'
try: d=json.load(open(sf))
except Exception: d={}
verdict='pass' if rc==0 else 'fail'
summary=''
try:
    r=json.load(open(rep))
    summary='%d fail / %d warn' % (r.get('fail_count',0), r.get('warn_count',0))
    fails=[f for f in r.get('findings',[]) if f.get('severity')=='fail'][:6]
except Exception as e:
    fails=[]; summary='report unreadable: %s' % e
d['visualGate']={'status':verdict,'report':rep,'summary':summary,'top_findings':fails}
json.dump(d, open(sf,'w'), indent=2)
print('[visual-gate] stamped visualGate.status=%s (%s)' % (verdict, summary))
" 2>&1
fi

exit $GATE_RC
