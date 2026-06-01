#!/usr/bin/env bash
# webdev-deploy.sh
# Reconcile the webdev container's runtime environment to a target project.
# Used by Phase 8 (DEPLOY) of the website-build pipeline.
#
# Usage:
#   webdev-deploy.sh <client> <project> [--service <svc>] [--expected-title <text>]
#
# Behavior:
#   1. Inspect docker-compose.yml for the client.
#   2. If WEBDEV_PROJECT_NAME already matches <project>: skip rewrite.
#   3. If different: rewrite WEBDEV_PROJECT_NAME and env_file path atomically.
#   4. Ensure /mnt/clients/<client>/webdev/<project>/.env.local exists.
#   5. Recreate the webdev service via `docker compose ... up -d --no-deps`.
#   6. Wait for HTTP 200 from the webdev's host port (timeout 60s).
#   7. (Optional) verify <title> contains expected business name.
#
# Exit codes:
#   0 deployed and verified
#   1 reconciliation or healthcheck failed
#   2 invalid arguments / compose missing

set -euo pipefail

CLIENT=""
PROJECT=""
SERVICE=""
EXPECTED_TITLE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service) SERVICE="$2"; shift 2 ;;
    --expected-title) EXPECTED_TITLE="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    --*) echo "unknown flag: $1" >&2; exit 2 ;;
    *)
      if [[ -z "$CLIENT" ]]; then CLIENT="$1"
      elif [[ -z "$PROJECT" ]]; then PROJECT="$1"
      else echo "unexpected positional: $1" >&2; exit 2
      fi
      shift ;;
  esac
done

if [[ -z "$CLIENT" || -z "$PROJECT" ]]; then
  echo "ERROR: usage: webdev-deploy.sh <client> <project>" >&2
  exit 2
fi

COMPOSE_DIR="/mnt/clients/$CLIENT/compose"
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.yml"
ENV_FILE="$COMPOSE_DIR/.env"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "ERROR: compose file not found: $COMPOSE_FILE" >&2
  exit 2
fi

# --- Discover webdev service name ---------------------------------------------
# Two deploy mechanisms exist across clients:
#   (a) WEBDEV_PROJECT_NAME env var in compose  -> rewrite the env, recreate.
#   (b) older `.active-project` file (e.g. test-dev) -> write the file, restart.
# Detect which one this client uses.
USE_ACTIVE_PROJECT=0
if [[ -z "$SERVICE" ]]; then
  SERVICE="$(awk '
    /^services:/ { in_services=1; next }
    in_services && /^  [a-z][a-z0-9_-]+:/ {
      svc=$1; sub(/:$/, "", svc); current=svc; next
    }
    in_services && current && /WEBDEV_PROJECT_NAME/ { print current; exit }
  ' "$COMPOSE_FILE")"
fi
if [[ -z "$SERVICE" ]]; then
  # Fallback: find the webdev service by image and use the .active-project mechanism.
  SERVICE="$(awk '
    /^services:/ { in_services=1; next }
    in_services && /^  [a-z][a-z0-9_-]+:/ { svc=$1; sub(/:$/, "", svc); current=svc; next }
    in_services && current && /image:[[:space:]]*jambot\/webdev/ { print current; exit }
  ' "$COMPOSE_FILE")"
  [[ -n "$SERVICE" ]] && USE_ACTIVE_PROJECT=1
fi
if [[ -z "$SERVICE" ]]; then
  echo "ERROR: no webdev service found in $COMPOSE_FILE (no WEBDEV_PROJECT_NAME and no jambot/webdev image)" >&2
  echo "       (pass --service <name> to override discovery)" >&2
  exit 2
fi
echo "[deploy] client=$CLIENT  project=$PROJECT  service=$SERVICE  mode=$([[ $USE_ACTIVE_PROJECT == 1 ]] && echo active-project || echo env-var)"

# --- Read current state -------------------------------------------------------
ACTIVE_PROJECT_FILE="/mnt/clients/$CLIENT/openclaw/workspace/Websites/.active-project"
if [[ "$USE_ACTIVE_PROJECT" == "1" ]]; then
  CURRENT_PROJECT="$(cat "$ACTIVE_PROJECT_FILE" 2>/dev/null | tr -d '[:space:]' || true)"
  echo "[deploy] current .active-project=$CURRENT_PROJECT"
