"""container_path_check.py — pre-send check: does the path I am quoting
actually exist in the RECIPIENT'S namespace?

WHY (2026-09-20, host@mesh, five times in one day): host told josh's desk agents that a
file or key was "at /config/... or /agent-desk/..." by looking from the HOST side of a bind
mount. Each time the host side looked fine and the desk side did not have it. The fifth was
the worst kind: host verified eight keys correctly with `ssh -T` from inside the container,
and in the SAME message asserted a ninth from a GitHub deploy-key TITLE — a name that was
not a file on that desk at all. Four near-name tracthome keys exist and open four different
repos, so a wrong key filename is not a typo, it is a different repo.

Host paths and container paths are different namespaces joined by bind mounts, and the host
side always looks fine. Knowing the rule does not help: the host had this exact lesson
written in its own memory file and broke it on the ninth line of the paragraph where it had
just applied it eight times.

THREE VERDICTS, never two (MEMORY: three-verdicts-never-two). A path is OK, MISSING, or
UNCHECKABLE — and UNCHECKABLE is printed with its reason, never folded into OK. A silent
pass from a checker that could not run is the defect class this file exists to stop.

ADVISORY, NEVER BLOCKING. It prints to stderr and lets the send proceed. A message can
legitimately name a path that does not exist yet ("create /config/x"), and a mesh lane must
not wedge because a container is restarting. The intel filter blocks; this one warns.
"""
from __future__ import annotations

import os
import re
import subprocess

# Paths that live inside a container's namespace. A bare /home/mike/... or /mnt/... path is
# the HOST's and is not checked here — the recipient may legitimately be told about one.
CONTAINER_PREFIXES = ("/config/", "/agent-desk", "/workspace/", "/home/node/", "/mnt/shared-skills/")

# Trailing punctuation that is prose, not part of the path.
_TRAIL = ".,;:!?)]}'\"`"

_PATH_RE = re.compile(r"(?<![\w/])(/(?:config|agent-desk[\w-]*|workspace|home/node|mnt/shared-skills)/[^\s`'\"<>|]+)")

# A fenced block or an inline `code span` is where paths are usually quoted; we scan the whole
# body rather than only code spans, because the misses being caught were in prose.


def _docker(args, timeout=25):
    """Run docker. Returns (rc, stdout, stderr); rc=127 means no way to run it here.

    The host needs `sg docker -c` (mike is in the docker group but non-login shells do not pick
    it up). A DESK does not have `sg` at all — measured 2026-09-20 by josh-desk-2, whose send
    printed `FileNotFoundError(2)` because this reached for a host-only idiom from inside a
    container. Try the plain binary first, fall back to sg, and report 127 rather than raising."""
    # ONE invocation style, deliberately. The first fix here tried plain `docker` first and fell
    # back to sg — but the callers build a shell-string script already wrapped in single quotes
    # for the sg form, so the direct-argv form received the quotes literally and every exec came
    # back rc=127. Two styles need two quotings; keeping one style and failing cleanly is simpler
    # and is what the local fallback below is for.
    try:
        p = subprocess.run(["sg", "docker", "-c", "docker " + " ".join(args)],
                           capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, OSError):
        return 127, "", "no sg/docker available from here"
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def container_for(agent: str) -> tuple[str | None, str]:
    """Map a mesh agent name to the container whose namespace it lives in.

    Returns (container_name, why). container_name None means 'not a container-backed agent,
    or the mapping could not be established' — the why says which.
    """
    # <tenant>-desk-N and <tenant>-desktop both live in that tenant's webtop.
    m = re.fullmatch(r"([a-z0-9][a-z0-9-]*?)-(?:desk-\d+|desktop)", agent)
    if not m:
        return None, "not a desk agent"
    tenant = m.group(1)
    # bun's webtop predates the -<tenant> suffix convention.
    for cand in (f"webtop-ubuntu-os-{tenant}", "webtop-ubuntu-os" if tenant == "bun" else None):
        if not cand:
            continue
        rc, out, _ = _docker(["inspect", "--format", "'{{.State.Running}}'", cand])
        if rc == 0 and "true" in out:
            # Confirm by the container's own AGENT_URI rather than trusting the name.
            rc2, uri, _ = _docker(["exec", cand, "printenv", "AGENT_URI"])
            if rc2 == 0 and uri and not uri.startswith(tenant):
                return None, f"{cand} reports AGENT_URI={uri}, which is not {tenant}'s — refusing to guess"
            return cand, "running"
        if rc == 0:
            return None, f"{cand} exists but is not running"
    return None, f"no running webtop found for tenant {tenant}"


