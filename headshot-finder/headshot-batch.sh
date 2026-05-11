#!/usr/bin/env bash
# headshot-batch.sh — batch wrapper around headshot-finder.sh. Reads a CSV
# (id,first,last,company[,domain]) and runs the pipeline for each row,
# writing results to <out-dir>/<id>.jpg + <out-dir>/results.csv. Idempotent —
# skips IDs whose <id>.jpg already exists.
#
# Usage:
#   headshot-batch.sh <input.csv> <out-dir> [--rate-seconds N] [--limit N]
#
# Defaults: --rate-seconds 3 (1 call per 3s ≈ 1200/hr max), --limit 0 (no cap).

set -uo pipefail

if [[ $# -lt 2 ]]; then
    echo "usage: headshot-batch.sh <input.csv> <out-dir> [--rate-seconds N] [--limit N]" >&2
    exit 2
fi

CSV="$1"; OUT_DIR="$2"; shift 2
RATE=3
LIMIT=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --rate-seconds) RATE="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

[[ -f "$CSV" ]] || { echo "headshot-batch.sh: input CSV not found: $CSV" >&2; exit 2; }
mkdir -p "$OUT_DIR"
HERE="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$OUT_DIR/results.csv"

# Initialize results.csv if not present
if [[ ! -f "$RESULTS" ]]; then
    echo "id,status,source,confidence,image_url,linkedin_url,notes" > "$RESULTS"
fi

processed=0
ok=0
miss=0
skip=0
err=0

# Skip header row, iterate data rows. Process-substitution keeps counters in
# the current shell (pipe-to-while puts the loop in a subshell, counters die).
while IFS=, read -r id first last company domain || [[ -n "$id" ]]; do
    # Strip CSV quoting + whitespace
    id=$(echo "$id" | tr -d '"' | xargs)
    first=$(echo "$first" | tr -d '"' | xargs)
    last=$(echo "$last" | tr -d '"' | xargs)
    company=$(echo "$company" | tr -d '"' | xargs)
    domain=$(echo "${domain:-}" | tr -d '"' | xargs)

    [[ -z "$id" || -z "$first" || -z "$last" ]] && continue

    out_jpg="$OUT_DIR/${id}.jpg"
    if [[ -f "$out_jpg" ]]; then
        echo "[$id] skip (already have $out_jpg)" >&2
        skip=$((skip+1))
        continue
    fi

    if (( LIMIT > 0 && processed >= LIMIT )); then
        echo "headshot-batch.sh: limit ${LIMIT} reached" >&2
        break
    fi

    domain_arg=()
    [[ -n "$domain" ]] && domain_arg=(--domain "$domain")

    if result=$("$HERE/headshot-finder.sh" "$first" "$last" "$company" "${domain_arg[@]}" --out "$out_jpg" 2>/dev/null); then
        # parse result JSON for csv row
        line=$(echo "$result" | python3 -c "
import json,sys,csv,io
r = json.load(sys.stdin)
buf = io.StringIO()
w = csv.writer(buf)
w.writerow([
    '$id','ok',
    r.get('source') or '',
    r.get('confidence') or 0,
    r.get('image_url') or '',
    r.get('linkedin_url') or '',
    (r.get('notes') or '').replace('\\n',' ')[:200],
])
print(buf.getvalue().rstrip('\\n'))
" 2>/dev/null)
        echo "$line" >> "$RESULTS"
        echo "[$id] OK $first $last @ $company → $(echo "$result" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("source",""), d.get("confidence",0))' 2>/dev/null)" >&2
        ok=$((ok+1))
    else
        line=$(python3 -c "
import csv,io
buf = io.StringIO()
w = csv.writer(buf)
w.writerow(['$id','miss','','','','',''])
print(buf.getvalue().rstrip('\\n'))
")
        echo "$line" >> "$RESULTS"
        echo "[$id] miss $first $last @ $company" >&2
        miss=$((miss+1))
    fi

    processed=$((processed+1))
    sleep "$RATE"
done < <(tail -n +2 "$CSV")

echo "" >&2
echo "DONE  processed=$processed  ok=$ok  miss=$miss  skip=$skip  err=$err" >&2
echo "results CSV: $RESULTS" >&2
echo "images:      $OUT_DIR/<id>.jpg" >&2
