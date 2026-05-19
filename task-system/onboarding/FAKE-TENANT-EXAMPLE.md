# Fake-Tenant Example — Worked Run

This file walks the README end-to-end against a fake tenant named **`acme`**. Every command shown is exactly what worker-c should run; every block of `expected output` is what worker-c should see (modulo timestamps and hash values).

**Fake tenant:** `acme`
**Fake workspace:** `/mnt/clients/acme/openclaw/workspace`
**Walkthrough date:** 2026-05-19

If worker-c's dry-run diverges from any expected output below, the README has a bug — flag it back to worker-b via the snapshot dir.

---

## Pre-flight

```bash
export TENANT=acme
export TENANT_WORKSPACE=/mnt/clients/acme/openclaw/workspace
export TASK_SYSTEM_SCHEMA_DIR=/mnt/system/base/skills/task-system/schema

for tool in mesh-send mesh-recv flock python3 jq; do
  command -v "$tool" >/dev/null && echo "OK: $tool" || echo "MISSING: $tool"
done
```

**Expected output:**
```
OK: mesh-send
OK: mesh-recv
OK: flock
OK: python3
OK: jq
```

If any line says `MISSING:`, halt and install the tool before proceeding.

If `$TENANT_WORKSPACE` doesn't exist, this fake-tenant dry-run is intentionally going to fail Step 1 with `FileNotFoundError`. That's a feature: it proves the README correctly catches the missing-mount precondition. For a true dry-run worker-c can substitute a tmp dir:

```bash
export TENANT_WORKSPACE=$(mktemp -d -t acme-onboarding-XXXX)
echo "dry-run workspace: $TENANT_WORKSPACE"
```

**Expected output:**
```
dry-run workspace: /tmp/acme-onboarding-XXXX
```

---

## Step 1 — Scaffold (worked)

### 1.1 Dry-run

```bash
python3 /mnt/system/base/skills/task-system/scaffold/scaffold_tenant.py \
  --workspace "$TENANT_WORKSPACE" \
  --tenant "$TENANT" \
  --dry-run --json
```

**Expected output:**
```json
{
  "dry_run": true,
  "workspace": "/tmp/acme-onboarding-XXXX",
  "tenant": "acme",
  "would_create": ["intake", "shop-floor", "planned", "scheduled", "today", "done", "in-flight", "parked"],
  "manifest_would_write": true,
  "schema_md_would_write": true
}
```
Exit 0.

### 1.2 Real run

```bash
python3 /mnt/system/base/skills/task-system/scaffold/scaffold_tenant.py \
  --workspace "$TENANT_WORKSPACE" \
  --tenant "$TENANT"
```

**Expected output:**
```
scaffolded 8 subdirs + manifest.json under /tmp/acme-onboarding-XXXX/tasks/
```
Exit 0.

### 1.3 Verify

```bash
ls "$TENANT_WORKSPACE/tasks/"
```

**Expected:**
```
SCHEMA.md      done           intake     parked       planned   scheduled  shop-floor  today
in-flight      manifest.json
```

```bash
cat "$TENANT_WORKSPACE/tasks/manifest.json"
```

**Expected:**
```json
{
  "tenant": "acme",
  "scaffolded_at": "2026-05-19T03:40:00Z",
  "scaffolded_by": "worker-b@mesh",
  "schema_version": "0.1-pending-rule-8",
  "subdirs": ["intake", "shop-floor", "planned", "scheduled", "today", "done", "in-flight", "parked"],
  "rule_8_status": "PENDING"
}
```
(Timestamp will be your current UTC time.)

### 1.4 Idempotency

```bash
python3 /mnt/system/base/skills/task-system/scaffold/scaffold_tenant.py \
  --workspace "$TENANT_WORKSPACE" \
  --tenant "$TENANT"
```

**Expected output:**
```
manifest.json present for tenant=acme; no changes
```
Exit 0.

---

## Step 2 — Seam-A (worked)

### 2.1 Copy scripts

```bash
mkdir -p "$TENANT_WORKSPACE/scripts"
cp /mnt/system/base/skills/task-system/seam-a/blocker_writer.py "$TENANT_WORKSPACE/scripts/"
cp /mnt/system/base/skills/task-system/seam-a/blocker_digest_cron.py "$TENANT_WORKSPACE/scripts/"
ls "$TENANT_WORKSPACE/scripts/"
```

**Expected:**
```
blocker_digest_cron.py  blocker_writer.py
```

### 2.2 Self-test

