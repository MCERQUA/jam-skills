# intake-internal — three internal-channel intake adapters

Per Rule 7 (all channels feed one pipeline) + Rule 8 (single tenant agent +
dedupe at intake) of the v0.1.1 spec amendment, every inbound channel
writes a v0.1.2 `task.json` into `tasks/intake/` with `raised_by`
populated. This snapshot supplies three of those channel adapters:

| Adapter            | `raised_by` | input shape                                       |
|--------------------|-------------|---------------------------------------------------|
| `mesh_intake.py`   | `mesh`      | parsed mesh-inbox dict (frontmatter+body)         |
| `manual_intake.py` | `manual`    | CLI flags                                         |
| `brief_intake.py`  | `brief`     | parsed morning-brief item dict                    |

The external-channel adapters (`email_intake.py` for `raised_by="email"`,
`sms_intake.py` for `raised_by="sms"`, voice flows for `raised_by="voice"`)
ship separately — they own the channel-specific I/O and call into the
same `intake_common.finalize_intake` core.

## Files

| File                       | Purpose                                              |
|----------------------------|------------------------------------------------------|
| `intake_common.py`         | Shared helpers + `finalize_intake` (dedupe → write). |
| `mesh_intake.py`           | mesh-channel adapter.                                |
| `manual_intake.py`         | manual-channel adapter (lib + CLI).                  |
| `brief_intake.py`          | brief-channel adapter.                               |
| `_mock_dedupe.py`          | Fallback dedupe implementation for dev/tests.        |
| `test_intake_internal.py`  | Test suite. Exit 0 = all green.                      |
| `COMPLETION-NOTICE.md`     | Written last; signals "intake-internal ready".       |

## Schema lockstep

Everything written here round-trips against
`/agent-desk/snapshots/2026-05-18-canonical-schema-v0.1.2/task_schema.py`.
That's the integration test — `intake_common.write_task_file` rejects
non-conforming records before touching the filesystem.

All Rule 8 fields (`dedup_hash`, `recipient_role`, `linked_to`) are
populated by the adapter:

- `dedup_hash` — `sha1:<tenant>:<source_ref|NONE>:<summary-shingle>`.
  Versioned label, not an actual hex digest; downstream dedupe does the
  fuzzy matching, this is just the structural fingerprint per Rule 8.
- `recipient_role` — `null` at intake. Outbound writers set this later.
- `linked_to` — `[]` for verdict=accept; `[<matched-task-id>]` for
  verdict=merge or escalate.

## Verdict semantics

`finalize_intake` calls
`dedupe.scan_for_duplicates(workspace, tenant, source_ref, summary, dedup_hash)`
and acts on the verdict:

| Verdict     | Action                                                                                              |
|-------------|-----------------------------------------------------------------------------------------------------|
| `accept`    | Write `tasks/intake/<task-id>/task.json`. Return new `task_id`.                                     |
| `reject`    | Do **not** write. Return the **existing** task_id (caller idempotency).                             |
| `merge`     | Write task.json with `linked_to=[existing]` + sibling `host-question.md`. No mesh-send.             |
| `escalate`  | Same as `merge`. Tenant agent surfaces the marker as `kind: question` to host@mesh on next bootstrap.|

Any other verdict raises `ValueError` — the adapter is strict about the
contract.

## CLI — manual_intake

```bash
python3 manual_intake.py \
    --tenant cca \
    --workspace /mnt/clients/josh/openclaw/workspace \
    --summary  "Email Acme about decking install timing" \
    --raised-by manual \
    --source-ref "josh-pad:2026-05-18-line-12" \
    --operator-phone "+14374559131" \
    --json
```

Output (verdict=accept):

```json
{
  "verdict":    "accept",
  "task_id":    "2026-05-18-2137-cca-email-acme-about-decking",
  "task_path":  "/mnt/clients/josh/openclaw/workspace/tasks/intake/2026-05-18-2137-cca-email-acme-about-decking/task.json",
  "linked_to":  [],
  "match_reason": null,
  "dedup_hash": "sha1:cca:josh-pad:2026-05-18-line-12:email-acme-about"
}
```

