# Tenant Onboarding — Task System Deployment (v0.1.3)

End-to-end walkthrough for deploying the task system to a new tenant. Every command in this README is copy-pasteable. Each step ends with a verification check.

**Author:** worker-b@mesh (josh-desktop submesh, milestone-5)
**Reviewer:** worker-c will dry-run this against a fake tenant — see `FAKE-TENANT-EXAMPLE.md`.

---

## TL;DR

Five steps, in order:

1. **Scaffold** the tenant's `tasks/` directory layout.
2. **Wire Seam-A** intake + blocker-digest cron (writes `blocker.json` + daily digest).
3. **Run integration smoke** harness against the new tenant.
4. **Hook up patterns-aggregator** (cross-tenant rollup, host-side).
5. **Verify** end-to-end (expected output, success signals, failure recovery).

A one-page tickbox version is in `CHECKLIST.md`. A fully-worked sample run is in `FAKE-TENANT-EXAMPLE.md`.

---

## Pre-requisites

### 1. Bind mounts (per-tenant)

The tenant's openclaw workspace MUST be reachable at:

```
/mnt/clients/<tenant>/openclaw/workspace
```

If this path doesn't exist, see [§ Out-of-band: host help needed](#out-of-band-host-help-needed) — host has to mount it (Dockerfile/compose edit).

### 2. System skill mount

The deployed task-system code MUST exist at:

```
/mnt/system/base/skills/task-system/
├── schema/                  # canonical v0.1.3 — task_schema.py, task-json-schema.json
├── scaffold/                # tenant-scaffolder — scaffold_tenant.py
├── seam-a/                  # blocker_writer.py, blocker_digest_cron.py
├── bootstrap-smoke/         # smoke_test.py + scenarios/
└── patterns-aggregator/     # patterns_aggregator.py (host-side cron)
```

The 4-tenant landscape (as of 2026-05-19, per host msgs 020/024/028/033):

| Tenant   | Deploy state                                  | Workspace path                                |
|----------|-----------------------------------------------|-----------------------------------------------|
| josh     | **LIVE** (host confirmed 2026-05-19)          | `/mnt/clients/josh/openclaw/workspace`        |
| danielle | **LIVE** (host confirmed 2026-05-19)          | `/mnt/clients/danielle/openclaw/workspace`    |
| src      | snapshot ready, pending VPS deploy            | `/mnt/clients/src/openclaw/workspace`         |
| bun      | snapshot ready, pending VPS deploy            | `/mnt/clients/bun/openclaw/workspace`         |

For a brand-new tenant (`acme` is used as the example throughout this README), all five steps below run from scratch.

### 3. Required env vars

```bash
export TENANT=acme
export TENANT_WORKSPACE=/mnt/clients/${TENANT}/openclaw/workspace
export TASK_SYSTEM_SCHEMA_DIR=/mnt/system/base/skills/task-system/schema
```

### 4. Required mesh-CLI tools

These must resolve in `$PATH` (verify with `command -v <tool>`):

- `mesh-send` (`--to`, `--kind`, `--subject`) — used by seam-A digest cron
- `mesh-recv` — for verification, not strictly required by deploy
- `flock` (util-linux) — required by patterns-aggregator cron wrapper

```bash
# Verify all tools resolve before starting
for tool in mesh-send mesh-recv flock python3 jq; do
  command -v "$tool" >/dev/null && echo "OK: $tool" || echo "MISSING: $tool"
done
```

Expected: 5 `OK:` lines. Any `MISSING:` halts onboarding — install before continuing.

---

## Step 1 — Scaffold the tenant

Creates the 8-state `tasks/` directory layout plus `manifest.json` and `SCHEMA.md`.

**Reference:** `/agent-desk/snapshots/2026-05-18-tenant-scaffolder/README.md`

### 1.1 Dry-run first

```bash
python3 /mnt/system/base/skills/task-system/scaffold/scaffold_tenant.py \
  --workspace "$TENANT_WORKSPACE" \
  --tenant "$TENANT" \
  --dry-run --json
```

