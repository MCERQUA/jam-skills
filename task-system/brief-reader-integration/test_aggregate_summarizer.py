"""
test_aggregate_summarizer — 14 named assertions covering ties, empty cycles,
malformed input, missing files, fallback-to-latest, staleness.

Round-trips through the real upstream patterns_aggregator (no mock).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "2026-05-19-patterns-aggregator"))

from aggregate_summarizer import (  # noqa: E402
    gather_patterns_aggregate,
    load_yesterday_aggregate,
    summarize_for_brief,
)
from patterns_aggregator import aggregate as patterns_aggregate  # noqa: E402


STATE_DIRS = ("intake", "shop-floor", "planned", "scheduled",
              "today", "in-flight", "parked", "done")


def _scaffold(root: Path, name: str) -> Path:
    ws = root / name
    for s in STATE_DIRS:
        (ws / "tasks" / s).mkdir(parents=True, exist_ok=True)
    return ws


def _write_patterns(ws: Path, payload: dict) -> None:
    (ws / "tasks" / "patterns.json").write_text(json.dumps(payload))


def _write_task(ws: Path, state: str, task_id: str, record: dict) -> None:
    d = ws / "tasks" / state / task_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "task.json").write_text(json.dumps(record))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="agg-summ-test-"))
    try:
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

        today = date(2026, 5, 20)
        yesterday = today - timedelta(days=1)

        tied_root = tmp / "tied"
        src = _scaffold(tied_root, "src")
        josh = _scaffold(tied_root, "josh")
        bun = _scaffold(tied_root, "bun")
        danielle = _scaffold(tied_root, "danielle")

        _write_patterns(src, {
            "promoted": ["a", "b"],
            "blocker_patterns": [{"task": "x", "pattern": "unresolved-blocker"}],
            "brief_guidance": "",
        })
        _write_patterns(josh, {
            "promoted": ["c"],
            "blocker_patterns": [{"task": "y", "pattern": "unresolved-blocker"}],
            "brief_guidance": "",
        })
        _write_patterns(bun, {
            "promoted": [],
            "blocker_patterns": [{"task": "z", "pattern": "missing-plan"}],
            "brief_guidance": "",
        })
        _write_patterns(danielle, {
            "promoted": [],
            "blocker_patterns": [{"task": "w", "pattern": "missing-plan"}],
            "brief_guidance": "",
        })
        _write_task(src, "planned", "t1", {"failure_modes":
            ["interleave_corruption", "parallel_shift_writer_race"]})
        _write_task(src, "planned", "t2", {"failure_modes": ["interleave_corruption"]})
        _write_task(josh, "planned", "t3", {"failure_modes":
            ["interleave_corruption", "parallel_shift_writer_race"]})
        _write_task(bun, "planned", "t4", {"failure_modes":
            ["parallel_shift_writer_race"]})

        tied_tenants = [
            ("src", src), ("josh", josh), ("bun", bun), ("danielle", danielle),
        ]
        tied_patterns_dir = tied_root / "patterns"
        patterns_aggregate(tied_tenants, tied_patterns_dir, date=yesterday.isoformat())

        s_tied = load_yesterday_aggregate(tied_patterns_dir, today=today)
        expect(
            "[1] yesterday file found (no fallback)",
            s_tied.used_fallback is False
            and s_tied.aggregate_date == yesterday,
            f"used_fallback={s_tied.used_fallback} agg_date={s_tied.aggregate_date}",
        )
        expect(
            "[2] tied failure_modes surface both members alphabetically",
            s_tied.top_failure_modes is not None
            and s_tied.top_failure_modes.members
                == ("interleave_corruption", "parallel_shift_writer_race"),
            f"got {s_tied.top_failure_modes.members if s_tied.top_failure_modes else None}",
        )
        expect(
            "[3] tied failure_modes share count=3 each",
            s_tied.top_failure_modes is not None
            and s_tied.top_failure_modes.count == 3,
            f"count={s_tied.top_failure_modes.count if s_tied.top_failure_modes else None}",
        )
        expect(
            "[4] tied recurring blocker patterns surface both alphabetically",
            s_tied.top_recurring_patterns is not None
            and s_tied.top_recurring_patterns.members
                == ("missing-plan", "unresolved-blocker"),
            f"got {s_tied.top_recurring_patterns.members if s_tied.top_recurring_patterns else None}",
        )

        md_tied = summarize_for_brief(s_tied)
        expect(
            "[5] tied brief mentions both top failure-mode classes + 'tied' label",
            "tied at 3 occurrences each" in md_tied
            and "interleave_corruption" in md_tied
            and "parallel_shift_writer_race" in md_tied,
            "tied surfacing wrong",
        )
        expect(
            "[6] tied brief mentions both recurring patterns",
            "missing-plan" in md_tied and "unresolved-blocker" in md_tied
            and "tied across 2 tenants each" in md_tied,
            "recurring tie surfacing wrong",
        )

        empty_root = tmp / "empty"
        solo = _scaffold(empty_root, "solo")
        _write_patterns(solo, {"promoted": [], "blocker_patterns": [], "brief_guidance": ""})
        empty_patterns_dir = empty_root / "patterns"
        patterns_aggregate([("solo", solo)], empty_patterns_dir, date=yesterday.isoformat())
        s_empty = load_yesterday_aggregate(empty_patterns_dir, today=today)
        md_empty = summarize_for_brief(s_empty)
        expect(
            "[7] empty cycle yields reviewer nudge",
            "rarely accurate" in md_empty
            and s_empty.top_failure_modes is None
            and s_empty.top_recurring_patterns is None,
            f"got summary={s_empty} md={md_empty!r}",
        )
        expect(
            "[8] empty cycle still reports 0 promoted, 1 tenant",
            "0 tasks promoted" in md_empty and "1 tenant" in md_empty,
            f"got md={md_empty!r}",
        )

        empty_dir = tmp / "noaggregates"
        empty_dir.mkdir()
        s_missing = load_yesterday_aggregate(empty_dir, today=today)
        md_missing = summarize_for_brief(s_missing)
        expect(
            "[9] no-aggregates dir yields explicit fallback message",
            s_missing.aggregate_path is None
            and "did not produce a file" in md_missing,
            f"got md={md_missing!r}",
        )

        fallback_dir = tmp / "fallback"
        fallback_dir.mkdir()
        old_date = yesterday - timedelta(days=4)
        patterns_aggregate(tied_tenants, fallback_dir, date=old_date.isoformat())
        s_fb = load_yesterday_aggregate(fallback_dir, today=today)
        md_fb = summarize_for_brief(s_fb)
        expect(
            "[10] yesterday absent → fallback to most recent older aggregate",
            s_fb.used_fallback is True
            and s_fb.aggregate_date == old_date
            and s_fb.staleness_days == (today - old_date).days,
            f"got used_fallback={s_fb.used_fallback} date={s_fb.aggregate_date} stale={s_fb.staleness_days}",
        )
        expect(
            "[11] fallback brief includes 'falling back' warning",
            "falling back" in md_fb or "showing most recent" in md_fb,
            f"got md={md_fb!r}",
        )

        garbage_dir = tmp / "garbage"
        garbage_dir.mkdir()
        (garbage_dir / f"{yesterday.isoformat()}-aggregate.md").write_text(
            "this is not valid frontmatter\n\nrandom text\n"
        )
        s_garbage = load_yesterday_aggregate(garbage_dir, today=today)
        md_garbage = summarize_for_brief(s_garbage)
        expect(
            "[12] malformed aggregate doesn't crash; renders zero-count block",
            s_garbage.tenants_reporting == 0
            and s_garbage.total_promoted == 0
            and s_garbage.top_failure_modes is None
            and "Yesterday's task-system patterns" in md_garbage,
            f"got summary={s_garbage}",
        )

        gathered = gather_patterns_aggregate(tied_patterns_dir, today=today)
        expect(
            "[13] gather_patterns_aggregate returns same as summarize+load",
            "interleave_corruption" in gathered
            and "Yesterday's task-system patterns" in gathered,
            "one-call helper wrong",
        )

        no_recur_root = tmp / "norecur"
        ws_only = _scaffold(no_recur_root, "solo2")
        _write_patterns(ws_only, {
            "promoted": ["a"],
            "blocker_patterns": [{"task": "x", "pattern": "unique-pattern"}],
            "brief_guidance": "",
        })
        _write_task(ws_only, "planned", "t", {"failure_modes": ["transition_illegal"]})
        no_recur_dir = no_recur_root / "patterns"
        patterns_aggregate([("solo2", ws_only)], no_recur_dir, date=yesterday.isoformat())
        s_nr = load_yesterday_aggregate(no_recur_dir, today=today)
        md_nr = summarize_for_brief(s_nr)
        expect(
            "[14] no-recurring-pattern case mentions 'no single pattern in ≥2 tenants'",
            "no single pattern in ≥2 tenants" in md_nr
            and "transition_illegal" in md_nr,
            f"got md={md_nr!r}",
        )

        print()
        print(f"aggregate_summarizer: {passes}/{passes + len(fails)} assertions PASS")
        if fails:
            for f in fails:
                print(f"  FAIL :: {f}")
            return 1
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
