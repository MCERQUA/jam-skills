# OpenClaw Web Tools Reference

Two lightweight web tools for search and content extraction. NOT browser automation — use the Browser tool for JS-heavy sites.

---

## Tools

| Tool | Purpose | Default |
|------|---------|---------|
| `web_search` | Search via Perplexity, Brave, Gemini, Grok, or Kimi | Enabled (needs API key) |
| `web_fetch` | HTTP GET + readable extraction (HTML → markdown/text) | Enabled by default |

Results cached 15 minutes (configurable).

---

## Search Providers

| Provider | Env Var | Pros | Notes |
|----------|---------|------|-------|
| **Perplexity** | `PERPLEXITY_API_KEY` | Domain/language/region/freshness filters, content extraction | `tools.web.search.perplexity.apiKey` |
| **Brave** | `BRAVE_API_KEY` | Fast, structured results | `tools.web.search.apiKey` |
| **Gemini** | `GEMINI_API_KEY` | Google Search grounding, AI-synthesized | `tools.web.search.gemini.apiKey` |
| **Grok** | `XAI_API_KEY` | xAI web-grounded responses | `tools.web.search.grok.apiKey` |
| **Kimi** | `KIMI_API_KEY` / `MOONSHOT_API_KEY` | Moonshot web search | `tools.web.search.kimi.apiKey` |

### Auto-Detection Order

If no `provider` set, checks keys in order: Brave → Gemini → Kimi → Perplexity → Grok. Falls back to Brave (missing-key error).

### Setup

```bash
openclaw configure --section web   # interactive key setup
```

Or set env var in `~/.openclaw/.env`.

---

## web_search Config

```json5
{
  tools: {
    web: {
      search: {
        enabled: true,
        provider: "brave",           // or "perplexity", "gemini", "grok", "kimi"
        apiKey: "BSA...",             // Brave key (or use env var)
        maxResults: 5,
        timeoutSeconds: 30,
        cacheTtlMinutes: 15,
        // Perplexity-specific:
        perplexity: { apiKey: "pplx-..." },
        // Gemini-specific:
        gemini: { apiKey: "AIza...", model: "gemini-2.5-flash" },
        // Grok-specific:
        grok: { apiKey: "xai-..." },
        // Kimi-specific:
        kimi: { apiKey: "..." },
      },
    },
  },
}
```

### web_search Parameters

| Parameter | Description |
|-----------|-------------|
| `query` | Search query (required) |
| `count` | Results to return (1–10, default 5) |
| `country` | 2-letter ISO code (e.g. "US", "DE") |
| `language` | ISO 639-1 code (e.g. "en", "de") |
| `freshness` | `day`, `week`, `month`, `year` |
| `date_after` | Results after YYYY-MM-DD |
| `date_before` | Results before YYYY-MM-DD |
| `ui_lang` | UI language (Brave only) |
| `domain_filter` | Domain allow/deny array (Perplexity only). Prefix `-` to exclude |
| `max_tokens` | Total content budget, default 25000 (Perplexity only) |
| `max_tokens_per_page` | Per-page token limit, default 2048 (Perplexity only) |

### Gemini Notes

- Citation URLs auto-resolved from Google redirect URLs to direct URLs
- Redirect resolution uses SSRF guard (private/internal targets blocked)
- Default model `gemini-2.5-flash` (any grounding-capable Gemini model works)

---

## web_fetch Config

```json5
{
  tools: {
    web: {
      fetch: {
        enabled: true,
        maxChars: 50000,
        maxCharsCap: 50000,
        maxResponseBytes: 2000000,
        timeoutSeconds: 30,
        cacheTtlMinutes: 15,
        maxRedirects: 3,
        userAgent: "Mozilla/5.0 ...",
        readability: true,
        firecrawl: {
          enabled: true,
          apiKey: "FIRECRAWL_KEY",    // or FIRECRAWL_API_KEY env var
          baseUrl: "https://api.firecrawl.dev",
          onlyMainContent: true,
          maxAgeMs: 86400000,         // 1 day
          timeoutSeconds: 60,
        },
      },
    },
  },
}
```

### web_fetch Parameters

| Parameter | Description |
|-----------|-------------|
| `url` | URL to fetch (required, http/https only) |
| `extractMode` | `markdown` or `text` |
| `maxChars` | Truncate long pages (clamped by `maxCharsCap`) |

### web_fetch Notes

- Uses Readability first, then Firecrawl fallback (if configured)
- Blocks private/internal hostnames; re-checks redirects
- Chrome-like User-Agent + `Accept-Language` by default
- `maxResponseBytes` caps download before parsing (truncated with warning)
- Cached 15 min by default

---

## Tool Policy

If using tool profiles/allowlists, add `web_search`/`web_fetch` or `group:web`:

```json5
{
  tools: {
    allow: ["group:web"],
  },
}
```