**Expected output:** JSON with `would_create: [intake, shop-floor, planned, scheduled, today, done, in-flight, parked]` and `manifest_would_write: true`. Exit code 0.

### 1.2 Run for real

```bash
python3 /mnt/system/base/skills/task-system/scaffold/scaffold_tenant.py \
  --workspace "$TENANT_WORKSPACE" \
  --tenant "$TENANT"
```

**Expected output:** `scaffolded 8 subdirs + manifest.json under <path>/tasks/` and exit 0.

### 1.3 Verify

```bash
ls "$TENANT_WORKSPACE/tasks/"
cat "$TENANT_WORKSPACE/tasks/manifest.json"
```

**Expected:** 8 state subdirs (`intake/`, `shop-floor/`, `planned/`, `scheduled/`, `today/`, `done/`, `in-flight/`, `parked/`) + `manifest.json` + `SCHEMA.md`. The manifest has `tenant: "<your-tenant>"`, `scaffolded_by: "worker-b@mesh"` (or whichever agent ran it), and `schema_version: "0.1-pending-rule-8"` (or current).

### 1.4 Idempotency check

Re-run the same command. Exit code must remain 0; no files are touched.

```bash
python3 /mnt/system/base/skills/task-system/scaffold/scaffold_tenant.py \
  --workspace "$TENANT_WORKSPACE" \
  --tenant "$TENANT"
```

**Expected:** `manifest.json present for tenant=<your-tenant>; no changes`. Exit 0.

### 1.5 Failure modes (Step 1)

