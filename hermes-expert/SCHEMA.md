# Hermes Expert — Per-Section JSON Schema (v1)

Every file under `sections/<id>.json` MUST conform to this exact shape. Indexer agents read this file to stay in sync.

## Required shape

```json
{
  "id": "configuration",
  "title": "Configuration",
  "source_path": "website/docs/user-guide/configuration.md",
  "url": "https://hermes-agent.nousresearch.com/docs/user-guide/configuration",
  "category": "user-guide",
  "subcategory": "",
  "summary": "1-2 sentence purpose paraphrased from the doc lede.",
  "key_concepts": ["short noun phrase", "another concept"],
  "env_vars": [
    {"name": "ANTHROPIC_API_KEY", "purpose": "API key for Anthropic provider", "required": false, "default": null}
  ],
  "cli_commands": [
    {"command": "hermes config show", "purpose": "Print resolved config"}
  ],
  "config_keys": [
    {"path": "model.provider", "type": "string", "default": "anthropic", "description": "Model provider name", "example": "anthropic"}
  ],
  "slash_commands": [
    {"command": "/sessions", "purpose": "List & resume sessions"}
  ],
  "code_examples": [
    {"language": "yaml", "caption": "Minimal config", "code": "model:\n  provider: anthropic\n  default: claude-sonnet-4-5"}
  ],
  "gotchas": ["short string per gotcha"],
  "cross_refs": ["other-section-id"],
  "keywords": ["yaml", "config", "provider"],
  "full_text": "<full markdown body verbatim>"
}
```

## Rules

- **`id`** — kebab-case, derived from the source filename without `.md`. Disambiguate collisions across subcategories with a `<subcat>-<name>` form. See ID Map below.
- **Never omit a key.** If the doc has no env vars, set `"env_vars": []`. If subcategory empty, `""`. If a single default is null, use JSON `null` (not the string).
- **`full_text`** — copy the full markdown body between this section's `<!-- source: ... -->` marker and the next, with the marker stripped. Preserve fenced code blocks, lists, and tables verbatim. Escape `"` and `\n` inside the JSON string.
- **`summary`** — 1-2 sentences max, what THIS doc covers.
- **`key_concepts`** — 3-8 short noun phrases describing topics.
- **`env_vars` / `cli_commands` / `config_keys` / `slash_commands`** — extract everything the doc mentions explicitly. Don't invent. If the same env var is mentioned multiple times, list it once.
- **`code_examples`** — preserve every distinct code block. Use the language tag from the fence (or `""` if untagged). `caption` is short; can be `""` if the block is freestanding.
- **`gotchas`** — pitfalls, warnings, "common mistakes," `:::warning` callouts, "don't do X" notes. Short strings.
- **`cross_refs`** — `id`s of other sections referenced (e.g. by markdown link or `[See: X]`). Best-effort.
- **`keywords`** — 5-15 search terms a future agent might query, including synonyms.
- **JSON must be valid.** Validate by parsing before writing.

## Subagent return contract

Each bucket agent returns a single JSON object summarizing its bucket:

```json
{
  "bucket": "<bucket-name>",
  "manifest": [
    {
      "id": "configuration",
      "title": "Configuration",
      "category": "user-guide",
      "subcategory": "",
      "file": "sections/configuration.json",
      "summary": "...",
      "keywords": ["..."]
    }
  ]
}
```

Return only the JSON. No prose around it.

## ID Map (resolve collisions deterministically)

