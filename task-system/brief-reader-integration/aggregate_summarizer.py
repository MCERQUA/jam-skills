"""
aggregate_summarizer — read /mesh/BLACKBOARD/task-system/patterns/<date>-aggregate.md
and render a plain-English block for Mike's morning brief.

Primary entrypoint:
    gather_patterns_aggregate(patterns_dir, today) -> str

Returns markdown ready to inject into the brief between the reflection section
and the open-tasks section. Always non-empty; missing/stale/malformed inputs
produce a clear fallback or warning.

Ties: when ≥2 failure modes or ≥2 blocker patterns share the top count,
this module surfaces ALL tied entries (alphabetical for run-to-run stability).
This is intentionally different from picking one — the daily-improvement loop
needs to see "the system has multiple equally-frequent failure classes" rather
than a flickering single winner.

Author: src-desktop@mesh
Spec:   v0.2 spec amendment Rule 9 — consumer-side render contract
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

AGGREGATE_GLOB = "*-aggregate.md"
AGGREGATE_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-aggregate\.md$")
DEFAULT_STALE_WARN_DAYS = 2


@dataclass(frozen=True)
class TopGroup:
    """A set of entries tied for the top count. Members always sorted alphabetically."""
    count: int
    members: tuple[str, ...]
    tenants_by_member: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def is_tie(self) -> bool:
        return len(self.members) > 1


@dataclass(frozen=True)
class AggregateSummary:
    aggregate_path: Path | None
    aggregate_date: date | None
    requested_date: date
    staleness_days: int
    used_fallback: bool
    tenants_reporting: int
    total_promoted: int
    total_blocker_patterns: int
    distinct_failure_modes: int
    top_failure_modes: TopGroup | None
    top_recurring_patterns: TopGroup | None
    warnings: tuple[str, ...]


def _parse_frontmatter(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not text.startswith("---"):
        return out
    end = text.find("\n---", 4)
    if end == -1:
        return out
    for line in text[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def _int_fm(fm: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(fm.get(key, default))
    except (TypeError, ValueError):
        return default


def _section(text: str, header_prefix: str) -> str:
    idx = text.find(header_prefix)
    if idx == -1:
        return ""
    rest = text[idx:]
    nxt = rest.find("\n## ", 1)
    return rest[:nxt] if nxt != -1 else rest


def _table_rows(section_text: str, header_must_contain: tuple[str, ...]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if stripped.startswith("|---") or stripped.startswith("| ---"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        if all(any(h in c for h in header_must_contain) for c in cells[:1]):
            continue
        if any(c == "_(no cross-tenant blocker pattern repeats)_" for c in cells):
            continue
        rows.append(cells)
    return rows


def _parse_top_failure_modes(text: str) -> TopGroup | None:
    section = _section(text, "## Failure modes — plan-time counts")
    if not section:
        return None
    rows = _table_rows(section, header_must_contain=("Enum value",))
    if not rows:
        return None
    parsed: list[tuple[str, int, tuple[str, ...]]] = []
    for cells in rows:
        if len(cells) < 3:
            continue
        enum = cells[0].strip("`").strip()
        try:
            count = int(cells[1])
        except ValueError:
            continue
        tenants = tuple(
            t.strip() for t in cells[2].split(",")
            if t.strip() and t.strip() != "—"
        )
        if not enum:
            continue
        parsed.append((enum, count, tenants))
    if not parsed:
        return None
    top_count = max(p[1] for p in parsed)
    if top_count == 0:
        return None
    tied = [(e, t) for (e, c, t) in parsed if c == top_count]
    tied.sort(key=lambda kv: kv[0])
    members = tuple(e for e, _ in tied)
    tenants_by = {e: t for e, t in tied}
    return TopGroup(count=top_count, members=members, tenants_by_member=tenants_by)


def _parse_top_recurring_patterns(text: str) -> TopGroup | None:
    section = _section(text, "## Blocker patterns appearing in")
    if not section:
        return None
    rows = _table_rows(section, header_must_contain=("Pattern",))
    if not rows:
        return None
    parsed: list[tuple[str, tuple[str, ...]]] = []
    for cells in rows:
        if len(cells) < 2:
            continue
        pat = cells[0].strip("`").strip()
        if not pat or "(no cross-tenant" in pat:
            continue
        tenants = tuple(
            t.strip() for t in cells[1].split(",")
            if t.strip() and t.strip() != "—"
        )
        if not tenants:
            continue
        parsed.append((pat, tenants))
    if not parsed:
        return None
    top_count = max(len(t) for _, t in parsed)
    if top_count < 2:
        return None
    tied = [(p, t) for p, t in parsed if len(t) == top_count]
    tied.sort(key=lambda kv: kv[0])
    members = tuple(p for p, _ in tied)
    tenants_by = {p: t for p, t in tied}
    return TopGroup(count=top_count, members=members, tenants_by_member=tenants_by)


def _candidate_for_date(patterns_dir: Path, d: date) -> Path | None:
    p = patterns_dir / f"{d.isoformat()}-aggregate.md"
    return p if p.is_file() else None


def _find_latest_aggregate(patterns_dir: Path) -> Path | None:
    if not patterns_dir.is_dir():
        return None
    candidates: list[tuple[str, Path]] = []
    for p in patterns_dir.glob(AGGREGATE_GLOB):
        m = AGGREGATE_NAME_RE.match(p.name)
        if m:
            candidates.append((m.group(1), p))
    if not candidates:
        return None
    candidates.sort(key=lambda kv: kv[0], reverse=True)
    return candidates[0][1]


def _parse_aggregate(
    path: Path | None,
    requested: date,
    today: date,
    used_fallback: bool,
    fallback_warning: str | None,
) -> AggregateSummary:
    warnings: list[str] = []
    if fallback_warning:
        warnings.append(fallback_warning)

    if path is None:
        return AggregateSummary(
            aggregate_path=None,
            aggregate_date=None,
            requested_date=requested,
            staleness_days=-1,
            used_fallback=used_fallback,
            tenants_reporting=0,
            total_promoted=0,
            total_blocker_patterns=0,
            distinct_failure_modes=0,
            top_failure_modes=None,
            top_recurring_patterns=None,
            warnings=tuple(warnings + ["no patterns aggregate found — daily cron may not have run"]),
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
    if agg_date is None:
        warnings.append(f"could not parse date from filename {path.name!r}")

    staleness = (today - agg_date).days if agg_date else -1
    if agg_date and staleness > DEFAULT_STALE_WARN_DAYS:
        warnings.append(
            f"latest aggregate is {staleness} days old "
            f"({agg_date.isoformat()}) — patterns cron may be failing"
        )

    return AggregateSummary(
        aggregate_path=path,
        aggregate_date=agg_date,
        requested_date=requested,
        staleness_days=staleness,
        used_fallback=used_fallback,
        tenants_reporting=_int_fm(fm, "tenants_reporting"),
        total_promoted=_int_fm(fm, "total_promoted"),
        total_blocker_patterns=_int_fm(fm, "total_blocker_patterns"),
        distinct_failure_modes=_int_fm(fm, "distinct_failure_modes"),
        top_failure_modes=_parse_top_failure_modes(text),
        top_recurring_patterns=_parse_top_recurring_patterns(text),
        warnings=tuple(warnings),
    )


def load_yesterday_aggregate(
    patterns_dir: Path,
    today: date | None = None,
) -> AggregateSummary:
    """Load yesterday's aggregate. Fall back to most recent if yesterday absent."""
    today = today or datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    patterns_dir = Path(patterns_dir)

    direct = _candidate_for_date(patterns_dir, yesterday)
    if direct is not None:
        return _parse_aggregate(direct, yesterday, today, used_fallback=False, fallback_warning=None)

    fallback = _find_latest_aggregate(patterns_dir)
    if fallback is None:
        return _parse_aggregate(
            None, yesterday, today,
            used_fallback=False,
            fallback_warning=None,
        )
    return _parse_aggregate(
        fallback, yesterday, today,
        used_fallback=True,
        fallback_warning=(
            f"yesterday's aggregate ({yesterday.isoformat()}) absent; "
            f"falling back to most recent aggregate"
        ),
    )


