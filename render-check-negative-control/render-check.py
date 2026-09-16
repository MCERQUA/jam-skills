#!/usr/bin/env python3
"""
render-check.py — does a canvas page actually RENDER, proven with a NEGATIVE CONTROL.

    render-check.py --old <old.html> --new <new.html> [--mode auto|host|tenant]
                     [--require <selector>]... [--dump-dir <dir>]

WHY (pledge a60201cb, origin ICA field-dock 2026-09-15)
--------------------------------------------------------
ICA's "Field Dock" canvas page returned HTTP 200 on every request and rendered BLANK for ~7
hours because one inline <script> had a syntax error (`window.__DOCK_DATA__ =
{/*DATA*/{..}/*DATA*/}`). The checker that was supposed to catch this (check-page-inline-js.py)
had `node` off PATH in the calling shell, silently fell back to a weaker "shape" check, and
printed OK. Links were texted to two client users before Mike found it by clicking the link.

A checker that has never been shown a broken page is not evidence it can see one. This tool
NEVER reports a bare PASS on a single file. It always takes an OLD (known/assumed-broken) copy
and a NEW (fixed) copy, runs the SAME check on both, and only reports success if the check
actually DISCRIMINATES: OLD must FAIL and NEW must PASS. If both pass, the check could not tell
the difference between broken and fixed — verdict CANNOT-TELL, never PASS.
    See also: /mnt/system/base/skills/daily-receipts-ledger (unrelated pattern, same directory
    layout convention) and memory file a-200-page-is-not-a-working-page.md for the full incident.

TWO MODES — it always prints which one ran, never silently degrades
---------------------------------------------------------------------
  host    — loads the page in real headless Chrome (chrome-headless-shell), catches
            window.onerror / unhandledrejection / console.error, and checks whether the body
            actually grew visible content beyond its static shell. Sees RUNTIME errors too
            (undefined property access, etc.), not just syntax errors.
  tenant  — tenant containers have node but no playwright/chrome. Extracts every inline
            <script> block and runs `node --check` on each. Catches every SYNTAX error (the
            ICA class) but is BLIND to runtime errors — this is stated in the output, always.

Mode is auto-selected: host if a chrome-headless-shell/chromium binary is found, else tenant if
node is found, else CANNOT-TELL (no capability at all — never silently reports PASS).

VERDICTS — three, never two
----------------------------
  PASS         OLD failed the check, NEW passed it. The check discriminates. NEW is credibly OK.
  FAIL         NEW still fails (regardless of OLD) — do not ship NEW.
  CANNOT-TELL  OLD also passed (no discrimination), or the harness itself could not render/parse
               either file (no chrome, no node, chrome crashed, etc). NEVER folded into PASS.

Exit codes: 0 = PASS, 2 = FAIL, 3 = CANNOT-TELL.

Self-test: see self-test.sh in this directory (fixtures/broken.html + fixtures/fixed.html
reproduce the exact ICA syntax-error class; fixtures/both-ok-{a,b}.html demonstrate the
CANNOT-TELL path when a check cannot discriminate).
"""
from __future__ import annotations

import argparse
import http.server
import io
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

# ---------------------------------------------------------------------------
# shared: inline-<script> extraction (same pattern as check-page-inline-js.py)
# ---------------------------------------------------------------------------
_SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)


def inline_scripts(html: str) -> list[str]:
    return [m for m in _SCRIPT_RE.findall(html) if m.strip()]


def find_node() -> str | None:
    """node on PATH, else newest nvm install, else /usr/local/bin. Host shells and cron
    frequently have no node on PATH — this is exactly the gap that let the ICA page through
    (fixed in check-page-inline-js.py by commit 71110be1; same logic here)."""
    found = shutil.which("node")
    if found:
        return found

    def ver(p: Path) -> tuple[int, ...]:
        nums = re.findall(r"\d+", p.parent.parent.name)
        return tuple(int(x) for x in nums[:3]) if nums else (0,)

    nvm = sorted(Path.home().glob(".nvm/versions/node/v*/bin/node"), key=ver)
    for cand in reversed(nvm):
        if cand.is_file():
            return str(cand)
    return "/usr/local/bin/node" if Path("/usr/local/bin/node").is_file() else None


CHROME_CANDIDATES = [
    # discovered on this host 2026-09-16 — relocated cache dir, NOT ~/.cache
    "/mnt/system/relocated/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell",
    os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-linux64/chrome-headless-shell"),
    os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell"),
    os.path.expanduser("~/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"),
    os.path.expanduser("~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"),
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
]


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("chromium", "chromium-browser", "google-chrome"):
        w = shutil.which(name)
        if w:
            return w
    return None


