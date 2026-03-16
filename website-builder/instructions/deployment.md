# Deployment

How to go from dev server to production.

---

## JamBot Dev Server (default)

All JamBot client websites run as dev servers via `jambot-add-website.sh`. This is the standard workflow:

1. Agent builds the site in `workspace/Websites/<project>/`
2. Admin runs: `sudo bash scripts/jambot-add-website.sh <user> <project>`
3. Site is live at `https://dev-<user>.jam-bot.com`
4. Hot reload — agent edits files, user sees changes instantly

**This is sufficient for most clients.** The dev server handles production traffic fine for small business sites.

---

## Static Build (zero-memory production)

For sites that don't need hot reload (finished, stable):

```bash
# Build and serve statically — container stops, nginx serves files directly
sudo bash scripts/jambot-switch-website.sh <user> <project> --build-static
```

This runs `next build` + `next export`, copies the output to nginx static serving, and parks the webdev container. Zero memory usage.

---

## Vercel Deployment

For clients who want Vercel hosting:

### 1. Push to GitHub
The site should already have a GitHub repo from the scaffold step.

### 2. Connect to Vercel
```bash
# Install Vercel CLI (inside the container or on host)
pnpm add -g vercel

# Deploy
cd Websites/<project>
vercel --prod
```

### 3. Environment Variables
Add all `.env.local` variables to Vercel:
- Project Settings → Environment Variables
- Add: `RESEND_API_KEY`, `CONTACT_EMAIL`, etc.

### 4. Custom Domain
In Vercel dashboard:
- Settings → Domains → Add `www.clientdomain.com`
- Update DNS records at client's registrar

---

## Netlify Deployment

### 1. Build settings
- Build command: `next build`
- Publish directory: `.next`
- Install command: `pnpm install`

### 2. Add `netlify.toml`:
```toml
[build]
  command = "pnpm build"
  publish = ".next"

[[plugins]]
  package = "@netlify/plugin-nextjs"
```

---

## Self-Hosted (Docker)

For advanced cases where the client runs their own server:

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable && pnpm build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

Add to `next.config.ts`:
```typescript
const nextConfig: NextConfig = {
  output: "standalone",
};
```

---

## Pre-Deployment Checklist

Before any deployment:
- [ ] Run `pnpm build` — zero errors
- [ ] All environment variables documented in `.env.local.example`
- [ ] `.env.local` is in `.gitignore` (never commit secrets)
- [ ] OG image exists at `public/og/default.png`
- [ ] Favicon exists at `public/favicon.ico`
- [ ] Sitemap generates correctly (check `/sitemap.xml`)
- [ ] Robots.txt allows indexing (check `/robots.txt`)
- [ ] All images load (no 404s)
- [ ] Contact form works (test submission)
- [ ] Mobile responsive (check on phone or 375px)
- [ ] Quality checklist passes (see `quality-checklist.md`)
