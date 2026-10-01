#!/usr/bin/env bash
# self-test.sh: controls for live_delivery.py (the writer) and page.html (the page).
# Builds its own fixtures in a fresh temp dir and never touches a real uploads directory.
# Exit 0 only if every writer check passes AND the writer mutant (the file-not-delivered
# refusal removed) is caught. The page checks need Playwright; where it is not importable they
# print SKIPPED and are not counted as passes. LD_PYTHON=<python with playwright> to run them.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d "${TMPDIR:-/tmp}/ld-selftest.XXXXXX")"
cleanup() { case "$T" in */ld-selftest.??????) [ "${LD_KEEP:-0}" = 1 ] || rm -rf -- "$T" ;; esac; }
trap cleanup EXIT
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "  ok   $1"; }
bad() { FAIL=$((FAIL+1)); echo "  FAIL $1"; }
sha() { python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }
expect_rc() { # expect_rc <want> <label> <cmd...>
  local want="$1" label="$2"; shift 2
  "$@" >"$T/out" 2>&1; local rc=$?
  if [ "$rc" = "$want" ]; then ok "$label (rc $rc)"; else bad "$label (want rc $want, got $rc): $(head -c 300 "$T/out")"; fi
}
jq_py() { python3 -c "import json,sys; m=json.load(open(sys.argv[1])); print($2)" "$1"; }

