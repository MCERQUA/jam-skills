#!/usr/bin/env bash
# cron-template.sh — two-phase schedule firing for canonical task.json v0.1.4
#
# Author:   worker-b@mesh (milestone-4, 2026-05-19)
# Runtime:  host@mesh OS crontab (verified canonical scheduler per
#           /workspace/.agents/cron-landscape-2026-05-19.md §1a)
# Depends:  jq, mesh-send, mesh-ack, mesh-delegate, mesh-task-claim, date(1) GNU
#
# Usage (manual / one-shot):
#   cron-template.sh --task-id 2026-05-19-0930-josh-brief-task-74-plan --phase research
#   cron-template.sh --task-id 2026-05-19-0930-josh-brief-task-74-plan --phase execute
#
# Cron installation pattern (host crontab — two lines per scheduled task):
#   # Brief task #74: research phase at 13:00 UTC, execution phase at 14:00 UTC, 2026-05-20
#   0 13 20 5 * /mesh/bin/cron-template.sh --task-id 2026-05-20-0930-josh-brief-task-74 --phase research >> /mesh/logs/cron-task-74.log 2>&1
#   0 14 20 5 * /mesh/bin/cron-template.sh --task-id 2026-05-20-0930-josh-brief-task-74 --phase execute  >> /mesh/logs/cron-task-74.log 2>&1
#
# Default-resolution: if --phase research is invoked and task.json has
# research_at == null, the script COMPUTES research_at = scheduled_at - 3600s
# but does NOT write the value back (defaults are scheduler-side per
# SCHEDULE-DESIGN.md §3). If --phase execute is invoked and state == parked,
# execution ABORTS and alerts the recipient_role party.

set -euo pipefail

# ---------- config ----------
TASKS_ROOT="${TASKS_ROOT:-/workspace/tasks}"
DEFAULT_RESEARCH_LEAD_SECONDS="${DEFAULT_RESEARCH_LEAD_SECONDS:-3600}"
SELF_AGENT_URI="${SELF_AGENT_URI:-host@mesh}"
RESEARCH_AGENT_URI="${RESEARCH_AGENT_URI:-josh-desktop@mesh}"
EXEC_AGENT_URI="${EXEC_AGENT_URI:-josh-desktop@mesh}"
ALERT_FALLBACK="${ALERT_FALLBACK:-mike-voice@mesh}"

# ---------- arg parse ----------
TASK_ID=""
PHASE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --task-id) TASK_ID="$2"; shift 2 ;;
    --phase)   PHASE="$2";   shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 64 ;;
  esac
done
[[ -z "$TASK_ID" || -z "$PHASE" ]] && { echo "usage: $0 --task-id <id> --phase research|execute" >&2; exit 64; }
[[ "$PHASE" == "research" || "$PHASE" == "execute" ]] || { echo "phase must be research|execute" >&2; exit 64; }

now_iso() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
iso_to_epoch() { date -u -d "$1" +%s; }

# ---------- locate task.json (walk known state dirs) ----------
TASK_JSON=""
for STATE_DIR in intake shop-floor planned scheduled today in-flight parked done; do
  CANDIDATE="$TASKS_ROOT/$STATE_DIR/$TASK_ID/task.json"
  if [[ -f "$CANDIDATE" ]]; then
    TASK_JSON="$CANDIDATE"
    break
  fi
done
[[ -z "$TASK_JSON" ]] && { echo "task.json not found for id=$TASK_ID under $TASKS_ROOT" >&2; exit 66; }

# ---------- helpers ----------
jget() { jq -r "$1" "$TASK_JSON"; }
recipient_target() {
  local role; role="$(jget '.recipient_role // "null"')"
  case "$role" in
    operator) echo "${TENANT_OPERATOR_URI:-$ALERT_FALLBACK}" ;;
    client)   echo "$ALERT_FALLBACK" ;;  # never alert client direct
    mike|null|other|"") echo "$ALERT_FALLBACK" ;;
    *)        echo "$ALERT_FALLBACK" ;;
  esac
}

STATE="$(jget '.state')"
SCHEDULED_AT="$(jget '.scheduled_at // empty')"
RESEARCH_AT="$(jget '.research_at // empty')"
TENANT="$(jget '.tenant')"
SUMMARY="$(jget '.summary')"

# ---------- resolve effective research_at (scheduler-side default) ----------
if [[ -z "$RESEARCH_AT" && -n "$SCHEDULED_AT" ]]; then
  RESEARCH_EPOCH=$(( $(iso_to_epoch "$SCHEDULED_AT") - DEFAULT_RESEARCH_LEAD_SECONDS ))
  EFFECTIVE_RESEARCH_AT="$(date -u -d "@$RESEARCH_EPOCH" +"%Y-%m-%dT%H:%M:%SZ")"
else
  EFFECTIVE_RESEARCH_AT="$RESEARCH_AT"
fi

