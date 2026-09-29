#!/usr/bin/env bash
# self-test.sh: controls for retire.py. Run from anywhere; it builds its own fixtures in a fresh
# temp dir and never touches a real uploads directory. Exit 0 only if every check passes AND the
# mutant (a gate keyed on the FILENAME instead of the bytes) is caught by the rename check.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d "${TMPDIR:-/tmp}/rdd-selftest.XXXXXX")"
# Remove only the directory mktemp just made for us, and only if it is the shape we asked for.
# RDD_KEEP=1 keeps the fixtures for inspection.
cleanup() { case "$T" in */rdd-selftest.??????) [ "${RDD_KEEP:-0}" = 1 ] || rm -rf -- "$T" ;; esac; }
trap cleanup EXIT
PASS=0; FAIL=0
sha() { python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }
ok()  { PASS=$((PASS+1)); echo "  ok   $1"; }
bad() { FAIL=$((FAIL+1)); echo "  FAIL $1"; }
expect_rc() { # expect_rc <want> <label> <cmd...>
  local want="$1" label="$2"; shift 2
  "$@" >"$T/out" 2>&1; local rc=$?
  if [ "$rc" = "$want" ]; then ok "$label (rc $rc)"; else bad "$label (want rc $want, got $rc): $(head -c 300 "$T/out")"; fi
}

run_suite() { # run_suite <path-to-retire.py>
  local R="$1" U="$T/uploads.$RANDOM"
  mkdir -p "$U"
  head -c 4096 /dev/urandom > "$U/a.png"
  head -c 4096 /dev/urandom > "$U/b.png"
  printf '{"at":"2026-01-01T00:00:00+00:00","filename":"a.png","size":4096}\n{"at":"2026-01-01T00:00:00+00:00","filename":"b.png","size":4096}\n' > "$U/.uploads-index.jsonl"
  local sha_before; sha_before="$(sha "$U/a.png")"

  echo "[A] refusals write nothing"
  expect_rc 1 "retire with an empty --why is refused" python3 "$R" retire "$U" a.png --by client --why "  "
  expect_rc 1 "retire with an empty --by is refused" python3 "$R" retire "$U" a.png --by "" --why "no"
  expect_rc 1 "retire of an absent file is refused" python3 "$R" retire "$U" nope.png --by client --why "no"
  expect_rc 1 "retire of a path, not a bare name, is refused" python3 "$R" retire "$U" ../a.png --by client --why "no"
  [ "$(wc -l < "$U/.uploads-index.jsonl")" -eq 2 ] && [ ! -e "$U/.retired-refs.jsonl" ] \
    && ok "no index row and no ledger after refusals" || bad "a refusal wrote something"

  echo "[B] retire = index row + deny row, bytes untouched"
  expect_rc 0 "retire a.png" python3 "$R" retire "$U" a.png --by "client via agent msg 039" --why "scratch all of them" --set v1
  expect_rc 0 "retire a.png again (idempotent)" python3 "$R" retire "$U" a.png --by "client via agent msg 039" --why "scratch all of them"
  [ "$(grep -c '"event": "retired"' "$U/.uploads-index.jsonl")" -eq 2 ] && ok "index carries the retired rows (append-only, history kept)" || bad "retired rows missing"
  [ "$(grep -c "$sha_before" "$U/.retired-refs.jsonl")" -eq 1 ] && ok "deny ledger holds the sha exactly once" || bad "deny ledger count wrong"
  grep -q '"retired_note": "scratch all of them"' "$U/.uploads-index.jsonl" && ok "the client's words are kept verbatim" || bad "reason not verbatim"
  [ -f "$U/a.png" ] && [ "$(sha "$U/a.png")" = "$sha_before" ] && ok "bytes still there, unchanged" || bad "bytes moved or changed"

  echo "[C] effective state (last row wins)"
  [ "$(python3 "$R" state "$U" a.png)" = "retired" ] && ok "a.png reads retired" || bad "a.png state wrong"
  [ "$(python3 "$R" state "$U" b.png)" = "live" ] && ok "b.png reads live" || bad "b.png state wrong"
  [ "$(python3 "$R" state "$U" --live | tr '\n' ' ')" = "b.png " ] && ok "--live lists only b.png (the pick surface view)" || bad "--live leaked a retired file"
  printf '{"filename":"c.png","event":"archived-by-someone"}\n' >> "$U/.uploads-index.jsonl"
  python3 "$R" state "$U" --live | grep -q '^c.png$' && bad "an unknown event was treated as live" || ok "an unknown event is NOT live"

  echo "[D] the attach-step gate is keyed on bytes"
  cp "$U/a.png" "$T/renamed-copy.png"
  expect_rc 1 "a RENAMED copy of a retired file is refused" python3 "$R" check "$T/renamed-copy.png" --ledger "$U/.retired-refs.jsonl"
  expect_rc 0 "a clean file passes" python3 "$R" check "$U/b.png" --ledger "$U/.retired-refs.jsonl"
  expect_rc 1 "one retired file in a batch refuses the batch" python3 "$R" check "$U/b.png" "$T/renamed-copy.png" --ledger "$U/.retired-refs.jsonl"

  echo "[E] other copies go in via deny, and ledgers stack"
  head -c 4096 /dev/urandom > "$T/uncropped-original.png"
  expect_rc 0 "deny an uncropped original into a second ledger" python3 "$R" deny "$T/uncropped-original.png" --ledger "$T/rig.jsonl" --by "client via agent msg 039" --why "scratch all of them" --where "rig warehouse"
  expect_rc 1 "check across both ledgers refuses it" python3 "$R" check "$T/uncropped-original.png" --ledger "$U/.retired-refs.jsonl" --ledger "$T/rig.jsonl"

  echo "[F] cannot-tell is never a pass"
  expect_rc 3 "no --ledger at all" python3 "$R" check "$U/b.png"
  expect_rc 0 "a missing ledger passes and says so" python3 "$R" check "$U/b.png" --ledger "$T/none.jsonl"
  grep -q "no ledger at" "$T/out" && ok "...and the note names the missing path" || bad "missing ledger passed silently"
  expect_rc 3 "a missing ledger with --require-ledger" python3 "$R" check "$U/b.png" --ledger "$T/none.jsonl" --require-ledger
  printf '{"sha256":"not-a-hash"}\n' > "$T/broken.jsonl"
  expect_rc 3 "a malformed ledger" python3 "$R" check "$U/b.png" --ledger "$T/broken.jsonl"
  expect_rc 3 "an unreadable input" python3 "$R" check "$T/does-not-exist.png" --ledger "$U/.retired-refs.jsonl"
  U2="$T/uploads-broken.$RANDOM"; mkdir -p "$U2"; cp "$U/b.png" "$U2/"; cp "$T/broken.jsonl" "$U2/.retired-refs.jsonl"; : > "$U2/.uploads-index.jsonl"
  expect_rc 3 "retire with a malformed ledger writes nothing" python3 "$R" retire "$U2" b.png --by x --why y
  [ ! -s "$U2/.uploads-index.jsonl" ] && ok "...and no index row was written" || bad "index row written past a broken ledger"

  echo "[G] un-retire is a later registration row"
  printf '{"at":"2026-01-02T00:00:00+00:00","filename":"a.png","size":4096,"note":"client asked for it back"}\n' >> "$U/.uploads-index.jsonl"
  [ "$(python3 "$R" state "$U" a.png)" = "live" ] && ok "a later registration row makes a.png live again" || bad "un-retire failed"
}