# The 2026-09-20 miss was not a PATH at all — it was a bare key NAME in backticks
# ("you already hold `jambot-josh-tracthomecontractorinsurance.com`"), taken from a GitHub
# deploy-key TITLE. Nothing with a slash in it was wrong, so a path-only checker walks past
# the exact sentence that caused the damage. Trigger only when the body is talking about
# keys, so an ordinary backticked repo name or command is never flagged.
_KEYISH = re.compile(r"`([A-Za-z0-9][\w.@-]{6,})`")
_KEY_STORES = ("/config/.ssh", "/agent-desk/desk/deploy-keys/write")
# PROXIMITY, not document-level. The first live firing (2026-09-20) flagged `mesh-send`
# in a message ABOUT keys — a body-wide "does this mention keys" trigger makes every
# backticked token a candidate, and an advisory checker that cries wolf gets ignored,
# which is the same as not existing. The word must be near the token.
_KEY_NEAR = re.compile(r"(?:\bkeys?\b|ssh -T|deploy[- ]key)", re.I)
_WINDOW = 70
# Tool and command names that appear in backticks beside the word "key" all day.
_NOT_A_KEY = {"mesh-send", "mesh-ack", "mesh-recv", "mesh-claim", "ssh-keygen", "read_only",
              "installation_id", "docker exec", "git push", "gh api"}


