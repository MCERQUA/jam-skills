---
name: playwright-cli
description: "Agent-optimized browser automation via playwright-cli. Token-efficient CLI with snapshot-based element targeting, session management, --json output, and CDP attach. Prefer over Puppeteer scripting for most browser tasks."
metadata:
  version: 0.1.9
---

# Browser Automation with playwright-cli

`playwright-cli` is the preferred browser tool for agents. It avoids dumping accessibility trees into context — you get terse CLI commands and stable element refs from snapshots instead.

## Quick Start

```bash
playwright-cli open https://example.com
playwright-cli snapshot          # get element refs (e1, e2, e3...)
playwright-cli click e5
playwright-cli fill e3 "search term" --submit
playwright-cli screenshot --filename=result.png
playwright-cli close
```

## Core Commands

```bash
playwright-cli open [url]        # open browser, optionally navigate
playwright-cli goto <url>        # navigate to url
playwright-cli snapshot          # ARIA snapshot with element refs — do this before clicking
playwright-cli snapshot --boxes  # snapshot + bounding box [box=x,y,w,h] per element
playwright-cli snapshot --depth=4 <ref>  # partial snapshot for efficiency
playwright-cli click <ref>       # ref from snapshot (e5), CSS selector, or locator
playwright-cli dblclick <ref>
playwright-cli fill <ref> <text>
playwright-cli fill <ref> <text> --submit   # fill + press Enter
playwright-cli type <text>       # type into focused element
playwright-cli press <key>       # Enter, ArrowDown, Tab, Escape, etc.
playwright-cli hover <ref>
playwright-cli select <ref> <value>
playwright-cli check <ref>
playwright-cli uncheck <ref>
playwright-cli upload ./file.pdf
playwright-cli drag <startRef> <endRef>
playwright-cli drop <ref> --path=./file.png   # drop file onto element
playwright-cli eval "document.title"
playwright-cli eval "el => el.textContent" e5
playwright-cli eval "el => el.getAttribute('data-testid')" e5
playwright-cli dialog-accept [prompt]
playwright-cli dialog-dismiss
playwright-cli resize 1920 1080
playwright-cli close
```

## Navigation

```bash
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload
```

## Screenshots & Output

```bash
playwright-cli screenshot                    # saves to .playwright-cli/
playwright-cli screenshot --filename=out.png # save to specific file
playwright-cli pdf --filename=page.pdf

# Machine-parseable output — pipe to jq or use in scripts
playwright-cli --json eval "document.title"
playwright-cli --raw eval "document.body.innerText"  # strip metadata, return value only
playwright-cli --raw snapshot > page.yml             # snapshot to file
```

## Tabs

```bash
playwright-cli tab-list
playwright-cli tab-new https://example.com
playwright-cli tab-select 0
playwright-cli tab-close
```

## Sessions (run multiple browsers in parallel)

```bash
playwright-cli open                          # default session
playwright-cli -s=work open https://site.com # named session
playwright-cli -s=work click e5
playwright-cli list                          # list all active sessions
playwright-cli close-all
playwright-cli kill-all

# Persistent profile — cookies survive browser restart
playwright-cli open --persistent
playwright-cli -s=mywork open https://site.com --persistent
```

Set env var to prefix all calls with a session name:
```bash
PLAYWRIGHT_CLI_SESSION=mywork playwright-cli open https://example.com
```

## Storage — Cookies / LocalStorage / SessionStorage

```bash
playwright-cli cookie-list
playwright-cli cookie-get session_id
playwright-cli cookie-set session_id abc123
playwright-cli cookie-clear
playwright-cli localstorage-list
playwright-cli localstorage-get theme
playwright-cli localstorage-set theme dark
playwright-cli state-save auth.json
playwright-cli state-load auth.json
```

## Network / DevTools

```bash
playwright-cli console             # list console messages
playwright-cli network             # list network requests since page load
playwright-cli route "**/*.jpg" --status=404        # mock requests
playwright-cli route "https://api.example.com/**" --body='{"mock":true}'
playwright-cli route-list
playwright-cli unroute
playwright-cli tracing-start
playwright-cli tracing-stop
playwright-cli video-start recording.webm
playwright-cli video-stop
```

## Attach to Existing Browser (CDP)

```bash
playwright-cli attach --cdp=chrome         # attach to running Chrome
playwright-cli attach --cdp=http://localhost:9222
playwright-cli list --all                  # discover all attachable Chrome/Edge instances
playwright-cli detach                      # disconnect without closing browser
```

## Targeting Elements

After `snapshot`, use refs (`e5`, `e12`) for stable targeting. Also accepts CSS selectors and Playwright locators:

```bash
playwright-cli click e15                                    # ref from snapshot (preferred)
playwright-cli click "#main > button.submit"               # CSS selector
playwright-cli click "getByRole('button', { name: 'Submit' })"  # Playwright locator
playwright-cli click "getByTestId('submit-button')"        # test id
```

## DevTools Helpers

```bash
playwright-cli generate-locator e5          # generate stable Playwright locator for element
playwright-cli generate-locator e5 --raw    # locator string only, for assertions
playwright-cli highlight e5                 # persistent visual overlay on element
playwright-cli highlight e5 --style="outline: 3px dashed red"
playwright-cli highlight --hide             # remove all highlights
playwright-cli run-code "async page => await page.context().grantPermissions(['geolocation'])"
playwright-cli run-code --filename=script.js
```

## Typical Agent Workflow

```bash
# 1. Open page
playwright-cli open https://example.com

# 2. Snapshot to get element refs
playwright-cli snapshot

# 3. Interact using refs
playwright-cli fill e3 "hello@example.com"
playwright-cli fill e7 "password123"
playwright-cli click e9

# 4. Verify result
playwright-cli snapshot
playwright-cli screenshot --filename=after-login.png

# 5. Close
playwright-cli close
```

## Configuration

Config file at `.playwright/cli.config.json` or pass `--config=path/to/config.json`. Key options:
- `browser.browserName` — chromium (default), firefox, webkit
- `browser.cdpEndpoint` — attach to existing browser
- `outputDir` — where screenshots/snapshots save
- `outputMode` — "file" (write to disk) or "stdout"
- `timeouts.action` — default 5000ms
- `timeouts.navigation` — default 60000ms

## Notes

- Headless by default. `--headed` only works with `open`.
- Session state (cookies, localStorage) is in-memory by default — add `--persistent` to save to disk.
- After each command, playwright-cli prints a snapshot of current page state to `.playwright-cli/`.
- Use `--raw` to suppress the snapshot output and get only the return value.
- Snapshots write `.yml` files to `.playwright-cli/` in the working directory.
