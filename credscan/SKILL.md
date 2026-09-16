# credscan — credential exposure scanning (value-shape mode)

Scans text surfaces for exposed credentials by VALUE SHAPE, not just `KEY=` assignment
lines. Humans paste secrets into comments, prose, chat, and docs — matching only
assignment syntax misses exactly those (2026-09 foamology finding: a live key sat in a
comment block invisible to every assignment-shaped redactor).

## What it does

1. **Name matches** — known credential variable names (`credscan-pinned-names.env`)
   appearing as bare mentions. Severity LOW by default (a name is not a value).
2. **Value-prefix matches** — key-shaped value regexes (e.g. `AKIA[0-9A-Z]{16}`,
   provider-specific prefixes) anywhere in the file, any line type. Severity CRITICAL
   on match, subject to adjudication (step 3).
3. **Adjudication pass** — `sec-adjudicate-findings.py/v2` measures match length and
   Shannon entropy; short/low-entropy matches are downgraded CRITICAL→MEDIUM with
   `adjudication: downgraded-low-entropy` and flagged for human review, not auto-rotation.

## Surfaces scanned

Mesh-visible text: `/mnt/agent-mesh/mesh/` (BLACKBOARD, reflections), agent inbox/sent
trees, workspaces. Host-side transcript roots (`~/.claude/projects`, `~/.z-code-home`)
are scanned by the host-side runs (SEC-034 sink set).

## Known false-positive class (do NOT rotate on these)

Value-shaped strings inside **published third-party package artifacts** (node_modules,
dist, compiled .wasm/.js bundles). Verified case 2026-09-16: an AKIA-shaped match in
`next/dist/compiled/amphtml-validator/validator_wasm.js` — the file is byte-identical to
the npm-registry copy installed elsewhere on the host, so the strings ship with the
package. Before escalating any node_modules/vendor match: hash the file and compare to
the same package installed from the registry. Identical → vendor fixture, close LOW.

## Running

`bin/sec-scanner-v0.1.sh` (security-officer workspace) — nightly, writes findings JSONL
to `agents/security-officer/findings/`, alerts CRITICAL/HIGH via mesh-send with
fingerprint dedup (unchanged finding sets emit a one-line carry-forward, not a full body).

## Hard rule

Findings record the EXPOSURE LOCATION and a fingerprint (sha256[:6]), never the value.
