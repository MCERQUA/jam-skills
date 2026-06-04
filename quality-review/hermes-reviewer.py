#!/usr/bin/env python3
"""hermes-reviewer.py — ONE seat in the Quality Council: an independent Hermes reviewer.

The Quality Council is a TEAM of parallel lenses (correctness, security, data, lifecycle,
cross-system, UX) + the automated quality-review checks. This script is *one* additional
seat: it asks the Hermes agent — which runs its OWN framework + memory, so it reasons
divergently from the openclaw/Claude lenses — to review a finished deliverable and return
findings in the council's three tiers (BLOCKER / PASS-WITH-NOTE / CONSIDERATION).

It does NOT replace the council. The host/orchestrator consolidates this reviewer's findings
with the other lenses, fixes blockers, and re-runs until a clean round (see
docs/jambot/quality-council-system.md).

Hermes is reached via its OpenAI-compatible API on the container (port 18790, not host-
published → called via `docker exec`). A FRESH session id per review avoids the known
poisoned-session empty-response bug (memory: hermes-session-poison-empty-response).

Usage:
  hermes-reviewer.py --target-file /path/to/deliverable.html --kind "brand report" \
      --context "On The Mark Spray Foam onboarding brand report" --out /tmp/hermes-review.json
  hermes-reviewer.py --target-url https://garage-sale.jam-bot.com --kind website
  echo "<text to review>" | hermes-reviewer.py --kind "plan" --stdin

Exit code: 0 always (a reviewer never blocks the pipeline by crashing); BLOCKER findings are
in the JSON for the consolidator to act on. Prints the findings JSON to stdout.
"""
import argparse, json, os, subprocess, sys, time, uuid

HERMES_CONTAINER = os.environ.get("HERMES_REVIEW_CONTAINER", "hermes-test-dev")
HERMES_PORT = "18790"
HERMES_KEY = "a3dca84ebfd971a4f50b620b36c1a9bc59e90be9f8058fab35ca362a6ec4597d"
MAX_CONTENT = 18000  # cap content sent to keep the review prompt sane

RUBRIC = """You are ONE independent reviewer on a Quality Council — a multi-perspective review
team. Other reviewers cover correctness, security, data, lifecycle, cross-system, and UX. YOUR
value is your independent judgment: review this deliverable from your own perspective and surface
what a real review would catch before shipping to a paying client or to the operator (Mike).

Return findings in EXACTLY three severity tiers — and DO NOT be over-picky (a flagged-and-tracked
note is better than blocking on polish):
- BLOCKER: real correctness bug, security/credential issue, data-loss, broken/dead/missing content,
  fabricated or placeholder data, or anything that would embarrass us in front of the client. Must fix before ship.
- PASS-WITH-NOTE: fine to ship, but attach a follow-up to monitor/schedule/watch.
- CONSIDERATION: polish / nice-to-have. Not a blocker.

Respond with ONLY a JSON object, no prose before or after:
{"verdict":"PASS|FAIL","summary":"<one line>","findings":[{"tier":"BLOCKER|PASS-WITH-NOTE|CONSIDERATION","area":"<short>","issue":"<what>","fix":"<suggested fix>"}]}
verdict=FAIL iff there is at least one BLOCKER."""


def load_content(args) -> str:
    if args.stdin:
        return sys.stdin.read()
    if args.target_file:
        try:
            return open(args.target_file, encoding="utf-8", errors="replace").read()
        except Exception as e:
            return f"(could not read {args.target_file}: {e})"
    if args.target_url:
        # fetch via the container's curl (host may be datacenter-blocked; keep it simple)
        try:
            r = subprocess.run(["curl", "-s", "-m", "20", "-L", args.target_url],
                               capture_output=True, text=True, timeout=30)
            return r.stdout or f"(empty fetch from {args.target_url})"
        except Exception as e:
            return f"(could not fetch {args.target_url}: {e})"
    return ""


def call_hermes(prompt: str, timeout_s: int = 180) -> str:
    """POST to Hermes OpenAI-compatible API via docker exec. Fresh session id (anti-poison)."""
    sid = f"qc-review-{uuid.uuid4().hex[:12]}"
    payload = {
        "model": "hermes-agent",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0.3,
    }
    host_tmp = f"/tmp/hermes-review-{sid}.json"
    open(host_tmp, "w").write(json.dumps(payload))
    cont_tmp = f"/tmp/{os.path.basename(host_tmp)}"
    try:
        subprocess.run(["sg", "docker", "-c",
                        f"docker cp {host_tmp} {HERMES_CONTAINER}:{cont_tmp}"],
                       check=True, capture_output=True, timeout=30)
        cmd = (f"docker exec {HERMES_CONTAINER} curl -s -m {timeout_s} "
               f"-H 'Authorization: Bearer {HERMES_KEY}' "
               f"-H 'Content-Type: application/json' "
               f"-H 'X-Hermes-Session-Id: {sid}' "
               f"-d @{cont_tmp} http://localhost:{HERMES_PORT}/v1/chat/completions")
        r = subprocess.run(["sg", "docker", "-c", cmd],
                           capture_output=True, text=True, timeout=timeout_s + 30)
        out = r.stdout.strip()
        try:
            data = json.loads(out)
            return (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        except Exception:
            return out  # raw (may already be the content)
    except Exception as e:
        return f'{{"verdict":"ERROR","summary":"hermes call failed: {e}","findings":[]}}'
    finally:
        try:
            os.remove(host_tmp)
            subprocess.run(["sg", "docker", "-c", f"docker exec {HERMES_CONTAINER} rm -f {cont_tmp}"],
                           capture_output=True, timeout=15)
        except Exception:
            pass


def extract_json(text: str) -> dict:
    text = text.strip()
    # strip code fences
    if "```" in text:
        import re
        m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
        if m:
            text = m.group(1)
    # find first {...} block
    s, e = text.find("{"), text.rfind("}")
    if s >= 0 and e > s:
        try:
            return json.loads(text[s:e + 1])
        except Exception:
            pass
    return {"verdict": "UNPARSED", "summary": "hermes returned non-JSON", "findings": [],
            "raw": text[:800]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-file")
    ap.add_argument("--target-url")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--kind", default="deliverable")
    ap.add_argument("--context", default="")
    ap.add_argument("--out")
    args = ap.parse_args()

    content = load_content(args)
    if len(content) > MAX_CONTENT:
        content = content[:MAX_CONTENT] + f"\n\n...[truncated {len(content)-MAX_CONTENT} chars]"

    prompt = (f"{RUBRIC}\n\n=== DELIVERABLE TO REVIEW ===\n"
              f"Kind: {args.kind}\nContext: {args.context}\n\n--- content ---\n{content}\n--- end ---")

    print(f"[hermes-reviewer] reviewing {args.kind} via {HERMES_CONTAINER} ...", file=sys.stderr)
    t0 = time.time()
    raw = call_hermes(prompt)
    result = extract_json(raw)
    result["_reviewer"] = "hermes"
    result["_elapsed_s"] = round(time.time() - t0, 1)

    out_json = json.dumps(result, indent=2)
    if args.out:
        open(args.out, "w").write(out_json)
    print(out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