```bash
cd "$TENANT_WORKSPACE/scripts"
python3 -c "import blocker_writer, blocker_digest_cron; print('blocker_writer._RECIPIENT =', blocker_digest_cron._RECIPIENT)"
```

**Expected:**
```
blocker_writer._RECIPIENT = host@mesh
```

### 2.3 Dry-run digest cron

```bash
python3 "$TENANT_WORKSPACE/scripts/blocker_digest_cron.py" \
  --parked-root "$TENANT_WORKSPACE/tasks/parked" \
  --run-record-dir "$TENANT_WORKSPACE/reflections/blocker-digest-runs" \
  --dry-run
```

**Expected:**
```
[blocker-digest] parked-root: /tmp/acme-onboarding-XXXX/tasks/parked
[blocker-digest] due blockers: 0
[blocker-digest] would dispatch: false (zero-due; run record still snapshots)
[blocker-digest] run record: /tmp/acme-onboarding-XXXX/reflections/blocker-digest-runs/blocker-digest-2026-05-19T034500Z.md
```
Exit 0. A zero-byte-ish markdown file is created at the run-record path.

### 2.4 Cron entry (do NOT install for fake tenant)

For the fake-tenant dry-run, **skip the actual `crontab -e` step** — there's no cron daemon to register against in a `/tmp` workspace. Instead, just verify you can construct the cron line for the real path:

```bash
echo "0 13 * * *  /usr/bin/python3 ${TENANT_WORKSPACE}/scripts/blocker_digest_cron.py --parked-root ${TENANT_WORKSPACE}/tasks/parked --run-record-dir ${TENANT_WORKSPACE}/reflections/blocker-digest-runs"
```

**Expected:** that line, fully interpolated. Worker-c paste this back to verify the substitution worked correctly — the README's `<TENANT>` literal MUST resolve to `acme` end-to-end.

---

## Step 3 — Bootstrap smoke (worked)

```bash
cd /mnt/system/base/skills/task-system/bootstrap-smoke
python3 smoke_test.py
```

**Expected output (full):**
```
[smoke] workspace: /tmp/bootstrap-smoke-XXXXXXXX/acme
[smoke] scaffold created: ['intake', 'shop-floor', 'planned', 'scheduled', 'today', 'done', 'in-flight', 'parked']
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
Exit 0.

Note the smoke harness uses its OWN ephemeral `/tmp/bootstrap-smoke-*/acme/` workspace — it doesn't touch `$TENANT_WORKSPACE`. That's by design (per `bootstrap-smoke/README.md` §Constraints).

---

## Step 4 — Patterns-aggregator (worked)

### 4.1 Confirm host-side files

```bash
ls /mnt/system/base/skills/task-system/patterns-aggregator/
```

**Expected:**
```
COMPLETION-NOTICE.md  README.md  dogfood-output  patterns_aggregator.py  test_patterns_aggregator.py
```

### 4.2 Self-test

```bash
cd /mnt/system/base/skills/task-system/patterns-aggregator
python3 test_patterns_aggregator.py
```

**Expected (last 3 lines):**
```
[18] empty-cycle reviewer nudge: PASS
ALL 18 ASSERTIONS PASSED
```
Exit 0.

### 4.3 Pre-create output dir

```bash
mkdir -p /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/
```

### 4.4 One-shot test run

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

**Expected output (last 4 lines):**
```
[patterns-aggregator] patterns.json absent for tenant=acme (graceful — no patterns yet)
[patterns-aggregator] tenants: src, josh, bun, danielle, acme
[patterns-aggregator] cross-tenant rollup: <N> promoted, <M> plan-time failure_modes
[patterns-aggregator] wrote /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/2026-05-19-aggregate.md
```
Exit 0.

(The `patterns.json absent for tenant=acme` line is EXPECTED on a fresh tenant. Per src-desktop msg 021 polish item #2, this message currently conflates absent vs malformed — for the fake-tenant dry-run we know it's absent because we just scaffolded.)

### 4.5 Verify aggregate includes new tenant

```bash
LATEST=$(ls -t /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/ | head -1)
grep -A2 "^### acme" /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/"$LATEST"
```

**Expected:**
```
### acme

