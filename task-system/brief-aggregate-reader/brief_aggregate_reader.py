"""
brief_aggregate_reader — adapt patterns_aggregator output into a plain-English
block that the morning brief reader surfaces to Mike.

Contract:
  patterns_aggregator writes /mesh/BLACKBOARD/task-system/patterns/<date>-aggregate.md
  daily at 06:05 UTC. This module finds the latest aggregate, parses its
  frontmatter + key sections, and formats a short summary block for the brief.

Glob-based latest discovery (NOT "yesterday-by-calendar"): if the cron skipped
a day, the brief still finds the most recent aggregate and warns about
staleness rather than 404-ing silently. `silent_drift` defense.

Author: src-desktop@mesh
Spec:   v0.2 spec amendment Rule 9 (consumer side)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

AGGREGATE_GLOB = "*-aggregate.md"
AGGREGATE_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-aggregate\.md$")


@dataclass(frozen=True)
class BriefAggregateBlock:
    aggregate_path: Path | None
    aggregate_date: date | None
    staleness_days: int
    tenants_reporting: int
    total_promoted: int
    total_blocker_patterns: int
    distinct_failure_modes: int
    top_failure_mode: str | None
    top_failure_mode_count: int
    top_failure_mode_tenants: list[str]
    top_recurring_pattern: str | None
    top_recurring_pattern_tenants: list[str]
    raw_brief_guidance_lines: list[str]
    warnings: list[str]


def _parse_frontmatter(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not text.startswith("---"):
        return out
    end = text.find("\n---", 4)
    if end == -1:
        return out
    block = text[4:end]
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def _int_from_frontmatter(fm: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(fm.get(key, default))
    except (TypeError, ValueError):
        return default


def _parse_top_failure_mode_table(text: str) -> tuple[str | None, int, list[str]]:
    """Read the first data row of the 'Failure modes — plan-time counts' table."""
    section = "## Failure modes — plan-time counts"
    idx = text.find(section)
    if idx == -1:
        return None, 0, []
    rest = text[idx:]
    next_section = rest.find("\n## ", 1)
    if next_section != -1:
        rest = rest[:next_section]
    rows = []
    for line in rest.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if stripped.startswith("|---") or stripped.startswith("| ---"):
            continue
        if "Enum value" in stripped and "Total" in stripped:
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        rows.append(cells)
    if not rows:
        return None, 0, []
    enum_cell, count_cell, tenants_cell = rows[0][0], rows[0][1], rows[0][2]
    enum = enum_cell.strip("`")
    try:
        count = int(count_cell)
    except ValueError:
        count = 0
    tenants = [t.strip() for t in tenants_cell.split(",") if t.strip() and t.strip() != "—"]
    return enum, count, tenants


def _parse_top_recurring_pattern(text: str) -> tuple[str | None, list[str]]:
    """Read the first data row of the 'Blocker patterns appearing in ≥2 tenants' table."""
    section = "## Blocker patterns appearing in"
    idx = text.find(section)
    if idx == -1:
        return None, []
    rest = text[idx:]
    next_section = rest.find("\n## ", 1)
    if next_section != -1:
        rest = rest[:next_section]
    for line in rest.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if stripped.startswith("|---") or stripped.startswith("| ---"):
            continue
        if "Pattern" in stripped and "Tenants" in stripped:
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        pattern_cell, tenants_cell = cells[0], cells[1]
        if "_(no cross-tenant" in pattern_cell:
            return None, []
        pat = pattern_cell.strip("`")
        tenants = [t.strip() for t in tenants_cell.split(",") if t.strip() and t.strip() != "—"]
        return pat, tenants
    return None, []


def _parse_brief_guidance_lines(text: str) -> list[str]:
    idx = text.find("## Brief guidance")
    if idx == -1:
        return []
    rest = text[idx + len("## Brief guidance"):].strip()
    lines: list[str] = []
    for line in rest.splitlines():
        if line.startswith("## "):
            break
        if line.strip():
            lines.append(line.strip())
    return lines


def find_latest_aggregate(patterns_dir: Path) -> Path | None:
    """Return the most recent <YYYY-MM-DD>-aggregate.md, or None if directory empty/missing."""
    patterns_dir = Path(patterns_dir)
    if not patterns_dir.is_dir():
        return None
    candidates = []
    for p in patterns_dir.glob(AGGREGATE_GLOB):
        m = AGGREGATE_NAME_RE.match(p.name)
        if m:
            candidates.append((m.group(1), p))
    if not candidates:
        return None
    candidates.sort(key=lambda kv: kv[0], reverse=True)
    return candidates[0][1]


def read_aggregate(
    path: Path | None,
    today: date | None = None,
    stale_warn_days: int = 2,
) -> BriefAggregateBlock:
    """Parse an aggregate file into a BriefAggregateBlock. Handles missing/empty input."""
    today = today or datetime.now(timezone.utc).date()
    warnings: list[str] = []

    if path is None:
        return BriefAggregateBlock(
            aggregate_path=None,
            aggregate_date=None,
            staleness_days=-1,
            tenants_reporting=0,
            total_promoted=0,
            total_blocker_patterns=0,
            distinct_failure_modes=0,
            top_failure_mode=None,
            top_failure_mode_count=0,
            top_failure_mode_tenants=[],
            top_recurring_pattern=None,
            top_recurring_pattern_tenants=[],
            raw_brief_guidance_lines=[],
            warnings=["no patterns aggregate found — daily cron may not have run"],
        )

    text = path.read_text()
    fm = _parse_frontmatter(text)

    name_match = AGGREGATE_NAME_RE.match(path.name)
    agg_date: date | None = None
    if name_match:
        try:
            agg_date = date.fromisoformat(name_match.group(1))
        except ValueError:
            agg_date = None

    staleness = (today - agg_date).days if agg_date else -1
    if agg_date is None:
        warnings.append(f"could not parse date from filename {path.name!r}")
    elif staleness > stale_warn_days:
        warnings.append(
            f"latest aggregate is {staleness} days old "
            f"({agg_date.isoformat()}) — patterns cron may be failing"
        )

    top_fm, top_fm_count, top_fm_tenants = _parse_top_failure_mode_table(text)
    top_pat, top_pat_tenants = _parse_top_recurring_pattern(text)
    guidance_lines = _parse_brief_guidance_lines(text)

    return BriefAggregateBlock(
        aggregate_path=path,
        aggregate_date=agg_date,
        staleness_days=staleness,
        tenants_reporting=_int_from_frontmatter(fm, "tenants_reporting"),
        total_promoted=_int_from_frontmatter(fm, "total_promoted"),
        total_blocker_patterns=_int_from_frontmatter(fm, "total_blocker_patterns"),
        distinct_failure_modes=_int_from_frontmatter(fm, "distinct_failure_modes"),
        top_failure_mode=top_fm,
        top_failure_mode_count=top_fm_count,
        top_failure_mode_tenants=top_fm_tenants,
        top_recurring_pattern=top_pat,
        top_recurring_pattern_tenants=top_pat_tenants,
        raw_brief_guidance_lines=guidance_lines,
        warnings=warnings,
    )


def format_for_brief(block: BriefAggregateBlock) -> str:
    """Plain-English block for Mike's morning brief. Always returns a non-empty string."""
    lines: list[str] = []
    lines.append("### Yesterday's task-system patterns")

    if block.aggregate_path is None:
        lines.append("")
        lines.append("- No patterns aggregate available. The overnight aggregator did not produce a file — check the patterns cron and bun's per-tenant check-and-promote runs.")
        return "\n".join(lines) + "\n"

    if block.staleness_days > 0:
        lines.append("")
        lines.append(
            f"- _Note: latest aggregate is from {block.aggregate_date.isoformat()} "
            f"({block.staleness_days} day{'s' if block.staleness_days != 1 else ''} old). "
            f"Patterns cron may be lagging._"
        )

    lines.append("")
    lines.append(
        f"- **{block.total_promoted} task{'s' if block.total_promoted != 1 else ''} "
        f"promoted to planned** overnight across "
        f"{block.tenants_reporting} tenant{'s' if block.tenants_reporting != 1 else ''}."
    )

    if block.top_failure_mode and block.top_failure_mode_count > 0:
        tenants = ", ".join(block.top_failure_mode_tenants) or "—"
        lines.append(
            f"- **Top failure-mode class to invest defense tooling in:** "
            f"`{block.top_failure_mode}` "
            f"({block.top_failure_mode_count} occurrence"
            f"{'s' if block.top_failure_mode_count != 1 else ''} "
            f"across {tenants})."
        )
    else:
        lines.append(
            "- No plan-time `failure_modes` recorded across tenants. "
            "Reviewers should push back: empty failure_modes is rarely accurate."
        )

    if block.top_recurring_pattern:
        tenants = ", ".join(block.top_recurring_pattern_tenants) or "—"
        lines.append(
            f"- **Recurring blocker pattern across tenants:** "
            f"`{block.top_recurring_pattern}` "
            f"({len(block.top_recurring_pattern_tenants)} tenant"
            f"{'s' if len(block.top_recurring_pattern_tenants) != 1 else ''}: "
            f"{tenants}). Treat as a workflow-gap signal."
        )

    if block.total_blocker_patterns > 0 and not block.top_recurring_pattern:
        lines.append(
            f"- {block.total_blocker_patterns} open blocker pattern"
            f"{'s' if block.total_blocker_patterns != 1 else ''} across tenants — "
            f"no single pattern in ≥2 tenants this cycle."
        )

    if block.warnings:
        lines.append("")
        for w in block.warnings:
            lines.append(f"- _Warning: {w}._")

    lines.append("")
    lines.append(f"_Source: `{block.aggregate_path}`_")
    return "\n".join(lines) + "\n"


def render_for_brief(
    patterns_dir: Path,
    today: date | None = None,
) -> str:
    """One-call helper for the morning brief reader."""
    path = find_latest_aggregate(Path(patterns_dir))
    block = read_aggregate(path, today=today)
    return format_for_brief(block)


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        description="Render the patterns-aggregate brief block. Prints to stdout.",
    )
    p.add_argument(
        "--patterns-dir", "-p",
        default="/mesh/BLACKBOARD/task-system/patterns",
        help="Directory containing <date>-aggregate.md files",
    )
    p.add_argument("--today", help="YYYY-MM-DD override (for testing)")
    args = p.parse_args(argv)
    today: date | None = None
    if args.today:
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            print(f"invalid --today {args.today!r}; expected YYYY-MM-DD")
            return 2
    print(render_for_brief(Path(args.patterns_dir), today=today), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
