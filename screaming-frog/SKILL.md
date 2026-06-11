# Screaming Frog SEO Spider v24.1 — Headless CLI Skill

Screaming Frog v24.1 installed on VPS in user-space (no root required). Runs fully headless.
Free tier: 500 URLs per crawl. Paid license: $279 USD/year for unlimited.

## Binary / Wrapper

```
/mnt/system/base/tools/screaming-frog/screaming-frog.sh
```

Bundled JRE at:
```
/mnt/system/base/tools/screaming-frog/usr/share/screamingfrogseospider/jre/bin/java
```

## Setup (already done — do not repeat)

1. Downloaded `screamingfrogseospider_24.1_amd64.deb`
2. Extracted with `dpkg-deb -x` to `/mnt/system/base/tools/screaming-frog/`
3. Created wrapper script at `screaming-frog.sh` with correct paths
4. Accepted EULA by adding to `~/.ScreamingFrogSEOSpider/spider.config`:
   ```
   eula.version=15
   eula.accepted=15
   ```

## Standard Headless Crawl

```bash
mkdir -p /tmp/sf-output
/mnt/system/base/tools/screaming-frog/screaming-frog.sh \
  --headless \
  --crawl https://example.com \
  --output-folder /tmp/sf-output \
  --export-format csv \
  --export-tabs "Internal:All"
```

Output: `/tmp/sf-output/internal_all.csv` — one row per URL with status, title, meta, H1, indexability, word count, readability, etc.

## Useful Flags

| Flag | Description |
|------|-------------|
| `--headless` | Run without display (required on server) |
| `--crawl <url>` | URL to crawl |
| `--output-folder <path>` | Where to write CSV exports |
| `--export-format csv` | Format (also: xls, xlsx) |
| `--export-tabs "Internal:All"` | Export the Internal tab (all URLs) |
| `--save-crawl` | Save crawl file (requires paid license) |
| `--config <path>` | Use a saved spider config file |
| `--bulk-export "Internal:All"` | Alternative export syntax |

## Common --export-tabs Values

```
Internal:All                     ← main URLs audit (use this)
External:All                     ← external links
Response Codes:Client Error (4xx)  ← broken links only
Response Codes:Server Error (5xx)  ← server errors
Page Titles:All                  ← title tag audit
Meta Description:All             ← meta description audit
H1:All                           ← H1 audit
Images:All                       ← image audit
```

Multiple tabs: `--export-tabs "Internal:All,Page Titles:All,H1:All"`

## What the Internal:All CSV Contains

- `Address` — URL
- `Status Code` — 200, 301, 404, etc.
- `Status` — OK, Redirect, Client Error, etc.
- `Indexability` — Indexable / Non-Indexable
- `Title 1` — Page title and length
- `Meta Description 1` — Meta desc and length
- `H1-1`, `H2-1` — First H1 and H2
- `Word Count`, `Readability` — Content quality signals
- `Inlinks`, `Outlinks` — Link counts
- `Response Time` — TTFB in seconds

## Integration Patterns

### 1. Brand Report technical crawl
```bash
DOMAIN="client.com"
OUTPUT="/tmp/sf-${DOMAIN}"
mkdir -p "$OUTPUT"
/mnt/system/base/tools/screaming-frog/screaming-frog.sh \
  --headless --crawl "https://${DOMAIN}" \
  --output-folder "$OUTPUT" \
  --export-format csv \
  --export-tabs "Internal:All,Response Codes:Client Error (4xx)"
# Parse: internal_all.csv for broken links, missing titles, thin content
```

### 2. Quick broken-link check
```bash
/mnt/system/base/tools/screaming-frog/screaming-frog.sh \
  --headless --crawl https://example.com \
  --output-folder /tmp/sf-out \
  --export-format csv \
  --export-tabs "Response Codes:Client Error (4xx)"
```

### 3. MCP server (paid license required for useful output)
```bash
/mnt/system/base/tools/screaming-frog/screaming-frog.sh \
  --mcp-streamable-http-server
```

## Free Tier Limits
- 500 URL crawl cap per crawl (enforced automatically)
- No `--save-crawl` (requires license)
- No configuration save/load (requires license)
- JavaScript rendering limited (requires license for full JS crawl)
- CSV export works fine in free tier

## File Locations
- Tool dir: `/mnt/system/base/tools/screaming-frog/`
- Wrapper: `/mnt/system/base/tools/screaming-frog/screaming-frog.sh`
- User config: `~/.ScreamingFrogSEOSpider/spider.config`
- Crawl DB (temp): `~/.ScreamingFrogSEOSpider/ProjectInstanceData/` (auto-cleaned)
