#!/usr/bin/env bash
set -euo pipefail

# SinaLite API helper script
# Usage: sinalite-api.sh <command> [args...]
# Requires: SINALITE_CLIENT_ID, SINALITE_CLIENT_SECRET in environment

SINALITE_API_URL="${SINALITE_API_URL:-https://liveapi.sinalite.com}"
SINALITE_STORE_CODE="${SINALITE_STORE_CODE:-9}"
TOKEN_CACHE="/tmp/sinalite_token"
TOKEN_MAX_AGE=3600

# --- Auth ---

get_token() {
  # Return cached token if fresh
  if [[ -f "$TOKEN_CACHE" ]]; then
    local cache_age=$(( $(date +%s) - $(stat -c %Y "$TOKEN_CACHE" 2>/dev/null || stat -f %m "$TOKEN_CACHE" 2>/dev/null) ))
    if (( cache_age < TOKEN_MAX_AGE )); then
      cat "$TOKEN_CACHE"
      return 0
    fi
  fi

  if [[ -z "${SINALITE_CLIENT_ID:-}" || -z "${SINALITE_CLIENT_SECRET:-}" ]]; then
    echo "ERROR: SINALITE_CLIENT_ID and SINALITE_CLIENT_SECRET must be set" >&2
    return 1
  fi

  local response
  response=$(curl -sf -X POST "${SINALITE_API_URL}/auth/token" \
    -H "Content-Type: application/json" \
    -d "{\"client_id\":\"${SINALITE_CLIENT_ID}\",\"client_secret\":\"${SINALITE_CLIENT_SECRET}\",\"audience\":\"https://apiconnect.sinalite.com\",\"grant_type\":\"client_credentials\"}" 2>&1) || {
    echo "ERROR: Auth request failed: $response" >&2
    return 1
  }

  local token
  token=$(echo "$response" | jq -r '.access_token' 2>/dev/null) || {
    echo "ERROR: Invalid auth response: $response" >&2
    return 1
  }

  if [[ "$token" == "null" || -z "$token" ]]; then
    echo "ERROR: No access_token in response: $response" >&2
    return 1
  fi

  echo "$token" > "$TOKEN_CACHE"
  echo "$token"
}

api_get() {
  local path="$1"
  local token
  token=$(get_token) || return 1
  curl -sf -H "Authorization: Bearer ${token}" "${SINALITE_API_URL}${path}" 2>&1 || {
    echo "ERROR: GET ${path} failed" >&2
    return 1
  }
}

api_post_json() {
  local path="$1"
  local body="$2"
  local token
  token=$(get_token) || return 1
  curl -sf -X POST "${SINALITE_API_URL}${path}" \
    -H "Authorization: Bearer ${token}" \
    -H "Content-Type: application/json" \
    -d "$body" 2>&1 || {
    echo "ERROR: POST ${path} failed" >&2
    return 1
  }
}

# --- Commands ---

cmd_auth() {
  local token
  token=$(get_token) || exit 1
  echo "{\"access_token\":\"${token}\",\"cached\":true}"
}

cmd_products() {
  api_get "/product"
}

cmd_product() {
  local id="${1:?Usage: sinalite-api.sh product <id> [storeCode]}"
  local store_code="${2:-$SINALITE_STORE_CODE}"
  api_get "/product/${id}/${store_code}"
}

cmd_price() {
  local id="${1:?Usage: sinalite-api.sh price <id> <storeCode> <options_json>}"
  local store_code="${2:?Usage: sinalite-api.sh price <id> <storeCode> <options_json>}"
  local options="${3:?Usage: sinalite-api.sh price <id> <storeCode> <options_json>}"
  # Validate JSON
  echo "$options" | jq . > /dev/null 2>&1 || {
    echo "ERROR: Invalid JSON for options: $options" >&2
    return 1
  }
  api_post_json "/price/${id}/${store_code}" "$options"
}

cmd_estimate() {
  local items="${1:?Usage: sinalite-api.sh estimate '<items_json>' <state> <zip> <country>}"
  local state="${2:?Missing state}"
  local zip="${3:?Missing zip}"
  local country="${4:?Missing country}"
  echo "$items" | jq . > /dev/null 2>&1 || {
    echo "ERROR: Invalid JSON for items: $items" >&2
    return 1
  }
  local body="{\"items\":${items},\"shippingInfo\":{\"ShipState\":\"${state}\",\"ShipZip\":\"${zip}\",\"ShipCountry\":\"${country}\"}}"
  api_post_json "/order/shippingEstimate" "$body"
}

cmd_order() {
  local order_json="${1:?Usage: sinalite-api.sh order '<order_json>'}"
  echo "$order_json" | jq . > /dev/null 2>&1 || {
    echo "ERROR: Invalid JSON for order: $order_json" >&2
    return 1
  }
  api_post_json "/order/new" "$order_json"
}

# --- Main ---

case "${1:-help}" in
  auth)     cmd_auth ;;
  products) cmd_products ;;
  product)  shift; cmd_product "$@" ;;
  price)    shift; cmd_price "$@" ;;
  estimate) shift; cmd_estimate "$@" ;;
  order)    shift; cmd_order "$@" ;;
  help|--help|-h)
    echo "SinaLite API Helper"
    echo ""
    echo "Usage: sinalite-api.sh <command> [args...]"
    echo ""
    echo "Commands:"
    echo "  auth                      Get/cache bearer token"
    echo "  products                  List all products"
    echo "  product <id> [store]      Product options + pricing (store: 6=CA, 9=US, default 9)"
    echo "  price <id> <store> <json> Live price quote for option combo"
    echo "  estimate <json> <st> <zip> <ctry>  Shipping rates"
    echo "  order <json>              Submit order"
    echo ""
    echo "Environment: SINALITE_CLIENT_ID, SINALITE_CLIENT_SECRET, SINALITE_API_URL, SINALITE_STORE_CODE"
    ;;
  *)
    echo "ERROR: Unknown command '${1}'. Run with 'help' for usage." >&2
    exit 1
    ;;
esac