echo "== retire.py self-test =="
run_suite "$HERE/retire.py"
REAL_FAIL=$FAIL

echo "== mutant: the gate hashes the FILENAME instead of the bytes =="
M="$T/mutant-retire.py"
sed 's/sha = sha256_file(p)$/sha = hashlib.sha256(os.path.basename(p).encode()).hexdigest()/' "$HERE/retire.py" > "$M"
if cmp -s "$M" "$HERE/retire.py"; then
  echo "  FAIL mutant did not apply (the line it edits has moved); the rename control is unproven"; MUT_OK=0
else
  PASS_B=$PASS; FAIL=0
  run_suite "$M" > "$T/mutant.log" 2>&1
  if grep -q "FAIL a RENAMED copy of a retired file is refused" "$T/mutant.log"; then
    echo "  ok   the rename check goes RED on the mutant ($FAIL check(s) red)"; MUT_OK=1
  else
    echo "  FAIL the mutant passed the rename check; that control cannot see the defect"; MUT_OK=0
  fi
  PASS=$PASS_B
fi

echo "== $PASS passed, $REAL_FAIL failed, mutant caught: $MUT_OK =="
[ "${RDD_KEEP:-0}" = 1 ] && echo "(fixtures kept in $T)"
[ "$REAL_FAIL" -eq 0 ] && [ "$MUT_OK" -eq 1 ]
