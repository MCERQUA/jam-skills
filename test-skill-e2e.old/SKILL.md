---
name: test-skill-e2e
description: End-to-end test skill — safe to delete
metadata:
  tags: test
---

## Test Skill

This is a test skill to verify the shared skills server is working.
If you can read this, the symlink + volume mount chain is functioning correctly.

### Verification checklist
- [ ] Created in /mnt/system/base/skills/
- [ ] Symlinked to client workspace
- [ ] Readable inside container via /mnt/shared-skills/
- [ ] Resolved through symlink from workspace/skills/
