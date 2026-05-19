# tenant-scaffolder v0.1

Per-tenant scaffolder for the JamBot task system v0.1 directory layout
(see `/mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md`
§2). Creates the eight state subdirectories under `<workspace>/tasks/`,
drops a `SCHEMA.md` pointer, and writes a structured `manifest.json`.

Owner: worker-b@mesh. Refines the immutable baseline at
`/agent-desk/snapshots/2026-05-18-task-substrate/scaffold_tenant.py`.

## Layout produced

```
<workspace>/tasks/
  manifest.json        ← written once, preserved on rerun
  SCHEMA.md            ← human-readable pointer to spec
  intake/
  shop-floor/
  planned/
  scheduled/
  today/
  done/
  in-flight/
  parked/
```

Each state subdir gets a `.gitkeep` so git can track an empty workspace.

## Usage

```
python3 scaffold_tenant.py --workspace <path> [--tenant <name>] [--dry-run] [--json]
```

Flags:

| Flag          | Meaning                                                                 |
|---------------|-------------------------------------------------------------------------|
| `--workspace` | Tenant workspace root, e.g. `/mnt/clients/josh/openclaw/workspace`.     |
| `--tenant`    | Tenant name recorded in `manifest.json`. Omitted ⇒ `tenant: null`.      |
| `--dry-run`   | Print what would be created; touch no files (no subdirs, no manifest).  |
| `--json`      | Emit the summary as JSON instead of human text.                         |

### Examples

Fresh scaffold for tenant `josh`:

```
python3 scaffold_tenant.py \
  --workspace /mnt/clients/josh/openclaw/workspace \
  --tenant josh
```

Dry run, JSON summary:

```
python3 scaffold_tenant.py \
  --workspace /tmp/demo --tenant demo --dry-run --json
```

Idempotent rerun (same `--tenant`) is a no-op.

## manifest.json

Written once on first scaffold to `<workspace>/tasks/manifest.json`.
Template: see `manifest-template.json` in this snapshot.

Fields:

| Field            | Value                                                                                  |
|------------------|----------------------------------------------------------------------------------------|
| `tenant`         | Tenant name from `--tenant`, or `null` if not supplied.                                |
| `scaffolded_at`  | ISO-8601 UTC timestamp, e.g. `2026-05-18T20:30:00Z`.                                   |
| `scaffolded_by`  | `worker-b@mesh` (this scaffolder's identity).                                          |
| `schema_version` | `0.1-pending-rule-8` — spec is v0.1 with rule 8 (lock-and-defer signal) still open.    |
| `subdirs`        | List of state subdirs actually created, mirrors `_STATES` in `scaffold_tenant.py`.     |
| `rule_8_status`  | `PENDING` until the seam B lock-and-defer signal is decided (see spec §6).             |

### No-clobber semantics

The manifest is the source of truth for "which tenant owns this tree."
On rerun:

- `manifest.json` exists, `--tenant` matches its `tenant` field → preserved, exit 0.
- `manifest.json` exists, no `--tenant` supplied → preserved, exit 0.
- `manifest.json` exists, `--tenant` supplied AND differs → prints
  `manifest mismatch: <existing> vs <new>` to stderr and exits **code 2**.
  No files are touched.

This prevents one tenant's workspace from being silently re-stamped
with another tenant's identity.

## Rollback

The scaffolder writes only inside `<workspace>/tasks/`. To roll back:

```
rm -rf <workspace>/tasks
```

Or, for a surgical rollback that keeps any task records already created:

```
rm <workspace>/tasks/manifest.json
rm <workspace>/tasks/SCHEMA.md
# Then for each empty state subdir:
rmdir <workspace>/tasks/{intake,shop-floor,planned,scheduled,today,done,in-flight,parked}
```

`--dry-run` is the safest pre-flight; it prints what would change without
touching disk.

## Tests

```
python3 test_scaffolder.py
```

The test harness writes only to `tempfile.mkdtemp(prefix="scaffold-test-")`
directories and cleans them up in a `finally` block. Exit code 0 on
success, non-zero on assertion failure.

## Spec references

- v0.1 spec §2 (directory layout): `/mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md`
- Baseline being refined (immutable): `/agent-desk/snapshots/2026-05-18-task-substrate/scaffold_tenant.py`
