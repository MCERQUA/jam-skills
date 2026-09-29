#!/usr/bin/env python3
"""retire.py: take a delivered asset OUT OF USE without deleting it (fleet skill retire-dont-delete).

Four verbs, standard library only, one file:

  retire.py retire <uploads_dir> <filename> --by WHO --why "their words" [--set NAME] [--url-base URL]
      Append ONE row to <uploads_dir>/.uploads-index.jsonl (event: retired, the reason verbatim,
      who asked, live size, sha256) and add the file's sha256 to <uploads_dir>/.retired-refs.jsonl.
      The bytes, the URL and any freeze record stay exactly as they are.

  retire.py deny <file>... --ledger PATH --by WHO --why "..." [--set NAME] [--where TEXT]
      Add copies that are NOT in an upload index (uncropped originals, local drafts, warehouse
      gens) to a deny ledger. Every copy your generation rig can reach belongs in one.

  retire.py check <file>... [--ledger PATH]... [--require-ledger]
      The attach-step gate. Exit 0 clean · 1 a file is retired · 3 cannot tell.
      Keyed on sha256, so a renamed copy is refused.

  retire.py state <uploads_dir> [filename] [--live]
      Effective state per filename, reading the index IN ORDER (the last row wins). A later
      registration row un-retires a file. `--live` prints only usable filenames, for pick surfaces.

Ledger row schema (same as the Mac image rig's RETIRED-REFS.jsonl, so ledgers are interchangeable):
  {"sha256", "name", "where", "set", "kind", "why", "by", "at", "ref"}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import sys
from datetime import datetime, timezone

INDEX_NAME = ".uploads-index.jsonl"
LEDGER_NAME = ".retired-refs.jsonl"   # leading dot on purpose: tenant web servers answer 403 for dotfiles
SHA_RE = re.compile(r"[0-9a-f]{64}")
LIVE, RETIRED, PULLED = "live", "retired", "pulled"


class CannotTell(Exception):
    """The check could not be evaluated. Callers map this to exit 3, never to a pass."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def append_jsonl(path: str, row: dict) -> None:
    # One write() of one complete line in append mode, so a concurrent reader never sees half a row.
    with open(path, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_ledger(path: str) -> dict:
    """{sha256: row}. A malformed row RAISES CannotTell: a gate that cannot read its list must not
    pass everything. A missing file returns {} and the caller decides what that means."""
    out = {}
    with open(path) as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as e:
                raise CannotTell(f"{path}:{n}: not JSON ({e})")
            sha = row.get("sha256", "") if isinstance(row, dict) else ""
            if not SHA_RE.fullmatch(sha):
                raise CannotTell(f"{path}:{n}: row has no valid sha256")
            out[sha] = row
    return out


def effective_states(index_path: str) -> tuple[dict, int]:
    """{filename: state}, reading every row in order so the LAST row per filename wins.
    A row with no `event` is a registration (live). `retired` and `pulled` withdraw the file.
    Any other event is reported as `unknown:<event>`, which pick surfaces must treat as not live.
    Returns (states, rows_without_a_filename)."""
    states, nameless = {}, 0
    with open(index_path) as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as e:
                raise CannotTell(f"{index_path}:{n}: not JSON ({e})")
            if not isinstance(row, dict):
                raise CannotTell(f"{index_path}:{n}: not an object")
            name = row.get("filename") or row.get("file")   # `file` = a legacy writer's key
            if not name:
                nameless += 1
                continue
            ev = row.get("event")
            states[name] = LIVE if ev in (None, "", "registered") else (
                ev if ev in (RETIRED, PULLED) else f"unknown:{ev}")
    return states, nameless


def deny_row(path: str, sha: str, by: str, why: str, set_name: str, where: str, kind: str) -> dict:
    return {"sha256": sha, "name": os.path.basename(path), "where": where, "set": set_name,
            "kind": kind, "why": why, "by": by, "at": now()[:10], "ref": ""}


def add_to_ledger(ledger: str, rows: list) -> int:
    known = load_ledger(ledger) if os.path.exists(ledger) else {}
    added = 0
    for r in rows:
        if r["sha256"] in known:
            continue
        append_jsonl(ledger, r)
        known[r["sha256"]] = r
        added += 1
    return added


def require_words(by: str, why: str) -> None:
    if not (why or "").strip():
        sys.exit("refusing: no --why. An empty reason is worse than none, because it looks recorded. "
                 "Quote the client's own words.")
    if not (by or "").strip():
        sys.exit("refusing: no --by. Name who asked (the client, their agent and message id).")


def cmd_retire(a) -> int:
    require_words(a.by, a.why)
    path = os.path.join(a.uploads_dir, a.filename)
    if os.path.basename(a.filename) != a.filename:
        sys.exit(f"refusing: {a.filename!r} is not a bare filename in {a.uploads_dir}")
    if not os.path.isfile(path):
        sys.exit(f"refusing: no {a.filename} in {a.uploads_dir}. Retiring an absent file records nothing; "
                 f"find where it actually is (it may have been renamed; `check` it by content).")
    sha, size, why = sha256_file(path), os.path.getsize(path), a.why.strip()
    row = {"at": now(), "filename": a.filename, "original_name": a.filename,
           "mime": mimetypes.guess_type(a.filename)[0] or "application/octet-stream",
           "size": size, "sha256": sha, "note": f"RETIRED: {why}", "event": RETIRED,
           "retired_note": why, "retired_by": a.by.strip()}
    if os.environ.get("AGENT_URI"):
        row["from"] = os.environ["AGENT_URI"]
    if a.url_base:
        row["url"] = f"{a.url_base.rstrip('/')}/{a.filename}"
    if a.dry_run:
        print("DRY-RUN index row:", json.dumps(row, ensure_ascii=False))
        return 0
    ledger = os.path.join(a.uploads_dir, LEDGER_NAME)
    # Ledger FIRST: if the second write fails, the file is already refused at every attach step,
    # which is the half that prevents harm. An index row with no ledger row would look done and
    # still let the bytes back in.
    added = add_to_ledger(ledger, [deny_row(path, sha, a.by.strip(), why, a.set or "",
                                            f"{a.uploads_dir} (bytes kept)", "delivered")])
    append_jsonl(os.path.join(a.uploads_dir, INDEX_NAME), row)
    print(f"RETIRED {a.filename} sha256={sha[:12]} size={size} "
          f"(deny ledger: {'added' if added else 'already listed'}). Bytes and URL untouched.")
    return 0


def cmd_deny(a) -> int:
    require_words(a.by, a.why)
    rows = []
    for p in a.files:
        if not os.path.isfile(p):
            sys.exit(f"refusing: {p} is not a file")
        rows.append(deny_row(p, sha256_file(p), a.by.strip(), a.why.strip(), a.set or "",
                             a.where or os.path.dirname(os.path.abspath(p)), a.kind))
    added = add_to_ledger(a.ledger, rows)
    print(f"deny ledger {a.ledger}: {added} added, {len(rows) - added} already listed")
    return 0


def cmd_check(a) -> int:
    ledgers = a.ledger or []
    retired, looked = {}, []
    try:
        if not ledgers:
            raise CannotTell("no --ledger given; a check against nothing is not a check")
        for L in ledgers:
            if not os.path.exists(L):
                if a.require_ledger:
                    raise CannotTell(f"no ledger at {L} (--require-ledger)")
                print(f"note: no ledger at {L}, so nothing there is known to be retired")
                continue
            retired.update(load_ledger(L))
            looked.append(L)
        hits = []
        for p in a.files:
            try:
                sha = sha256_file(p)
            except OSError as e:
                raise CannotTell(f"cannot read {p}: {e}")
            row = retired.get(sha)
            if row:
                hits.append((p, row))
    except CannotTell as e:
        print(f"CANNOT-TELL: {e}", file=sys.stderr)
        return 3
    for p, row in hits:
        print(f"RETIRED: {p} is {row.get('name', '?')} ({row.get('set') or 'no set'}): "
              f"{row.get('why', '')} [by {row.get('by', '?')}]")
    if hits:
        print("refused: a retired file is never a reference, anchor, edit base or pick again.")
        return 1
    print(f"clean: {len(a.files)} file(s), none in {len(retired)} retired hash(es) from {len(looked)} ledger(s)")
    return 0


def cmd_state(a) -> int:
    try:
        states, nameless = effective_states(os.path.join(a.uploads_dir, INDEX_NAME))
    except (CannotTell, OSError) as e:
        print(f"CANNOT-TELL: {e}", file=sys.stderr)
        return 3
    if a.filename:
        print(states.get(a.filename, "unregistered"))
        return 0
    for name, st in sorted(states.items()):
        if a.live and st != LIVE:
            continue
        print(name if a.live else f"{st}\t{name}")
    if nameless:
        print(f"note: {nameless} index row(s) carry no filename and were skipped", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("retire")
    r.add_argument("uploads_dir"); r.add_argument("filename")
    r.add_argument("--by", required=True); r.add_argument("--why", required=True)
    r.add_argument("--set"); r.add_argument("--url-base"); r.add_argument("--dry-run", action="store_true")
    d = sub.add_parser("deny")
    d.add_argument("files", nargs="+"); d.add_argument("--ledger", required=True)
    d.add_argument("--by", required=True); d.add_argument("--why", required=True)
    d.add_argument("--set"); d.add_argument("--where"); d.add_argument("--kind", default="copy")
    c = sub.add_parser("check")
    c.add_argument("files", nargs="+"); c.add_argument("--ledger", action="append")
    c.add_argument("--require-ledger", action="store_true")
    s = sub.add_parser("state")
    s.add_argument("uploads_dir"); s.add_argument("filename", nargs="?"); s.add_argument("--live", action="store_true")
    a = ap.parse_args()
    try:
        return {"retire": cmd_retire, "deny": cmd_deny, "check": cmd_check, "state": cmd_state}[a.cmd](a)
    except CannotTell as e:   # e.g. a malformed ledger met by `retire` or `deny`: write nothing, say so
        print(f"CANNOT-TELL: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