else
  CURRENT_PROJECT="$(grep -E "^\s*-\s*WEBDEV_PROJECT_NAME=" "$COMPOSE_FILE" | head -1 | sed -E 's/.*=([^[:space:]]+).*/\1/' || true)"
  echo "[deploy] current WEBDEV_PROJECT_NAME=$CURRENT_PROJECT"
fi

NEEDS_REWRITE=0
if [[ "$CURRENT_PROJECT" != "$PROJECT" ]]; then NEEDS_REWRITE=1; fi

# --- Ensure target project's .env.local exists --------------------------------
TARGET_ENV_DIR="/mnt/clients/$CLIENT/webdev/$PROJECT"
TARGET_ENV_LOCAL="$TARGET_ENV_DIR/.env.local"
if [[ ! -d "$TARGET_ENV_DIR" ]]; then
  mkdir -p "$TARGET_ENV_DIR"
fi
if [[ ! -f "$TARGET_ENV_LOCAL" ]]; then
  : > "$TARGET_ENV_LOCAL"
  echo "[deploy] created empty $TARGET_ENV_LOCAL"
fi

# --- Reconcile the target project ---------------------------------------------
if [[ "$USE_ACTIVE_PROJECT" == "1" ]]; then
  # .active-project mechanism: just (re)write the file. Always write it (idempotent)
  # so a re-run on the same project still asserts the intended target.
  echo "$PROJECT" > "$ACTIVE_PROJECT_FILE"
  echo "[deploy] wrote .active-project=$PROJECT"
elif [[ "$NEEDS_REWRITE" == "1" ]]; then
  BACKUP="$COMPOSE_FILE.bak.$(date +%Y%m%d-%H%M%S)"
  cp "$COMPOSE_FILE" "$BACKUP"
  echo "[deploy] backup written: $BACKUP"

  # Update WEBDEV_PROJECT_NAME=...
  sed -i -E "s|(- WEBDEV_PROJECT_NAME=)[^[:space:]]+|\1$PROJECT|" "$COMPOSE_FILE"

  # Update env_file pointing at /mnt/clients/$CLIENT/webdev/<project>/.env.local
  sed -i -E "s|(- /mnt/clients/$CLIENT/webdev/)[^/]+(/.env.local)|\1$PROJECT\2|" "$COMPOSE_FILE"

  # Verify the rewrite produced expected values.
  NEW_PROJECT="$(grep -E "^\s*-\s*WEBDEV_PROJECT_NAME=" "$COMPOSE_FILE" | head -1 | sed -E 's/.*=([^[:space:]]+).*/\1/' || true)"
  if [[ "$NEW_PROJECT" != "$PROJECT" ]]; then
    echo "[deploy] ERROR: rewrite did not stick. Restoring backup." >&2
    cp "$BACKUP" "$COMPOSE_FILE"
    exit 1
  fi
  echo "[deploy] rewrote WEBDEV_PROJECT_NAME -> $PROJECT"
else
  echo "[deploy] compose already targets $PROJECT, no rewrite needed"
fi

# --- Clear stale .next so `next dev` boots clean ------------------------------
# CRITICAL: the webdev container mounts the openclaw workspace directly
# (/mnt/clients/<client>/openclaw/workspace/Websites -> /app/websites) and runs
# `next dev`. Phase 7 (quality-gate) runs `next build`, leaving a PRODUCTION `.next`
# in that SAME dir. `next dev` then serves mismatched chunks ("Cannot find module
# './NNN.js'", stray pages-router _document.js) -> 500. Move the stale build aside
# (preserve, don't delete) so the dev server compiles a fresh dev .next.
PROJ_DIR="/mnt/clients/$CLIENT/openclaw/workspace/Websites/$PROJECT"
if [[ -d "$PROJ_DIR/.next" ]]; then
  mv "$PROJ_DIR/.next" "$PROJ_DIR/.next.stale-$(date +%Y%m%d-%H%M%S)" 2>/dev/null \
    && echo "[deploy] cleared stale .next (moved aside)" \
    || echo "[deploy] WARN: could not move .next aside"
