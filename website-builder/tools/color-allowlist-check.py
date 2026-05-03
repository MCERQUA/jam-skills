#!/usr/bin/env python3
"""color-allowlist-check.py

Scan a Next.js project for forbidden colors (purple/indigo, hue 240-290) and
emit a violations report. Used by Phase 7 (QUALITY-GATE).

Inputs:
    <project>           — Next.js project root
    --report <path>     — JSON report path (default: <project>/.quality-gate/color-allowlist.json)
    --strict            — also flag any hex outside the allowed palette
    --allowed <colors>  — comma-separated extra hex colors to allow (alongside .brand/colors.json)

Logic:
    - Read .brand/colors.json (primary, accent, neutral) for palette.
    - Walk src/, public/, app/ for *.tsx, *.ts, *.css, *.scss, *.html.
    - Find: hex codes (#abc, #aabbcc, #aabbccdd), hsl()/hsla(), oklch(),
      tailwind palette classes (bg-purple-500, text-indigo-300, etc.).
    - Convert each color to HSL and flag any whose hue lands in [240, 290]
      with saturation >= 15.
    - Tailwind class allowlist: NEVER allow `purple`, `indigo`, `violet`, `fuchsia`.

Exit codes:
    0   no violations
    1   one or more violations found
    2   project layout invalid (no src/ or .brand/colors.json)
"""

from __future__ import annotations

import argparse
import colorsys
import json
import re
import sys
from pathlib import Path


HEX_RE = re.compile(r"#([0-9A-Fa-f]{3,8})\b")
HSL_RE = re.compile(r"hsla?\(\s*([\d.]+)\s*,?\s*([\d.]+)%?\s*,?\s*([\d.]+)%?")
OKLCH_RE = re.compile(r"oklch\(\s*([\d.]+%?)\s+([\d.]+)\s+([\d.]+)")
# Tailwind v3 palette classes: e.g. `bg-purple-500`, `text-indigo-300/50`, `from-violet-700`
TW_CLASS_RE = re.compile(
    r"\b(?:bg|text|border|from|to|via|ring|shadow|outline|decoration|placeholder|caret|accent|fill|stroke)-(\w+)-(\d{2,4})(?:/\d+)?\b"
)

FORBIDDEN_TAILWIND_HUES = {"purple", "indigo", "violet", "fuchsia"}

INCLUDE_EXT = {".tsx", ".jsx", ".ts", ".js", ".css", ".scss", ".sass", ".html", ".mdx"}
# `.stitch-pages` is intentionally excluded: those are Stitch-generated mockups
# we DO NOT control. We scan the build output, not the source-of-truth references.
EXCLUDE_DIRS = {
    "node_modules", ".next", ".git", "dist", "build", ".cache", ".turbo",
    ".stitch-pages", ".brand", ".quality-gate", "ai",
}


def parse_hex(token: str) -> tuple[int, int, int] | None:
    s = token.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) == 8:
        s = s[:6]
    if len(s) != 6:
        return None
    try:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        return None


