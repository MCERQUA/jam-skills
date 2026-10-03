# sec-detect-selftest

Prove the fleet's credential-detection scanner still FIRES on real-shaped secret
values — before a real leak depends on it. Catches the silent-failure class where a
scanner script exits 0 every night while its patterns have quietly stopped matching
(edited length threshold, renamed array, broken regex).

Owner: security-officer@mesh. Fleet-share of the workspace selftest (pledge 71da8612
lineage, shipped as pledge 7536da5a, 2026-10-02).

## What it does

- IMPORTS the live `VALUE_PATTERNS` array from the production scanner
  (`sec-scanner-v0.1.sh`) at run time — no pattern copy exists to drift.
- Generates one SYNTHETIC positive per pattern family (match-shaped fake value, built
  to match its own pattern by construction) and asserts the scanner's regex fires.
- Two planted NEGATIVES prove the classes that must stay quiet:
  elided values (`sk-ant-oat01-XXXX...0`, SEC-036) and prose slugs mentioning a
  pattern name (SEC-022).
- Fixtures are mktemp'd under /tmp (outside scan surfaces) and deleted on exit.

## Run

    bash sec-detect-selftest.sh                     # default: production scanner on the mesh mount
    bash sec-detect-selftest.sh /path/to/scanner.sh # any scanner with a VALUE_PATTERNS array
    SEC_SCANNER=/path bash sec-detect-selftest.sh   # env form

Requires bash. Exit 0 = every testable family PASSES. Exit 1 = at least one planted
positive did not fire or a negative matched — the scanner is BLIND; do not trust its
"clean" scans until fixed. Exit 3 = wrong interpreter.

## Heartbeat (pb-20260717-001)

Wire into any nightly/security cron and treat a missing run as failure — a selftest
that stops running degrades to exactly the silence it exists to catch. security-officer
runs it nightly; other agents may run it against their own scanner copies.

Adding a pattern to the scanner? Run this immediately — if your new family has no
`gen_pos` case it will be listed as SKIP, which is visible, not silent.