def _format_member_with_tenants(
    member: str,
    tenants: tuple[str, ...],
) -> str:
    if tenants:
        return f"`{member}` (across {', '.join(tenants)})"
    return f"`{member}`"


def _format_top_failure_modes(group: TopGroup) -> str:
    s = "s" if group.count != 1 else ""
    if group.is_tie:
        parts = [
            _format_member_with_tenants(m, group.tenants_by_member.get(m, ()))
            for m in group.members
        ]
        joined = "; ".join(parts)
        return (
            f"- **Top failure-mode classes (tied at {group.count} occurrence{s} each):** "
            f"{joined}. Invest defense tooling on whichever lands a same-week recurrence first."
        )
    member = group.members[0]
    tenants = group.tenants_by_member.get(member, ())
    tenant_str = f"across {', '.join(tenants)}" if tenants else "across no tenant data"
    return (
        f"- **Top failure-mode class to invest defense tooling in:** "
        f"`{member}` ({group.count} occurrence{s} {tenant_str})."
    )


def _format_top_recurring_patterns(group: TopGroup) -> str:
    t = "s" if group.count != 1 else ""
    if group.is_tie:
        parts = []
        for m in group.members:
            tenants = group.tenants_by_member.get(m, ())
            parts.append(f"`{m}` ({', '.join(tenants) or '—'})")
        joined = "; ".join(parts)
        return (
            f"- **Recurring blocker patterns (tied across {group.count} tenant{t} each):** "
            f"{joined}. Treat each as a workflow-gap signal."
        )
    member = group.members[0]
    tenants = group.tenants_by_member.get(member, ())
    return (
        f"- **Recurring blocker pattern across tenants:** "
        f"`{member}` ({group.count} tenant{t}: {', '.join(tenants) or '—'}). "
        f"Treat as a workflow-gap signal."
    )


