---
anchor: 18
slug: clawhavoc-supply-chain
status: confirmed
introduced: late-2025 / early-2026 (campaign window)
changelog_line: null
upstream_pages:
  - https://docs.openclaw.ai/tools/skills.md
  - https://docs.openclaw.ai/plugins/architecture.md
old_behavior: "ClawHub installs ran with no built-in scanner; `capability-evolver` (#1 on ClawHub, 35k installs) and ~1,467 other community skills were caught exfiltrating data."
new_behavior: "Treat ALL ClawHub installs as untrusted code. Mandatory pattern: install Skill Vetter first; read source of every skill; reject any skill with a `scripts/` folder unless audited; one skill at a time + 3-day cost-and-traffic check after install."
skill_files_affected:
  - annotations/tools__skills.md (extend with supply-chain risk + Skill Vetter recommendation)
  - annotations/plugins__architecture.md (extend with allowlist pattern)
  - annotations/skills__skill-vetter.md (new — mandatory tool)
  - overrides/skill-allowlist.md (new — JamBot tenant allowlist + blocklist)
sources:
  - https://reddit.com/comments/1rlptnf (209/41 — `capability-evolver` exfiltration case, github clawhub#95)
  - https://reddit.com/comments/1rp8t9r (401/71 — "blind skill installs" as #3 most common debug mistake)
  - https://reddit.com/comments/1r4t9q8 (384/80 — ClawHub malicious-skill risk)
  - https://reddit.com/comments/1riudg5 (495/95 — first-72-hours rules: no skills week-1)
  - https://reddit.com/comments/1ssuze9 (322/39 — 1,467 malicious skills caught)
  - https://reddit.com/comments/1rmgt2m (671/134 — Clawshell as runtime security layer)
---

# Anchor #18 — ClawHavoc supply-chain campaign + flagship skill incident

## What changed

**Late-2025 / early-2026 ClawHavoc campaign:** 1,467 malicious skills were caught on ClawHub. Vectors observed:
- Typosquatting popular skill names
- `.env` file exfiltration
- Generic infostealers
- Cloud-storage exfiltration (specifically: data sent to Chinese object stores)

**Flagship case (r/openclaw 1rlptnf, u/krazzmann +24):** `capability-evolver`, the #1-ranked skill on ClawHub with 35,000 installs, was caught exfiltrating data to a Chinese cloud storage provider. Author removed it post-incident. Tracking issue: `github.com/openclaw/clawhub#95`.

## Why it matters for JamBot

JamBot ships skills mounted into tenant containers from `/mnt/system/base/skills/`. If we pull anything from ClawHub into that path without review, every tenant inherits the compromise simultaneously. The blast radius is multi-tenant — single bad skill = mass exfil event.

**JamBot rule (also in CLAUDE.md):** the `/mnt/system/base/skills/` directory is allowlist-only. Any new skill from ClawHub goes through code review and a 3-day cost-and-traffic monitor before tenant rollout. See `overrides/skill-allowlist.md`.

## Mandatory tooling

- **Skill Vetter** (`clawhub.ai/spclaudehome/skill-vetter`) — agent-driven scanner that reviews skill source before install. Install this BEFORE any other ClawHub item.
- **Clawshell** (per r/openclaw 1rmgt2m) — runtime security layer; PII + secrets guard. Candidate for tenant containers.

## Skill-install policy (excerpt — full in playbook)

1. Skill Vetter installed and recent (≤30d).
2. Read skill source manually. Reject if:
   - `scripts/` folder exists without explicit justification
   - Network calls to non-public-API hosts
   - File reads outside the skill's declared scope
   - Use of `eval`, `Function`, dynamic `require` without bounded inputs
3. One skill at a time. Wait 3 days. Check `~/.openclaw/logs/` for egress traffic + token cost.
4. Production-pin the skill version (don't auto-update unless the source has been re-vetted).

## Suggested blocklist (as of 2026-05-23)

- `capability-evolver` (post-incident; even though removed, copycats may exist)
- `self-improving-agent` (132 stars, unaudited per community)
- Any skill whose only contributor account is < 30 days old

## References

- Reddit thread 1rlptnf — capability-evolver exfiltration case + clawhub#95
- Reddit thread 1rp8t9r — "blind skill installs" as a top-5 debug pattern
- Reddit thread 1ssuze9 — ClawHavoc campaign scale (1,467 skills)
- Reddit thread 1r4t9q8 — practical "treat every install as untrusted"
- Reddit thread 1riudg5 — onboarding rule: zero skill installs in week 1
- Reddit thread 1rmgt2m — Clawshell as runtime security layer candidate