def extract_key_names(body: str) -> list[str]:
    out, seen = [], set()
    for m in _KEYISH.finditer(body):
        tok = m.group(1)
        # skip things that are plainly not a filename on disk
        if tok.startswith(("http", "/")) or "/" in tok or tok.isdigit():
            continue
        if re.fullmatch(r"[0-9a-f]{7,40}", tok):  # a git sha
            continue
        if tok in _NOT_A_KEY or tok.startswith("mesh-"):
            continue
        # SHAPE, not just proximity (2026-09-20, josh-desk-2): their message said "worker-c's
        # `imgscan`" — a MODULE name — and the body happened to mention keys nearby, so the
        # key branch swept it up and printed MISSING for something that was never a claim about
        # a file. A MISSING that is not a defect trains readers to skim past MISSING lines,
        # which is exactly the failure this check exists to prevent. Every real key on these
        # desks carries a dot or a hyphen (`<repo>.com-write`, `jambot-josh-<repo>`); a bare
        # single word does not.
        # MEASURED SHAPE, not "has punctuation". The dot-or-hyphen rule still swept up REPO
        # names: 2026-09-20 this flagged `sprayfoaminsurance-ca` MISSING when the host merely
        # mentioned the repo in a sentence about keys. Measured across both stores on josh's
        # desk: 546 key files, 473 ending in `-write` (the rest are its `.broken-`/`.rotated-`
        # variants, which still contain it). The one case that started this feature —
        # `jambot-josh-tracthomecontractorinsurance.com`, a GitHub deploy-key TITLE the host
        # asserted as a file — begins `jambot-`. Those two shapes catch the real thing and
        # leave repo names alone.
        if "-write" not in tok and not tok.startswith("jambot-"):
            continue
        lo, hi = max(0, m.start() - _WINDOW), min(len(body), m.end() + _WINDOW)
        if not _KEY_NEAR.search(body[lo:hi]):
            continue
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def extract_paths(body: str) -> list[str]:
    seen, out = set(), []
    for raw in _PATH_RE.findall(body):
        p = raw.rstrip(_TRAIL)
        if not p.startswith(CONTAINER_PREFIXES):
            continue
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def check(body: str, recipients: list[str]) -> list[tuple[str, str, str]]:
    """Return [(path, verdict, detail)] for every container path asserted in the body.

    verdict is one of OK / MISSING / UNCHECKABLE.
    """
    paths = extract_paths(body)
    keys = extract_key_names(body)
    # A bare key name is checked as "does a file by this name exist in either key store".
    probes = list(paths) + [f"{d}/{k}" for k in keys for d in _KEY_STORES]
    if not probes:
        return []
    if os.environ.get("MESH_SKIP_PATH_CHECK"):
        return [(p, "UNCHECKABLE", "MESH_SKIP_PATH_CHECK set") for p in paths]

    # SAME-CONTAINER PEERS: a desk writing to another desk in the SAME container shares its
    # filesystem, so the recipient's namespace IS this one and a local stat is the RIGHT vantage —
    # no docker required. This is most of the traffic between the josh desks, and before this it
    # fell into the docker path, failed FileNotFoundError, and was reported UNVERIFIED (correctly,
    # but uselessly). Only used when docker is genuinely unreachable from here.
    if _docker(["version"])[0] == 127:
        findings = []
        for p in paths + [f"{d}/{k}" for k in keys for d in _KEY_STORES]:
            label = p if p in paths else p.rsplit("/", 1)[-1]
            findings.append((label, "OK" if os.path.exists(p) else "MISSING",
                             "checked on THIS filesystem (no docker here; valid only because the "
                             "recipient shares this container)"))
        return findings

    findings: list[tuple[str, str, str]] = []
    for agent in recipients:
        cname, why = container_for(agent)
        if cname is None:
            if why == "not a desk agent":
                continue
            findings += [(p, "UNCHECKABLE", f"{agent}: {why}") for p in paths]
            findings += [(k, "UNCHECKABLE", f"{agent}: {why}") for k in keys]
            continue
        # One exec for all probes: cheaper than one per path (runc init was the box's biggest
        # fork source on 2026-08-27) and it keeps the check to a single container attach.
        script = "; ".join(f'[ -e "{p}" ] && echo "OK {p}" || echo "MISSING {p}"' for p in probes)
        try:
            rc, out, err = _docker(["exec", "-u", "abc", cname, "sh", "-c", f"'{script}'"], timeout=40)
        except subprocess.TimeoutExpired:
            findings += [(p, "UNCHECKABLE", f"{agent}: docker exec timed out") for p in paths]
            continue
        if rc != 0:
            findings += [(p, "UNCHECKABLE", f"{agent}: docker exec rc={rc} {err[:80]}") for p in probes]
            continue
        got = {}
        for line in out.splitlines():
            if " " in line:
                v, _, p = line.partition(" ")
                got[p.strip()] = v.strip()
        for p in paths:
            v = got.get(p)
            if v in ("OK", "MISSING"):
                findings.append((p, v, f"{agent} ({cname})"))
            else:
                findings.append((p, "UNCHECKABLE", f"{agent}: no verdict line returned"))
        for k in keys:
            vs = [got.get(f"{d}/{k}") for d in _KEY_STORES]
            if "OK" in vs:
                findings.append((k, "OK", f"{agent} ({cname}) key store"))
            elif all(v == "MISSING" for v in vs):
                findings.append((k, "MISSING",
                                 f"{agent} ({cname}): no key file by that name in {' or '.join(_KEY_STORES)}"))
            else:
                findings.append((k, "UNCHECKABLE", f"{agent}: no verdict line returned"))
    seen_lbl = set()
    deduped = []
    for lbl, verdict, detail in findings:
        # One row per thing mentioned. Probing two key stores for one name produced two
        # identical MISSING lines for a single occurrence (josh-desk-2, 2026-09-20). Keep the
        # most informative verdict: OK beats MISSING beats UNCHECKABLE.
        rank = {"OK": 0, "MISSING": 1, "UNCHECKABLE": 2}
        prev = next((i for i, x in enumerate(deduped) if x[0] == lbl), None)
        if prev is None:
            deduped.append((lbl, verdict, detail))
        elif rank.get(verdict, 9) < rank.get(deduped[prev][1], 9):
            deduped[prev] = (lbl, verdict, detail)
    return deduped


def render(findings) -> tuple[str, bool]:
    """Human-readable stderr block. Returns (text, any_problem)."""
    if not findings:
        return "", False
    bad = [f for f in findings if f[1] == "MISSING"]
    unk = [f for f in findings if f[1] == "UNCHECKABLE"]
    ok = [f for f in findings if f[1] == "OK"]
    lines = []
    if bad:
        lines.append("mesh-send: ⚠ PATH NOT PRESENT IN THE RECIPIENT'S NAMESPACE (advisory — message still sent):")
        for p, _, d in bad:
            lines.append(f"    MISSING  {p}   {d if d.startswith('checked') else 'checked inside ' + d}")
        lines.append("    A key is named by what it AUTHENTICATES to (ssh -T), never by filename or GitHub title.")
    if unk:
        lines.append("mesh-send: ? could not check these paths (NOT a pass):")
        for p, _, d in unk:
            lines.append(f"    UNCHECKABLE  {p}   {d}")
    if ok and (bad or unk):
        lines.append(f"mesh-send: {len(ok)} other path(s) verified present.")
    return "\n".join(lines), bool(bad or unk)
