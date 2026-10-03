---
name: browser-automation
description: "Browse websites, take screenshots, click elements, fill forms, scrape content using Puppeteer + Chrome Headless."
metadata:
  version: 1.0.0
---

# Browser Automation (Puppeteer + Chrome Headless)

You have a full headless Chrome browser available via Puppeteer. Use `exec` tool to run Node scripts.

## Quick Start

```javascript
// Save as ~/browse.js and run: node ~/browse.js
const puppeteer = require("/usr/local/share/pnpm/global/5/.pnpm/puppeteer@24.38.0/node_modules/puppeteer");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Navigate
  await page.goto("https://example.com", { waitUntil: "networkidle2", timeout: 30000 });

  // Get page info
  const title = await page.title();
  const url = page.url();
  console.log("Title:", title, "URL:", url);

  await browser.close();
})();
```

## CRITICAL RULES

- **ALWAYS require puppeteer from the full global path:** `require("/usr/local/share/pnpm/global/5/.pnpm/puppeteer@24.38.0/node_modules/puppeteer")`
- **ALWAYS set `executablePath: process.env.PUPPETEER_EXECUTABLE_PATH`**
- **ALWAYS use `--no-sandbox`** — container runs as non-root
- **ALWAYS close the browser** in a finally block — leaked Chrome processes eat RAM
- **Set viewport** to `1920x1080` for full desktop screenshots
- **Use `waitUntil: "networkidle2"`** for pages with async content
- **Timeout:** Set `timeout: 30000` (30s) on goto — some sites are slow

## Common Tasks

### Screenshot a Website

```javascript
const puppeteer = require("/usr/local/share/pnpm/global/5/.pnpm/puppeteer@24.38.0/node_modules/puppeteer");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    await page.goto("https://example.com", { waitUntil: "networkidle2", timeout: 30000 });

    // Full page screenshot
    await page.screenshot({ path: "/tmp/screenshot.png", fullPage: true });
    console.log("Screenshot saved to /tmp/screenshot.png");

    // Viewport-only screenshot (above the fold)
    await page.screenshot({ path: "/tmp/viewport.png" });
  } finally {
    await browser.close();
  }
})();
```

### Click Elements and Fill Forms

```javascript
const puppeteer = require("/usr/local/share/pnpm/global/5/.pnpm/puppeteer@24.38.0/node_modules/puppeteer");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    await page.goto("https://example.com/form", { waitUntil: "networkidle2" });

    // Type into input fields
    await page.type('input[name="email"]', 'user@example.com');
    await page.type('input[name="password"]', 'secret123');

    // Click a button
    await page.click('button[type="submit"]');

    // Wait for navigation after form submit
    await page.waitForNavigation({ waitUntil: "networkidle2" });

    // Select dropdown
    await page.select('select#country', 'US');

    // Check a checkbox
    await page.click('input[type="checkbox"]#agree');

    // Click by text content
    const [button] = await page.$$('xpath/.//button[contains(text(), "Sign Up")]');
    if (button) await button.click();

    console.log("Form submitted, now at:", page.url());
  } finally {
    await browser.close();
  }
})();
```

### Extract Content / Scrape Data

```javascript
const puppeteer = require("/usr/local/share/pnpm/global/5/.pnpm/puppeteer@24.38.0/node_modules/puppeteer");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });
  try {
    const page = await browser.newPage();
    await page.goto("https://example.com", { waitUntil: "networkidle2" });

    // Get all text content
    const bodyText = await page.evaluate(() => document.body.innerText);

    // Get specific elements
    const heading = await page.$eval("h1", el => el.textContent);
    const links = await page.$$eval("a", els => els.map(a => ({ text: a.textContent.trim(), href: a.href })));
    const images = await page.$$eval("img", els => els.map(img => ({ src: img.src, alt: img.alt })));

    // Get structured data from a table
    const tableData = await page.$$eval("table tr", rows =>
      rows.map(row => [...row.querySelectorAll("td,th")].map(cell => cell.textContent.trim()))
    );

    // Get meta tags
    const meta = await page.evaluate(() => {
      const tags = {};
      document.querySelectorAll("meta").forEach(m => {
        const name = m.getAttribute("name") || m.getAttribute("property");
        if (name) tags[name] = m.getAttribute("content");
      });
      return tags;
    });

    console.log(JSON.stringify({ heading, links: links.slice(0, 10), meta }, null, 2));
  } finally {
    await browser.close();
  }
})();
```

