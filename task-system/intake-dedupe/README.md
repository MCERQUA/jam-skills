# Dedupe library — Rule 8 dedupe contract

Production implementation of `compute_dedup_hash` + `scan_for_duplicates` per v0.1.1 amendment Rule 8. Imported by both `intake-internal` (worker-b's adapters) and `intake-external` (worker-c's adapters).

## Two interfaces, one implementation

**Primary** — worker-b's explicit-kwarg contract:
```python
from dedupe import scan_for_duplicates, compute_dedup_hash

result = scan_for_duplicates(
    workspace=Path("/mnt/clients/josh/openclaw/workspace"),
    tenant="josh",
    source_ref="gmail-thread-abc",
    summary="Acme roofing quote followup",
    dedup_hash=compute_dedup_hash("josh", "gmail-thread-abc", "Acme roofing quote followup"),
)
# → {"verdict": "accept|reject|escalate", "existing_task_id": str|None, "match_reason": str|None}
```

**Compat wrapper** — worker-c's record-dict contract:
```python
from dedupe import scan

result = scan(workspace, task_json_record)
# → {"verdict": "accept|reject", "linked_to": [task_id, ...], "existing_id": str|None}
# (escalate normalises to reject — both stop the duplicate write)
```

Both interfaces exist so the two downstream snapshots work unchanged against this library.

## Scan rules (in order)

1. **Same-tenant `source_ref` collision** (any state, including `done/`) → `verdict=reject`. The existing task wins; the new intake doesn't write. Returns the existing `task_id` so the caller can populate `linked_to` if it wants an audit trail.

2. **Same-tenant exact-summary match on an open-state task** (`shop-floor | planned | scheduled | today | in-flight | parked`) → `verdict=escalate`. Two intakes for the same intent surfaced via different channels — the tenant agent surfaces this to host before proceeding.

3. **Cross-tenant exact-summary match** (any state) → `verdict=escalate`. Same intent showing up in a different tenant — possible misroute or cross-client coordination. Surfaces for human review.

4. **No match** → `verdict=accept`. Caller proceeds normally.

`done/` is intentionally excluded from same-tenant semantic-match because completed tasks shouldn't block new intake of the same intent (a finished task last week doesn't preclude the same topic recurring today). Cross-tenant `done/` IS checked, because cross-tenant matches are rare and worth flagging regardless of completion.

## Hash format

`sha1:<tenant>:<source_ref|NONE>:<shingle>`

- The `sha1:` prefix is a **version label**, not an actual SHA-1 digest. Future hash schemes (true hash + fuzzy match) can co-exist by adding a new prefix (`sha2:`, `fuzzy:`, etc.).
- Empty / missing `source_ref` collapses to the literal `NONE` to keep the hash stable.
- `<shingle>` = first 3 alpha-tokens of the summary, slugified.

## Cross-tenant scan layout

The scan walks `workspace.parent.iterdir()` to find sibling tenants. This matches the host deploy layout where tenants live under `/mnt/clients/<tenant>/openclaw/workspace/`. If `workspace.parent` doesn't exist, cross-tenant scan is silently a no-op (single-tenant deploys still work).

## Malformed input handling

- Garbage `task.json` files (invalid JSON, truncated, etc.) are silently skipped — they don't crash the scan. Logged at debug level downstream.
- Missing `tasks/` dir under `workspace` → returns `accept` (nothing to compare against).
- `None` / `""` `source_ref` collapses to the same `NONE` marker so empty-source intake (e.g. manual CLI without source_ref) deduplicates consistently across runs.

## CLI

```bash
python3 dedupe.py \
    --workspace /mnt/clients/josh/openclaw/workspace \
    --tenant josh \
    --source-ref gmail-thread-abc \
    --summary "Acme roofing quote followup"
```

Prints JSON `{dedup_hash, verdict, existing_task_id, match_reason}` and exits 0.

## Performance

Single-pass scan across `tasks/<state>/<task-id>/task.json` files; O(N) in task count per tenant. For typical small tenants (<100 open tasks) the scan completes in single-digit milliseconds. No caching layer — Rule 8 spec requires a fresh scan per intake to avoid stale-state false-accepts.

## Tests

`test_dedupe.py` — 15 assertions covering:
- `compute_dedup_hash` determinism + tenant/source_ref differentiation + empty-source stability
- `scan_for_duplicates` accept / reject / escalate paths across same-tenant and cross-tenant
- `done/` exclusion from same-tenant semantic-match
- Malformed JSON / missing tasks/ dir handling
- `scan()` compat wrapper accept / reject / escalate-normalised-to-reject paths

Run: `python3 test_dedupe.py` (exits 0 on PASS).

## Dependencies on other snapshots

- Validates against `task.json` records — does NOT require the schema validator at scan time. Records are read as raw dicts (defensive against partially-written / older schema versions).
- Consumed by `intake-internal/intake_common.py` (worker-b) and `intake-external/intake_common.py` (worker-c).
- Tenant scaffolder defines the `tasks/<state>/` layout the scanner walks.
