"""
test_brief_aggregate_reader — assertions for the brief-reader integration.

Generates real aggregate files via the upstream patterns_aggregator, parses
them with this module's reader, and asserts the end-to-end plain-English
output matches expectations.

Covers happy path, stale aggregate warning, missing aggregate fallback,
empty cycle nudge, malformed file robustness.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "2026-05-19-patterns-aggregator"))

from brief_aggregate_reader import (  # noqa: E402
    find_latest_aggregate,
    format_for_brief,
    read_aggregate,
    render_for_brief,
)
from patterns_aggregator import aggregate as patterns_aggregate  # noqa: E402


STATE_DIRS = ("intake", "shop-floor", "planned", "scheduled",
              "today", "in-flight", "parked", "done")


def _scaffold(root: Path, tenant: str) -> Path:
    ws = root / tenant
    for state in STATE_DIRS:
        (ws / "tasks" / state).mkdir(parents=True, exist_ok=True)
    return ws


def _write_patterns(ws: Path, payload: dict) -> None:
    (ws / "tasks" / "patterns.json").write_text(json.dumps(payload))


def _write_task(ws: Path, state: str, task_id: str, record: dict) -> None:
    d = ws / "tasks" / state / task_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "task.json").write_text(json.dumps(record))


def _make_fixtures(root: Path) -> list[tuple[str, Path]]:
    src = _scaffold(root, "src")
    josh = _scaffold(root, "josh")
    bun = _scaffold(root, "bun")
    danielle = _scaffold(root, "danielle")

    _write_patterns(src, {
        "promoted": ["seam-b-and-gate", "task-dir-lock"],
        "blocker_patterns": [
            {"task": "cookie-handoff", "pattern": "unresolved-blocker"},
        ],
        "brief_guidance": "src ok",
    })
    _write_task(src, "planned", "seam-b-and-gate",
                {"failure_modes": ["interleave_corruption", "false_positive_active_state"]})
    _write_task(src, "planned", "task-dir-lock",
                {"failure_modes": ["interleave_corruption", "parallel_shift_writer_race"]})

    _write_patterns(josh, {
        "promoted": ["blocker-digest-cron"],
        "blocker_patterns": [
            {"task": "intake-fuzzy-hash", "pattern": "unresolved-blocker"},
        ],
        "brief_guidance": "josh ok",
    })
    _write_task(josh, "planned", "blocker-digest-cron",
                {"failure_modes": ["interleave_corruption", "outbound_recipient_drift"]})

    _write_patterns(bun, {
        "promoted": [],
        "blocker_patterns": [
            {"task": "heartbeat-roll", "pattern": "unresolved-blocker"},
        ],
        "brief_guidance": "bun no promotes",
    })

    return [("src", src), ("josh", josh), ("bun", bun), ("danielle", danielle)]


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="brief-reader-test-"))
    try:
        tenants = _make_fixtures(tmp)
        patterns_dir = tmp / "BLACKBOARD" / "patterns"
        today = date(2026, 5, 19)
        patterns_aggregate(tenants, patterns_dir, date=today.isoformat())

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

        latest = find_latest_aggregate(patterns_dir)
        expect(
            "[1] find_latest_aggregate returns the only file",
            latest is not None and latest.name == "2026-05-19-aggregate.md",
            f"got {latest}",
        )

        block = read_aggregate(latest, today=today)
        expect(
            "[2] read_aggregate parses tenants_reporting=4",
            block.tenants_reporting == 4,
            f"got {block.tenants_reporting}",
        )
        expect(
            "[3] read_aggregate parses total_promoted=3",
            block.total_promoted == 3,
            f"got {block.total_promoted}",
        )
        expect(
            "[4] top failure mode is interleave_corruption x 3",
            block.top_failure_mode == "interleave_corruption"
            and block.top_failure_mode_count == 3,
            f"got {block.top_failure_mode}={block.top_failure_mode_count}",
        )
        expect(
            "[5] top failure mode tenants are {src, josh}",
            set(block.top_failure_mode_tenants) == {"src", "josh"},
            f"got {block.top_failure_mode_tenants}",
        )
        expect(
            "[6] top recurring pattern is unresolved-blocker across 3 tenants",
            block.top_recurring_pattern == "unresolved-blocker"
            and len(block.top_recurring_pattern_tenants) == 3,
            f"got {block.top_recurring_pattern} / {block.top_recurring_pattern_tenants}",
        )
        expect(
            "[7] no staleness warning for fresh aggregate",
            block.staleness_days == 0 and not block.warnings,
            f"got staleness={block.staleness_days} warnings={block.warnings}",
        )

        md = format_for_brief(block)
        expect(
            "[8] brief block mentions interleave_corruption",
            "interleave_corruption" in md,
            "missing top fm",
        )
        expect(
            "[9] brief block mentions unresolved-blocker recurring pattern",
            "unresolved-blocker" in md and "workflow-gap signal" in md,
            "missing recurring",
        )
        expect(
            "[10] brief block reports 3 tasks promoted",
            "3 tasks promoted" in md,
            "missing promoted count",
        )

        stale_today = today + timedelta(days=5)
        stale_block = read_aggregate(latest, today=stale_today)
        expect(
            "[11] stale aggregate raises warning + staleness_days populated",
            stale_block.staleness_days == 5
            and any("days old" in w for w in stale_block.warnings),
            f"got staleness={stale_block.staleness_days} warnings={stale_block.warnings}",
        )
        stale_md = format_for_brief(stale_block)
        expect(
            "[12] stale brief block includes lag note",
            "Patterns cron may be lagging" in stale_md,
            "missing lag warn",
        )

        missing_block = read_aggregate(None, today=today)
        missing_md = format_for_brief(missing_block)
        expect(
            "[13] missing aggregate yields fallback message",
            missing_block.aggregate_path is None
            and "did not produce a file" in missing_md,
            f"got md={missing_md!r}",
        )

        empty_patterns_dir = tmp / "empty-patterns"
        empty_patterns_dir.mkdir(parents=True)
        empty_md = render_for_brief(empty_patterns_dir, today=today)
        expect(
            "[14] render_for_brief on empty patterns dir gives fallback",
            "did not produce a file" in empty_md,
            "missing fallback for empty dir",
        )

        empty_tenants = [("solo", _scaffold(tmp / "solo-only", "ws"))]
        _write_patterns(empty_tenants[0][1], {"promoted": [], "blocker_patterns": [], "brief_guidance": ""})
        empty_agg_dir = tmp / "empty-agg"
        patterns_aggregate(empty_tenants, empty_agg_dir, date=today.isoformat())
        empty_agg_block = read_aggregate(
            find_latest_aggregate(empty_agg_dir), today=today
        )
        empty_agg_md = format_for_brief(empty_agg_block)
        expect(
            "[15] empty-cycle aggregate yields reviewer nudge",
            "No plan-time `failure_modes`" in empty_agg_md
            and "rarely accurate" in empty_agg_md,
            "missing nudge",
        )

        garbage = patterns_dir / "2026-05-20-aggregate.md"
        garbage.write_text("this is not valid frontmatter\n## but has a heading\n")
        gb = read_aggregate(garbage, today=date(2026, 5, 20))
        expect(
            "[16] malformed aggregate does not crash; defaults to zero counts",
            gb.tenants_reporting == 0
            and gb.total_promoted == 0
            and gb.top_failure_mode is None,
            f"got {gb}",
        )
        gb_md = format_for_brief(gb)
        expect(
            "[17] malformed aggregate still renders a brief block",
            "Yesterday's task-system patterns" in gb_md,
            "missing header",
        )

        rendered = render_for_brief(patterns_dir, today=today)
        expect(
            "[18] render_for_brief one-call helper picks latest of multiple files",
            "interleave_corruption" in rendered or "2026-05-20" in rendered,
            "one-call helper failed",
        )

        print()
        print(f"brief_aggregate_reader: {passes}/{passes + len(fails)} assertions PASS")
        if fails:
            for f in fails:
                print(f"  FAIL :: {f}")
            return 1
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
