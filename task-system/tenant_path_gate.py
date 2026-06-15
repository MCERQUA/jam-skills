"""tenant_path_gate — static gate: fail any fleet helper that writes to a
host-only path NOT behind a runtime resolver. Run BEFORE a helper is "verified".
Catches the bug class that ate complete_task's convergence writes on the webtop
(hardcoded /mnt/agent-mesh) and no-op'd its ledger bridge (/home/mike host script)
— both invisible until run from a tenant container.

Scans STRING LITERALS only (via tokenize) — comments and path-component checks
like `"clients" in parts` are correctly ignored.

PASS (any one):
  - file imports mesh_paths (canonical resolver), OR
  - each host-only string literal also has its tenant-mount counterpart in-file
    (a hand-rolled candidates resolver — allowed, nudged toward mesh_paths).
FAIL: a host-only path string with no tenant counterpart and no mesh_paths import.

Usage: python3 tenant_path_gate.py <file.py> ...   # exit 1 on any FAIL
"""
import io
import re
import sys
import tokenize

HOST_ONLY = [r"/mnt/agent-mesh\b", r"/home/mike\b", r"/mnt/clients\b"]
TENANT_COUNTERPART = "/mesh"


def _string_literals(src: str):
    """Yield (lineno, value) for every STRING token (skips comments)."""
    try:
        toks = tokenize.generate_tokens(io.StringIO(src).readline)
        for tok in toks:
            if tok.type == tokenize.STRING:
                # only PATH-LIKE literals: a real path constant has no whitespace.
                # Docstrings, argparse help= text, and any prose mentioning a path
                # contain spaces/newlines -> skip (host review 2026-06-14: these were
                # the entire false-positive set across the task-system skill).
                if any(c.isspace() for c in tok.string) or "\\" in tok.string:
                    continue  # prose/docstring/help= (whitespace) or regex pattern (backslash) — not a path value
                yield tok.start[0], tok.string
    except (tokenize.TokenError, IndentationError):
        # fall back to whole-source if the file won't tokenize cleanly
        yield 0, src


def scan(path: str) -> list[str]:
    src = open(path).read()
    if re.search(r"\b(import\s+mesh_paths|from\s+mesh_paths\s+import)", src):
        return []
    has_tenant_mount = bool(re.search(r"(?<![\w-])/mesh(/|[\"\'])", src))
    violations = []
    for lineno, sval in _string_literals(src):
        for pat in HOST_ONLY:
            for m in re.finditer(pat, sval):
                literal = m.group(0)
                if literal.startswith("/mnt/agent-mesh") and has_tenant_mount:
                    continue  # hand-rolled candidates resolver present
                violations.append(
                    f"{path}:{lineno}: host-only path '{literal}' in a string "
                    f"literal, no tenant counterpart / no mesh_paths — breaks on webtop/voice")
    return violations


def main(argv):
    if not argv:
        print("usage: tenant_path_gate.py <file.py> ..."); return 2
    all_v = []
    for f in argv:
        all_v += scan(f)
    if all_v:
        print("TENANT-PATH GATE: FAIL"); [print("  -", v) for v in all_v]
        print("  fix: route through mesh_paths.receipts_dir()/ledger_root()/blackboard_root()")
        return 1
    print(f"TENANT-PATH GATE: PASS ({len(argv)} file(s) clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
