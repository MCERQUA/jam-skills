# OpenClaw on Hetzner — Install Reference

Runs OpenClaw Gateway on a Hetzner VPS using Docker. ~$5/month for a CX11 (2 vCPU, 2GB RAM).

---

## Core Setup

```bash
# 1. Provision Hetzner VPS (CX11 or CX21), SSH in

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER && newgrp docker

# 3. Create workspace dir (persists on host)
mkdir -p ~/.openclaw/workspace

# 4. Run OpenClaw via Docker
docker run -d \
  --name openclaw \
  --restart unless-stopped \
  -v ~/.openclaw:/root/.openclaw \
  -e OPENCLAW_GATEWAY_TOKEN="your-secret-token" \
  -e ZAI_API_KEY="your-zai-key" \
  -p 127.0.0.1:18789:18789 \   # loopback only — access via SSH tunnel
  openclaw/gateway:latest
```

---

## Critical: Persistence Pattern

**All long-lived state must live on the host** via volume mounts — not inside the container.

| Lives on Host | Lives in Image |
|--------------|----------------|
| `~/.openclaw/` (config, sessions, workspace) | Node.js, openclaw binary |
| API keys (via env or config) | CLI tools baked in at build time |

**Anything installed inside a running container disappears on restart.**

If you need extra CLI tools (e.g. `wacli`, `goplaces`), add them to a custom Dockerfile:
```dockerfile
FROM openclaw/gateway:latest
RUN curl -L https://example.com/tool -o /usr/local/bin/tool && chmod +x /usr/local/bin/tool
```

---

## Access Pattern

Gateway binds to `127.0.0.1:18789` (loopback only). Access from your laptop via SSH tunnel:

```bash
ssh -L 18789:127.0.0.1:18789 user@your-hetzner-ip -N
# Then connect openclaw CLI to ws://127.0.0.1:18789
```

This avoids public exposure entirely — smaller attack surface.

---

## Security

- Keep gateway on loopback + SSH tunnel (recommended) OR use Tailscale serve
- For multi-user / team: dedicated VPS per team if users are potentially adversarial
- Firewall: block all inbound except SSH (22) and your known IPs

```bash
# UFW quickstart
ufw allow ssh
ufw enable
```

---

## Terraform (IaC)

Community-maintained Terraform repos available for reproducible Hetzner deployments:
- Provisions VPS, firewall rules, and backups
- Search GitHub: `openclaw hetzner terraform`

---

## Useful Commands

```bash
docker logs -f openclaw          # follow gateway logs
docker restart openclaw          # restart gateway
docker exec -it openclaw openclaw status   # run CLI inside container
docker pull openclaw/gateway:latest && docker restart openclaw  # update
```