run_suite() { # run_suite <path-to-live_delivery.py>
  local L="$1" R="$T/run.$RANDOM"; local U="$R/uploads" P="$R/pages"
  mkdir -p "$U" "$P"
  local W=(--uploads "$U" --pages "$P" --base-url https://example.test)
  local M="$U/job-a.json"

  echo "[A] seed writes the whole placeholder set first"
  expect_rc 0 "seed 3 slots" python3 "$L" --job job-a "${W[@]}" --seed 3 --title "Job A" --ask "Reply with a number."
  [ "$(jq_py "$M" "len(m['clips'])")" = 3 ] && ok "3 slots in the manifest" || bad "slot count wrong"
  [ "$(jq_py "$M" "sorted(set(c['status'] for c in m['clips']))")" = "['queued']" ] && ok "every slot starts queued" || bad "seed status wrong"
  [ "$(jq_py "$M" "m['schema']")" = "live-delivery/1" ] && ok "schema live-delivery/1" || bad "schema wrong"
  local before; before="$(sha "$M")"
  expect_rc 1 "re-seed over a live manifest without --force is refused" python3 "$L" --job job-a "${W[@]}" --seed 5
  [ "$(sha "$M")" = "$before" ] && ok "...and the manifest is unchanged" || bad "a refused re-seed changed the manifest"
  echo '{"not":"ours"}' > "$U/job-b.json"; local b0; b0="$(sha "$U/job-b.json")"
  expect_rc 1 "seed over someone else's JSON is refused" python3 "$L" --job job-b "${W[@]}" --seed 2
  expect_rc 1 "...even with --force" python3 "$L" --job job-b "${W[@]}" --seed 2 --force
  [ "$(sha "$U/job-b.json")" = "$b0" ] && ok "...and that file is byte-identical" || bad "a foreign JSON was overwritten"
  expect_rc 1 "--seed 0 is refused" python3 "$L" --job job-c "${W[@]}" --seed 0
  [ ! -e "$U/job-c.json" ] && ok "...and wrote nothing" || bad "a refused seed wrote a manifest"
  printf '{"shots":[{"n":7,"id":"s07","title":"Close","description":"the button"},{"n":2,"id":"s02","title":"Open","purpose":"the cold open"}]}' > "$R/shots.json"
  expect_rc 0 "seed from a shot list" python3 "$L" --job job-d "${W[@]}" --seed "$R/shots.json"
  [ "$(jq_py "$U/job-d.json" "[(c['n'],c['beat'],c['label'],c['shows']) for c in m['clips']]")" = "[(1, 's02', 'Open', 'the cold open'), (2, 's07', 'Close', 'the button')]" ] \
    && ok "shot-list rows become slots in plan order, renumbered 1..N, shows carried" || bad "shot-list seeding wrong: $(jq_py "$U/job-d.json" "[(c['n'],c['beat'],c['label'],c['shows']) for c in m['clips']]")"

  echo "[B] a slot flips only to a file that is actually delivered"
  expect_rc 1 "ready with no file is refused" python3 "$L" --job job-a "${W[@]}" --set 1 --status ready
  before="$(sha "$M")"
  expect_rc 1 "a file that is not in uploads is refused" python3 "$L" --job job-a "${W[@]}" --set 1 --status ready --file not-there.mp4
  [ "$(sha "$M")" = "$before" ] && ok "...and the manifest is unchanged" || bad "a refused flip changed the manifest"
  expect_rc 1 "a path instead of a bare name is refused" python3 "$L" --job job-a "${W[@]}" --set 1 --status ready --file ../x.mp4
  expect_rc 1 "an unknown slot is refused" python3 "$L" --job job-a "${W[@]}" --set 9 --status rendering
  expect_rc 1 "an unknown status is REFUSED (1), never read as cannot-tell (2)" python3 "$L" --job job-a "${W[@]}" --set 1 --status done
  expect_rc 1 "a bad flag is a refusal (1), never cannot-tell (2)" python3 "$L" --job job-a "${W[@]}" --set 1 --no-such-flag
  expect_rc 1 "--set with nothing to change is refused" python3 "$L" --job job-a "${W[@]}" --set 1
  expect_rc 0 "rendering" python3 "$L" --job job-a "${W[@]}" --set 1 --status rendering
  head -c 64 /dev/urandom > "$U/take-1.mp4"; head -c 64 /dev/urandom > "$U/take-1b.mp4"; head -c 64 /dev/urandom > "$U/take-1c.mp4"
  expect_rc 0 "ready with a delivered file" python3 "$L" --job job-a "${W[@]}" --set 1 --status ready --file take-1.mp4 --measure duration_s=8.5 --measure seed=42 --measure look=warm --note "first pass"
  [ "$(jq_py "$M" "m['clips'][0]['url']")" = "/uploads/take-1.mp4" ] && ok "the writer composes the URL" || bad "url wrong"
  [ "$(jq_py "$M" "m['clips'][0]['measurements']")" = "{'duration_s': 8.5, 'seed': 42, 'look': 'warm'}" ] && ok "measurements typed (float, int, text)" || bad "measurements wrong: $(jq_py "$M" "m['clips'][0]['measurements']")"
  expect_rc 0 "add an alternate take" python3 "$L" --job job-a "${W[@]}" --set 1 --file take-1c.mp4 --alt --note "other lens"
  [ "$(jq_py "$M" "(m['clips'][0]['file'], [a['file'] for a in m['clips'][0]['alternates']])")" = "('take-1.mp4', ['take-1c.mp4'])" ] && ok "an alternate never replaces the primary" || bad "alternate handling wrong"
  expect_rc 1 "--alt with a --status is refused" python3 "$L" --job job-a "${W[@]}" --set 1 --file take-1c.mp4 --alt --status failed
  expect_rc 0 "replace the primary" python3 "$L" --job job-a "${W[@]}" --set 1 --file take-1b.mp4
  [ "$(jq_py "$M" "[s['file'] for s in m['clips'][0]['superseded']]")" = "['take-1.mp4']" ] && ok "the displaced primary stays declared under superseded[]" || bad "superseded missing"
  expect_rc 0 "a failed roll is marked failed" python3 "$L" --job job-a "${W[@]}" --set 2 --status failed --note "the render died"
  expect_rc 0 "header finding" python3 "$L" --job job-a "${W[@]}" --header --finding "take 1 is the one"
  [ "$(jq_py "$M" "m['finding']")" = "take 1 is the one" ] && ok "the finding is in the header" || bad "finding missing"
  ls -a "$U" | grep -q -- '\.tmp$' && bad "a temp file was left behind in uploads" || ok "no temp file left in uploads (atomic rename)"

  echo "[C] what a destination-side checker can join on"
  python3 - "$M" > "$T/declared" <<'PY'
import json, sys
m = json.load(open(sys.argv[1])); out = set()
for c in m["clips"]:
    for x in [c] + list(c.get("alternates") or []) + list(c.get("superseded") or []):
        if isinstance(x, dict) and x.get("file"):
            out.add(x["file"])
print(" ".join(sorted(out)))
PY
  [ "$(cat "$T/declared")" = "take-1.mp4 take-1b.mp4 take-1c.mp4" ] && ok "primary, alternate and superseded files are all declared" || bad "declared set wrong: $(cat "$T/declared")"

  echo "[D] --check: a declared file that moved is named"
  expect_rc 0 "--check with every file present" python3 "$L" --job job-a "${W[@]}" --check
  mv "$U/take-1b.mp4" "$R/moved.mp4"
  expect_rc 1 "--check after the primary moved" python3 "$L" --job job-a "${W[@]}" --check
  grep -q "MISSING slot 1: take-1b.mp4" "$T/out" && ok "...and it names the slot and the file" || bad "missing file not named"
  mv "$R/moved.mp4" "$U/take-1b.mp4"

  echo "[E] cannot-tell is never a verdict"
  printf '{"schema":"live-delivery/1","clips":[' > "$U/job-e.json"; local e0; e0="$(sha "$U/job-e.json")"
  expect_rc 1 "a broken manifest is refused as not-a-manifest" python3 "$L" --job job-e "${W[@]}" --set 1 --status rendering
  [ "$(sha "$U/job-e.json")" = "$e0" ] && ok "...and left byte-identical" || bad "a broken manifest was rewritten"
  if command -v ssh >/dev/null 2>&1; then
    expect_rc 2 "an unreachable --ssh host is CANNOT-TELL (2)" python3 "$L" --job job-a --tenant t --ssh ld-selftest.invalid --set 1 --status rendering
  else
    echo "  skip no ssh binary here: the remote cannot-tell check did not run"
  fi
  expect_rc 1 "no target at all is refused" python3 "$L" --job job-a --uploads "$R/no-such-dir" --set 1 --status rendering

  echo "[F] the page is published once, and only over our own page"
  expect_rc 1 "publish before seed is refused" python3 "$L" --job job-f "${W[@]}" --publish-page
  expect_rc 0 "publish after seed" python3 "$L" --job job-a "${W[@]}" --publish-page
  grep -q "live-delivery-page/1" "$P/job-a.html" && ok "the page carries the template mark" || bad "template mark missing"
  grep -q '"/uploads/" + JOB + ".json"' "$P/job-a.html" && ok "the page derives its manifest from its own filename" || bad "page does not derive its manifest"
  grep -q "direct /uploads/ file URL" "$T/out" && ok "publishing prints the gated-link rule" || bad "gated-link rule not printed"
  expect_rc 0 "re-publishing over our own page (template update)" python3 "$L" --job job-a "${W[@]}" --publish-page
  python3 "$L" --job job-d "${W[@]}" --seed 1 --force >/dev/null 2>&1
  echo '<html>somebody else</html>' > "$P/job-d.html"
  expect_rc 1 "publishing over a foreign page is refused" python3 "$L" --job job-d "${W[@]}" --publish-page
  grep -q "somebody else" "$P/job-d.html" && ok "...and the foreign page is untouched" || bad "a foreign page was overwritten"
}

echo "== live_delivery.py self-test =="
run_suite "$HERE/live_delivery.py"
REAL_FAIL=$FAIL; REAL_PASS=$PASS

echo "== mutant: the file-not-delivered refusal is removed =="
MUT="$T/mutant-live_delivery.py"
sed 's/^        if not delivered:$/        if False:/' "$HERE/live_delivery.py" > "$MUT"
if cmp -s "$MUT" "$HERE/live_delivery.py"; then
  echo "  FAIL mutant did not apply (the line it edits has moved); the delivery control is unproven"; MUT_OK=0
else
  FAIL=0
  run_suite "$MUT" > "$T/mutant.log" 2>&1
  if grep -q "FAIL a file that is not in uploads is refused" "$T/mutant.log"; then
    echo "  ok   the delivery check goes RED on the mutant ($FAIL check(s) red)"; MUT_OK=1
  else
    echo "  FAIL the mutant passed the delivery check; that control cannot see the defect"; MUT_OK=0
  fi
fi
PASS=$REAL_PASS

echo "== page.html in a real browser =="
PY="${LD_PYTHON:-python3}"
"$PY" "$HERE/page-check.py" "$HERE/page.html"; PRC=$?
PAGE="skipped"
if [ "$PRC" = 0 ]; then
  PAGE="ok"
  echo "== page mutant: the unreadable-list error box is suppressed =="
  PM="$T/mutant-page.html"
  sed 's/^    errEl.hidden = false;$/    errEl.hidden = true;/' "$HERE/page.html" > "$PM"
  if cmp -s "$PM" "$HERE/page.html"; then
    echo "  FAIL page mutant did not apply"; PAGE="mutant-unapplied"
  else
    "$PY" "$HERE/page-check.py" "$PM" > "$T/page-mutant.log" 2>&1
    if grep -q "FAIL no manifest: the error box is shown" "$T/page-mutant.log" \
       && grep -q "FAIL a failed re-read says so" "$T/page-mutant.log"; then
      echo "  ok   the honest-degradation checks go RED on the page mutant ($(grep -c '  FAIL' "$T/page-mutant.log") red)"
    else
      echo "  FAIL the page mutant passed a named check; honest degradation is unproven"; PAGE="mutant-missed"
    fi
  fi
elif [ "$PRC" != 4 ]; then
  PAGE="FAILED"
fi

echo "== writer: $PASS passed, $REAL_FAIL failed, mutant caught: $MUT_OK · page: $PAGE =="
[ "${LD_KEEP:-0}" = 1 ] && echo "(fixtures kept in $T)"
[ "$REAL_FAIL" -eq 0 ] && [ "$MUT_OK" -eq 1 ] && { [ "$PAGE" = ok ] || [ "$PAGE" = skipped ]; }
