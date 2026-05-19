"""
test_patterns_aggregator — named assertions for the cross-tenant aggregator.

Builds synthetic per-tenant workspaces with mixed states, failure_modes,
and blocker_patterns; asserts the rollup + cross-tenant aggregate + rendered
markdown all match expectations.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from patterns_aggregator import (  # noqa: E402
    STATE_DIRS,
    TenantRollup,
    aggregate,
    aggregate_rollups,
    render_markdown,
    rollup_tenant,
)


def _write_task(workspace: Path, state: str, task_id: str, record: dict) -> None:
    task_dir = workspace / "tasks" / state / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.json").write_text(json.dumps(record))


def _write_patterns(workspace: Path, payload: dict) -> None:
    (workspace / "tasks").mkdir(parents=True, exist_ok=True)
    (workspace / "tasks" / "patterns.json").write_text(json.dumps(payload))


def _scaffold(root: Path, tenant: str) -> Path:
    ws = root / tenant
    for state in STATE_DIRS:
        (ws / "tasks" / state).mkdir(parents=True, exist_ok=True)
    return ws


def _make_fixtures(root: Path) -> list[tuple[str, Path]]:
    src = _scaffold(root, "src")
    josh = _scaffold(root, "josh")
    bun = _scaffold(root, "bun")
    danielle = _scaffold(root, "danielle")

    _write_patterns(src, {
        "generated_at": "2026-05-19T01:00:00Z",
        "promoted_count": 2,
        "promoted": ["seam-b-and-gate", "task-dir-lock"],
        "blocker_patterns": [
            {"task": "cookie-writer-handoff", "pattern": "unresolved-blocker",
             "hint": "claude-direct ownership pending"},
        ],
        "brief_guidance": "src has 2 promoted, 1 blocker.",
    })
    _write_task(src, "planned", "seam-b-and-gate", {
        "id": "seam-b-and-gate", "failure_modes":
            ["false_positive_active_state", "interleave_corruption"],
    })
    _write_task(src, "planned", "task-dir-lock", {
        "id": "task-dir-lock", "failure_modes":
            ["parallel_shift_writer_race", "interleave_corruption"],
    })
    _write_task(src, "today", "cookie-writer-handoff", {
        "id": "cookie-writer-handoff", "failure_modes":
            ["orphan_after_crash"],
    })

    _write_patterns(josh, {
        "generated_at": "2026-05-19T01:00:00Z",
        "promoted_count": 1,
        "promoted": ["blocker-digest-cron"],
        "blocker_patterns": [
            {"task": "intake-adapter-fuzzy-hash", "pattern": "unresolved-blocker"},
        ],
        "brief_guidance": "josh has 1 promoted, 1 blocker.",
    })
    _write_task(josh, "planned", "blocker-digest-cron", {
        "id": "blocker-digest-cron", "failure_modes":
            ["outbound_recipient_drift", "interleave_corruption"],
    })
    _write_task(josh, "done", "v0.1.1-bundle", {
        "id": "v0.1.1-bundle", "failure_modes":
            ["worker_self_report_passed_but_unverified"],
    })

    _write_patterns(bun, {
        "generated_at": "2026-05-19T01:00:00Z",
        "promoted_count": 0,
        "promoted": [],
        "blocker_patterns": [
            {"task": "heartbeat-rollout", "pattern": "unresolved-blocker"},
        ],
        "brief_guidance": "bun nothing promoted today.",
    })
    _write_task(bun, "shop-floor", "heartbeat-rollout", {
        "id": "heartbeat-rollout", "failure_modes":
            ["sentinel_traps_silent_skip"],
    })

    return [
        ("src", src), ("josh", josh), ("bun", bun), ("danielle", danielle),
    ]


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="patterns-test-"))
    try:
        tenants = _make_fixtures(root)
        passes = 0
        fails: list[str] = []

        def expect(name: str, cond: bool, detail: str = ""):
            nonlocal passes
            if cond:
                passes += 1
                print(f"  PASS  {name}")
            else:
                fails.append(f"{name}: {detail}")
                print(f"  FAIL  {name} :: {detail}")

        src_rollup = rollup_tenant("src", tenants[0][1])
        expect("[1] src.promoted_count=2", src_rollup.promoted_count == 2,
               f"got {src_rollup.promoted_count}")
        expect(
            "[2] src.failure_modes counts interleave_corruption twice",
            src_rollup.failure_modes["interleave_corruption"] == 2,
            f"got {src_rollup.failure_modes['interleave_corruption']}",
        )
        expect(
            "[3] src.task_counts_by_state reflects 2 planned + 1 today",
            src_rollup.task_counts_by_state.get("planned") == 2
            and src_rollup.task_counts_by_state.get("today") == 1,
            f"got {src_rollup.task_counts_by_state}",
        )
        expect(
            "[4] src.blocker_patterns has 1 entry",
            len(src_rollup.blocker_patterns) == 1,
            f"got {len(src_rollup.blocker_patterns)}",
        )

        empty_rollup = rollup_tenant("danielle", tenants[3][1])
        expect(
            "[5] empty tenant rollup yields zero counts + error noting missing patterns.json",
            empty_rollup.promoted_count == 0 and any(
                "patterns.json" in e for e in empty_rollup.errors
            ),
            f"got promoted={empty_rollup.promoted_count} errors={empty_rollup.errors}",
        )

        rollups = [rollup_tenant(t, w) for t, w in tenants]
        agg = aggregate_rollups(rollups, date="2026-05-19")

        expect(
            "[6] aggregate.total_promoted = 3 (src=2 + josh=1 + bun=0 + danielle=0)",
            agg.total_promoted == 3,
            f"got {agg.total_promoted}",
        )
        expect(
            "[7] aggregate.failure_modes['interleave_corruption'] = 3 (src 2 + josh 1)",
            agg.failure_modes["interleave_corruption"] == 3,
            f"got {agg.failure_modes['interleave_corruption']}",
        )
        expect(
            "[8] interleave_corruption appears in {src, josh}",
            agg.failure_mode_tenants["interleave_corruption"] == {"src", "josh"},
            f"got {agg.failure_mode_tenants['interleave_corruption']}",
        )
        expect(
            "[9] unresolved-blocker pattern appears in 3 tenants",
            len(agg.blocker_pattern_tenants["unresolved-blocker"]) == 3,
            f"got {agg.blocker_pattern_tenants['unresolved-blocker']}",
        )
        expect(
            "[10] aggregate failure_modes counter has 7 distinct enums",
            len(agg.failure_modes) == 7,
            f"got {len(agg.failure_modes)} :: {dict(agg.failure_modes)}",
        )

        md = render_markdown(agg)
        expect(
            "[11] rendered md begins with frontmatter",
            md.startswith("---\n") and "\ndate: 2026-05-19\n" in md,
            "frontmatter check failed",
        )
        expect(
            "[12] md surfaces top class to invest defense tooling",
            "Top class to invest defense tooling in" in md
            and "interleave_corruption" in md,
            "top-class line missing",
        )
        expect(
            "[13] md surfaces recurring blocker pattern across tenants",
            "Recurring blocker pattern across tenants" in md
            and "unresolved-blocker" in md,
            "recurring-blocker line missing",
        )
        expect(
            "[14] md lists all 4 tenant detail sections",
            all(f"### {t}" in md for t in ("src", "josh", "bun", "danielle")),
            "tenant sections incomplete",
        )

        out_dir = root / "out"
        path = aggregate(tenants, out_dir, date="2026-05-19")
        expect(
            "[15] aggregate() writes <date>-aggregate.md to output_dir",
            path == out_dir / "2026-05-19-aggregate.md" and path.exists(),
            f"got {path} exists={path.exists()}",
        )

        non_string_fm_ws = _scaffold(root, "broken")
        _write_patterns(non_string_fm_ws, {
            "promoted": [], "blocker_patterns": [], "brief_guidance": "n/a",
        })
        _write_task(non_string_fm_ws, "intake", "non-string-fm", {
            "id": "non-string-fm",
            "failure_modes": [{"not": "a string"}, "interleave_corruption"],
        })
        broken_rollup = rollup_tenant("broken", non_string_fm_ws)
        expect(
            "[16] non-string failure_mode entry recorded as error, not crash",
            any("non-string" in e for e in broken_rollup.errors)
            and broken_rollup.failure_modes["interleave_corruption"] == 1,
            f"got errors={broken_rollup.errors} fm={dict(broken_rollup.failure_modes)}",
        )

        only_done_ws = _scaffold(root, "only-done")
        _write_patterns(only_done_ws, {"promoted": [], "blocker_patterns": [], "brief_guidance": "all done"})
        _write_task(only_done_ws, "done", "shipped", {
            "id": "shipped", "failure_modes": ["transition_illegal"],
        })
        done_rollup = rollup_tenant("only-done", only_done_ws)
        expect(
            "[17] done/ tasks counted into failure_modes (postmortem fuel pre-schema)",
            done_rollup.failure_modes["transition_illegal"] == 1,
            f"got {dict(done_rollup.failure_modes)}",
        )

        empty_only_ws = _scaffold(root, "empty-only")
        _write_patterns(empty_only_ws, {"promoted": [], "blocker_patterns": [], "brief_guidance": ""})
        empty_agg = aggregate_rollups([rollup_tenant("empty-only", empty_only_ws)], "2026-05-19")
        empty_md = render_markdown(empty_agg)
        expect(
            "[18] empty cycle renders nudge to reject empty failure_modes",
            "rarely accurate" in empty_md,
            "nudge missing",
        )

        print()
        print(f"patterns_aggregator: {passes}/{passes + len(fails)} assertions PASS")
        if fails:
            for f in fails:
                print(f"  FAIL :: {f}")
            return 1
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
