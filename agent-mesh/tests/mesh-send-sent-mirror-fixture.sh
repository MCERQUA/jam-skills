#!/usr/bin/env bash
# mesh-send-sent-mirror-fixture.sh — a fan-out (same sender, same subject, same day, N recipients)
# must leave N files in the sender's sent/, each with the SAME name as the copy in its recipient's inbox.
#
# Found 2026-10-04 (host@mesh): the sequence number is allocated per RECIPIENT inbox, and the sent/
# mirror reused that name, so every recipient whose inbox was at the same number overwrote the previous
# mirror. Measured: 30 sends of one subject -> 11 files in host/sent (11 recipients got -004-). The
# weekly prompts (~35 lanes -> 14 mirrors) and the nightly kickoff had been losing mirrors the same way,
# and the urgent rate limit counts sent/, so overwritten urgents were invisible to it too.
#
# Runs against a throwaway MESH_ROOT (never the real mesh). Pass a mesh-send path to test another copy.
# Exit 0 = every case as expected.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); MS="${1:-$HERE/../bin/mesh-send}"
T=$(mktemp -d)   # left in place (fleet never deletes); it is under the system temp dir
mkdir -p $T/mesh/cc $T/agents/host/inbox $T/agents/host/sent/archive
for r in a b c d; do mkdir -p $T/agents/$r/inbox/.read; done
D=$(date -u +%Y-%m-%d)
send(){ echo body | MESH_ROOT=$T AGENT_URI=host@mesh MESH_NO_CC_RELAY=1 python3 "$MS" --kind announcement \
          --end-of-turn none --subject fan --to "$1" >/dev/null 2>&1; }
fail=0; chk(){ if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1 :: got [$3]"; fail=1; fi; }

for r in a b c; do send $r@mesh; done
chk "1 three sends -> three sent/ mirrors" "3" "$(ls $T/agents/host/sent | grep -c -- '-host-fan\.md$')"
ok=yes
for r in a b c; do
  f=$(ls $T/agents/$r/inbox | grep -- '-host-fan\.md$')
  [ -n "$f" ] && [ -f "$T/agents/host/sent/$f" ] && grep -q "READERS: \[$r@mesh\]" "$T/agents/host/sent/$f" || ok=no
done
chk "2 each mirror has its recipient's inbox name and names that recipient" "yes" "$ok"

# a mirror already moved to sent/archive/ still owns its name
printf -- '---\nKIND: announcement\nAUTHOR: host@mesh\nREADERS: [x@mesh]\n---\nold\n' > "$T/agents/host/sent/archive/$D-001-host-arch.md"
echo body | MESH_ROOT=$T AGENT_URI=host@mesh MESH_NO_CC_RELAY=1 python3 "$MS" --kind announcement \
  --end-of-turn none --subject arch --to d@mesh >/dev/null 2>&1
chk "3 a name held in sent/archive/ is not reused" "no" \
  "$( [ -f "$T/agents/host/sent/$D-001-host-arch.md" ] && echo yes || echo no)"
chk "4 archived mirror untouched" "old" "$(tail -1 "$T/agents/host/sent/archive/$D-001-host-arch.md")"
chk "5 every send still delivered (a,b,c,d)" "4" "$(ls $T/agents/{a,b,c,d}/inbox/*.md 2>/dev/null | wc -l)"
echo "sandbox: $T"
exit $fail
