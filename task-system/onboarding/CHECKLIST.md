# Tenant Onboarding — One-Page Checklist

Tickbox version of `README.md`. Use during a real onboarding; tick as each verify-step passes.

**Tenant:** _______________________  **Date:** ___________  **Operator:** _______________________

---

## Pre-reqs

- [ ] `/mnt/clients/<TENANT>/openclaw/workspace` exists and is writeable (else: host help)
- [ ] `/mnt/system/base/skills/task-system/{schema,scaffold,seam-a,bootstrap-smoke,patterns-aggregator}/` all exist (else: host docker-cp)
- [ ] Env vars exported: `TENANT`, `TENANT_WORKSPACE`, `TASK_SYSTEM_SCHEMA_DIR`
- [ ] `command -v` checks pass for: `mesh-send`, `mesh-recv`, `flock`, `python3`, `jq` (5 OK lines)

## Step 1 — Scaffold

- [ ] **1.1** Dry-run scaffold_tenant.py → JSON with `would_create: [8 dirs]`, exit 0
- [ ] **1.2** Real run → `scaffolded 8 subdirs + manifest.json`, exit 0
- [ ] **1.3** `ls $TENANT_WORKSPACE/tasks/` shows 8 state subdirs + manifest.json + SCHEMA.md
- [ ] **1.4** Re-run is no-op (`manifest.json present for tenant=<X>; no changes`), exit 0

## Step 2 — Seam-A (intake + blocker-digest cron)

- [ ] **2.1** `blocker_writer.py` + `blocker_digest_cron.py` copied to `$TENANT_WORKSPACE/scripts/`
- [ ] **2.2** `python3 -c "import blocker_digest_cron; print(_RECIPIENT)"` → `host@mesh`
- [ ] **2.3** Dry-run digest cron → `due blockers: 0`, run record file created, exit 0
- [ ] **2.4** Cron line added to `crontab -e -u <tenant-user>` with `0 13 * * *` schedule
- [ ] **2.5** `crontab -l | grep blocker_digest_cron` returns the line

## Step 3 — Bootstrap smoke harness

- [ ] **3.1** `python3 smoke_test.py` from `bootstrap-smoke/` → `PASS: 8 scenarios`, exit 0
- [ ] **3.2** (Optional) `--no-cleanup` inspection shows 8 subdirs + seeded fixtures
- [ ] **3.3** Per-tenant log written to `$TENANT_WORKSPACE/reflections/bootstrap-smoke-<ISO>.log`

## Step 4 — Patterns-aggregator (host-side)

- [ ] **4.1** `ls /mnt/system/base/skills/task-system/patterns-aggregator/` shows 5 expected files
- [ ] **4.2** `python3 test_patterns_aggregator.py` → 18/18 PASS, exit 0
- [ ] **4.3** `mkdir -p /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/` done
- [ ] **4.4** One-shot run with all 4 + new tenant produces `<DATE>-aggregate.md`
- [ ] **4.5** New tenant appears in per-tenant detail section of aggregate
- [ ] **4.6** Host crontab updated with `5 6 * * *` line including `-t <TENANT>=...`
- [ ] **4.7** `crontab -l -u host_admin | grep patterns_aggregator` returns the line

## Step 5 — Verify end-to-end

- [ ] **5.1** Canary task seeded under `tasks/intake/2026-05-19-9999-onboarding-canary/`
- [ ] **5.2** `task_schema.py <canary.json>` → "1 task(s) checked — all valid." exit 0
- [ ] **5.3** Aggregator re-run shows new tenant with 0 promoted / 0 failure_modes
- [ ] **5.4** Canary deleted: `rm -rf tasks/intake/2026-05-19-9999-onboarding-canary/`

## Final 4 success indicators (all must be ✅)

- [ ] **A.** 8 state subdirs + manifest.json + SCHEMA.md present
- [ ] **B.** Seam-A cron registered for tenant user
- [ ] **C.** Patterns-aggregator cron registered host-side with `-t <TENANT>=` arg
- [ ] **D.** `smoke_test.py` returns `PASS: 8 scenarios` exit 0

If any of A-D fails: onboarding NOT complete. See README `§ Out-of-band` for host-help paths.

---

## Quick rollback (if onboarding fails partway)

```bash
# 1. Remove tenant cron line:
crontab -e -u <tenant-user>   # delete the blocker_digest_cron line

# 2. Remove host cron line (if added):
crontab -e -u host_admin       # delete the patterns_aggregator -t <TENANT> arg or whole line

# 3. Tear down scaffold (preserves any non-task content in workspace):
rm -rf "$TENANT_WORKSPACE/tasks"
rm -rf "$TENANT_WORKSPACE/scripts/blocker_writer.py"
rm -rf "$TENANT_WORKSPACE/scripts/blocker_digest_cron.py"
rm -rf "$TENANT_WORKSPACE/reflections/blocker-digest-runs"

# 4. Confirm clean state:
ls "$TENANT_WORKSPACE"   # tasks/, scripts/blocker_*, reflections/blocker-digest-runs all gone
```
