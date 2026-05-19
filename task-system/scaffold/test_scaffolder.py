"""
Tests for the per-tenant scaffolder.

Covers:
  - 8 state subdirs + SCHEMA.md created on fresh scaffold
  - idempotent rerun (no errors, no clobber)
  - manifest.json written with expected keys
  - rerun with same --tenant is idempotent
  - rerun with conflicting --tenant exits code 2 (subprocess)
  - --dry-run does not create manifest.json
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import scaffold_tenant


SCRIPT = str(Path(__file__).resolve().parent / "scaffold_tenant.py")

_MANIFEST_REQUIRED_KEYS = {
    "tenant",
    "scaffolded_at",
    "scaffolded_by",
    "schema_version",
    "subdirs",
    "rule_8_status",
}


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="scaffold-test-"))
    try:
        # ---- [1] scaffolder creates all 8 states + SCHEMA.md ----
        summary = scaffold_tenant.scaffold(work, tenant="josh")
        assert set(summary["created"]) == set(scaffold_tenant._STATES), summary
        assert (work / "tasks" / "SCHEMA.md").exists()
        print("[1] scaffolder creates all 8 states + SCHEMA.md: OK")

        # ---- [2] idempotent (same tenant) ----
        rerun = scaffold_tenant.scaffold(work, tenant="josh")
        assert rerun["created"] == [], rerun
        assert set(rerun["existed"]) == set(scaffold_tenant._STATES), rerun
        assert rerun["manifest"] == "preserved", rerun
        print("[2] scaffolder idempotent on rerun with same --tenant: OK")

        # ---- [3] manifest.json written with correct keys ----
        manifest_path = work / "tasks" / "manifest.json"
        assert manifest_path.exists(), "manifest.json missing after scaffold"
        manifest = json.loads(manifest_path.read_text())
        missing = _MANIFEST_REQUIRED_KEYS - set(manifest.keys())
        assert not missing, f"manifest missing keys: {missing}"
        assert manifest["tenant"] == "josh"
        assert manifest["scaffolded_by"] == "worker-b@mesh"
        assert manifest["schema_version"] == "0.1-pending-rule-8"
        assert manifest["rule_8_status"] == "PENDING"
        assert set(manifest["subdirs"]) == set(scaffold_tenant._STATES)
        # ISO-Z timestamp shape
        assert manifest["scaffolded_at"].endswith("Z"), manifest["scaffolded_at"]
        assert "T" in manifest["scaffolded_at"]
        print("[3] manifest.json written with correct keys + values: OK")

        # ---- [4] conflict: rerun with different --tenant exits 2 (subprocess) ----
        result = subprocess.run(
            [
                sys.executable,
                SCRIPT,
                "--workspace",
                str(work),
                "--tenant",
                "danielle",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2, (
            f"expected exit 2 on tenant conflict, got {result.returncode}; "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "manifest mismatch" in result.stderr, result.stderr
        assert "josh" in result.stderr and "danielle" in result.stderr, result.stderr
        # manifest must not have been clobbered
        manifest_after = json.loads(manifest_path.read_text())
        assert manifest_after["tenant"] == "josh", manifest_after
        print("[4] conflicting --tenant exits 2 + no clobber: OK")

        # ---- [5] --dry-run does not create manifest.json ----
        work2 = Path(tempfile.mkdtemp(prefix="scaffold-test-dry-"))
        try:
            dry_summary = scaffold_tenant.scaffold(
                work2, dry_run=True, tenant="acme"
            )
            assert dry_summary["manifest"] == "would-create", dry_summary
            assert not (work2 / "tasks" / "manifest.json").exists(), (
                "dry-run must not create manifest.json"
            )
            # Subdirs also should not exist (dry-run is no-op on disk)
            for state in scaffold_tenant._STATES:
                assert not (work2 / "tasks" / state).exists(), (
                    f"dry-run created subdir {state}"
                )
            print("[5] --dry-run does not create manifest.json or subdirs: OK")
        finally:
            shutil.rmtree(work2, ignore_errors=True)

        # ---- [6] fresh scaffold via CLI subprocess (--json), tenant=null ----
        work3 = Path(tempfile.mkdtemp(prefix="scaffold-test-cli-"))
        try:
            cli = subprocess.run(
                [
                    sys.executable,
                    SCRIPT,
                    "--workspace",
                    str(work3),
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
            assert cli.returncode == 0, (
                f"CLI scaffold failed: stdout={cli.stdout!r} stderr={cli.stderr!r}"
            )
            cli_summary = json.loads(cli.stdout)
            assert cli_summary["manifest"] == "created", cli_summary
            assert cli_summary["tenant"] is None, cli_summary
            m3 = json.loads((work3 / "tasks" / "manifest.json").read_text())
            assert m3["tenant"] is None, m3
            print("[6] CLI fresh scaffold with no --tenant -> manifest.tenant=null: OK")
        finally:
            shutil.rmtree(work3, ignore_errors=True)

        print("\nALL SCAFFOLDER ASSERTIONS PASSED")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
