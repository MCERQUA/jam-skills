#!/usr/bin/env bash
# admin-review.sh — agent action review chain (v3: sequential dual-reviewer)
#
# FLOW (locked in 2026-05-11 by Mike):
#   filing-agent -> ubuntu-tmux@host (first reviewer, ALWAYS)
#                -> opines (risk/reversibility/blast/verdict)
#                -> forwards to interactive@host (second reviewer)
#                -> interactive opines with tmux's opinion as context
#                -> if both APPROVE: execute
#                -> if either ESCALATES (or they disagree): email Mike with both opinions
#
# FALLBACK: filing-agent's mesh-msg may land on interactive first if tmux watcher missed it.
# Interactive's FIRST job is to wake tmux (host-mesh-keeper.sh start) — never skip tmux.
# If tmux genuinely won't restart after N minutes, separate cron escalates with [CRITICAL] note.
#
# ADMIN BYPASS: if user's clerk_user_id resolves to role=admin, execute immediately + audit.
#
# Subcommands:
#   request <tenant> <summary> <details> [--user-clerk-id ID] [--user-role ROLE]
#   status  <id>                              -> pending|approved|rejected|escalated|unknown
#   read    <id>                              -> dump pending file
#   opine   <id> <APPROVE|ESCALATE> --risk "..." --reversibility "..." --blast "..." --reasoning "..."
#   reject  <id> --reason "..."               -> Mike-tier hard rejection (terminal)
#   list    [--mine]                          -> pending requests (--mine = current AGENT_URI)
#   wake-partner                              -> ensure tmux host-mesh keeper is up
#
# Required env: AGENTMAIL_API_KEY (for Mike-tier escalation only).

set -uo pipefail

QUEUE_BASE=/mnt/agent-mesh/admin-review
PENDING_DIR=$QUEUE_BASE/pending
RESOLVED_DIR=$QUEUE_BASE/resolved
AUDIT_LOG=$QUEUE_BASE/audit-admin-bypass.log
ADMIN_EMAIL="mikecerqua@gmail.com"
# Default to the canonical host inbox. The previous default (jambot-admin-review@agentmail.to)
# never existed on the AgentMail account → all sends 404'd silently. Override with
# ADMIN_REVIEW_FROM_INBOX once a dedicated admin-review inbox is provisioned.
FROM_INBOX="${ADMIN_REVIEW_FROM_INBOX:-jam-bot@agentmail.to}"
TMUX_REVIEWER="${ADMIN_REVIEW_TMUX:-bun-desktop@mesh}"
INTERACTIVE_REVIEWER="${ADMIN_REVIEW_INTERACTIVE:-host@mesh}"

die() { echo "admin-review.sh: $*" >&2; exit 2; }

is_admin() {  # is_admin <clerk_user_id>
    [[ -z "${1:-}" ]] && return 1
    python3 - "$1" <<'PY' 2>/dev/null
import json, sys
try:
    r = json.load(open('/mnt/system/base/identity-registry.json')).get('users', {})
    sys.exit(0 if r.get(sys.argv[1], {}).get('role') == 'admin' else 1)
except Exception:
    sys.exit(1)
PY
}

mesh_send_safe() {  # mesh_send_safe <to> <subject> <body> [--end-of-turn ...]
    local to="$1" subject="$2" body="$3"; shift 3
    if ! command -v mesh-send >/dev/null 2>&1; then
        echo "WARN: mesh-send unavailable — would have sent to $to: $subject" >&2
        return 1
    fi
    printf '%s\n' "$body" | mesh-send --to "$to" --kind message --subject "$subject" "$@" >/dev/null 2>&1
}

