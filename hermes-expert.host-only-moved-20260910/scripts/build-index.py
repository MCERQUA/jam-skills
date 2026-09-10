#!/usr/bin/env python3
"""Build /mnt/system/base/skills/hermes-expert/index.json from sections/*.json.

Reads every sections/<id>.json, emits a master index with:
- sections: array of section summaries (id, title, category, file, summary, keywords)
- categories: map of category -> [section ids]
- by_env_var: map of env var -> [section ids that mention it]
- by_cli_command: map of `hermes ...` command -> [section ids]
- by_config_key: map of dotted config path -> [section ids]
- by_slash_command: map of /command -> [section ids]
- by_keyword: map of keyword -> [section ids]

Idempotent; safe to re-run.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/mnt/system/base/skills/hermes-expert")
SECTIONS_DIR = ROOT / "sections"
INDEX_FILE = ROOT / "index.json"


def main() -> int:
    sections: list[dict] = []
    categories: defaultdict[str, list[str]] = defaultdict(list)
    by_env_var: defaultdict[str, set[str]] = defaultdict(set)
    by_cli: defaultdict[str, set[str]] = defaultdict(set)
    by_config: defaultdict[str, set[str]] = defaultdict(set)
    by_slash: defaultdict[str, set[str]] = defaultdict(set)
    by_keyword: defaultdict[str, set[str]] = defaultdict(set)

    files = sorted(SECTIONS_DIR.glob("*.json"))
    for path in files:
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            print(f"ERROR parsing {path}: {exc}", file=sys.stderr)
            return 1

        sid = data.get("id") or path.stem
        title = data.get("title", "")
        category = data.get("category", "")
        subcategory = data.get("subcategory", "")
        summary = data.get("summary", "")
        keywords = data.get("keywords", []) or []
        url = data.get("url", "")
        source_path = data.get("source_path", "")

        sections.append({
            "id": sid,
            "title": title,
            "category": category,
            "subcategory": subcategory,
            "file": f"sections/{path.name}",
            "url": url,
            "source_path": source_path,
            "summary": summary,
            "keywords": keywords[:15],
        })

        cat_key = f"{category}/{subcategory}" if subcategory else category
        categories[cat_key].append(sid)

        for ev in data.get("env_vars") or []:
            name = (ev or {}).get("name", "").strip()
            if name:
                by_env_var[name].add(sid)

        for cmd in data.get("cli_commands") or []:
            c = (cmd or {}).get("command", "").strip()
            if c:
                by_cli[c].add(sid)

        for cfg in data.get("config_keys") or []:
            p = (cfg or {}).get("path", "").strip()
            if p:
                by_config[p].add(sid)

        for sc in data.get("slash_commands") or []:
            s = (sc or {}).get("command", "").strip()
            if s:
                by_slash[s].add(sid)

        for kw in keywords:
            k = (kw or "").strip().lower()
            if k:
                by_keyword[k].add(sid)

    sections.sort(key=lambda s: (s["category"], s["subcategory"], s["id"]))
    for k in categories:
        categories[k].sort()

    out = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "https://hermes-agent.nousresearch.com/docs/",
        "raw_bundle": "raw/llms-full.txt",
        "schema": "SCHEMA.md",
        "section_count": len(sections),
        "categories": {k: sorted(v) for k, v in sorted(categories.items())},
        "sections": sections,
        "by_env_var": {k: sorted(v) for k, v in sorted(by_env_var.items())},
        "by_cli_command": {k: sorted(v) for k, v in sorted(by_cli.items())},
        "by_config_key": {k: sorted(v) for k, v in sorted(by_config.items())},
        "by_slash_command": {k: sorted(v) for k, v in sorted(by_slash.items())},
        "by_keyword": {k: sorted(v) for k, v in sorted(by_keyword.items())},
    }

    INDEX_FILE.write_text(json.dumps(out, indent=2, sort_keys=False, ensure_ascii=False))
    print(f"wrote {INDEX_FILE} — {len(sections)} sections, "
          f"{len(by_env_var)} env vars, {len(by_cli)} cli commands, "
          f"{len(by_config)} config keys, {len(by_slash)} slash commands, "
          f"{len(by_keyword)} keywords")
    return 0


if __name__ == "__main__":
    sys.exit(main())
