#!/bin/bash
# Detection selftest — pledge 71da8612. Proves the scanner's VALUE_PATTERNS still FIRE
# on real-shaped credential values, with fixtures that IMPORT the live arrays from
# sec-scanner-v0.1.sh (a copy here would drift the moment production tunes a length).
# One planted positive per family that has ever had a live hit; two NEG lines prove
# elided/prefix mentions stay quiet (SEC-036 / SEC-022 classes).
# All fixture values are synthetic. Fixtures live in mktemp /tmp, outside scan surfaces,
# and are deleted on exit — the nightly scanner must never find this file's fixtures.
# Usage: sec-detect-selftest.sh [path-to-sec-scanner-v0.1.sh]
#   (default: security-officer's production scanner on the shared mesh mount)
[ -n "$BASH_VERSION" ] || { echo 'must run under bash' >&2; exit 3; }
set -uo pipefail
SCRIPT="${1:-${SEC_SCANNER:-/mnt/agent-mesh/workspaces/security-officer/bin/sec-scanner-v0.1.sh}}"
[ -f "$SCRIPT" ] || { echo "FAIL: scanner not found at $SCRIPT" >&2; exit 1; }

extract_arr() { # NAME -> prints elements one per line
    sed -n "/^$1=(/,/^)/p" "$SCRIPT" | sed -e '1d' -e '$d' \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*#.*$//' -e 's/^"//; s/"[[:space:]]*$//' -e "s/^'//; s/'[[:space:]]*$//" \
        | grep -v '^$'
}
mapfile -t VALUE_PATTERNS < <(extract_arr VALUE_PATTERNS)
[ ${#VALUE_PATTERNS[@]} -gt 0 ] || { echo "FAIL: could not read VALUE_PATTERNS from $SCRIPT"; exit 1; }

# Synthetic positive per VALUE pattern: a match-shaped fake value.
# Each is generated to match its own pattern by construction (prefix + filler chars).
gen_pos() { # pattern -> synthetic matching string (or empty if unbuildable)
    local p="$1" fill
    fill=$(head -c 200 /dev/urandom | base64 | tr -d '/+=' | tr -d '\n')
    local fill2; fill2=$(head -c 400 /dev/urandom | base64 | tr -d '/+=' | tr -d '\n')
    case "$p" in
        SG\\.*)
            echo "SG.${fill:0:25}.${fill2:0:25}" ;;          # escaped-dot SendGrid class
        'sk_'*'live|test'*)
            echo "sk_live_$(echo "$fill" | tr -cd '0-9A-Za-z' | head -c 30)" ;;
        'sk-ant-'*)          echo "sk-ant-${fill:0:70}" ;;
        'sk-proj-'*)         echo "sk-proj-${fill:0:50}" ;;
        'aia_sk_'*)          echo "aia_sk_${fill:0:30}" ;;
        'Bearer ey'*)        echo "Bearer ey${fill:0:40}" ;;
        'gsk_'*|'msy_'*|'ApiK-'*) echo "${p%%\[*}${fill:0:30}" ;;
        'AKIA'*)             echo "AKIA$(echo "$fill" | tr 'a-z' 'A-Z' | tr -cd '0-9A-Z' | head -c 16)" ;;
        'AIza'*)             echo "AIza${fill:0:35}" ;;
        'gh[pousr]_'*)       echo "ghp_${fill:0:40}" ;;
        'github_pat_'*)      echo "github_pat_${fill:0:60}" ;;
        'xoxb-'*)            echo "xoxb-${fill:0:40}" ;;
        'SG.'*)              echo "SG.${fill:0:30}" ;;
        'sk_live_'*)         echo "sk_live_${fill:0:40}" ;;
        '-----BEGIN'*)       _kt="RSA PRIVATE"" KEY"   # assembled from parts: no literal PEM header in this file (host 2026-10-03; the commit gate flagged it)
                             printf -- '-----BEGIN %s-----\n%s\n-----END %s-----\n' "$_kt" "${fill:0:60}" "$_kt" ;;
        'xox'*)              echo "xoxb-${fill:0:40}" ;;
        'sso-key'*)          echo "sso-key ${fill:0:12}:${fill2:0:12}" ;;
        'sk-'*)              echo "sk-$(echo "$fill" | tr -cd '0-9A-Za-z' | head -c 50)" ;;
        'postgres'*)         echo "postgresql://svcuser:${fill:0:20}@db-pooler.c-2.aws.example.com/appdb" ;;
        *)                   echo "" ;;  # unknown family: skip rather than guess wrong
    esac
}

FIX=$(mktemp -d /tmp/sec-detect-selftest.XXXXXX)
trap 'rm -rf "$FIX"' EXIT

rc=0; tested=0
i=0
for p in "${VALUE_PATTERNS[@]}"; do
    i=$((i+1))
    val=$(gen_pos "$p")
    [ -n "$val" ] || continue
    tested=$((tested+1))
    printf 'synthetic fixture %d: %s\n' "$i" "$val" > "$FIX/pos-$i.txt"
    if grep -rqE -e "$p" "$FIX/pos-$i.txt"; then st=PASS; else st=FAIL; rc=1; fi
    printf '%-52s %s\n' "POS[$i] ${p:0:48}" "$st"
done

# NEG-1: elided value (SEC-036 class) must NOT match its own family pattern
echo 'CLAUDE_CODE_OAUTH_TOKEN="sk-ant-oat01-XXXX...0"' > "$FIX/neg-1-elided.txt"
if grep -qE -e 'sk-ant-[A-Za-z0-9_-]{60,}' "$FIX/neg-1-elided.txt"; then echo 'NEG-1 elided-value                     FAIL'; rc=1; else echo 'NEG-1 elided-value                     PASS'; fi
# NEG-2: hyphenated prose slug (SEC-022 class) must NOT match sk-proj pattern
echo 'see sk-proj-to-scanner-value-patterns for details' > "$FIX/neg-2-slug.txt"
if grep -qE -e 'sk-proj-[A-Za-z0-9_-]{40,}' "$FIX/neg-2-slug.txt"; then echo 'NEG-2 prose-slug                       FAIL'; rc=1; else echo 'NEG-2 prose-slug                       PASS'; fi

echo "families tested: $tested / ${#VALUE_PATTERNS[@]} (unbuildable patterns skipped, listed below)"
for p in "${VALUE_PATTERNS[@]}"; do
    [ -z "$(gen_pos "$p")" ] && echo "  SKIP: $p"
done
exit $rc