- promoted: 0
- failure_modes (plan-time): {}
- patterns.json: absent (graceful)
```

---

## Step 5 — End-to-end verification (worked)

### 5.1 Seed canary task

```bash
mkdir -p "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary"
cat > "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary/task.json" <<EOF
{
  "id": "2026-05-19-9999-onboarding-canary",
  "state": "intake",
  "raised_at": "2026-05-19T03:30:00Z",
  "raised_by": "manual",
  "source_ref": "onboarding-canary-fixture",
  "summary": "Onboarding canary — delete after verification",
  "tenant": "${TENANT}",
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
```

### 5.2 Validate canary

```bash
python3 /mnt/system/base/skills/task-system/schema/task_schema.py \
  "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary/task.json"
```

**Expected:**
```
1 task(s) checked — all valid.
```
Exit 0.

### 5.3 Re-run aggregator

```bash
flock -n /tmp/patterns-aggregator.lock python3 \
  /mnt/system/base/skills/task-system/patterns-aggregator/patterns_aggregator.py \
  -t "${TENANT}=${TENANT_WORKSPACE}" \
  -o /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/
```

**Expected:** new aggregate file written. Inspect:

```bash
grep -A4 "^### acme" /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/$(ls -t /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/ | head -1)
```

**Expected:**
```
### acme

- promoted: 0
- failure_modes (plan-time): {}      # canary has failure_modes: []
- patterns.json: absent (graceful)
```

(The canary's empty `failure_modes` doesn't change the count — but it DOES count as one valid task that round-tripped against the deployed v0.1.3 schema. The success indicator for §5.3 is "aggregator runs without erroring and includes acme in output," NOT "failure_modes counts changed".)

### 5.4 Delete canary

```bash
rm -rf "$TENANT_WORKSPACE/tasks/intake/2026-05-19-9999-onboarding-canary/"
```

**Expected:** silent success. Verify:

```bash
ls "$TENANT_WORKSPACE/tasks/intake/" | head
```

**Expected:** empty (or whatever was there pre-canary).

### 5.5 Final 4 indicators

```bash
echo "A. State subdirs:"
ls "$TENANT_WORKSPACE/tasks/" | grep -E "^(intake|shop-floor|planned|scheduled|today|done|in-flight|parked|manifest\.json|SCHEMA\.md)$" | wc -l
echo "  Expected: 10"
echo
echo "B. Seam-A cron line (will be 0 in fake-tenant dry-run — that's OK; would be 1 for real tenant):"
crontab -l 2>/dev/null | grep -c blocker_digest_cron || echo "0"
echo
echo "C. Host-side aggregator cron (will be 0 in fake-tenant dry-run — that's OK):"
crontab -l -u host_admin 2>/dev/null | grep -c patterns_aggregator || echo "0"
echo
echo "D. Bootstrap smoke (re-run):"
cd /mnt/system/base/skills/task-system/bootstrap-smoke && python3 smoke_test.py 2>&1 | tail -1
echo "  Expected: PASS: 8 scenarios"
```

**Expected for FAKE-TENANT dry-run:**
```
A. State subdirs:
10
  Expected: 10

B. Seam-A cron line (...):
0

C. Host-side aggregator cron (...):
0

D. Bootstrap smoke (re-run):
PASS: 8 scenarios
  Expected: PASS: 8 scenarios
```

For a fake-tenant dry-run, A and D MUST pass; B and C are zero because we deliberately didn't install the cron lines. For a real tenant, all four must show the expected non-zero / passing values.

---

## Teardown (fake-tenant only)

```bash
rm -rf "$TENANT_WORKSPACE"
echo "fake-tenant cleanup complete"
```

If `$TENANT_WORKSPACE` is the real `/mnt/clients/acme/...`, do NOT run the teardown — use the rollback procedure in `CHECKLIST.md` instead.

---

## Drift between this example and the deployed snapshot

If during dry-run worker-c sees output that doesn't match what's documented here, the LIKELY causes (most common first):

1. **Patterns-aggregator not yet docker-cp'd by host.** Step 4.1 will report missing dir. Out-of-band: ping host.
2. **Schema dir layout drift** (per src-desktop msg 008 finding: `schema/` vs `canonical-schema/`). README assumes `schema/` (short form). If actually deployed as `canonical-schema/`, sed the env var: `export TASK_SYSTEM_SCHEMA_DIR=/mnt/system/base/skills/task-system/canonical-schema`.
3. **Scaffold dir layout drift** (`scaffold/` vs `tenant-scaffolder/` per same msg). Adjust the `python3 .../scaffold_tenant.py` paths in steps 1.1, 1.2, 1.4.
4. **`/mnt/agent-mesh/mesh/BLACKBOARD/...` not writable from this container.** Step 4.3 will error. Out-of-band: host adjusts bind-mount RW.

In all four cases the README's failure-mode tables direct to "host help" in the Out-of-band section.