| Source path | id |
|---|---|
| `getting-started/installation.md` | `installation` |
| `getting-started/quickstart.md` | `quickstart` |
| `getting-started/learning-path.md` | `learning-path` |
| `getting-started/updating.md` | `updating` |
| `getting-started/termux.md` | `termux` |
| `getting-started/nix-setup.md` | `nix-setup` |
| `user-guide/cli.md` | `cli` |
| `user-guide/tui.md` | `tui` |
| `user-guide/configuration.md` | `configuration` |
| `user-guide/configuring-models.md` | `configuring-models` |
| `user-guide/sessions.md` | `sessions` |
| `user-guide/profiles.md` | `profiles` |
| `user-guide/git-worktrees.md` | `git-worktrees` |
| `user-guide/docker.md` | `docker` |
| `user-guide/security.md` | `security` |
| `user-guide/checkpoints-and-rollback.md` | `checkpoints-and-rollback` |
| `user-guide/features/overview.md` | `features-overview` |
| `user-guide/features/tools.md` | `tools` |
| `user-guide/features/skills.md` | `skills` |
| `user-guide/features/curator.md` | `curator` |
| `user-guide/features/memory.md` | `memory` |
| `user-guide/features/memory-providers.md` | `memory-providers` |
| `user-guide/features/context-files.md` | `context-files` |
| `user-guide/features/context-references.md` | `context-references` |
| `user-guide/features/personality.md` | `personality` |
| `user-guide/features/plugins.md` | `plugins` |
| `user-guide/features/built-in-plugins.md` | `built-in-plugins` |
| `user-guide/features/cron.md` | `cron` |
| `user-guide/features/delegation.md` | `delegation` |
| `user-guide/features/kanban.md` | `kanban` |
| `user-guide/features/kanban-tutorial.md` | `kanban-tutorial` |
| `user-guide/features/goals.md` | `goals` |
| `user-guide/features/code-execution.md` | `code-execution` |
| `user-guide/features/hooks.md` | `hooks` |
| `user-guide/features/batch-processing.md` | `batch-processing` |
| `user-guide/features/voice-mode.md` | `voice-mode` |
| `user-guide/features/browser.md` | `browser` |
| `user-guide/features/vision.md` | `vision` |
| `user-guide/features/image-generation.md` | `image-generation` |
| `user-guide/features/tts.md` | `tts` |
| `user-guide/messaging/index.md` | `messaging-overview` |
| `user-guide/messaging/telegram.md` | `messaging-telegram` |
| `user-guide/messaging/discord.md` | `messaging-discord` |
| `user-guide/messaging/slack.md` | `messaging-slack` |
| `user-guide/messaging/whatsapp.md` | `messaging-whatsapp` |
| `user-guide/messaging/signal.md` | `messaging-signal` |
| `user-guide/messaging/email.md` | `messaging-email` |
| `user-guide/messaging/sms.md` | `messaging-sms` |
| `user-guide/messaging/matrix.md` | `messaging-matrix` |
| `user-guide/messaging/mattermost.md` | `messaging-mattermost` |
| `user-guide/messaging/homeassistant.md` | `messaging-homeassistant` |
| `user-guide/messaging/webhooks.md` | `messaging-webhooks` |
| `integrations/index.md` | `integrations-overview` |
| `integrations/providers.md` | `providers` |
| `user-guide/features/mcp.md` | `mcp` |
| `user-guide/features/acp.md` | `acp` |
| `user-guide/features/api-server.md` | `api-server` |
| `user-guide/features/honcho.md` | `honcho` |
| `user-guide/features/provider-routing.md` | `provider-routing` |
| `user-guide/features/fallback-providers.md` | `fallback-providers` |
| `user-guide/features/credential-pools.md` | `credential-pools` |
| `guides/tips.md` | `tips` |
| `guides/local-llm-on-mac.md` | `guide-local-llm-on-mac` |
| `guides/daily-briefing-bot.md` | `guide-daily-briefing-bot` |
| `guides/team-telegram-assistant.md` | `guide-team-telegram-assistant` |
| `guides/python-library.md` | `guide-python-library` |
| `guides/use-mcp-with-hermes.md` | `guide-use-mcp` |
| `guides/use-voice-mode-with-hermes.md` | `guide-use-voice-mode` |
| `guides/use-soul-with-hermes.md` | `guide-use-soul` |
| `guides/build-a-hermes-plugin.md` | `guide-build-plugin` |
| `guides/automate-with-cron.md` | `guide-automate-cron` |
| `guides/work-with-skills.md` | `guide-work-with-skills` |
| `guides/delegation-patterns.md` | `guide-delegation-patterns` |
| `guides/github-pr-review-agent.md` | `guide-gh-pr-review` |
| `developer-guide/contributing.md` | `dev-contributing` |
| `developer-guide/architecture.md` | `dev-architecture` |
| `developer-guide/agent-loop.md` | `dev-agent-loop` |
| `developer-guide/prompt-assembly.md` | `dev-prompt-assembly` |
| `developer-guide/context-compression-and-caching.md` | `dev-context-compression` |
| `developer-guide/gateway-internals.md` | `dev-gateway-internals` |
| `developer-guide/session-storage.md` | `dev-session-storage` |
| `developer-guide/provider-runtime.md` | `dev-provider-runtime` |
| `developer-guide/adding-tools.md` | `dev-adding-tools` |
| `developer-guide/adding-providers.md` | `dev-adding-providers` |
| `developer-guide/adding-platform-adapters.md` | `dev-adding-platform-adapters` |
| `developer-guide/creating-skills.md` | `dev-creating-skills` |
| `developer-guide/extending-the-cli.md` | `dev-extending-the-cli` |
| `developer-guide/acp-internals.md` | `dev-acp-internals` |
| `developer-guide/browser-supervisor.md` | `dev-browser-supervisor` |
| `developer-guide/context-engine-plugin.md` | `dev-context-engine-plugin` |
| `developer-guide/cron-internals.md` | `dev-cron-internals` |
| `developer-guide/image-gen-provider-plugin.md` | `dev-image-gen-plugin` |
| `developer-guide/memory-provider-plugin.md` | `dev-memory-provider-plugin` |
| `developer-guide/model-provider-plugin.md` | `dev-model-provider-plugin` |
| `developer-guide/plugin-llm-access.md` | `dev-plugin-llm-access` |
| `developer-guide/programmatic-integration.md` | `dev-programmatic-integration` |
| `developer-guide/tools-runtime.md` | `dev-tools-runtime` |
| `developer-guide/trajectory-format.md` | `dev-trajectory-format` |
| `developer-guide/video-gen-provider-plugin.md` | `dev-video-gen-plugin` |
| `reference/cli-commands.md` | `ref-cli-commands` |
| `reference/slash-commands.md` | `ref-slash-commands` |
| `reference/profile-commands.md` | `ref-profile-commands` |
| `reference/environment-variables.md` | `ref-environment-variables` |
| `reference/tools-reference.md` | `ref-tools` |
| `reference/toolsets-reference.md` | `ref-toolsets` |
| `reference/mcp-config-reference.md` | `ref-mcp-config` |
| `reference/model-catalog.md` | `ref-model-catalog` |
| `reference/skills-catalog.md` | `ref-skills-catalog` |
| `reference/optional-skills-catalog.md` | `ref-optional-skills-catalog` |
| `reference/faq.md` | `ref-faq` |
| `guides/automation-templates.md` | `guide-automation-templates` |
| `guides/aws-bedrock.md` | `guide-aws-bedrock` |
| `guides/azure-foundry.md` | `guide-azure-foundry` |
| `guides/cron-script-only.md` | `guide-cron-script-only` |
| `guides/cron-troubleshooting.md` | `guide-cron-troubleshooting` |
| `guides/google-gemini.md` | `guide-google-gemini` |
| `guides/local-ollama-setup.md` | `guide-local-ollama-setup` |
| `guides/microsoft-graph-app-registration.md` | `guide-microsoft-graph` |
| `guides/migrate-from-openclaw.md` | `guide-migrate-from-openclaw` |
| `guides/minimax-oauth.md` | `guide-minimax-oauth` |
| `guides/oauth-over-ssh.md` | `guide-oauth-over-ssh` |
| `guides/operate-teams-meeting-pipeline.md` | `guide-operate-teams-meeting` |
| `guides/webhook-github-pr-review.md` | `guide-webhook-gh-pr-review` |
| `guides/xai-grok-oauth.md` | `guide-xai-grok-oauth` |
| `docs/index.md` | `docs-index` |
| `user-guide/features/codex-app-server-runtime.md` | `codex-app-server-runtime` |
| `user-guide/features/computer-use.md` | `computer-use` |
| `user-guide/features/extending-the-dashboard.md` | `extending-dashboard` |
| `user-guide/features/kanban-worker-lanes.md` | `kanban-worker-lanes` |
| `user-guide/features/lsp.md` | `lsp` |
| `user-guide/features/skins.md` | `skins` |
| `user-guide/features/spotify.md` | `spotify` |
| `user-guide/features/subscription-proxy.md` | `subscription-proxy` |
| `user-guide/features/tool-gateway.md` | `tool-gateway` |
| `user-guide/features/web-dashboard.md` | `web-dashboard` |
| `user-guide/features/web-search.md` | `web-search` |
| `user-guide/messaging/bluebubbles.md` | `messaging-bluebubbles` |
| `user-guide/messaging/dingtalk.md` | `messaging-dingtalk` |
| `user-guide/messaging/feishu.md` | `messaging-feishu` |
| `user-guide/messaging/google_chat.md` | `messaging-google-chat` |
| `user-guide/messaging/line.md` | `messaging-line` |
| `user-guide/messaging/msgraph-webhook.md` | `messaging-msgraph-webhook` |
| `user-guide/messaging/open-webui.md` | `messaging-open-webui` |
| `user-guide/messaging/qqbot.md` | `messaging-qqbot` |
| `user-guide/messaging/simplex.md` | `messaging-simplex` |
| `user-guide/messaging/teams-meetings.md` | `messaging-teams-meetings` |
| `user-guide/messaging/teams.md` | `messaging-teams` |
| `user-guide/messaging/wecom-callback.md` | `messaging-wecom-callback` |
| `user-guide/messaging/wecom.md` | `messaging-wecom` |
| `user-guide/messaging/weixin.md` | `messaging-weixin` |
| `user-guide/messaging/yuanbao.md` | `messaging-yuanbao` |
| `user-guide/profile-distributions.md` | `profile-distributions` |
| `user-guide/skills/godmode.md` | `godmode-skill` |
| `user-guide/skills/google-workspace.md` | `google-workspace-skill` |
| `user-guide/windows-native.md` | `windows-native` |
| `user-guide/windows-wsl-quickstart.md` | `windows-wsl-quickstart` |