# ---------------------------------------------------------------------------
# TENANT mode — node --check on every extracted inline <script>
# ---------------------------------------------------------------------------
def tenant_check(path: Path) -> tuple[bool | None, str]:
    """(True, why)=parses (False, why)=syntax error (None, why)=CANNOT-TELL (no node)."""
    node = find_node()
    if not node:
        return None, "CANNOT-TELL: no node runtime found (PATH, ~/.nvm, /usr/local/bin)"
    try:
        html = path.read_text(errors="replace")
    except OSError as e:
        return False, f"unreadable ({type(e).__name__})"
    scripts = inline_scripts(html)
    if not scripts:
        return True, "OK (mode=tenant, no inline script to check)"
    for i, js in enumerate(scripts):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js)
            tmp = f.name
        try:
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=60)
        finally:
            Path(tmp).unlink(missing_ok=True)
        if r.returncode != 0:
            err = (r.stderr or r.stdout).strip().splitlines()
            return False, f"script block #{i}: does not parse: {err[0][:200] if err else 'unknown error'}"
    return True, f"OK (mode=tenant, {len(scripts)} inline script block(s) parse — RUNTIME errors NOT checked)"


# ---------------------------------------------------------------------------
# HOST mode — real headless Chrome, error sink + rendered-content check
# ---------------------------------------------------------------------------
ERR_HOOK = (
    '<script>window.__jsErrors=[];'
    'window.addEventListener("error",function(e){window.__jsErrors.push("onerror: "+(e.message||"")+" @"+(e.filename||"")+":"+(e.lineno||""))});'
    'window.addEventListener("unhandledrejection",function(e){window.__jsErrors.push("unhandledrejection: "+e.reason)});'
    'var __oce=console.error;console.error=function(){window.__jsErrors.push("console.error: "+Array.prototype.join.call(arguments," "));__oce.apply(console,arguments)};'
    "</script>"
)
SINK = (
    '<script>setTimeout(function(){var d=document.createElement("div");'
    'd.id="__jserrsink";d.setAttribute("data-count",String(window.__jsErrors.length));'
    'd.setAttribute("data-bodylen",String((document.body.innerText||"").replace(/\\s+/g,"").length));'
    'd.textContent=window.__jsErrors.join(" ||| ");document.body.appendChild(d);},%d);</script>'
)


def _make_handler(served: dict[str, str]):
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            name = self.path.lstrip("/").split("?")[0]
            html = served.get(name)
            if html is None:
                self.send_response(404)
                self.end_headers()
                return
            b = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

    return H


def host_render(path: Path, wait_ms: int = 5000, dump_path: str | None = None) -> tuple[bool | None, str]:
    """Loads the page in real Chrome. (True, why)=rendered clean (False, why)=JS error or blank
    body (None, why)=CANNOT-TELL (no chrome, chrome crashed, or the sink never fired)."""
    chrome = find_chrome()
    if not chrome:
        return None, "CANNOT-TELL: no chrome-headless-shell/chromium binary found"
    try:
        html = path.read_text(errors="replace")
    except OSError as e:
        return False, f"unreadable ({type(e).__name__})"

    injected = html
    if "<head>" in injected:
        injected = injected.replace("<head>", "<head>" + ERR_HOOK, 1)
    else:
        injected = ERR_HOOK + injected
    tail = SINK % 3500
    if "</body>" in injected:
        injected = injected.replace("</body>", tail + "</body>", 1)
    else:
        injected += tail

    served = {"page.html": injected}
    srv = socketserver.TCPServer(("127.0.0.1", 0), _make_handler(served))
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    profile = tempfile.mkdtemp(prefix="render-check-profile-")
    try:
        url = f"http://127.0.0.1:{port}/page.html"
        cmd = [
            chrome, "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
            "--user-data-dir=" + profile,
            # every host but the harness resolves to NOTFOUND — a page that @imports a
            # CDN font must not hang the load waiting on egress that never answers.
            "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
            "--disable-background-networking", "--disable-component-update",
            "--no-first-run", "--no-default-browser-check", "--mute-audio",
            f"--virtual-time-budget={wait_ms}", "--dump-dom", url,
        ]
        if "headless-shell" not in os.path.basename(chrome):
            cmd.insert(1, "--headless=new")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            dom = r.stdout
        except Exception as e:
            return None, f"CANNOT-TELL: chrome failed to run: {e}"
    finally:
        srv.shutdown()
        shutil.rmtree(profile, ignore_errors=True)

    if dump_path:
        Path(dump_path).write_text(dom, encoding="utf-8")

    if not dom.strip():
        return None, "CANNOT-TELL: chrome produced no DOM"

    sink = re.search(r'<div id="__jserrsink" data-count="(\d+)" data-bodylen="(\d+)"[^>]*>(.*?)</div>', dom, re.S)
    if not sink:
        return None, "CANNOT-TELL: error sink never rendered — page may not have finished loading"
    nerr, bodylen, errtext = int(sink.group(1)), int(sink.group(2)), sink.group(3).strip()

    if nerr:
        return False, f"{nerr} JS error(s): {errtext[:300]}"
    if bodylen < 5:
        return False, f"body rendered essentially empty ({bodylen} visible chars after load) — page may be blank despite 200/no-JS-error"
    return True, f"OK (mode=host, 0 JS errors, {bodylen} visible chars rendered)"