email_mike() {  # email_mike <subject> <body>
    # Routes through the canonical email-send-pro wrapper (branded responsive HTML).
    # Signature unchanged so all callers (cmd_opine dual-escalation, etc.) work as-is.
    # tenant=system (ops/admin email). The wrapper resolves its own AgentMail key
    # from .platform-keys.env — no key passed explicitly.
    command -v /usr/local/bin/email-send-pro >/dev/null 2>&1 || {
        echo "WARN: email-send-pro missing — email skipped" >&2; return 1; }
    local payload
    payload=$(SUBJ="$1" BODY="$2" TO="$ADMIN_EMAIL" FROM_INBOX="$FROM_INBOX" python3 -c '
import json, os
subj = os.environ["SUBJ"]
body = os.environ["BODY"].strip()
# Use the first non-empty line as the intro, the remainder as a detail section.
lines = [l for l in body.splitlines()]
intro = next((l.strip() for l in lines if l.strip()), subj)
rest = body[len(intro):].strip() if body.startswith(intro) else body
print(json.dumps({
    "tenant": "system",
    "to": [os.environ["TO"]],
    "from_inbox": os.environ["FROM_INBOX"],
    "subject": subj,
    "intro": intro,
    "sections": [
        {"heading": "Details", "body": rest or "See the pending file referenced above for full context."}
    ],
    "signature_style": "brief",
    "labels": ["admin-review"],
}))')
    echo "$payload" | /usr/local/bin/email-send-pro --send --from-inbox "$FROM_INBOX" >/dev/null 2>&1
}

resolve_request() {  # resolve_request <id> <approved|rejected|escalated> <body-suffix>
    local id="$1" disp="$2" suffix="$3"
    local file="$PENDING_DIR/${id}.md"
    [[ -f "$file" ]] || return 1
    sed -i "s|^status: pending|status: ${disp}|" "$file"
    printf '\n\n---\n\n%s\n' "$suffix" >> "$file"
    mkdir -p "$RESOLVED_DIR"
    mv "$file" "$RESOLVED_DIR/${id}.md"
    # Notify filing agent
    local filed_by=$(grep -m1 '^filed_by:' "$RESOLVED_DIR/${id}.md" | awk '{print $2}')
    if [[ -n "$filed_by" && "$filed_by" != "unknown-agent" ]]; then
        mesh_send_safe "$filed_by" "admin-review-${disp}-${id}" \
            "Request ${id} → ${disp}. Read /mnt/agent-mesh/admin-review/resolved/${id}.md for full disposition + reason to relay to user." \
            --end-of-turn "${filed_by} — disposition received, act + tell user"
    fi
}

opinion_count() {  # opinion_count <file>  → number of '## Opinion by' headers in body
    local file="$1"
    grep -c "^## Opinion by " "$file" 2>/dev/null || echo 0
}

# ===========================================================================
# request: file a new review (admin bypass first; otherwise notify tmux)
# ===========================================================================
cmd_request() {
    local tenant="${1:?usage: request <tenant> <summary> <details> [--user-clerk-id ID] [--user-role ROLE]}"
    local summary="${2:?usage: request <tenant> <summary> <details>}"
    local details="${3:?usage: request <tenant> <summary> <details>}"
    shift 3 || true
    local user_clerk_id="" user_role=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --user-clerk-id) user_clerk_id="$2"; shift 2 ;;
            --user-role)     user_role="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    local now_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local short_uuid=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:8])')
    local id="AR-$(date -u +%Y%m%d)-${short_uuid}"
    local agent_uri="${AGENT_URI:-${HOSTNAME:-unknown-agent}}"

    # Admin bypass — direct execution + audit log, no chain
    if [[ "$user_role" == "admin" ]] || is_admin "$user_clerk_id"; then
        mkdir -p "$QUEUE_BASE"
        printf '%s  AUTO-EXECUTED (admin bypass)  agent=%s  tenant=%s  user_clerk=%s  summary=%s\n' \
            "$now_iso" "$agent_uri" "$tenant" "${user_clerk_id:-unset}" "$summary" >> "$AUDIT_LOG"
        echo "ADMIN_BYPASS:${id}"
        return 0
    fi

    # Normal path: file pending + notify tmux (first reviewer, always)
    mkdir -p "$PENDING_DIR"
    local file="$PENDING_DIR/${id}.md"
    cat > "$file" <<META