echo "[$(now_iso)] task=$TASK_ID tenant=$TENANT phase=$PHASE state=$STATE research_at=${EFFECTIVE_RESEARCH_AT:-<none>} scheduled_at=${SCHEDULED_AT:-<none>}"

# =====================================================================
# PHASE: research
# =====================================================================
if [[ "$PHASE" == "research" ]]; then
  # Guard: skip if already past completion or parked.
  case "$STATE" in
    done)
      echo "skipping research: state=done already"
      exit 0
      ;;
    parked)
      echo "skipping research: state=parked (already blocked, awaiting human)"
      exit 0
      ;;
  esac

  # Guard: research-only-no-execution tasks emit a warning but still run.
  if [[ -z "$SCHEDULED_AT" ]]; then
    echo "WARN: research_at set but scheduled_at is null — research-only task. proceeding."
  fi

  # Claim lock if required.
  LOCK_REQUIRED="$(jget '.lock_required')"
  if [[ "$LOCK_REQUIRED" == "true" ]]; then
    mesh-task-claim --task-id "$TASK_ID" --by "$SELF_AGENT_URI" --phase research \
      || { echo "lock claim failed for $TASK_ID; deferring"; exit 75; }
  fi

  # Dispatch research run to the canonical planning agent.
  # mesh-delegate writes the task to the agent's inbox and returns once acknowledged.
  mesh-delegate \
    --to "$RESEARCH_AGENT_URI" \
    --task-id "$TASK_ID" \
    --action plan-research \
    --message "RESEARCH PHASE — task=$TASK_ID tenant=$TENANT summary='$SUMMARY'. Read $TASK_JSON, surface blockers, write plan-$TASK_ID.md, transition state planned→scheduled or planned→parked (with failure_modes) per SCHEDULE-DESIGN.md §4."

  # The research agent is responsible for re-reading task.json, appending to
  # state_history, and (if blocker found) transitioning to parked. This script
  # does NOT mutate task.json — that's the agent's job, per Rule 8 (single
  # writer per state transition).

  echo "research dispatched for $TASK_ID; agent=$RESEARCH_AGENT_URI"
  exit 0
fi

# =====================================================================
# PHASE: execute
# =====================================================================
if [[ "$PHASE" == "execute" ]]; then
  # CRITICAL: re-read state. Research phase may have parked the task.
  case "$STATE" in
    parked)
      FAILURES="$(jget '.failure_modes | join(",")')"
      ALERT_TO="$(recipient_target)"
      echo "ABORT execute: task parked by research. failure_modes=[$FAILURES]"
      mesh-send \
        --to "$ALERT_TO" \
        --cc "$ALERT_FALLBACK" \
        --subject "EXECUTION SKIPPED — task $TASK_ID parked by research" \
        --body "Task $TASK_ID (tenant=$TENANT) was scheduled for execution at $SCHEDULED_AT but research phase parked it with failure_modes=[$FAILURES]. parked_until=$(jget '.parked_until // "null"'). Review $TASK_JSON and un-park (state → scheduled) or close."
      exit 0
      ;;
    done)
      echo "skipping execute: state=done already"
      exit 0
      ;;
    intake|shop-floor|planned)
      # Research either didn't run or didn't transition to scheduled.
      # Treat as deferred — alert and abort.
      ALERT_TO="$(recipient_target)"
      echo "ABORT execute: research phase did not transition task to scheduled (state=$STATE)"
      mesh-send \
        --to "$ALERT_TO" \
        --subject "EXECUTION DEFERRED — task $TASK_ID research incomplete (state=$STATE)" \
        --body "Task $TASK_ID expected state=scheduled by $SCHEDULED_AT but is still $STATE. Likely cause: research-phase cron did not fire or the research agent did not complete its transition. Inspect $TASK_JSON."
      exit 0
      ;;
    scheduled|today|in-flight)
      ;;
    *)
      echo "ABORT execute: unknown state $STATE"; exit 70 ;;
  esac

  # Claim lock for execution.
  LOCK_REQUIRED="$(jget '.lock_required')"
  if [[ "$LOCK_REQUIRED" == "true" ]]; then
    mesh-task-claim --task-id "$TASK_ID" --by "$SELF_AGENT_URI" --phase execute \
      || { echo "lock claim failed for $TASK_ID; deferring"; exit 75; }
  fi

  # Dispatch execution to the executor agent.
  mesh-delegate \
    --to "$EXEC_AGENT_URI" \
    --task-id "$TASK_ID" \
    --action execute \
    --message "EXECUTE PHASE — task=$TASK_ID tenant=$TENANT summary='$SUMMARY'. Read $TASK_JSON + plan-$TASK_ID.md, do the work, write result-$TASK_ID.md, transition state to done (with completed_at + outcome)."

  echo "execute dispatched for $TASK_ID; agent=$EXEC_AGENT_URI"
  exit 0
fi
