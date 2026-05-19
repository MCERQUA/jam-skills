# External-channel intake adapters — v0.1.2 / Rule 7

Three single-call adapters that turn an external-channel payload (email,
SMS, voice) into a v0.1.2 `task.json` filed under
`<workspace>/tasks/intake/<task-id>/`. They are the channel-side half of
**Rule 7** ("all channels feed one pipeline") and the upstream of
**Rule 8** (dedupe-at-intake before promotion to `shop-floor/`).

- Spec base: `/mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md` §3, §8
- v0.1.1 amendment: `/mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md` (Rules 7 + 8)
- Canonical schema (v0.1.2): `/agent-desk/snapshots/2026-05-18-canonical-schema-v0.1.2/task_schema.py`
- Dedupe library: `/agent-desk/snapshots/2026-05-18-intake-dedupe/dedupe.py`
- Tenant scaffolder: `/agent-desk/snapshots/2026-05-18-tenant-scaffolder/scaffold_tenant.py`

These adapters do **NO** real network I/O. They accept a payload dict
that the tenant agent's channel reader has already extracted, and they
return a verdict + path. The channel reader (Gmail watcher, Twilio
webhook, OVU voice-loop) is responsible for the actual external connection.

---

## Files

| File | Purpose |
|---|---|
| `email_intake.py`         | `intake(payload, tenant, workspace) → dict` for `raised_by="email"` |
| `sms_intake.py`           | `intake(payload, tenant, workspace) → dict` for `raised_by="sms"`   |
| `voice_intake.py`         | `intake(payload, tenant, workspace) → dict` for `raised_by="voice"` |
| `intake_common.py`        | Shared task-builder, slugifier, dedupe-glue, schema validation |
| `test_intake_external.py` | 12 named assertions covering all three adapters (exit 0 = pass) |
| `COMPLETION-NOTICE.md`    | Written last; signals "intake-external adapters ready" |

---

## Function signature

Every adapter exposes a single function with the same signature:

```python
def intake(payload: dict, tenant: str, workspace: Path) -> dict:
    ...
```

Return value:

```python
{
    "verdict":      "accept" | "reject",
    "task_id":      "<YYYY-MM-DD>-<HHMM>-<slug>",
    "path_written": "<workspace>/tasks/intake/<task-id>/task.json"  # or None on reject
}
```

`accept` ⇒ `task.json` exists on disk under `tasks/intake/`.
`reject` ⇒ the payload is a Rule-8 duplicate (same `source_ref`, or
semantic match within the tenant's open tasks). The adapter does NOT
write a duplicate file; `task_id` points at the existing task it would
link to.

---

## Payload shapes

### Email (`email_intake.intake`)

```python
{
  "gmail_thread_id":  str,        # Gmail thread id — becomes source_ref
  "gmail_message_id": str,        # message that triggered intake
  "from_addr":        str,        # "Acme Roofing <ops@acme.example>"
  "to_addrs":         list[str],  # tenant inbox(es)
  "subject":          str,        # → summary (clamped to 120 chars)
  "snippet":          str,        # Gmail preview
  "body_text":        str,        # full text body
}
```

### SMS (`sms_intake.intake`)

Twilio-shaped:

```python
{
  "sid":         str,   # Twilio Message SID — source_ref
  "from_number": str,   # operator phone in E.164 ("+14374559131")
  "to_number":   str,   # tenant inbound number
  "body":        str,   # → summary (clamped to 120)
}
```

Sets `operator_phone = from_number`. Outbound replies to this task gate
through Rule 1 + `recipient_role=operator` per Rule 7.

### Voice (`voice_intake.intake`)

OVU/OpenVoiceUI-shaped:

```python
{
  "session_id":          str,   # OVU voice session
  "clerk_session_id":    str,   # Clerk session bound to transcript
  "transcript_line":     str,   # raw utterance text
  "line_index":          int,   # 0-based line within the session
  "turn_intent_summary": str,   # tenant agent's distilled intent → summary
}
```

`source_ref` is composed as `<session_id>:line:<line_index>` so multiple
utterances within one session don't collide on dedupe.

---

## What gets written

Every adapter goes through the same `intake_common.build_and_file` path:

1. **Compose** a v0.1.2 record. All required fields populated:
   - `raised_by` = channel name (per Rule 7 enum)
   - `source_ref` = channel-specific id
   - `summary` = source-derived text, clamped to 120 chars (schema §summary)
   - `id` = `<YYYY-MM-DD>-<HHMM>-<slug>`, slug derived from clamped summary
   - `dedup_hash` = `dedupe.compute_dedup_hash(tenant, source_ref, summary)`
   - `recipient_role` = `"mike"` (Rule 7 default; outbound writer may override)
   - `linked_to` = `[]` unless dedupe surfaces a link
   - `state_history` = `[{state: intake, at, by: <tenant>-<channel>@mesh}]`
2. **Validate** via `task_schema.validate_task_record`. If the adapter ever
   produces a non-conforming record it raises `ValueError`; this is a hard
   programming-error bar, not a runtime input-error path.
3. **Dedupe** via `dedupe.scan(workspace, record)`. On `reject` no file is
   written; the existing match's id is returned for linking by the caller.
4. **File** at `<workspace>/tasks/intake/<task-id>/task.json` on `accept`.

---

## Integration example

```python
from pathlib import Path
import email_intake

# 1. Channel reader (NOT part of this snapshot) extracts a Gmail thread:
payload = {
    "gmail_thread_id":  "gmail-thread-189f3b7ac2",
    "gmail_message_id": "gmail-msg-aa11bb22",
    "from_addr":        "Acme Roofing <ops@acme.example>",
    "to_addrs":         ["cca-inbox@mike.example"],
    "subject":          "Acme Roofing asked for an updated domain + hosting quote",
    "snippet":          "Hi Mike, can you send us a fresh quote …",
    "body_text":        "Hi Mike,\n\nWe'd like a fresh quote on domain + hosting.",
}

# 2. Tenant agent dispatches to the adapter under its own identity.
result = email_intake.intake(
    payload,
    tenant="cca",
    workspace=Path("/mnt/clients/josh/openclaw/workspace"),
)

if result["verdict"] == "accept":
    # Promote intake/ → shop-floor/ is the tenant agent's job (Rule 8).
    ...
else:
    # Rule 8 reject: link the existing task and notify the operator if needed.
    existing_task_id = result["task_id"]
```

---

## Tests

```bash
python3 test_intake_external.py
# 12 named assertions print [n] ...: OK; exit 0 on pass
```

The test harness creates a fresh tempdir workspace for each adapter,
runs the scaffolder, sends each payload once (accept), then a second
time (reject), and checks the round-trip + Rule-8 deduplication.

---

## Conventions

- **No network I/O.** All three adapters accept payload dicts. The
  channel reader owns Gmail / Twilio / OVU credentials and IDs;
  this layer is pure.
- **One identity at runtime.** Rule 8: the tenant agent owns the
  execution side. The `state_history.by` field on the intake entry
  reads `<tenant>-<channel>-intake@mesh` so the audit trail records
  which channel filed the task, while the agent that *promotes* it
  later writes its own URI to the next state-history entry.
- **`recipient_role` defaults to `mike`.** Outbound writers re-tag
  via Rule 7 before sending. The intake side cannot decide
  cross-tenant routing — that's a promotion-time call.
- **Dedupe is authoritative.** If `dedupe.scan` returns `reject`, the
  adapter does not write to disk. Callers may *not* re-attempt by
  mutating the payload — that would defeat Rule 8's intent.