---
id: ${id}
status: pending
filed_at: ${now_iso}
filed_by: ${agent_uri}
tenant: ${tenant}
summary: ${summary}
user_clerk_id: ${user_clerk_id:-unset}
user_role: ${user_role:-unknown}
current_reviewer: ${TMUX_REVIEWER}
turn: tmux-first
opinions_received: 0
re_ping_count: 0
last_re_ping_at: null
---

## Original request

${details}

META

    mesh_send_safe "$TMUX_REVIEWER" "admin-review-pending-${id}" \
        "ADMIN-REVIEW pending: ${id} (tenant=${tenant}, summary=\"${summary}\")
You are FIRST reviewer. Read it, opine, and forward to the second reviewer.
  read:    /mnt/shared-skills/admin-review/admin-review.sh read ${id}
  opine:   /mnt/shared-skills/admin-review/admin-review.sh opine ${id} APPROVE|ESCALATE \\
             --risk \"...\" --reversibility \"...\" --blast \"...\" --reasoning \"...\"
After you opine, this script auto-forwards to the second reviewer." \
        --end-of-turn "${TMUX_REVIEWER} — review and opine"
    echo "$id"
}

# ===========================================================================
# opine: a reviewer drops their opinion. If both opinions in, resolves.
# ===========================================================================
cmd_opine() {
    local id="${1:?usage: opine <id> <APPROVE|ESCALATE> --risk ... --reversibility ... --blast ... --reasoning ...}"
    local verdict="${2:?usage: opine <id> <APPROVE|ESCALATE> ...}"
    shift 2
    [[ "$verdict" =~ ^(APPROVE|ESCALATE)$ ]] || die "verdict must be APPROVE or ESCALATE (not '$verdict')"
    local risk="" rev="" blast="" reasoning=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --risk)          risk="$2"; shift 2 ;;
            --reversibility) rev="$2"; shift 2 ;;
            --blast)         blast="$2"; shift 2 ;;
            --reasoning)     reasoning="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    [[ -z "$risk" || -z "$rev" || -z "$blast" || -z "$reasoning" ]] && \
        die "all four required: --risk --reversibility --blast --reasoning"

    local file="$PENDING_DIR/${id}.md"
    [[ -f "$file" ]] || die "no pending request: $id"
    local now_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local reviewer="${AGENT_URI:-${HOSTNAME:-unknown}}"

    # Append opinion
    cat >> "$file" <<OPINION
## Opinion by ${reviewer} — ${verdict}  (${now_iso})
- **Risk:** ${risk}
- **Reversibility:** ${rev}
- **Blast radius:** ${blast}
- **Reasoning:** ${reasoning}

OPINION

    local count=$(opinion_count "$file")
    sed -i "s|^opinions_received:.*|opinions_received: ${count}|" "$file"

    if [[ "$count" -lt 2 ]]; then
        # First opinion — forward to second reviewer
        sed -i "s|^current_reviewer:.*|current_reviewer: ${INTERACTIVE_REVIEWER}|" "$file"
        sed -i "s|^turn:.*|turn: interactive-second|" "$file"
        local tenant=$(grep -m1 '^tenant:' "$file" | awk '{print $2}')
        local summary=$(grep -m1 '^summary:' "$file" | cut -d: -f2- | sed 's/^ //')
        mesh_send_safe "$INTERACTIVE_REVIEWER" "admin-review-second-turn-${id}" \
            "ADMIN-REVIEW (your turn): ${id} (tenant=${tenant}, summary=\"${summary}\")
