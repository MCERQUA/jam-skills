# X Bookmarks — Fetch & Research

You can fetch Mike's X/Twitter bookmarks and research them.

## Fetching Bookmarks

Run the fetch script to get recent bookmarks as JSON:

```bash
bash /home/node/.claude/skills/x-bookmarks/fetch-bookmarks.sh [count]
```

- Default: 20 bookmarks. Pass a number for more/fewer.
- Requires `X_CT0` and `X_AUTH_TOKEN` env vars (already configured).
- Returns a JSON array with fields: `id`, `author`, `author_name`, `text`, `posted_at`, `likes`, `retweets`, `views`, `links`, `media`.

## What To Do With Bookmarks

When Mike asks you to check his bookmarks, fetch his recent X bookmarks, or research what he's saved:

1. **Fetch** the bookmarks using the script above
2. **Identify** what each bookmark is about — especially any links (GitHub repos, articles, tools, products)
3. **Research** linked content:
   - GitHub repos: read the README, understand what it does, key features, tech stack
   - Articles/blog posts: summarize key points
   - Tools/products: what they do, how they work, pricing
   - Tweets with no links: summarize the insight or announcement
4. **Analyze relevance** to our systems:
   - **OpenVoiceUI / Canvas pages** — could this enhance the UI, add a new page, improve UX?
   - **OpenClaw / Agent skills** — new agent capability, tool, or integration?
   - **Infrastructure / DevOps** — server tooling, Docker, monitoring, deployment?
   - **Client tools** — useful for JamBot clients (local service businesses)?
   - **SEO / Marketing / Social** — content, analytics, lead generation?
   - **AI / LLM** — new models, techniques, APIs, frameworks?
   - **Browser automation** — scraping, extensions, testing?
   - **Development tools** — CLI tools, libraries, frameworks?
5. **Report** findings clearly with:
   - What it is (one sentence)
   - Why it matters to us (specific systems it applies to)
   - How we could use it (concrete integration ideas)
   - Priority: high (use immediately) / medium (plan for) / low (nice to know)
   - Effort: quick (hours) / moderate (days) / significant (week+)

## Example

Mike says: "Check my bookmarks" or "What's new in my X bookmarks?"

You fetch, research each one, then present a summary like:

**@somedev: "Just released page-agent.js — GUI agent that lives in the browser"**
- **What:** Browser automation agent from Alibaba, runs inside the page DOM
- **Applies to:** Browser extension v2, agent gateway, web scraping pipeline
- **How:** Could replace Puppeteer for in-page actions, lighter than full browser automation
- **Priority:** High | **Effort:** Moderate

## Notes

- Bookmarks are fetched from X's internal API using session cookies (not the paid API)
- Cookies expire periodically (~yearly). If you get auth errors, tell Mike to refresh his X cookies
- Always research the LINKS in bookmarks, not just the tweet text — the value is in what they point to
