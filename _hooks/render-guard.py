#!/usr/bin/env python3
# COPY of /home/mike/MIKE-AI/scripts/hooks/render-guard.py (the CANONICAL file, git main). Everything below the
# marker line is byte-identical to the canonical file minus its shebang. It lives here because
# /mnt/system/base/skills is the one host dir bind-mounted (read-only) into every openclaw container as
# /mnt/shared-skills, so the SMS brains (claude / z-code inside the container) can reach it as
#   python3 /mnt/shared-skills/_hooks/render-guard.py     (registered by scripts/sms-agent/brain-settings-merge.js)
# A symlink cannot work: /home/mike/... does not exist inside the container (measured 2026-09-16).
# Drift check: scripts/tests/test-render-guard.sh fails if this body differs from the canonical body.
# --- end of copy header ---
"""
render-guard.py — PreToolUse hook (matcher: Bash). BLOCKING. The VPS does not render video.

WHY A BLOCKING HOOK
-------------------
Mike, 2026-09-16: "insure that agents don't use remotion on the server — it bogs us down
unnecessarily, especially because we have the mac specifically to offload this stuff to, and if
the mac is busy it can hand off to the GPU box". Measured the same night (docs/jambot/
remotion-vps-render-guard-design-2026-09-16.md): the render toolchain (remotion, hyperframes,
headless Chrome, ffmpeg) is INSIDE every tenant image; 29/29 openclaw exec lanes are unbounded;
the two existing PreToolUse hooks are advisory by their own docstrings; all 29 tenant TOOLS.md
carry the "route video to the Mac" prose and prose addressed to the model it constrains is not a
guard. The host's own lane is the one with the most CPU to burn (800% budget, p90 already over).

BEHAVIOUR: reads the hook JSON on stdin ONLY (never shells out, never reads files — memory
`a-test-copy-still-writes-to-live-absolute-paths`), matches the command against RENDER verbs, and
on a match prints ONE line to stderr and exits 2 (Claude Code: block the tool call, show stderr).
Everything else exits 0 silently. Bypass for a human at the shell, one command:
JAMBOT_RENDER_ALLOWED=1 in the command's own env prefix (a prior session's instruction is not that).

Register (host / clone / coder: ~/.claude/settings.json; brains: via jambot-sms-agent-keeper.sh):
    "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
                    "command": "python3 /home/mike/MIKE-AI/scripts/hooks/render-guard.py"}]}]

Negative control (must block):  echo '{"tool_input":{"command":"npx remotion render src/index.ts Main out.mp4"}}' | python3 scripts/hooks/render-guard.py; echo rc=$?   -> rc=2
Positive controls (must pass):  ls remotion-project · mesh-send ... --subject 'remotion promo' · ffmpeg -i in.wav -ar 16000 out.wav · playwright probes (python) · mmdc
"""
from __future__ import annotations
import json, re, sys

HANDOFF = ("render-guard: the VPS does not render video. Hand the job to mac-claude@mesh — "
           "mesh-send --to mac-claude@mesh --kind task per /mnt/agent-mesh/mesh/contracts/video-to-mac.md "
           "(engine and node choice are the Mac's; overflow to the GPU box is the Mac's call). "
           "A human at the shell may prefix JAMBOT_RENDER_ALLOWED=1 for ONE command.")

PATTERNS = [
    # remotion / hyperframes render verbs, however invoked (npx, pnpm exec/dlx, direct, node .bin)
    (re.compile(r"(?<![\w/.-])(?:npx\s+(?:--yes\s+)?|pnpm\s+(?:exec|dlx)\s+|yarn\s+|bunx\s+)?(?:@remotion/cli\S*|remotion(?:b|d)?)(?:@\S+)?\s+(?:render|still|lambda|studio|benchmark|compositions)\b"), "remotion render verb"),
    (re.compile(r"node_modules/\.bin/remotion\b|@remotion/(?:renderer|cli|bundler)"), "remotion toolchain path"),
    # hyperframes as a COMMAND (start of command / after ; & | ( or a runner), never as a path segment —
    # the first version matched `ls .../bin/hyperframes` (measured 2026-09-16 by the step-3 builder).
    (re.compile(r"(?:^|[;&|(])\s*(?:npx\s+(?:--yes\s+)?|pnpm\s+(?:exec|dlx)\s+|bunx\s+|yarn\s+)?hyperframes(?=\s|$)"), "hyperframes"),
    # headless chrome used as a renderer (screenshot / pdf / dom dump) — a bare launch is not matched
    (re.compile(r"chrom(?:e|ium)(?:-headless-shell)?\b[^|;&]*--headless[^|;&]*--(?:screenshot|print-to-pdf|dump-dom)|chrom(?:e|ium)(?:-headless-shell)?\b[^|;&]*--(?:screenshot|print-to-pdf|dump-dom)[^|;&]*--headless"), "headless chrome render"),
    # ffmpeg as a renderer: synthetic sources or a frame-sequence encode
    (re.compile(r"\bffmpeg\b[^|;&]*\s-f\s+lavfi\b"), "ffmpeg lavfi render"),
    (re.compile(r"\bffmpeg\b[^|;&]*\s-i\s+\S*%0?\d+d\.(?:png|jpe?g|webp)\b"), "ffmpeg frame-sequence encode"),
]

def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # not our shape — never block on a parse error
    cmd = ""
    ti = payload.get("tool_input") if isinstance(payload, dict) else None
    if isinstance(ti, dict):
        cmd = str(ti.get("command") or "")
    if not cmd:
        return 0
    if re.search(r"(?:^|[\s;&|])JAMBOT_RENDER_ALLOWED=1\b", cmd):
        return 0
    # Text is not execution. A heredoc body (writing a doc that MENTIONS a render) is never a
    # render, and neither is a quoted string handed to echo/grep/mesh-send. So: heredoc bodies are
    # dropped for every pattern, and quoted strings are dropped for the VERB patterns only — a
    # `node -e "require('@remotion/renderer')"` is code that executes inside its quotes, so the
    # toolchain-path pattern still sees the raw command. (A gate must not refuse the report of
    # its own refusal — mac-claude 2026-09-16.)
    no_heredoc = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\1(?:\n|$)", " ", cmd, flags=re.S)
    no_quotes = re.sub(r"'[^']*'|\"(?:[^\"\\\\]|\\\\.)*\"", "''", no_heredoc)
    for rx, label in PATTERNS:
        target = no_heredoc if label in ("remotion toolchain path",) else no_quotes
        m = rx.search(target)
        if m:
            sys.stderr.write(f"{HANDOFF}\n  blocked: {label} — matched {m.group(0)[:80]!r}\n")
            return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