Verdict=reject exits 0 (idempotent re-submission is a normal-flow outcome,
not an error).

## Integration — tenant agent runtime

A tenant agent dispatches inbound events to whichever adapter matches the
channel. All three are pure functions over the workspace tree — no
mesh-send, no background polls, no external I/O beyond filesystem writes
inside `<workspace>/tasks/`.

```python
from mesh_intake   import intake_from_mesh_message
from manual_intake import intake_manual
from brief_intake  import intake_from_brief_item

WORKSPACE = "/mnt/clients/josh/openclaw/workspace"

# (1) a mesh-inbox message with kind=task lands for tenant `cca`.
result = intake_from_mesh_message(parsed_mesh_msg, WORKSPACE)
# parsed_mesh_msg keys: tenant, subject, from, at, message_id (optional).

# (2) Mike types a task into the CLI / Slack / a notebook surface.
result = intake_manual(
    tenant="cca",
    workspace=WORKSPACE,
    summary="Email Acme about decking install timing",
    source_ref="josh-pad:2026-05-18-line-12",
)

# (3) The morning-brief pipeline yields a digest item.
result = intake_from_brief_item(
    {"subject":         "Acme Roofing follow-up on Q3 invoice",
     "snippet":         "Acme writes asking when Q3 settles…",
     "gmail-thread-id": "gmail-thread-189f3b7ac2"},
    tenant="cca",
    workspace=WORKSPACE,
)

# All three return:
#   {"verdict": ..., "task_id": ..., "task_path": ..., "linked_to": ...,
#    "match_reason": ..., "dedup_hash": ...}
```

## Dedupe dependency

The adapters call `dedupe.scan_for_duplicates(**kwargs)` from
`/agent-desk/snapshots/2026-05-18-intake-dedupe/dedupe.py`. Until that
snapshot's `COMPLETION-NOTICE.md` lands, `intake_common.resolve_dedupe()`
falls back to the bundled `_mock_dedupe` in this directory, which
implements just enough of the Rule 8 contract to drive the test suite:

- `(tenant, source_ref)` collision → reject
- same-tenant identical-summary on an open-state task → escalate
- cross-tenant identical-summary in sibling workspaces → escalate
- otherwise → accept

When the real dedupe library lands, no adapter code changes — the
resolver swaps it in automatically and tests re-import the real module
via the `USING_REAL_DEDUPE` flag.

Tests inject a dedupe module explicitly via `dedupe_module=...` for
determinism; production runtime relies on the resolver.

## Running

```bash
# end-to-end test (exit 0 = all green)
python3 test_intake_internal.py

# manual entry via CLI
python3 manual_intake.py --tenant cca --workspace /path/to/workspace \
    --summary "..." --raised-by manual --source-ref "..."
```

## Constraints (per worker-b@mesh brief, 2026-05-18)

- Output ONLY to `/agent-desk/snapshots/2026-05-18-intake-internal/`.
- `task.json` MUST round-trip validate against `task_schema.py` v0.1.2.
- All Rule 8 fields populated (no PENDING markers — schema is post-flip).
- DO NOT mesh-send. DO NOT do external I/O outside the candidate
  `tasks/` tree.
- task-id format: `<YYYY-MM-DD>-<HHMM>-<slug>` matching the schema regex
  `^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9][a-z0-9-]*$`.

## References

- v0.1.2 canonical schema:
  `/agent-desk/snapshots/2026-05-18-canonical-schema-v0.1.2/`
- v0.1.1 spec amendment (Rule 7 + Rule 8):
  `/mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md`
- tenant scaffolder (workspace layout):
  `/agent-desk/snapshots/2026-05-18-tenant-scaffolder/`
- dedupe library (dependency):
  `/agent-desk/snapshots/2026-05-18-intake-dedupe/`
