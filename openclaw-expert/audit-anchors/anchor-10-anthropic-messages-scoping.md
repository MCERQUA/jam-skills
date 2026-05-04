---
anchor: 10
slug: anthropic-messages-scoping
status: confirmed
introduced: v2026.4.20
changelog_line: 2357
upstream_pages:
  - https://docs.openclaw.ai/providers/anthropic.md
  - https://docs.openclaw.ai/providers/openai.md
old_behavior: "anthropic-messages auto-defaulting applied to all providers without explicit api"
new_behavior: "scoped to Anthropic-owned providers only"
skill_files_affected:
  - "references/models-and-providers.md"
---

# Anchor #10 — Anthropic-messages auto-defaulting scoped

## What changed

v4.20 line 2357: "Anthropic/plugins: scope Anthropic `api: "anthropic-messages"` defaulting to Anthropic-owned providers, so `openai-codex` and other providers without an explicit `api` no longer get rewritten to the wrong transport. Fixes #64534."

## Symptom this fixed

Custom providers (e.g. `openai-codex`, third-party Anthropic-compat shims, internal anthropic-style proxies) were being silently rewritten to use anthropic-messages transport even when they spoke OpenAI chat-completions. Result: opaque transport errors, broken tool calls.

## Required action for custom providers

Any provider that uses anthropic-compat transport MUST now explicitly set:
```json5
{ providers: { custom: { api: "anthropic-messages", ... } } }
```

The auto-default is removed.

## JamBot impact

If any client config references a custom provider with `api` unset and expects anthropic-style behavior, it will break on 4.20+. Audit before pushing.

## Fix instruction

`annotations/providers__anthropic.md`: add note about explicit `api` requirement for custom providers post-v4.20.
