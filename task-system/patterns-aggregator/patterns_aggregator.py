"""
patterns_aggregator — roll per-tenant patterns.json files into a daily
cross-tenant aggregate markdown for the morning brief reader.

Inputs per tenant workspace:
  tasks/patterns.json                              (bun-desktop seam-C output)
  tasks/<state>/<task-id>/task.json                (all states, for failure_modes)

Output:
  <output_dir>/<YYYY-MM-DD>-aggregate.md

Plan-time failure_modes (task.json.failure_modes) are counted in v0.3 per
v0.2 spec amendment Rule 9. Postmortem failure_modes (state_history.notes,
schema not yet ratified) are reserved for v0.4 once the schema lands.

Author: src-desktop@mesh
Spec:   v0.2 spec amendment Rule 9 + seam-C patterns.json schema
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

STATE_DIRS = (
    "intake", "shop-floor", "planned", "scheduled",
    "today", "in-flight", "parked", "done",
)


@dataclass
class TenantRollup:
    tenant: str
    workspace: Path
    promoted: list[str] = field(default_factory=list)
    blocker_patterns: list[dict] = field(default_factory=list)
    brief_guidance: str | None = None
    failure_modes: Counter = field(default_factory=Counter)
    failure_mode_tasks: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    task_counts_by_state: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def promoted_count(self) -> int:
        return len(self.promoted)


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _walk_task_jsons(workspace: Path) -> Iterable[tuple[str, str, dict]]:
    """Yield (state, task_id, task_record) for every task.json under tasks/."""
    tasks_root = workspace / "tasks"
    if not tasks_root.exists():
        return
    for state in STATE_DIRS:
        state_dir = tasks_root / state
        if not state_dir.is_dir():
            continue
        for task_dir in state_dir.iterdir():
            if not task_dir.is_dir():
                continue
            record = _read_json(task_dir / "task.json")
            if record is None:
                continue
            yield state, task_dir.name, record


def rollup_tenant(tenant: str, workspace: Path) -> TenantRollup:
    rollup = TenantRollup(tenant=tenant, workspace=workspace)
    workspace = Path(workspace)

    pj = _read_json(workspace / "tasks" / "patterns.json")
    if pj is not None:
        rollup.promoted = list(pj.get("promoted", []))
        rollup.blocker_patterns = list(pj.get("blocker_patterns", []))
        rollup.brief_guidance = pj.get("brief_guidance")
    else:
        rollup.errors.append("tasks/patterns.json absent or unparseable")

    state_counter: Counter = Counter()
    for state, task_id, record in _walk_task_jsons(workspace):
        state_counter[state] += 1
        for fm in record.get("failure_modes") or []:
            if not isinstance(fm, str):
                rollup.errors.append(f"non-string failure_mode in {task_id}: {fm!r}")
                continue
            rollup.failure_modes[fm] += 1
            rollup.failure_mode_tasks[fm].append(task_id)
    rollup.task_counts_by_state = dict(state_counter)
    return rollup


@dataclass
class CrossTenantAggregate:
    date: str
    generated_at: str
    tenants: list[TenantRollup]
    total_promoted: int
    total_blocker_patterns: int
    failure_modes: Counter
    failure_mode_tenants: dict[str, set[str]]
    blocker_pattern_tenants: dict[str, set[str]]


def aggregate_rollups(
    rollups: list[TenantRollup],
    date: str,
) -> CrossTenantAggregate:
    fm_totals: Counter = Counter()
    fm_tenants: dict[str, set[str]] = defaultdict(set)
    bp_tenants: dict[str, set[str]] = defaultdict(set)
    total_promoted = 0
    total_blockers = 0

    for r in rollups:
        total_promoted += r.promoted_count
        total_blockers += len(r.blocker_patterns)
        for fm, count in r.failure_modes.items():
            fm_totals[fm] += count
            fm_tenants[fm].add(r.tenant)
        for bp in r.blocker_patterns:
            key = bp.get("pattern") if isinstance(bp, dict) else None
            if key:
                bp_tenants[key].add(r.tenant)

    return CrossTenantAggregate(
        date=date,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        tenants=rollups,
        total_promoted=total_promoted,
        total_blocker_patterns=total_blockers,
        failure_modes=fm_totals,
        failure_mode_tenants={k: set(v) for k, v in fm_tenants.items()},
        blocker_pattern_tenants={k: set(v) for k, v in bp_tenants.items()},
    )


def render_markdown(agg: CrossTenantAggregate) -> str:
    out: list[str] = []
    out.append("---")
    out.append(f"date: {agg.date}")
    out.append(f"generated_at: {agg.generated_at}")
    out.append(f"tenants_reporting: {len(agg.tenants)}")
    out.append(f"total_promoted: {agg.total_promoted}")
    out.append(f"total_blocker_patterns: {agg.total_blocker_patterns}")
    out.append(f"distinct_failure_modes: {len(agg.failure_modes)}")
    out.append("source: src-desktop@mesh patterns_aggregator (v0.3 spec ref: v0.2 amendment Rule 9)")
    out.append("---")
    out.append("")
    out.append(f"# Patterns aggregate — {agg.date}")
    out.append("")

    out.append("## Cross-tenant rollup")
    out.append("")
    out.append(f"- Tenants reporting: **{len(agg.tenants)}**")
    out.append(f"- Total promoted (shop-floor → planned): **{agg.total_promoted}**")
    out.append(f"- Open blocker patterns across tenants: **{agg.total_blocker_patterns}**")
    out.append(f"- Distinct failure_modes seen (plan-time): **{len(agg.failure_modes)}**")
    out.append("")

    if agg.failure_modes:
        out.append("## Failure modes — plan-time counts (all tenants)")
        out.append("")
        out.append("Per v0.2 spec amendment Rule 9: high counts here = the class to invest defense tooling in.")
        out.append("")
        out.append("| Enum value | Total | Tenants |")
        out.append("|---|---|---|")
        for fm, count in agg.failure_modes.most_common():
            tenants = sorted(agg.failure_mode_tenants.get(fm, set()))
            out.append(f"| `{fm}` | {count} | {', '.join(tenants) if tenants else '—'} |")
        out.append("")
    else:
        out.append("## Failure modes — plan-time counts (all tenants)")
        out.append("")
        out.append("_No plan-time `failure_modes` entries seen this cycle. Recommend reviewers push back: `failure_modes: []` is rarely accurate._")
        out.append("")

    if agg.blocker_pattern_tenants:
        out.append("## Blocker patterns appearing in ≥2 tenants")
        out.append("")
        out.append("Recurring patterns = skill or workflow gaps to close.")
        out.append("")
        out.append("| Pattern | Tenants |")
        out.append("|---|---|")
        any_multi = False
        for pat, tenants in sorted(
            agg.blocker_pattern_tenants.items(),
            key=lambda kv: (-len(kv[1]), kv[0]),
        ):
            if len(tenants) >= 2:
                any_multi = True
                out.append(f"| `{pat}` | {', '.join(sorted(tenants))} |")
        if not any_multi:
            out.append("| _(no cross-tenant blocker pattern repeats)_ | — |")
        out.append("")

    out.append("## Per-tenant detail")
    out.append("")
    for r in agg.tenants:
        out.append(f"### {r.tenant}")
        out.append("")
        out.append(f"- Workspace: `{r.workspace}`")
        out.append(f"- Promoted ({r.promoted_count}): "
                   + (", ".join(f"`{p}`" for p in r.promoted) if r.promoted else "_none_"))
        if r.task_counts_by_state:
            counts_str = ", ".join(
                f"{state}={r.task_counts_by_state.get(state, 0)}"
                for state in STATE_DIRS
                if r.task_counts_by_state.get(state, 0) > 0
            )
            out.append(f"- Task counts by state: {counts_str or '_no tasks_'}")
        if r.failure_modes:
            top = r.failure_modes.most_common(5)
            top_str = ", ".join(f"`{fm}`×{n}" for fm, n in top)
            out.append(f"- Top failure_modes (plan-time): {top_str}")
        if r.blocker_patterns:
            out.append(f"- Blocker patterns ({len(r.blocker_patterns)}):")
            for bp in r.blocker_patterns:
                if not isinstance(bp, dict):
                    continue
                task = bp.get("task", "?")
                pattern = bp.get("pattern", "?")
                hint = bp.get("hint") or bp.get("action") or ""
                out.append(f"  - `{task}` — `{pattern}`" + (f" — {hint}" if hint else ""))
        if r.brief_guidance:
            out.append(f"- Brief guidance: _{r.brief_guidance}_")
        if r.errors:
            out.append(f"- Errors: {'; '.join(r.errors)}")
        out.append("")

    out.append("## Brief guidance")
    out.append("")
    if agg.failure_modes:
        top_fm, top_count = agg.failure_modes.most_common(1)[0]
        tenants_with_top = sorted(agg.failure_mode_tenants.get(top_fm, set()))
        out.append(
            f"Top class to invest defense tooling in: **`{top_fm}`** "
            f"({top_count} occurrences across {len(tenants_with_top)} tenants — "
            f"{', '.join(tenants_with_top)})."
        )
        out.append("")
    if agg.blocker_pattern_tenants:
        multi = [
            (pat, t) for pat, t in agg.blocker_pattern_tenants.items() if len(t) >= 2
        ]
        if multi:
            multi.sort(key=lambda kv: (-len(kv[1]), kv[0]))
            top_pat, top_t = multi[0]
            out.append(
                f"Recurring blocker pattern across tenants: **`{top_pat}`** "
                f"({len(top_t)} tenants — {', '.join(sorted(top_t))}). "
                f"Treat as a workflow-gap signal."
            )
            out.append("")
    if not agg.failure_modes and not agg.blocker_pattern_tenants:
        out.append("_No cross-tenant signals to surface this cycle._")
        out.append("")

    return "\n".join(out) + "\n"


def aggregate(
    tenants: list[tuple[str, Path]],
    output_dir: Path,
    date: str | None = None,
) -> Path:
    """End-to-end: rollup → aggregate → render → write. Returns output path."""
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rollups = [rollup_tenant(t, Path(w)) for t, w in tenants]
    agg = aggregate_rollups(rollups, date)
    md = render_markdown(agg)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{date}-aggregate.md"
    tmp = out_path.with_suffix(".md.tmp")
    tmp.write_text(md)
    tmp.replace(out_path)
    return out_path


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Roll per-tenant patterns into daily aggregate.")
    p.add_argument(
        "--tenant", "-t", action="append", metavar="NAME=PATH", default=[],
        help="Tenant workspace mapping. Repeat per tenant. e.g. -t src=/mnt/clients/src/openclaw/workspace",
    )
    p.add_argument(
        "--output-dir", "-o", required=True,
        help="Output directory for <date>-aggregate.md",
    )
    p.add_argument("--date", help="YYYY-MM-DD override (default: today UTC)")
    args = p.parse_args(argv)

    tenants: list[tuple[str, Path]] = []
    for spec in args.tenant:
        if "=" not in spec:
            print(f"refusing malformed --tenant {spec!r}; expected NAME=PATH")
            return 2
        name, path = spec.split("=", 1)
        tenants.append((name, Path(path)))

    out = aggregate(tenants, Path(args.output_dir), args.date)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
