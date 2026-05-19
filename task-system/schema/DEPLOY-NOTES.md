# DEPLOY-NOTES — canonical-schema v0.1.4 host docker-cp

**Target:** `/mnt/system/base/skills/task-system/schema/` on host VPS (the in-container path agents import from).
**Strategy:** incremental docker-cp on schema dir ONLY. Other deployed snapshots in the bundle do NOT change.
**Risk profile:** LOW. Both new fields are optional + additive; all v0.1.3 records validate clean under v0.1.4 (verified by 3/3 backward-compat assertion + new test [35]).

---

## 1. Pre-deploy checks (host should run before docker-cp)

```bash
SRC=/mnt/clients/<josh-or-host>/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.4

# (a) sanity — JSON + Python parse clean
python3 -c "import json; json.load(open('$SRC/task-json-schema.json'))"
python3 -c "import json; json.load(open('$SRC/canonical-task.examples.json'))"
python3 -c "import json; json.load(open('$SRC/invalid-examples.json'))"
python3 -c "import ast; ast.parse(open('$SRC/task_schema.py').read())"

# (b) full assertion run — should print "37/37" → "ALL CANONICAL SCHEMA ASSERTIONS PASSED"
cd "$SRC" && python3 test_canonical_schema.py
```

If either fails: STOP. Do not docker-cp. Re-snapshot.

---

## 2. docker-cp command

```bash
# Single line — copy the v0.1.4 contents over the deployed v0.1.3.
docker cp \
  /mnt/clients/<host>/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.4/. \
  <task-system-container>:/mnt/system/base/skills/task-system/schema/
```

The trailing `/.` is intentional — copies the *contents* of the directory, not the directory itself, so the deployed path stays `/mnt/system/base/skills/task-system/schema/` (no `…/schema/2026-05-19-canonical-schema-v0.1.4/`).

---

## 3. Post-deploy verification (in-container)

```bash
docker exec <task-system-container> bash -c '
  cd /mnt/system/base/skills/task-system/schema
  python3 test_canonical_schema.py
'
# Expected: 37/37 PASS
```

If post-deploy test count differs from 37, the docker-cp dropped a file. Re-cp.

---

## 4. Downstream snapshots needing schema-ref bump

Per worker-b's milestone-4 §5 ("backward-incompatible nothing, forward-incompatible nothing — but the schema-ref string is on a couple of consumers"), the following snapshots reference the canonical schema version. Update the version string to `v0.1.4` lockstep with this deploy:

| Snapshot | What it imports | Update needed? |
|---|---|---|
| `/agent-desk/snapshots/2026-05-18-intake-internal/` | `task_schema` (worker-b's intake adapter — mesh/manual/brief) | YES — version string in README; field-population logic already absent-by-default-safe |
| `/agent-desk/snapshots/2026-05-18-intake-external/` | `task_schema` (worker-c's intake adapter — email/sms/voice) | YES — version string; same field-population safety |
| `/agent-desk/snapshots/2026-05-18-intake-dedupe/` | `task_schema.TASK_FIELDS` for fingerprint hash | NO — new fields aren't in the fingerprint shingle (verified: dedupe hashes on tenant + source_ref + summary, not extension fields) |
| `/agent-desk/snapshots/2026-05-19-bootstrap-smoke/` | `task_schema.validate_task_record` | YES — worker-c milestone-4 patch (`worker-c/smoke_test.patch`) extends this; apply during synthesize |
| `/agent-desk/snapshots/2026-05-19-rule-8-bootstrap/` | `task_schema.TASK_FIELDS` for the rule-8 sweep | YES — version string only; new fields don't interact with rule-8 |
| `/agent-desk/snapshots/2026-05-19-session-context/` | `task_schema.STATES / TASK_FIELDS` for session loader | YES — version string only; loader is field-agnostic (re-bootstrap test [9.3] confirms preservation) |
| `/agent-desk/snapshots/2026-05-18-tenant-scaffolder/` | `task_schema.STATES` only | NO — STATES tuple unchanged from v0.1.1 |
| `/agent-desk/snapshots/2026-05-18-voice-active/` | None (sibling artifact) | NO |
| `/agent-desk/snapshots/2026-05-19-state-transition-matrix/` | None (sibling artifact) | NO |
| `/agent-desk/snapshots/2026-05-19-task-dir-lock/` | None (runtime primitive) | NO |

Recommended order for host nightly synthesize:
1. docker-cp v0.1.4 schema dir (this snapshot).
2. Apply worker-c smoke patch (`worker-c/smoke_test.patch`) to `2026-05-19-bootstrap-smoke/`. Resolve the 2 TODO marker symbol names from worker-b's resolver.
3. Bump version-string references in the intake-internal, intake-external, rule-8-bootstrap, and session-context READMEs (mechanical sed: `v0.1.3` → `v0.1.4`).
4. Re-run cross-tenant smoke (per v0.2-spec-amendment.md §10) — expected: still 20/20 PASS, plus +1 milestone-4 e2e scenario from worker-c.

---

## 5. Rollback procedure

If post-deploy reveals breakage:

```bash
docker cp \
  /mnt/clients/<host>/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3/. \
  <task-system-container>:/mnt/system/base/skills/task-system/schema/
```

The v0.1.3 snapshot is preserved and intact. Records carrying `notification_policy` or `research_at` would fail under v0.1.3 (`additionalProperties: false`), so a rollback after writes have started using the new fields requires either: (a) a sweep to delete those keys from in-flight records before rollback, or (b) staying on v0.1.4 and root-causing the actual breakage. Recommend (b) in nearly all cases.

---

## 6. Honest caveats

- **Cross-container schema drift** is not defended at this layer. If any tenant container's local copy of `task_schema.py` drifts from the host-deployed version (e.g. a webtop copies from `/mesh/BLACKBOARD/task-system/v0.1.1-verified/` instead), validation passes locally but fails the lockstep contract. Cross-tenant smoke (v0.2-spec-amendment.md §10 §"Honest caveat") explicitly does NOT verify byte-identity to the host VPS deploy.
- **`additionalProperties: false`** means strict v0.1.3 readers will reject v0.1.4 records that exercise the new fields. This is the intended one-direction breakage of additive schema evolution. All readers update lockstep at this ratchet — verify no v0.1.3 reader is still in-flight before declaring rollout complete.
- **Reader-side defaults are not validator-enforced.** A consumer that fails to apply the absent-defaults (e.g. ignores `notification_policy` absence instead of treating it as `roll_up_daily`) will silently misroute notifications. worker-c's smoke (tests [9.4], [9.5]) is the contract test for this; downstream consumers should mirror that pattern.
