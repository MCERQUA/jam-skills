#!/usr/bin/env bash
# mesh-send-note-fixture.sh — proves BOTH halves of mesh-send's ack reminder on a throwaway tree.
#   presence half (2026-09-11): --replies-to <f> while <f> is still unacked in your inbox -> NOTE
#   absence half  (2026-09-16): no --replies-to, recipient has unacked msgs in your inbox -> NOTE naming them
# Silent on: another author's items, .dup/.acked names, items already in .read/, self-sends.
# Exit 0 = all 5 cases as expected. Never touches the real mesh (MESH_ROOT is a temp dir).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); MS="$HERE/../bin/mesh-send"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p $T/mesh/cc $T/agents/host/inbox/.read $T/agents/host/sent $T/agents/mac-claude/inbox $T/agents/bun-desktop/inbox
mk(){ printf -- '---\nKIND: message\nAUTHOR: %s\nREADERS: [host@mesh]\nREPLIES-TO: null\nSIZE: short\nEND-OF-TURN: host@mesh\n---\nbody\n' "$2" > "$1"; }
mk $T/agents/host/inbox/2026-09-16-001-mac-claude-a.md mac-claude@mesh
mk $T/agents/host/inbox/2026-09-16-002-mac-claude-b.md mac-claude@mesh
mk $T/agents/host/inbox/2026-09-16-003-josh-desktop-c.md josh-desktop@mesh
mk $T/agents/host/inbox/.read/2026-09-16-000-mac-claude-old.md mac-claude@mesh
mk $T/agents/host/inbox/2026-09-16-004-mac-claude-d.md.dup-x mac-claude@mesh
send(){ echo body | MESH_ROOT=$T AGENT_URI=host@mesh MESH_NO_CC_RELAY=1 python3 "$MS" "$@" 2>&1 >/dev/null | grep -E 'NOTE —' || true; }
fail=0; chk(){ if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1 :: got [$3]"; fail=1; fi; }
o=$(send --to mac-claude@mesh --kind message --subject t1)
chk "1 absence NOTE names 001+002 only" "yes" "$( grep -q 'WITHOUT --replies-to' <<<"$o" && grep -q '001-mac-claude-a.md, 2026-09-16-002-mac-claude-b.md\.' <<<"$o" && ! grep -q josh <<<"$o" && ! grep -q 'dup' <<<"$o" && echo yes || echo no)"
o=$(send --to mac-claude@mesh --kind message --subject t2 --replies-to 2026-09-16-001-mac-claude-a.md)
chk "2 presence NOTE only" "yes" "$( grep -q 'STILL UNACKED' <<<"$o" && ! grep -q 'WITHOUT' <<<"$o" && echo yes || echo no)"
o=$(send --to bun-desktop@mesh --kind message --subject t3); chk "3 silent for author with nothing unacked" "" "$o"
mv $T/agents/host/inbox/2026-09-16-00[12]-mac-claude-*.md $T/agents/host/inbox/.read/
o=$(send --to mac-claude@mesh --kind message --subject t4); chk "4 silent after ack" "" "$o"
o=$(send --to host@mesh --kind message --subject t5 --end-of-turn none); chk "5 silent on self-send" "" "$o"
n=$(ls $T/agents/mac-claude/inbox | wc -l); chk "sends still delivered (3)" "3" "$n"
exit $fail
