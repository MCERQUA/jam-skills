#!/usr/bin/env bash
# site-liveness.sh <domain> [<domain> ...] — is this site live FOR THE WORLD?
#
# WHY THIS EXISTS
# A bare `curl https://<domain>/` from inside this VPS (or any container on it) is NOT a
# liveness test. The host's stub resolver, and Hetzner's upstream recursive behind it, keep
# serving pre-NS-flip Afternic/AWS parking A-records for a long time after a domain has been
# pointed at Netlify. curl round-robins onto a dead parking IP, the TLS handshake times out,
# and curl reports 000 — indistinguishable from a site that is genuinely down.
#
# Measured 2026-08-20 on arizonaalpineacademy.com: bare curl 000 on BOTH :443 and :80 for
# five hours, while the site had been live since 03:25 with a valid issued certificate.
# `resolvectl flush-caches` does not help — the stale answer is at the UPSTREAM, not local.
#
# TELL: if :80 also returns 000, it is NOT an SSL problem. Netlify answers :80 with a 301
# even before a cert issues. :80 failing means the request never reached Netlify at all,
# which means resolution, not TLS.
#
# THIS SCRIPT resolves over DoH (dns.google, then cloudflare-dns.com) and pins curl with
# --resolve, so it never trusts the local resolver. Same technique as the block in
# host-deploy-and-verify.sh; extracted so any agent can call it standalone.
# No API tokens. Safe to run from any container.
#
# THREE OUTCOMES, deliberately distinct — "I could not look" is never reported as "down":
#   LIVE          apex answers 200 over the public IP
#   NOT-LIVE      resolved fine, but the site did not answer 200  (real problem)
#   CANNOT-CHECK  DoH could not resolve it at all                 (unknown, not a verdict)
#
# Usage:  bash site-liveness.sh foamcollege.com insulationguide.org
# Exit:   0 all LIVE · 1 any NOT-LIVE · 4 any CANNOT-CHECK (and none NOT-LIVE)
set -uo pipefail
[ $# -ge 1 ] || { echo "usage: site-liveness.sh <domain> [<domain> ...]"; exit 2; }

doh_lookup() {
    local domain="$1" ip=""
    for endpoint in "https://dns.google/resolve" "https://cloudflare-dns.com/dns-query"; do
        ip=$(curl -s --max-time 8 -H "accept: application/dns-json" \
             "${endpoint}?name=${domain}&type=A" 2>/dev/null \
             | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit()
if not isinstance(d,dict): sys.exit()
for a in (d.get('Answer') or []):
    if a.get('type')==1 and a.get('data'):
        print(a['data']); break" 2>/dev/null)
        [ -n "$ip" ] && { echo "$ip"; return 0; }
    done
    return 1
}

rc=0; saw_unknown=0
printf "%-38s %-16s %-6s %-6s %s\n" DOMAIN PUBLIC_IP HTTPS HTTP VERDICT
for d in "$@"; do
    ip=$(doh_lookup "$d") || ip=""
    if [ -z "$ip" ]; then
        printf "%-38s %-16s %-6s %-6s %s\n" "$d" "-" "-" "-" "⚠️  CANNOT-CHECK (DoH could not resolve — this is NOT 'down')"
        saw_unknown=1; continue
    fi
    s=$(curl -s --max-time 20 -o /dev/null -w '%{http_code}' --resolve "$d:443:$ip" "https://$d/" 2>/dev/null)
    p=$(curl -s --max-time 20 -o /dev/null -w '%{http_code}' --resolve "$d:80:$ip"  "http://$d/"  2>/dev/null)
    if [ "$s" = "200" ]; then
        v="✅ LIVE"
    elif [ "$p" = "000" ]; then
        v="❌ NOT-LIVE (:80 also 000 — not reaching the edge)"
        rc=1
    else
        v="❌ NOT-LIVE (edge reachable; likely cert not issued yet)"
        rc=1
    fi
    printf "%-38s %-16s %-6s %-6s %s\n" "$d" "$ip" "$s" "$p" "$v"
done
[ "$rc" = 0 ] && [ "$saw_unknown" = 1 ] && exit 4
exit $rc