def summarize_for_brief(summary: AggregateSummary) -> str:
    """Render the plain-English markdown block for Mike's morning brief."""
    lines: list[str] = ["### Yesterday's task-system patterns"]

    if summary.aggregate_path is None:
        lines.append("")
        lines.append(
            "- No patterns aggregate available. The overnight aggregator did not "
            "produce a file — check the patterns cron and bun's per-tenant "
            "check-and-promote runs."
        )
        return "\n".join(lines) + "\n"

    if summary.used_fallback and summary.aggregate_date:
        lines.append("")
        lines.append(
            f"- _Note: yesterday's aggregate "
            f"({summary.requested_date.isoformat()}) absent; "
            f"showing most recent ({summary.aggregate_date.isoformat()}, "
            f"{summary.staleness_days} day"
            f"{'s' if summary.staleness_days != 1 else ''} old)._"
        )
    elif summary.staleness_days > DEFAULT_STALE_WARN_DAYS:
        lines.append("")
        lines.append(
            f"- _Note: aggregate is {summary.staleness_days} days old "
            f"({summary.aggregate_date.isoformat() if summary.aggregate_date else 'unknown date'}). "
            f"Patterns cron may be lagging._"
        )

    lines.append("")
    promoted_s = "s" if summary.total_promoted != 1 else ""
    tenant_s = "s" if summary.tenants_reporting != 1 else ""
    lines.append(
        f"- **{summary.total_promoted} task{promoted_s} promoted to planned** "
        f"overnight across {summary.tenants_reporting} tenant{tenant_s}."
    )

    if summary.top_failure_modes:
        lines.append(_format_top_failure_modes(summary.top_failure_modes))
    else:
        lines.append(
            "- No plan-time `failure_modes` recorded across tenants. "
            "Reviewers should push back: empty `failure_modes` is rarely accurate."
        )

    if summary.top_recurring_patterns:
        lines.append(_format_top_recurring_patterns(summary.top_recurring_patterns))
    elif summary.total_blocker_patterns > 0:
        lines.append(
            f"- {summary.total_blocker_patterns} open blocker pattern"
            f"{'s' if summary.total_blocker_patterns != 1 else ''} "
            f"across tenants — no single pattern in ≥2 tenants this cycle."
        )

    if summary.warnings:
        lines.append("")
        for w in summary.warnings:
            lines.append(f"- _Warning: {w}._")

    lines.append("")
    lines.append(f"_Source: `{summary.aggregate_path}`_")
    return "\n".join(lines) + "\n"


def gather_patterns_aggregate(
    patterns_dir: str | Path = "/mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns",
    today: date | None = None,
) -> str:
    """One-call entry point for `morning_brief.py`.

    Returns markdown ready to inject between the reflection section and the
    open-tasks section. Always non-empty; brief composer can call without
    try/except.
    """
    summary = load_yesterday_aggregate(Path(patterns_dir), today=today)
    return summarize_for_brief(summary)


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        description="Render the patterns-aggregate brief block. Prints to stdout.",
    )
    p.add_argument(
        "--patterns-dir", "-p",
        default="/mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns",
        help="Directory containing <date>-aggregate.md files",
    )
    p.add_argument("--today", help="YYYY-MM-DD override (for testing the staleness clock)")
    args = p.parse_args(argv)
    today: date | None = None
    if args.today:
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            print(f"invalid --today {args.today!r}; expected YYYY-MM-DD")
            return 2
    print(gather_patterns_aggregate(args.patterns_dir, today=today), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
