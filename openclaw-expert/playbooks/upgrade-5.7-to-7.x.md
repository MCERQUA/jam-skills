# Playbook — Upgrading OpenClaw past the `2026.5.7` pin

**Status: NOT STARTED. This is a planning document, not a completed procedure.**
JamBot runs `2026.5.7` (verified in `openclaw-test-dev` 2026-07-25). Upstream npm `latest` is `2026.7.1-2`; a `2026.6.33` maintenance release also exists. The gap is ~2 months of releases including two security batches and a storage refactor.

**Do not run this as a checklist without an owner and a maintenance window.** It exists so the upgrade is *scoped* rather than discovered mid-outage.

---

## Why this is not a routine bump

Four of the seven new audit anchors describe changes that break or alter JamBot's specific deployment shape. Two of them are fleet-wide-outage class.

| Anchor | Version | Risk |
|---|---|---|
| **#22** gateway fails closed on non-loopback bind without explicit shared-secret/trusted-proxy auth | 5.17 | 🔴 **every tenant gateway refuses to start** |
| **#23** pairing + trusted-proxy hardening | 5.12 | 🔴 tenants start but reject connections |
| **#26B** Gateway WS protocol v4 required | 5.19 | 🟠 OVU connects, agent goes silent |
| **#24** database-first SQLite state migration | 6.5–6.9 | 🟠 backups/agent-repo snapshots silently under-capture |
| **#26A** agent cron scoped; mixed-version fails closed | 7.1 | 🟠 staggered rolls break tenant nightly reflections |
| **#27** Z.AI thinking ladder + 429 semantics | 6.8–7.1 | 🟡 circuit-breaker tuning stale |
| **#25** doctor reworked | 7.1 | 🟢 safer; rules unchanged |

Also relevant: `2026.5.12` removed the bundled BlueBubbles channel (breaking) — JamBot does not use it.

---

## Phase 0 — Decide the auth mode — ✅ **DONE 2026-07-25. Decision: (B), already implemented.**

**Outcome: (B) per-tenant shared secret. It was already in place fleet-wide before this decision was made — Phase 0 was a discovery exercise, not a build.** Nothing needs to be constructed here, and no OVU-side code change is required.

### Evidence

Fleet audit, all **26/26** openclaw tenants:

| Field | Value | Notes |
|---|---|---|
| `gateway.bind` | `"lan"` | the #22 trigger condition — yes, we bind non-loopback |
| `gateway.auth.mode` | `"token"` | **explicit shared-secret mode, already set** |
| `gateway.auth.token` | `"${OPENCLAW_GATEWAY_TOKEN}"` | expanded from env at load (proven — see below) |
| token value | unique 64-char per tenant | verified no two tenants share one |
| `gateway.trustedProxies` | `["172.16.0.0/12","10.0.0.0/8"]` | present too — *both* accepted modes configured |

`allowInsecureAuth` and `dangerouslyDisableDeviceAuth` live under **`gateway.controlUi.*`** and are Control-UI scoped. They were never substituting for gateway auth; anchor #22's original text got this wrong.

Verified against a **real `openclaw@2026.7.1` binary** in a throwaway `node:22-slim` container, with a copy of test-dev's config mounted read-only (originals untouched, md5 re-checked after):

- **our config as-is** → `openclaw gateway run` started, **exit 0, no fail-closed**
- **`doctor --lint --all`** → 51 checks; the `lan` bind is a **warning**, not an error
- **control (auth + trustedProxies removed)** → `Refusing to bind gateway to lan without auth.`

The control is the important half: it proves 7.1 really does fail closed, and that our token config is what satisfies it. Upstream's error text names the exact env var we already use (`OPENCLAW_GATEWAY_TOKEN`).

Env expansion was confirmed incidentally — 7.1 reported *"missing env var ZAI_API_KEY"* while raising nothing about the gateway token, which was supplied. So `${...}` in `openclaw.json` is resolved, and the token is a real secret rather than a literal string.

### Carried forward into later phases

- **Phase 2 gate (revised):** the canary no longer needs to prove the gateway starts — that is settled. It must still prove **#23** (pairing/trusted-proxy hardening), **#26B** (WS protocol v4 against the OVU client), **#26A** (cron), **#24** (SQLite), **#27** (breaker). Those are untouched by this test.
- **New Phase 5 item:** 7.1's `core/doctor/security` flags `gateway.auth.token` as a plaintext secret-bearing field and wants a SecretRef (`openclaw secrets configure`, verify `openclaw secrets audit --check`). Not a blocker; aligns with the per-role-secret direction in SUDO-QUEUE.
- **Do not "simplify" by deleting `trustedProxies`.** Carrying both modes is why #22 was a non-event for us, and #23 hardened the trusted-proxy path specifically.

