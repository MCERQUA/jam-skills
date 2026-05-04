---
anchor: 15
slug: rotateBytes-deprecated
status: confirmed
introduced: v2026.4.27
changelog_line: 872
upstream_pages:
  - https://docs.openclaw.ai/concepts/session.md
  - https://docs.openclaw.ai/reference/session-management-compaction.md
  - https://docs.openclaw.ai/gateway/configuration.md
old_behavior: "session.maintenance.rotateBytes triggered automatic sessions.json rotation backups"
new_behavior: "rotation removed; rotateBytes deprecated; doctor --fix removes the key"
skill_files_affected:
  - "references/sessions-and-context.md:64"
  - "references/gateway-configuration.md:254"
---

# Anchor #15 — `session.maintenance.rotateBytes` deprecated

## What changed

v4.27 line 872: "remove automatic oversized `sessions.json` rotation backups, deprecate `session.maintenance.rotateBytes`, and teach `openclaw doctor --fix` to remove the ignored key."

## Replacement

There is **no replacement for rotation itself** — it was removed entirely. The new related concept is `session.writeLock.acquireTimeoutMs` (default 60s, v5.2 line 71) which controls how long to wait for transcript lock acquisition.

## Doctor behavior

```bash
openclaw doctor --fix
# automatically removes any session.maintenance.rotateBytes key from openclaw.json
```

## JamBot impact

If `templates/openclaw.json` or any client config has `rotateBytes`, it should be removed proactively. After 5.2 doctor migration runs (anchor #7), the key will be silently stripped.

## Verification

```bash
docker exec openclaw-<user> sh -c 'cat ~/.openclaw/openclaw.json' | jq '.session.maintenance.rotateBytes'
# expect null after upgrade
```

## Fix instruction

`annotations/concepts__session.md`:
- Mark `rotateBytes` as DEPRECATED (with v4.27 date)
- Add `session.writeLock.acquireTimeoutMs` as the related-but-different new knob
- Note: rotation no longer happens automatically — bring your own log management
