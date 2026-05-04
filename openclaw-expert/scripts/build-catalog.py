#!/usr/bin/env python3
"""
Build catalog.json from upstream llms.txt.

Parses flat `- [Title](URL)` list, derives section from URL path,
applies JamBot relevance heuristic, preserves existing annotation
links + lastVerified timestamps when re-running.

Usage:
  python3 build-catalog.py [--input /path/to/llms.txt] [--output catalog.json]
  python3 build-catalog.py --diff   # compare new fetch against current catalog.json
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UPSTREAM = "https://docs.openclaw.ai/llms.txt"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = SKILL_ROOT / "catalog.json"

LINK_RE = re.compile(r"^\s*-\s*\[(?P<title>.+?)\]\((?P<url>https?://[^)]+)\)\s*$")

# Section taxonomy keyed by URL path prefix
SECTION_MAP = {
    "automation/": "Automation",
    "channels/": "Channels",
    "cli/": "CLI",
    "concepts/": "Concepts",
    "debug/": "Debug",
    "diagnostics/": "Diagnostics",
    "gateway/security/": "Gateway/Security",
    "gateway/": "Gateway",
    "help/": "Help",
    "install/": "Install",
    "nodes/": "Nodes",
    "platforms/mac/": "Platform/macOS",
    "platforms/": "Platform",
    "plugins/": "Plugins",
    "providers/": "Providers",
    "reference/templates/": "Reference/Templates",
    "reference/": "Reference",
    "security/": "Security",
    "start/": "Start",
    "tools/": "Tools",
    "web/": "Web",
    "api-reference/": "API",
}

# JamBot relevance heuristic
HIGH_RELEVANCE_PATHS = {
    # Concepts
    "concepts/compaction.md", "concepts/session.md", "concepts/session-pruning.md",
    "concepts/agent.md", "concepts/agent-loop.md", "concepts/agent-runtimes.md",
    "concepts/agent-workspace.md", "concepts/architecture.md", "concepts/context.md",
    "concepts/context-engine.md", "concepts/delegate-architecture.md",
    "concepts/memory.md", "concepts/memory-builtin.md", "concepts/memory-honcho.md",
    "concepts/memory-qmd.md", "concepts/memory-search.md", "concepts/active-memory.md",
    "concepts/model-failover.md", "concepts/model-providers.md", "concepts/multi-agent.md",
    "concepts/queue.md", "concepts/queue-steering.md", "concepts/retry.md",
    "concepts/streaming.md", "concepts/system-prompt.md", "concepts/soul.md",
    "concepts/dreaming.md", "concepts/commitments.md",
    # Gateway
    "gateway/configuration.md", "gateway/configuration-reference.md", "gateway/configuration-examples.md",
    "gateway/config-agents.md", "gateway/config-channels.md", "gateway/config-tools.md",
    "gateway/index.md", "gateway/heartbeat.md", "gateway/health.md", "gateway/doctor.md",
    "gateway/local-models.md", "gateway/multiple-gateways.md", "gateway/bridge-protocol.md",
    "gateway/protocol.md", "gateway/openai-http-api.md", "gateway/openresponses-http-api.md",
    "gateway/sandbox-vs-tool-policy-vs-elevated.md", "gateway/sandboxing.md",
    "gateway/trusted-proxy-auth.md", "gateway/operator-scopes.md",
    "gateway/troubleshooting.md", "gateway/network-model.md",
    "gateway/tools-invoke-http-api.md", "gateway/background-process.md",
    "gateway/secrets.md", "gateway/authentication.md",
    # Plugins
    "plugins/architecture.md", "plugins/architecture-internals.md",
    "plugins/building-plugins.md", "plugins/sdk-overview.md", "plugins/sdk-channel-plugins.md",
    "plugins/sdk-channel-turn.md", "plugins/sdk-provider-plugins.md", "plugins/sdk-agent-harness.md",
    "plugins/sdk-runtime.md", "plugins/sdk-setup.md", "plugins/sdk-entrypoints.md",
    "plugins/sdk-subpaths.md", "plugins/sdk-testing.md", "plugins/sdk-migration.md",
    "plugins/manifest.md", "plugins/voice-call.md", "plugins/codex-computer-use.md",
    "plugins/codex-harness.md", "plugins/memory-lancedb.md", "plugins/memory-wiki.md",
    "plugins/google-meet.md", "plugins/webhooks.md", "plugins/skill-workshop.md",
    "plugins/manage-plugins.md", "plugins/dependency-resolution.md",
    "plugins/plugin-inventory.md", "plugins/reference.md",
    # Providers we use
    "providers/zai.md", "providers/glm.md", "providers/minimax.md", "providers/groq.md",
    "providers/anthropic.md", "providers/openai.md", "providers/ollama.md",
    "providers/openrouter.md", "providers/index.md", "providers/models.md",
    "providers/elevenlabs.md", "providers/deepgram.md",
    # Reference
    "reference/prompt-caching.md", "reference/session-management-compaction.md",
    "reference/transcript-hygiene.md", "reference/token-use.md", "reference/api-usage-costs.md",
    "reference/AGENTS.default.md", "reference/templates/AGENTS.md", "reference/templates/SOUL.md",
    "reference/templates/BOOT.md", "reference/templates/BOOTSTRAP.md",
    "reference/templates/HEARTBEAT.md", "reference/templates/IDENTITY.md",
    "reference/templates/TOOLS.md", "reference/templates/USER.md",
    "reference/memory-config.md", "reference/rich-output-protocol.md",
    "reference/rpc.md", "reference/secretref-credential-surface.md",
    # Tools
    "tools/index.md", "tools/exec.md", "tools/exec-approvals.md", "tools/exec-approvals-advanced.md",
    "tools/elevated.md", "tools/browser.md", "tools/browser-control.md", "tools/browser-login.md",
    "tools/skills.md", "tools/skills-config.md", "tools/creating-skills.md", "tools/clawhub.md",
    "tools/slash-commands.md", "tools/subagents.md", "tools/thinking.md", "tools/steer.md",
    "tools/web.md", "tools/web-fetch.md", "tools/code-execution.md", "tools/apply-patch.md",
    "tools/trajectory.md", "tools/loop-detection.md", "tools/multi-agent-sandbox-tools.md",
    "tools/agent-send.md", "tools/llm-task.md",
    # Automation
    "automation/index.md", "automation/cron-jobs.md", "automation/hooks.md",
    "automation/standing-orders.md", "automation/taskflow.md", "automation/tasks.md",
    # Security
    "security/THREAT-MODEL-ATLAS.md", "security/network-proxy.md",
    # Channels we use
    "channels/index.md", "channels/whatsapp.md", "channels/telegram.md", "channels/discord.md",
    "channels/slack.md", "channels/signal.md", "channels/imessage.md", "channels/bluebubbles.md",
    "channels/matrix.md", "channels/access-groups.md", "channels/channel-routing.md",
    "channels/group-messages.md", "channels/pairing.md", "channels/troubleshooting.md",
    # Install
    "install/docker.md", "install/hetzner.md", "install/kubernetes.md", "install/podman.md",
    "install/clawdock.md", "install/installer.md", "install/updating.md",
    "install/development-channels.md",
    # Web
    "web/index.md", "web/control-ui.md", "web/dashboard.md", "web/webchat.md",
    # Help
    "help/faq.md", "help/faq-models.md", "help/environment.md", "help/troubleshooting.md",
    "help/debugging.md",
    # CLI core
    "cli/index.md", "cli/gateway.md", "cli/agents.md", "cli/skills.md", "cli/plugins.md",
    "cli/sessions.md", "cli/memory.md", "cli/cron.md", "cli/hooks.md", "cli/doctor.md",
    "cli/health.md", "cli/sandbox.md", "cli/config.md", "cli/voicecall.md", "cli/mcp.md",
    "cli/secrets.md", "cli/security.md", "cli/browser.md",
    # Nodes (canvas)
    "nodes/index.md", "nodes/audio.md", "nodes/voicewake.md", "nodes/talk.md",
    # Start
    "start/getting-started.md", "start/setup.md", "start/bootstrapping.md",
    # Misc
    "auth-credential-semantics.md", "logging.md", "network.md",
}

LOW_RELEVANCE_PATHS = {
    # Platform-specific stuff JamBot doesn't use
    "pi.md", "pi-dev.md",
    # Install on clouds we don't use
    "install/azure.md", "install/gcp.md", "install/oracle.md", "install/render.md",
    "install/northflank.md", "install/fly.md", "install/railway.md", "install/hostinger.md",
    "install/exe-dev.md", "install/nix.md", "install/digitalocean.md", "install/macos-vm.md",
    "install/raspberry-pi.md", "install/ansible.md", "install/migrating-claude.md",
    "install/migrating-hermes.md",
    # Channels we don't use
    "channels/feishu.md", "channels/googlechat.md", "channels/irc.md", "channels/line.md",
    "channels/mattermost.md", "channels/msteams.md", "channels/nextcloud-talk.md",
    "channels/nostr.md", "channels/qa-channel.md", "channels/qqbot.md",
    "channels/synology-chat.md", "channels/tlon.md", "channels/twitch.md",
    "channels/wechat.md", "channels/yuanbao.md", "channels/zalo.md", "channels/zalouser.md",
    "channels/location.md", "channels/matrix-migration.md", "channels/matrix-push-rules.md",
    "channels/broadcast-groups.md", "channels/groups.md",
    # Providers we don't use
    "providers/alibaba.md", "providers/arcee.md", "providers/azure-speech.md",
    "providers/bedrock.md", "providers/bedrock-mantle.md", "providers/cerebras.md",
    "providers/chutes.md", "providers/cloudflare-ai-gateway.md", "providers/comfy.md",
    "providers/deepinfra.md", "providers/deepseek.md", "providers/fal.md",
    "providers/fireworks.md", "providers/github-copilot.md", "providers/google.md",
    "providers/gradium.md", "providers/huggingface.md", "providers/inferrs.md",
    "providers/inworld.md", "providers/kilocode.md", "providers/litellm.md",
    "providers/lmstudio.md", "providers/mistral.md", "providers/moonshot.md",
    "providers/nvidia.md", "providers/opencode.md", "providers/opencode-go.md",
    "providers/perplexity-provider.md", "providers/qianfan.md", "providers/qwen.md",
    "providers/runway.md", "providers/senseaudio.md", "providers/sglang.md",
    "providers/stepfun.md", "providers/synthetic.md", "providers/tencent.md",
    "providers/together.md", "providers/venice.md", "providers/vercel-ai-gateway.md",
    "providers/vllm.md", "providers/volcengine.md", "providers/vydra.md",
    "providers/xai.md", "providers/xiaomi.md", "providers/claude-max-api-proxy.md",
    # Platform pages
    "platforms/index.md", "platforms/android.md", "platforms/ios.md", "platforms/linux.md",
    "platforms/macos.md", "platforms/windows.md",
}


def fetch_upstream(url: str) -> tuple[str, str]:
    """Fetch URL, return (text, sha256)."""
    req = urllib.request.Request(url, headers={"User-Agent": "openclaw-expert-catalog/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    return body.decode("utf-8"), hashlib.sha256(body).hexdigest()


def parse_links(text: str) -> list[dict]:
    """Extract (title, url) pairs from llms.txt body."""
    out = []
    for line in text.splitlines():
        m = LINK_RE.match(line)
        if not m:
            continue
        out.append({"title": m.group("title"), "url": m.group("url")})
    return out


def derive_section(url: str) -> str:
    path = url.replace("https://docs.openclaw.ai/", "")
    for prefix, name in SECTION_MAP.items():
        if path.startswith(prefix):
            return name
    return "Root"


def derive_id(url: str) -> str:
    path = url.replace("https://docs.openclaw.ai/", "").replace(".md", "")
    return path.replace("/", "__")


def derive_relevance(url: str) -> str:
    path = url.replace("https://docs.openclaw.ai/", "")
    if path in HIGH_RELEVANCE_PATHS:
        return "high"
    if path in LOW_RELEVANCE_PATHS:
        return "low"
    return "med"


def build_pages(links: list[dict]) -> list[dict]:
    seen_ids = set()
    pages = []
    for link in links:
        url = link["url"]
        if not url.startswith("https://docs.openclaw.ai/"):
            continue
        pid = derive_id(url)
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        pages.append({
            "id": pid,
            "url": url,
            "section": derive_section(url),
            "title": link["title"],
            "relevance": derive_relevance(url),
            "annotation": None,
            "audit_anchors": [],
            "lastVerified": None,
            "tags": [],
        })
    return pages


def merge_existing(new_pages: list[dict], existing_path: Path) -> list[dict]:
    """Preserve annotation/audit_anchors/lastVerified/tags from existing catalog."""
    if not existing_path.exists():
        return new_pages
    try:
        existing = json.loads(existing_path.read_text())
    except json.JSONDecodeError:
        return new_pages
    by_id = {p["id"]: p for p in existing.get("pages", [])}
    for page in new_pages:
        prior = by_id.get(page["id"])
        if not prior:
            continue
        for k in ("annotation", "audit_anchors", "lastVerified", "tags"):
            if prior.get(k):
                page[k] = prior[k]
    return new_pages


def diff_against(new_pages: list[dict], existing_path: Path) -> dict:
    """Return added/removed/title-changed lists."""
    if not existing_path.exists():
        return {"added": [p["id"] for p in new_pages], "removed": [], "title_changed": []}
    existing = json.loads(existing_path.read_text())
    old_by_id = {p["id"]: p for p in existing.get("pages", [])}
    new_by_id = {p["id"]: p for p in new_pages}
    added = [pid for pid in new_by_id if pid not in old_by_id]
    removed = [pid for pid in old_by_id if pid not in new_by_id]
    title_changed = [
        {"id": pid, "old": old_by_id[pid]["title"], "new": new_by_id[pid]["title"]}
        for pid in new_by_id
        if pid in old_by_id and old_by_id[pid]["title"] != new_by_id[pid]["title"]
    ]
    return {"added": added, "removed": removed, "title_changed": title_changed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="Local llms.txt path (skip fetch)")
    ap.add_argument("--output", default=str(DEFAULT_OUT))
    ap.add_argument("--diff", action="store_true", help="Print diff against existing catalog and exit")
    args = ap.parse_args()

    if args.input:
        text = Path(args.input).read_text()
        sha = hashlib.sha256(text.encode()).hexdigest()
    else:
        text, sha = fetch_upstream(UPSTREAM)

    links = parse_links(text)
    pages = build_pages(links)

    out_path = Path(args.output)

    if args.diff:
        d = diff_against(pages, out_path)
        print(json.dumps(d, indent=2))
        return

    pages = merge_existing(pages, out_path)
    pages.sort(key=lambda p: (p["section"], p["id"]))

    catalog = {
        "schema": "openclaw-expert-catalog/1",
        "upstream": UPSTREAM,
        "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "upstreamSha256": sha,
        "pageCount": len(pages),
        "relevanceCounts": {
            "high": sum(1 for p in pages if p["relevance"] == "high"),
            "med": sum(1 for p in pages if p["relevance"] == "med"),
            "low": sum(1 for p in pages if p["relevance"] == "low"),
        },
        "pages": pages,
    }

    out_path.write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"Wrote {out_path} — {len(pages)} pages "
          f"(high={catalog['relevanceCounts']['high']}, "
          f"med={catalog['relevanceCounts']['med']}, "
          f"low={catalog['relevanceCounts']['low']})")


if __name__ == "__main__":
    main()