### Original decision text (superseded, kept for provenance)

- **(A) Explicit trusted-proxy.** Closest to today. Keep `trustedProxies` covering the Docker bridge ranges and make the mode explicit. Note #23: explicit `trusted-proxy` mode fails closed if the identity check fails (5.12), partially relaxed for same-host callers in 5.19 (#82953).
- **(B) Per-tenant shared secret.** More durable, aligns with the per-role-secret direction already in the SUDO-QUEUE. ~~Requires an OVU-side change to present the secret — this is code, not config.~~ **Wrong — OVU already carries the token in its env.**

---

## Phase 1 — Read-only reconnaissance (no changes)

```bash
# Where we are
sg docker -c "docker exec openclaw-test-dev openclaw --version"
grep -rn "OPENCLAW_VERSION" /mnt/system/base/OpenVoiceUI/docker-compose.yml \
  /mnt/system/base/OpenVoiceUI/deploy/openclaw/Dockerfile \
  /mnt/system/base/OpenVoiceUI/setup-sudo.sh

# Where upstream is
curl -s https://registry.npmjs.org/openclaw/latest | python3 -c "import sys,json;print(json.load(sys.stdin)['version'])"

# Refresh the doc catalog + re-read the anchors
bash /mnt/system/base/skills/openclaw-expert/scripts/refresh-catalog.sh
```

Also inventory the OVU-side WS client against protocol v4 (anchor #26B) — OVU is **not** rebuilt by `bump-openclaw-version.sh` and versions independently.

---

## Phase 2 — Single-tenant canary (`test-dev` only)

1. Build a candidate image with the new version **without** touching the fleet tag.
2. Bring up `test-dev` only.
3. Gate on all of these before going further:
   - gateway starts (not fail-closed) → #22
   - OVU pairs and a **real voice turn completes end-to-end** → #23, #26B
   - `openclaw doctor --lint --all --json` is clean → #25
   - tenant cron jobs still list and fire → #26A
   - a Z.AI turn completes and the breaker does not trip on first 429 → #27
   - SQLite state present and `openclaw backup sqlite create` + `verify` succeed → #24

**Containers up is not a pass.** Every gate above requires a real turn or a real command.

---

## Phase 3 — Fix the backup/snapshot layer BEFORE the fleet roll

Anchor #24. `jambot-init-agent-repos.sh` snapshots `*.md`, `memory/`, `business/`, `openclaw.json` — none of which is the SQLite state. Either extend it to commit a verified `openclaw backup sqlite create` artifact, or explicitly document db state as out of scope and covered elsewhere. Do not roll the fleet with a snapshot job that reports success while capturing less than it used to.

---

## Phase 4 — Fleet roll

- **Roll outside 02:00–04:00 UTC.** That window holds the tenant nightly reflections; a straddling roll produces a mixed-version cron state that fails closed (#26A) and a night of missing reflections that will read as a monitoring failure.
- **Re-attach `jambot-shared` after every recreate** — post-start attachments do not survive `compose up -d`.
- Bump the version pin **only** via `bash /mnt/system/base/OpenVoiceUI/bump-openclaw-version.sh <version>`; the three installer paths must stay in sync. Commit the three changed files together.
- Roll in small batches with a real-turn check per batch, not all tenants at once.

---

## Phase 5 — Post-upgrade retuning

- Re-tune the Z.AI circuit breaker against the new 429 semantics (#27) rather than porting the current numbers forward.
- Re-verify `openclaw doctor` flags (`--fix`/`--repair`/`--force`) — do not assume they survived (#25).
- Consider adopting `doctor --lint --json --only <check>` in `jambot-health-monitor.sh` as a non-mutating health signal. Verify check ids against the running binary first.
- Re-audit the changelog for anything this pass missed and file new anchors. The 5.7→7.1 delta is ~7,500 changelog lines; this audit targeted config, auth, storage, cron, protocol, and provider behavior. **Channels, Control UI, macOS/iOS, and the Codex harness were not audited** — say so rather than implying full coverage.

---

## Rollback

Keep the previous image tag. Rollback = re-pin the old version, rebuild, roll back the fleet, re-attach shared networks. ⚠️ A tenant whose state was migrated **into** SQLite by a newer version may not cleanly roll back to a file-state version — this is the reason Phase 3 (verified backups) is not optional.