| Symptom | Cause | Recovery |
|---|---|---|
| `manifest mismatch: <existing> vs <new>` exit 2 | Another tenant already scaffolded this workspace | Pick a different `$TENANT_WORKSPACE` OR (if intentional re-stamp) delete `manifest.json` and re-run |
| `PermissionError` on mkdir | Workspace bind-mount is read-only | See [§ Out-of-band](#out-of-band-host-help-needed) — host fixes mount mode |
| `FileNotFoundError: $TENANT_WORKSPACE` | Tenant container/mount missing | See [§ Out-of-band](#out-of-band-host-help-needed) |

---

## Step 2 — Wire Seam-A (intake + blocker-digest cron)

Seam-A writes a sibling `blocker.json` whenever a task is parked, and runs a daily sweeper that emails Mike one consolidated digest of due blockers.

**Reference:** `/agent-desk/snapshots/2026-05-18-seam-a-poc/README.md` + `/mesh/BLACKBOARD/task-system/seam-a/`

### 2.1 Copy seam-A scripts into the tenant workspace

```bash
mkdir -p "$TENANT_WORKSPACE/scripts"
cp /mnt/system/base/skills/task-system/seam-a/blocker_writer.py "$TENANT_WORKSPACE/scripts/"
cp /mnt/system/base/skills/task-system/seam-a/blocker_digest_cron.py "$TENANT_WORKSPACE/scripts/"
```

### 2.2 Self-test seam-A scripts in place

```bash
cd "$TENANT_WORKSPACE/scripts"
python3 -c "
import blocker_writer, blocker_digest_cron
print('blocker_writer._RECIPIENT =', blocker_digest_cron._RECIPIENT)
"
```

**Expected:** `blocker_writer._RECIPIENT = host@mesh` (Rule 1 — recipient is hardcoded at module import; visible in any git diff).

### 2.3 Dry-run the digest cron (zero-due baseline)

```bash
python3 "$TENANT_WORKSPACE/scripts/blocker_digest_cron.py" \
  --parked-root "$TENANT_WORKSPACE/tasks/parked" \
  --run-record-dir "$TENANT_WORKSPACE/reflections/blocker-digest-runs" \
  --dry-run
```

**Expected output (no parked tasks yet, freshly scaffolded):**
```
[blocker-digest] parked-root: /mnt/clients/<tenant>/openclaw/workspace/tasks/parked
[blocker-digest] due blockers: 0
[blocker-digest] would dispatch: false (zero-due; run record still snapshots)
[blocker-digest] run record: /mnt/clients/<tenant>/openclaw/workspace/reflections/blocker-digest-runs/blocker-digest-<ISO>.md
```

Exit 0. A run record file IS created even on zero-due so the pipeline's health is auditable (per seam-A spec §3).

### 2.4 Install the cron entry

Append the following line to the tenant container's `crontab -e -u <tenant-user>` (or the tenant's systemd timer equivalent — see [§ Out-of-band](#out-of-band-host-help-needed) for which channel each tenant uses):

```cron
# Seam-A daily blocker digest — fires at 13:00 UTC (08:00 ET, before morning brief)
0 13 * * *  /usr/bin/python3 /mnt/clients/<TENANT>/openclaw/workspace/scripts/blocker_digest_cron.py \
            --parked-root /mnt/clients/<TENANT>/openclaw/workspace/tasks/parked \
            --run-record-dir /mnt/clients/<TENANT>/openclaw/workspace/reflections/blocker-digest-runs
```

**Substitute `<TENANT>` for your tenant name** before pasting.

### 2.5 Verify cron registration

```bash
crontab -l -u "<tenant-user>" | grep blocker_digest_cron
```

**Expected:** the line you just added. Exit 0.

### 2.6 Failure modes (Step 2)

| Symptom | Cause | Recovery |
|---|---|---|
| `ImportError: blocker_writer` | scripts dir not on PYTHONPATH for cron | Wrap cron command in `cd <scripts-dir> && python3 ...` or set `PYTHONPATH=<scripts-dir>` in the cron line |
| `mesh-send: recipient inbox not found` | `host@mesh` bind mount missing inside tenant container | See [§ Out-of-band](#out-of-band-host-help-needed) — host adds `/peer-inbox/host` bind |
| No digest file appears at 13:00 UTC | Cron daemon not running in tenant container | `service cron status` inside container; `service cron start` if needed |
| Digest sent but `_RECIPIENT` wrong | Someone edited `blocker_digest_cron.py` post-deploy | `git diff` the script vs the snapshot, restore from `/mnt/system/base/skills/task-system/seam-a/blocker_digest_cron.py` |

---

## Step 3 — Run the integration smoke harness

End-to-end test of: scaffold → seed prior state → `load_context` → `SessionContext` helpers → intake adapter accept → intake adapter reject (source_ref collision) → re-bootstrap.

**Reference:** `/agent-desk/snapshots/2026-05-19-bootstrap-smoke/README.md`

### 3.1 Smoke test against an ephemeral fake tenant (first pass — sanity check)

This runs the bundled `acme` fixture in `/tmp` so the deployed code is exercised without touching the real tenant workspace.

```bash
cd /mnt/system/base/skills/task-system/bootstrap-smoke
python3 smoke_test.py
```

**Expected output (last 10 lines):**
```
[smoke] (1) scaffold: PASS
[smoke] (2) seed prior task state: PASS
[smoke] (3) seed history (voice/gmail/sms/reflection/ledger): PASS
[smoke] (4) load_context — keys + counts + threads + transcript: PASS
[smoke] (5) SessionContext helpers: PASS
[smoke] (6) intake adapter — accept new summary: PASS
[smoke] (7) intake adapter — reject on source_ref collision: PASS
[smoke] (8) re-bootstrap — new intake task visible, count==4: PASS
PASS: 8 scenarios
```

Exit code MUST be 0. Any `FAIL: scenario <name>: <reason>` on stderr halts onboarding.

### 3.2 Inspect a kept workspace (optional, for debugging only)

```bash
python3 smoke_test.py --no-cleanup
ls /tmp/bootstrap-smoke-*/acme/tasks/
```

**Expected:** the same 8 subdirs, plus seeded task.json files matching the scenarios.

### 3.3 Per-tenant in-place smoke (does NOT pollute the real workspace)

The smoke harness is hermetic — it spins up its own `/tmp` workspace per run regardless of `$TENANT_WORKSPACE`. The previous run already proves the deployed code works. No additional run needed unless you also want to test the per-tenant scaffolder integration:

```bash
python3 smoke_test.py 2>&1 | tee "$TENANT_WORKSPACE/reflections/bootstrap-smoke-$(date -u +%Y-%m-%dT%H%M%SZ).log"
grep "^PASS: 8 scenarios" "$TENANT_WORKSPACE/reflections/bootstrap-smoke-"*.log
```

**Expected:** `grep` returns the PASS line. Exit 0.

### 3.4 Failure modes (Step 3)

| Symptom | Cause | Recovery |
|---|---|---|
| `FAIL: scenario (1) scaffold` | `scaffold_tenant.py` not on PYTHONPATH or `--workspace` arg unreachable | Re-check Step 1 paths; ensure `/mnt/system/base/skills/task-system/scaffold/` is in `sys.path` per smoke_test.py imports |
| `FAIL: scenario (4) load_context` | v0.1.3 schema not pinned | Check `$TASK_SYSTEM_SCHEMA_DIR` env var; export it before running smoke |
| `FAIL: scenario (7) reject on source_ref` | Dedupe layer is missing | Verify `/mnt/system/base/skills/task-system/` includes `intake-dedupe/` per snapshot manifest |
| `RuntimeError: TASK_SYSTEM_SCHEMA_DIR not set` | Step 0 pre-req skipped | `export TASK_SYSTEM_SCHEMA_DIR=/mnt/system/base/skills/task-system/schema` and retry |

---

## Step 4 — Hook up patterns-aggregator

Cross-tenant rollup. Counts promoted patterns + plan-time failure_modes per enum value, surfaces blockers recurring in ≥2 tenants. **This runs host-side, NOT inside the tenant container** — it needs read access to all 4 tenants' `tasks/patterns.json` simultaneously.

**Reference:** `/mesh/BLACKBOARD/task-system/2026-05-19/patterns-aggregator-v0.3.md` (productizes bun's seam-C `patterns.json` + src's v0.2 Rule 9 failure_modes counting; src-desktop host msgs 019, 021, 027 — 18/18 pass + 4 polish items deferred to v0.4).

### 4.1 Confirm host-side deploy is in place

```bash
ls /mnt/system/base/skills/task-system/patterns-aggregator/
```

**Expected files:** `patterns_aggregator.py`, `test_patterns_aggregator.py`, `README.md`, `COMPLETION-NOTICE.md`, `dogfood-output/`.

If this path is missing: host hasn't done the docker-cp deploy yet. See [§ Out-of-band](#out-of-band-host-help-needed).

### 4.2 Run the aggregator's own self-test

```bash
cd /mnt/system/base/skills/task-system/patterns-aggregator
python3 test_patterns_aggregator.py
```

**Expected:** `18/18 PASS` and exit 0.

### 4.3 Pre-create the BLACKBOARD output dir (dodges cron-vs-inotify race)

```bash
mkdir -p /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/
```

### 4.4 One-shot test run including the new tenant

```bash
flock -n /tmp/patterns-aggregator.lock python3 \
  /mnt/system/base/skills/task-system/patterns-aggregator/patterns_aggregator.py \
  -t src=/mnt/clients/src/openclaw/workspace \
  -t josh=/mnt/clients/josh/openclaw/workspace \
  -t bun=/mnt/clients/bun/openclaw/workspace \
  -t danielle=/mnt/clients/danielle/openclaw/workspace \
  -t "${TENANT}=${TENANT_WORKSPACE}" \
  -o /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/
```

**Expected output (last lines):**
```
[patterns-aggregator] tenants: src, josh, bun, danielle, <your-tenant>
[patterns-aggregator] cross-tenant rollup: <N> promoted, <M> plan-time failure_modes
[patterns-aggregator] wrote /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/2026-05-19-aggregate.md
```

Exit 0. Inspect the output:

```bash
ls -t /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/ | head -1
head -30 /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/$(ls -t /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/ | head -1)
```

**Expected:** markdown frontmatter + 5 sections (cross-tenant rollup, plan-time failure_modes sorted, recurring blocker patterns ≥2 tenants, per-tenant detail, brief guidance). Your new tenant should appear in the per-tenant detail section.

### 4.5 Install the recurring host cron entry

Edit host's crontab (`crontab -e -u host_admin`):

```cron
# patterns-aggregator daily — fires at 06:05 UTC (after overnight check-and-promote, before morning brief)
5 6 * * * host_admin flock -n /tmp/patterns-aggregator.lock python3 \
  /mnt/system/base/skills/task-system/patterns-aggregator/patterns_aggregator.py \
  -t src=/mnt/clients/src/openclaw/workspace \
  -t josh=/mnt/clients/josh/openclaw/workspace \
  -t bun=/mnt/clients/bun/openclaw/workspace \
  -t danielle=/mnt/clients/danielle/openclaw/workspace \
  -t <TENANT>=/mnt/clients/<TENANT>/openclaw/workspace \
  -o /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/
```

**Substitute `<TENANT>` for the new tenant name** before pasting.

### 4.6 Verify cron registration

```bash
crontab -l -u host_admin | grep patterns_aggregator
```

**Expected:** the line above. Exit 0.

### 4.7 Failure modes (Step 4)

| Symptom | Cause | Recovery |
|---|---|---|
| `patterns.json absent or unparseable for tenant=<X>` | Tenant hasn't promoted any patterns yet (fresh scaffold has no `patterns.json`) | **Expected on day 0** — the aggregator renders a graceful "no patterns yet" line per tenant. Wait for bun's seam-C promotion cycle to populate. Per src-desktop msg 021 polish item #2, this error message conflates absent vs malformed; if you want to disambiguate, check whether the file exists with `ls <workspace>/tasks/patterns.json` — absent is fine, malformed is a bug to file. |
| `flock: file in use` | Two cron runs overlapped | Expected on heavy days; `flock -n` correctly drops the second run rather than racing. No action needed. |
| Output file missing after cron fires | Output dir not pre-created OR inotify watcher race | Re-run Step 4.3, then manual-fire Step 4.4. Per src-desktop README §3 deploy plan, pre-creating dodges the race. |
| Aggregate is rendered but new tenant missing from per-tenant detail | `-t <TENANT>=<PATH>` arg omitted from cron line | Edit crontab, add the `-t` arg, save. |

---

## Step 5 — Verify (end-to-end)

A 60-second sequence that exercises the deployed code without touching production state.

### 5.1 Seed one fixture task into the new tenant

```bash
cat > "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary/task.json" <<'EOF'
{
  "id": "2026-05-19-9999-onboarding-canary",
  "state": "intake",
  "raised_at": "2026-05-19T03:30:00Z",
  "raised_by": "manual",
  "source_ref": "onboarding-canary-fixture",
  "summary": "Onboarding canary — delete after verification",
  "tenant": "REPLACE_WITH_TENANT_NAME",
  "operator_phone": null,
  "email_authorized_by_mike": null,
  "recipient": null,
  "state_history": [
    {"state": "intake", "at": "2026-05-19T03:30:00Z", "by": "onboarding-script"}
  ],
  "clerk_session_id": null,
  "lock_required": true,
  "defer_count": 0,
  "failure_modes": [],
  "dedup_hash": "sha1:onboarding-canary:fixture",
  "recipient_role": null,
  "linked_to": []
}
EOF

mkdir -p "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary"
# Then sed the tenant name into the file (the heredoc above writes a placeholder):
sed -i "s/REPLACE_WITH_TENANT_NAME/${TENANT}/" \
  "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary/task.json"
```

**Note:** The `mkdir -p` MUST run BEFORE the heredoc — fix order if you copy-paste:

```bash
mkdir -p "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary"
cat > "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary/task.json" <<EOF
{...as above, with "tenant": "${TENANT}" interpolated directly...}
EOF
```

### 5.2 Validate the canary against the deployed schema

```bash
python3 /mnt/system/base/skills/task-system/schema/task_schema.py \
  "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary/task.json"
```

**Expected:** `1 task(s) checked — all valid.` exit 0.

### 5.3 Re-run patterns-aggregator including the new tenant

```bash
flock -n /tmp/patterns-aggregator.lock python3 \
  /mnt/system/base/skills/task-system/patterns-aggregator/patterns_aggregator.py \
  -t "${TENANT}=${TENANT_WORKSPACE}" \
  -o /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/
```

**Expected:** new tenant appears in the per-tenant detail section, with 0 promoted and 0 failure_modes (the canary has `failure_modes: []`).

### 5.4 Delete the canary

```bash
rm -rf "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary/"
```

### 5.5 Final success indicators

✅ All four of these MUST be true before declaring onboarding done:

1. `ls $TENANT_WORKSPACE/tasks/` shows 8 state subdirs + `manifest.json` + `SCHEMA.md`.
2. `crontab -l -u <tenant-user> | grep blocker_digest_cron` returns the seam-A cron line.
3. `crontab -l -u host_admin | grep patterns_aggregator` returns the host-side cron line with `-t <TENANT>=` in it.
4. `python3 smoke_test.py` from `bootstrap-smoke/` returns `PASS: 8 scenarios` exit 0.

If any of the four fail, the onboarding is **not complete**. Roll back to the failing step and recover per the failure-mode table for that step.

---

## Out-of-band: host help needed

Several actions require host (VPS-side, root, or Dockerfile/compose) access that this README cannot perform from a tenant container:

| Action | Why host has to do it |
|---|---|
| Mount `/mnt/clients/<TENANT>/openclaw/workspace` | Docker compose volume edit + container recreate |
| Mount `/mnt/system/base/skills/task-system/` inside tenant | Same — bind from VPS to container |
| Add `/peer-inbox/host` bind to tenant container | Per src-desktop msg 008 finding — deploy-layout drift across tenant containers; josh + danielle currently differ from src |
| `docker cp` patterns-aggregator snapshot to `/mnt/system/...` | Read-only system mount on tenant side |
| Install host-side cron line | Host crontab, not tenant crontab |
| Initial smoke test inside the real tenant container (`docker exec`) | "Webtop pass is necessary but not sufficient for full production rollout" — per src-desktop msg 008 caveat |

When you hit one of these, **stop and ping host@mesh** with a message of KIND `task` or `question`, subject `tenant-onboarding-<TENANT>-host-step-N-blocked`. Do not attempt to bypass via writeable workarounds — the canonical path is the host crontab + mount config.

---

## References

- **Spec:** `/mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md` + v0.1.2 (Rule 8 + Rule 7 confirmed) + v0.1.3 (failure_modes enum locked) + v0.2 (Rules 9–12 additive)
- **Schema:** `/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3/` (deployed at `/mnt/system/base/skills/task-system/schema/`)
- **Scaffolder:** `/agent-desk/snapshots/2026-05-18-tenant-scaffolder/`
- **Seam-A:** `/agent-desk/snapshots/2026-05-18-seam-a-poc/` + `/mesh/BLACKBOARD/task-system/seam-a/`
- **Smoke harness:** `/agent-desk/snapshots/2026-05-19-bootstrap-smoke/`
- **Patterns-aggregator v0.3:** `/mesh/BLACKBOARD/task-system/2026-05-19/patterns-aggregator-v0.3.md` (full snapshot lives on src-desktop; host docker-cp deploys to `/mnt/system/base/skills/task-system/patterns-aggregator/`)
- **Tenant deploy status:** host msgs 020 (josh), 024 (danielle), 028 (src), 033 (bun all-done)
- **Deploy-layout drift caveat:** host msg 008 — `/mnt/system/base/skills/task-system/` mount status differs per tenant; verify before running.

---

## Out-of-scope (deliberately deferred)

- **Postmortem failure_modes counter** — depends on v0.4 schema for `state_history.notes` (per patterns-aggregator README §v0.4)
- **Per-day diff section** in aggregator output (v0.4)
- **Brief reader integration** — patterns-aggregator is the source; brief reader is the consumer (src-desktop msg 027 closed that loop, but integration walkthrough is its own onboarding)
- **Cost/time accounting (Rule 10)** — deferred
- **Cross-tenant task dependencies (Rule 12)** — not yet defined

If your new tenant needs any of these, the answer for now is "wait for v0.4."