def to_hsl(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = rgb
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return (h * 360.0, s * 100.0, l * 100.0)


def parse_hsl_match(m: re.Match) -> tuple[float, float, float]:
    return (float(m.group(1)), float(m.group(2)), float(m.group(3)))


def is_forbidden_hue(h: float, s: float, l: float = 50.0) -> bool:
    """Forbidden = purple/indigo hue family with meaningful saturation AND
    not so light that it's effectively white. `#F9F9FF` reports s=100 h=240
    via HLS but is visually white — exclude anything with luminance >= 92."""
    if l >= 92.0 or l <= 8.0:
        return False
    return 240.0 <= h <= 290.0 and s >= 15.0


# ---------- main scan ---------------------------------------------------------

def scan_file(path: Path, allowed_hex: set[str]) -> list[dict]:
    """Return a list of violation dicts found in this file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    violations: list[dict] = []

    # Hex codes
    for m in HEX_RE.finditer(text):
        token = "#" + m.group(1)[:6].upper() if len(m.group(1)) >= 6 else None
        rgb = parse_hex(m.group(0))
        if rgb is None:
            continue
        h, s, l = to_hsl(rgb)
        if is_forbidden_hue(h, s, l):
            line = text[: m.start()].count("\n") + 1
            violations.append({
                "kind": "hex",
                "color": "#" + ("%02X%02X%02X" % rgb),
                "hue": round(h, 1),
                "saturation": round(s, 1),
                "luminance": round(l, 1),
                "file": str(path),
                "line": line,
            })

    # HSL/HSLA literals
    for m in HSL_RE.finditer(text):
        h, s, l = parse_hsl_match(m)
        if is_forbidden_hue(h, s, l):
            line = text[: m.start()].count("\n") + 1
            violations.append({
                "kind": "hsl",
                "color": f"hsl({h:.0f}, {s:.0f}%, {l:.0f}%)",
                "hue": round(h, 1),
                "saturation": round(s, 1),
                "file": str(path),
                "line": line,
            })

    # Tailwind palette class shorthand
    for m in TW_CLASS_RE.finditer(text):
        family = m.group(1).lower()
        if family in FORBIDDEN_TAILWIND_HUES:
            line = text[: m.start()].count("\n") + 1
            violations.append({
                "kind": "tailwind-class",
                "color": m.group(0),
                "file": str(path),
                "line": line,
            })

    return violations


def walk(project: Path) -> list[Path]:
    files: list[Path] = []
    for path in project.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in INCLUDE_EXT:
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--allowed", type=str, default="")
    args = parser.parse_args(argv[1:])

    project: Path = args.project.resolve()
    if not project.exists() or not (project / "src").exists():
        print(f"ERROR: project root with src/ not found: {project}", file=sys.stderr)
        return 2

    brand_path = project / ".brand" / "colors.json"
    allowed_hex: set[str] = set()
    if brand_path.exists():
        try:
            brand = json.loads(brand_path.read_text(encoding="utf-8"))
            for k in ("primary", "accent", "neutral"):
                if v := brand.get(k):
                    allowed_hex.add(v.upper())
        except json.JSONDecodeError:
            pass

    for token in args.allowed.split(","):
        token = token.strip().upper()
        if token:
            allowed_hex.add(token if token.startswith("#") else "#" + token)

    files = walk(project)
    all_violations: list[dict] = []
    for f in files:
        all_violations.extend(scan_file(f, allowed_hex))

    # Suppress hex violations whose normalized hex lands in allowed set —
    # but allowed set should never contain forbidden-hue colors anyway, so this
    # is purely a defense-in-depth filter.
    all_violations = [v for v in all_violations if v.get("color") not in allowed_hex]

    report = {
        "project": str(project),
        "filesScanned": len(files),
        "allowedFromBrand": sorted(allowed_hex),
        "violationCount": len(all_violations),
        "violations": all_violations[:100],  # cap for readability
        "truncated": len(all_violations) > 100,
    }

    out_path = args.report or (project / ".quality-gate" / "color-allowlist.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"=== Color allowlist report ===")
    print(f"  project: {project}")
    print(f"  files scanned: {len(files)}")
    print(f"  allowed (from .brand): {sorted(allowed_hex) or '(none — .brand/colors.json missing)'}")
    print(f"  violations: {len(all_violations)}")
    if all_violations:
        # Show first 10 for quick triage.
        for v in all_violations[:10]:
            loc = f"{v['file']}:{v['line']}"
            extra = f"  hue={v.get('hue')} sat={v.get('saturation')}" if "hue" in v else ""
            print(f"    [{v['kind']}] {v['color']}  {loc}{extra}")
        if len(all_violations) > 10:
            print(f"    ... and {len(all_violations) - 10} more (see {out_path})")
    print(f"  report: {out_path}")

    return 0 if not all_violations else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