First reviewer (${reviewer}) opined: ${verdict}.
Read full request + their opinion before opining.
  read:  /mnt/shared-skills/admin-review/admin-review.sh read ${id}
  opine: /mnt/shared-skills/admin-review/admin-review.sh opine ${id} APPROVE|ESCALATE \\
           --risk \"...\" --reversibility \"...\" --blast \"...\" --reasoning \"...\"" \
            --end-of-turn "${INTERACTIVE_REVIEWER} — second-turn review"
        echo "opined; forwarded to ${INTERACTIVE_REVIEWER}"
        return 0
    fi

    # Second opinion in — reconcile
    # Each opinion header is: "## Opinion by <reviewer> — <APPROVE|ESCALATE>  (<iso>)"
    # Match by looking for the literal verdict tokens, not by field position
    # (em-dash + iso timestamp shift positions; $NF would grab the timestamp).
    local first_verdict=$(awk '/^## Opinion by / {for(i=1;i<=NF;i++) if($i=="APPROVE"||$i=="ESCALATE") {print $i; exit}}' "$file" | head -1)
    local second_verdict="$verdict"

    if [[ "$first_verdict" == "APPROVE" && "$second_verdict" == "APPROVE" ]]; then
        resolve_request "$id" "approved" "## Final disposition: APPROVED  (both reviewers agreed)
Filing agent: execute the action and tell the user."
        echo "approved (both reviewers agreed)"
        return 0
    fi

    # Either escalated, or they disagreed — go to Mike with both opinions
    sed -i "s|^current_reviewer:.*|current_reviewer: mike-via-email|" "$file"
    sed -i "s|^turn:.*|turn: mike-tier|" "$file"
    local tenant=$(grep -m1 '^tenant:' "$file" | awk '{print $2}')
    local summary=$(grep -m1 '^summary:' "$file" | cut -d: -f2- | sed 's/^ //')
    local body
    body=$(cat <<EMAIL
Dual-review reached you because: $([[ "$first_verdict" != "$second_verdict" ]] && echo "reviewers disagreed (${first_verdict} vs ${second_verdict})" || echo "at least one reviewer escalated")

REQUEST ID:   ${id}
TENANT:       ${tenant}
SUMMARY:      ${summary}

Both reviewer opinions are in the pending file:
  /mnt/agent-mesh/admin-review/pending/${id}.md

To approve: reply with first line   APPROVE ${id}
To reject:  reply with first line   REJECT ${id} <reason-back-to-user>

Re-ping fires every 4hr until you respond.
EMAIL
)
    email_mike "[ADMIN REVIEW — DUAL ESCALATION] ${tenant}: ${summary}" "$body"
    echo "escalated to Mike (both opinions on file)"
}

# ===========================================================================
# Other subcommands
# ===========================================================================
cmd_status() {
    local id="${1:?usage: status <id>}"
    if [[ -f "$PENDING_DIR/${id}.md" ]]; then
        local turn=$(grep -m1 '^turn:' "$PENDING_DIR/${id}.md" | awk '{print $2}')
        echo "pending (${turn})"
    elif [[ -f "$RESOLVED_DIR/${id}.md" ]]; then
        local disp=$(grep -m1 '^status:' "$RESOLVED_DIR/${id}.md" | awk '{print $2}')
        echo "${disp:-unknown}"
    else
        echo "unknown"; return 1
    fi
}

cmd_read() {
    local id="${1:?usage: read <id>}"
    if [[ -f "$PENDING_DIR/${id}.md" ]]; then cat "$PENDING_DIR/${id}.md"
    elif [[ -f "$RESOLVED_DIR/${id}.md" ]]; then cat "$RESOLVED_DIR/${id}.md"
    else die "no such request: $id"; fi
}