# ---------------------------------------------------------------------------
# negative-control orchestration
# ---------------------------------------------------------------------------
def run_check(path: Path, mode: str, dump_path: str | None) -> tuple[bool | None, str]:
    if mode == "host":
        return host_render(path, dump_path=dump_path)
    return tenant_check(path)


def pick_mode(requested: str) -> str:
    if requested != "auto":
        return requested
    if find_chrome():
        return "host"
    if find_node():
        return "tenant"
    return "none"


def negative_control(old: Path, new: Path, mode: str, dump_dir: str | None) -> int:
    resolved_mode = pick_mode(mode)
    print(f"MODE: {resolved_mode}"
          + ("  (no chrome AND no node found — cannot run any check)" if resolved_mode == "none" else ""))
    if resolved_mode == "tenant":
        print("  NOTE: tenant mode only catches SYNTAX errors (node --check on inline scripts).")
        print("        It is BLIND to runtime errors (undefined property access, etc).")
    if resolved_mode == "none":
        print("VERDICT: CANNOT-TELL — no chrome-headless-shell/chromium AND no node on this host")
        return 3

    old_dump = os.path.join(dump_dir, "old.dom.html") if dump_dir else None
    new_dump = os.path.join(dump_dir, "new.dom.html") if dump_dir else None

    old_ok, old_why = run_check(old, resolved_mode, old_dump)
    new_ok, new_why = run_check(new, resolved_mode, new_dump)

    def label(v: bool | None) -> str:
        return "PASS" if v else ("CANNOT-TELL" if v is None else "FAIL")

    print(f"  OLD [{old.name}] -> {label(old_ok)}: {old_why}")
    print(f"  NEW [{new.name}] -> {label(new_ok)}: {new_why}")

    if old_ok is None or new_ok is None:
        print("VERDICT: CANNOT-TELL — harness could not produce a verdict for one or both files")
        return 3

    if new_ok is False:
        print("VERDICT: FAIL — NEW copy still fails the check. Do not ship it.")
        return 2

    if old_ok is True and new_ok is True:
        print("VERDICT: CANNOT-TELL — OLD also passed. The check does not discriminate between "
              "the broken and fixed copy on this input; a real defect could pass unnoticed. "
              "This is not evidence NEW is fine — get a better negative control.")
        return 3

    # old_ok is False, new_ok is True
    print("VERDICT: PASS — negative control confirmed: OLD failed this check, NEW passed it.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True, help="known/assumed-broken copy of the page")
    ap.add_argument("--new", required=True, help="fixed copy of the page")
    ap.add_argument("--mode", choices=["auto", "host", "tenant"], default="auto")
    ap.add_argument("--dump-dir", help="write rendered DOM dumps here (host mode only)")
    ap.add_argument("--self-test", action="store_true", help="ignore --old/--new, run built-in fixtures")
    a = ap.parse_args()

    if a.dump_dir:
        os.makedirs(a.dump_dir, exist_ok=True)

    old = Path(a.old)
    new = Path(a.new)
    if not old.is_file():
        print(f"CANNOT-TELL: --old file not found: {old}")
        return 3
    if not new.is_file():
        print(f"CANNOT-TELL: --new file not found: {new}")
        return 3

    return negative_control(old, new, a.mode, a.dump_dir)


if __name__ == "__main__":
    sys.exit(main())
