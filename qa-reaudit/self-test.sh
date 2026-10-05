#!/bin/sh
# qa-reaudit self-test — autofill case + review-section detector (2026-10-05).
# Same verification shape as the ellipsis patch (host, 2026-10-04): one by-design
# fixture that must PASS, one positive control that must still FAIL, and detector
# controls both ways. Exit 0 = all assertions hold.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
ENGINE="$DIR/qa-reaudit.py"
OUT=$(mktemp -d)
fail() { echo "SELF-TEST FAIL: $1"; exit 1; }

python3 "$ENGINE" "$DIR/qa-autofill-deadlock-fixture.html" selftest "$OUT/deadlock" >/dev/null
python3 - "$OUT/deadlock" <<'EOF' || fail "deadlock fixture must be NO-SHIP with >=1 form-autofill-deadlock"
import json, sys
r = json.load(open(sys.argv[1] + "/audit-report.json"))
assert r["verdict"] == "NO-SHIP", r["verdict"]
bugs = [b for b in r["bugs"] if b["kind"] == "form-autofill-deadlock"]
assert bugs, r["bugs"]
EOF

python3 "$ENGINE" "$DIR/qa-autofill-good-fixture.html" selftest "$OUT/good" >/dev/null
python3 - "$OUT/good" <<'EOF' || fail "good fixture must be SHIP with 0 autofill bugs AND >=1 gated form exercised"
import json, sys
r = json.load(open(sys.argv[1] + "/audit-report.json"))
assert r["verdict"] == "SHIP", r["verdict"]
assert not [b for b in r["bugs"] if b["kind"] == "form-autofill-deadlock"], r["bugs"]
gated = [c["checks"]["form_probe"]["gated_forms"] for c in r["combinations"]]
assert sum(gated) >= 1, "probe never exercised a gated form — check is toothless"
EOF

python3 "$ENGINE" "$DIR/qa-review-sections-fixture.html" selftest "$OUT/reviews" >/dev/null
python3 - "$OUT/reviews" <<'EOF' || fail "review fixture: must find 'What Our Clients Say' structurally, must NOT flag services grid, verdict SHIP"
import json, sys
r = json.load(open(sys.argv[1] + "/audit-report.json"))
assert r["verdict"] == "SHIP", (r["verdict"], r["bugs"])
secs = r["review_sections"]
assert any(s["heading"] == "What Our Clients Say" for s in secs), secs
assert not any("services" in s["selector"] for s in secs), secs
EOF

echo "SELF-TEST PASS — autofill both ways + review-section controls OK ($OUT)"
