#!/bin/bash
# sec-overdue-scan.sh v2 — OPEN tickets past SLA, with BOTH directions of
# index/ticket disagreement surfaced as MISMATCH (host review 2026-10-05):
#   dir 1: INDEX open, ticket closed   (the SEC-035 class: false escalation)
#   dir 2: INDEX closed, ticket open   (the SEC-017/021 class: false closure)
# Ground truth is the ticket file's LATEST '**Status:' line (tail -1, not -m1 —
# SEC-007 carries an old OVERDUE above its RESOLVED). A blank or unrecognized
# status is CANNOT-TELL, never folded into open or closed. MITIGATED is its own
# verdict (SEC-055: residual open, not closed). CLOSED = resolved/done/closed/fixed
# (sec-enforcement-loop 66c119bd agreement; FIXED added per host).
# Usage: sec-overdue-scan.sh [SEC-ID ...]   (no args = all tickets)
[ -n "$BASH_VERSION" ] || { echo 'must run under bash' >&2; exit 3; }

SEC_DIR="${SEC_DIR:-/mnt/agent-mesh/mesh/SECURITY}"
INDEX="$SEC_DIR/INDEX.md"

now=$(date +%s)
FILTER="$*"
classify() {
  local s
  s=$(printf '%s' "$1" | tr -d '*✅' | tr '[:upper:]' '[:lower:]' | sed 's/^ *//;s/ *$//')
  [ -z "$s" ] && { echo CANNOT-TELL; return; }
  case "$s" in
    resolved*|done*|closed*|fixed*) echo CLOSED ;;
    mitigated*)                     echo MITIGATED ;;
    open*|escalated*|overdue*|partial*|blocked*) echo OPEN ;;
    *)                              echo CANNOT-TELL ;;
  esac
}

printf '%-10s %-9s %-11s %-11s %-8s %s\n' TICKET SEV INDEX TICKET AGE_H NOTE

while IFS='|' read -r _ id sev status rest; do
  id=$(echo "$id" | tr -d ' ')
  [ -n "$FILTER" ] && case " $FILTER " in *" $id "*) ;; *) continue ;; esac
  iverdict=$(classify "$status")
  ticket="$SEC_DIR/${id}.md"
  if [ ! -f "$ticket" ]; then
    [ "$iverdict" = CLOSED ] && continue
    printf '%-10s %-9s %-11s %-11s %-8s %s\n' "$id" "$(echo "$sev"|tr -d ' '|cut -c1-9)" "$iverdict" MISSING '-' 'ticket file absent'
    continue
  fi
  tstat=$(grep -i '^\*\*Status:' "$ticket" | tail -1)
  tverdict=$(classify "${tstat#\*\*Status:\*\*}")
  filed=$(grep -m1 -o 'Filed:\*\* [0-9-]*' "$ticket" | grep -o '[0-9-]*$')
  if [ -n "$filed" ]; then age_h=$(( (now - $(date -d "$filed" +%s)) / 3600 )); else age_h='?'; fi
  short=$(echo "$tstat" | sed 's/^\*\*Status:\*\* *//' | cut -c1-45)
  if [ "$iverdict" = OPEN ] && [ "$tverdict" = OPEN ]; then
    printf '%-10s %-9s %-11s %-11s %-8s %s\n' "$id" "$(echo "$sev"|tr -d ' '|cut -c1-9)" OPEN OPEN "${age_h}h" "$short"
  elif [ "$iverdict" != "$tverdict" ]; then
    printf '%-10s %-9s %-11s %-11s %-8s %s\n' "$id" "$(echo "$sev"|tr -d ' '|cut -c1-9)" "$iverdict" "$tverdict" "${age_h}h" "MISMATCH: $short"
  elif [ "$tverdict" = CANNOT-TELL ] || [ "$tverdict" = MITIGATED ]; then
    printf '%-10s %-9s %-11s %-11s %-8s %s\n' "$id" "$(echo "$sev"|tr -d ' '|cut -c1-9)" "$iverdict" "$tverdict" "${age_h}h" "$short"
  fi
done < <(grep '^| SEC-' "$INDEX")

# direction 2 sweep: ticket files with no INDEX row whose own status is OPEN
for ticket in "$SEC_DIR"/SEC-*.md; do
  id=$(basename "$ticket" .md)
  [ -n "$FILTER" ] && case " $FILTER " in *" $id "*) ;; *) continue ;; esac
  grep -q "^| $id " "$INDEX" && continue
  tstat=$(grep -i '^\*\*Status:' "$ticket" | tail -1)
  [ "$(classify "${tstat#\*\*Status:\*\*}")" = OPEN ] && \
    printf '%-10s %-9s %-11s %-11s %-8s %s\n' "$id" '-' NO-INDEX-ROW OPEN '?' "$(echo "$tstat"|cut -c1-45)"
done