cmd_reject() {
    local id="${1:?usage: reject <id> --reason ...}"; shift
    local reason=""
    while [[ $# -gt 0 ]]; do case "$1" in --reason) reason="$2"; shift 2;; *) shift;; esac; done
    [[ -z "$reason" ]] && die "--reason required (user must be told why)"
    [[ -f "$PENDING_DIR/${id}.md" ]] || die "no pending request: $id"
    local now_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local reviewer="${AGENT_URI:-${HOSTNAME:-unknown}}"
    resolve_request "$id" "rejected" "## Final disposition: REJECTED by ${reviewer} at ${now_iso}
**Reason (relay to user):** ${reason}"
    echo "rejected"
}

cmd_list() {
    local mine=false
    [[ "${1:-}" == "--mine" ]] && mine=true
    local now_epoch=$(date +%s)
    [[ ! -d "$PENDING_DIR" ]] && { echo "no pending dir"; return 0; }
    for f in "$PENDING_DIR"/*.md; do
        [[ -f "$f" ]] || continue
        local id=$(grep -m1 '^id:' "$f" | awk '{print $2}')
        local filed_at=$(grep -m1 '^filed_at:' "$f" | awk '{print $2}')
        local tenant=$(grep -m1 '^tenant:' "$f" | awk '{print $2}')
        local summary=$(grep -m1 '^summary:' "$f" | cut -d: -f2- | sed 's/^ //')
        local reviewer=$(grep -m1 '^current_reviewer:' "$f" | awk '{print $2}')
        local turn=$(grep -m1 '^turn:' "$f" | awk '{print $2}')
        if $mine; then
            [[ "$reviewer" == "${AGENT_URI:-host@mesh}" ]] || continue
        fi
        local age_s=$(( now_epoch - $(date -d "$filed_at" +%s 2>/dev/null || echo "$now_epoch") ))
        printf "%s  age=%dm  tenant=%s  turn=%s  reviewer=%s  %s\n" "$id" "$((age_s/60))" "$tenant" "$turn" "$reviewer" "$summary"
    done
}

cmd_wake_partner() {
    # Called by interactive when it picked up a request before tmux did (fallback).
    # Job: ensure tmux host-mesh-keeper is up, then exit so the caller can wait.
    local keeper=/home/mike/MIKE-AI/scripts/host-mesh-keeper.sh
    if [[ -x "$keeper" ]]; then
        bash "$keeper" status 2>&1 | grep -q "running" && { echo "tmux already up"; return 0; }
        bash "$keeper" start 2>&1
        sleep 3
        if bash "$keeper" status 2>&1 | grep -q "running"; then
            echo "tmux waked"
        else
            echo "ERROR: tmux failed to start; needs Mike intervention" >&2
            return 1
        fi
    else
        echo "WARN: host-mesh-keeper.sh missing at $keeper" >&2
        return 1
    fi
}

sub="${1:-}"; shift || true
case "$sub" in
    request)      cmd_request "$@" ;;
    status)       cmd_status "$@" ;;
    read)         cmd_read "$@" ;;
    opine)        cmd_opine "$@" ;;
    reject)       cmd_reject "$@" ;;
    list)         cmd_list "$@" ;;
    wake-partner) cmd_wake_partner ;;
    -h|--help|help|"")
        cat <<EOF
admin-review.sh v3 — sequential dual-reviewer chain

usage:
  admin-review.sh request  <tenant> <summary> <details> [--user-clerk-id ID] [--user-role ROLE]
  admin-review.sh status   <id>
  admin-review.sh read     <id>
  admin-review.sh opine    <id> APPROVE|ESCALATE --risk "..." --reversibility "..." --blast "..." --reasoning "..."
  admin-review.sh reject   <id> --reason "..."
  admin-review.sh list     [--mine]
  admin-review.sh wake-partner    (interactive uses this to revive tmux on fallback)

Chain: filing-agent → tmux-host (1st) → interactive-host (2nd) → Mike via email
Admin bypass: user role=admin → execute immediately + audit log
EOF
        ;;
    *) die "unknown subcommand: $sub" ;;
esac