fi

# --- Recreate the service -----------------------------------------------------
COMPOSE_ARGS=(-f "$COMPOSE_FILE")
if [[ -f "$ENV_FILE" ]]; then COMPOSE_ARGS+=(--env-file "$ENV_FILE"); fi

# Use sg docker if the calling user isn't already in the docker group.
if id -nG | tr ' ' '\n' | grep -qx docker; then
  DOCKER="docker"
else
  DOCKER="sg docker -c"
fi

echo "[deploy] recreating service $SERVICE"
if [[ "$DOCKER" == "docker" ]]; then
  docker compose "${COMPOSE_ARGS[@]}" up -d --no-deps "$SERVICE"
else
  sg docker -c "docker compose ${COMPOSE_ARGS[*]} up -d --no-deps $SERVICE"
fi

# Force a restart so `next dev` re-execs against the cleaned .next. Required for
# SAME-PROJECT re-runs: when compose is unchanged, `up -d` is a no-op and the old
# `next dev` keeps running against the dir whose .next we just moved aside -> 500
# until it restarts. `compose restart` re-runs the entrypoint (install + next dev).
echo "[deploy] restarting $SERVICE for a clean dev compile"
if [[ "$DOCKER" == "docker" ]]; then
  docker compose "${COMPOSE_ARGS[@]}" restart "$SERVICE" || true
else
  sg docker -c "docker compose ${COMPOSE_ARGS[*]} restart $SERVICE" || true
fi

# --- Discover the host port ---------------------------------------------------
CONTAINER_NAME="$SERVICE-$CLIENT"
# Compose typically names containers <project>-<service> when `name:` is set.
PROJECT_NAME="$(grep -E "^name:" "$COMPOSE_FILE" | head -1 | awk '{print $2}' || true)"
if [[ -n "$PROJECT_NAME" ]]; then
  CONTAINER_NAME="${PROJECT_NAME}-${SERVICE}-1"
fi

HOST_PORT="$(awk -v svc="$SERVICE" '
  $0 ~ "^  "svc":" { in_svc=1; next }
  in_svc && /^  [a-z][a-z0-9_-]+:/ { in_svc=0 }
  in_svc && /^    ports:/ { in_ports=1; next }
  in_svc && in_ports && /"[0-9]+:[0-9]+"/ {
    gsub(/[^0-9:]/, "")
    split($0, parts, ":")
    print parts[1]
    exit
  }
' "$COMPOSE_FILE")"

if [[ -z "$HOST_PORT" ]]; then
  echo "[deploy] WARN: could not discover host port for $SERVICE — skipping HTTP check"
  exit 0
fi
echo "[deploy] webdev exposed at host port $HOST_PORT"

# --- Wait for HTTP 200 --------------------------------------------------------
URL="http://127.0.0.1:$HOST_PORT/"
# 120s: a cold `next dev` recompile after restart (+ possible pnpm install) can exceed 60s.
DEADLINE=$(( $(date +%s) + 120 ))
LAST_CODE=""
while [[ $(date +%s) -lt $DEADLINE ]]; do
  LAST_CODE="$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 "$URL" || echo "000")"
  if [[ "$LAST_CODE" == "200" ]]; then break; fi
  sleep 2
done
if [[ "$LAST_CODE" != "200" ]]; then
  echo "[deploy] ERROR: webdev did not return 200 within 120s (last=$LAST_CODE)" >&2
  exit 1
fi
echo "[deploy] webdev healthy at $URL"

# --- Optional title verification ---------------------------------------------
if [[ -n "$EXPECTED_TITLE" ]]; then
  PAGE="$(curl -sS --max-time 5 "$URL")"
  if ! grep -qiF "$EXPECTED_TITLE" <<<"$PAGE"; then
    echo "[deploy] ERROR: expected title '$EXPECTED_TITLE' not found in response" >&2
    exit 1
  fi
  echo "[deploy] title check passed (found '$EXPECTED_TITLE')"
fi

echo "[deploy] DONE: $CLIENT/$PROJECT serving at $URL"