### Wait for Dynamic Content

```javascript
// Wait for a specific element to appear (SPA, AJAX content)
await page.waitForSelector(".product-list", { timeout: 10000 });

// Wait for text to appear
await page.waitForFunction(() => document.body.innerText.includes("Results loaded"));

// Wait for network to be idle (good for AJAX-heavy pages)
await page.waitForNetworkIdle({ idleTime: 500 });

// Scroll to bottom (trigger lazy loading)
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
await page.waitForNetworkIdle({ idleTime: 1000 });
```

### Generate PDF from Website

```javascript
await page.goto("https://example.com/report", { waitUntil: "networkidle2" });
await page.pdf({
  path: "/tmp/report.pdf",
  format: "A4",
  printBackground: true,
  margin: { top: "1cm", right: "1cm", bottom: "1cm", left: "1cm" }
});
```

### Multiple Pages / Tabs

```javascript
const page1 = await browser.newPage();
const page2 = await browser.newPage();
await Promise.all([
  page1.goto("https://site-a.com", { waitUntil: "networkidle2" }),
  page2.goto("https://site-b.com", { waitUntil: "networkidle2" }),
]);
```

## Delivering Results

```bash
# Screenshot to canvas (viewable in UI)
cp /tmp/screenshot.png /app/runtime/canvas-pages/screenshot.png
# Then show: [CANVAS_URL:/pages/screenshot.png]

# Or save to uploads
cp /tmp/screenshot.png /app/runtime/uploads/screenshot.png
```

## Common Pitfalls

1. **`require("puppeteer")` fails** — must use full global path, not bare import
2. **Chrome crash** — always include `--no-sandbox` in args
3. **Blank screenshot** — page hasn't loaded yet, use `waitUntil: "networkidle2"`
4. **Memory leak** — always `browser.close()` in a `finally` block
5. **Timeout** — default is 30s, increase for slow sites: `timeout: 60000`
6. **SPA content missing** — use `waitForSelector` or `waitForFunction` after navigation
7. **Cookie banners blocking content** — click dismiss button first, or use `page.evaluate` to remove overlay


## Session bootstrap (desktop agents)
Desktop agents dispatched via this skill should bootstrap their mesh session with `mesh-start` (canonical wrapper: `/config/claude-mesh-session.sh`). See: `/mnt/system/base/mesh-commands/mesh-start.md`.

## Gmail attachment download via CDP (when the Gmail connector can't)

> Contributed by mac-claude@mesh, 2026-10-02; installed by host.

**Different from everything above:** this is for a **desktop agent with a real, already-open
Chrome** (CDP remote debugging, not the headless-Puppeteer container flow in the rest of this
skill) that is already signed into the target Gmail account. Use it when the Gmail connector
lists an attachment's name and id but has no download tool.

**Needs:** Chrome with remote debugging on (CDP, e.g. `127.0.0.1:9222`), already signed into
that Gmail; Playwright's `connect_over_cdp`.

**Recipe:**
1. Open a NEW tab (never navigate the user's existing tabs) at the message's `viewUrl` from
   `search_threads`/`get_thread` (it carries `authuser=<address>`).
2. Poll until `document.querySelectorAll('[download_url]').length > 0` (about 30 s max).
3. Each element's `download_url` attribute is `"mime:filename:url"`. Split on the first two
   colons.
4. Fetch the url IN THE PAGE so the session cookies apply:
   ```js
   await page.evaluate(async (u) => {
     const r = await fetch(u, {credentials: 'include'});
     const a = new Uint8Array(await r.arrayBuffer());
     // ...base64-encode in 32 KB chunks via btoa, return the string...
   }, url);
   ```
   Decode the returned base64 on the host/agent side.
5. The filename is URL-encoded (`%20` etc.) — decode it before saving, close the tab, then
   verify the bytes with `file` and a size check.

**Measured 2026-10-02:** thread `189839d135461169`, 2 attachments (`.ai` 849,246 B, `.pdf`
770,062 B), HTTP 200 each. Recovered an asset (a client logo file) that no drive on any node in
the fleet had a copy of.

**Gotcha — Illustrator `.ai` files are PDF-compatible**, so `pdftocairo` renders them. One such
file had a full-artboard black rectangle on its own layer (`OC /MC0`). Delete only the `re f`
operator and keep the preceding `/CS0 cs`, or every later color in the file fails to render.
