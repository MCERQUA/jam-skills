# Playbook — Add a messaging channel to a tenant (Telegram / Discord / Slack / …)

**Anchors:** #12 (external plugin migration), #3 (strict tool-allowlist hard-error), #18 (supply-chain vetting), #19/#25 (config mutation), #26 (protocol v4).
**Related:** `overrides/skill-allowlist.md`, `playbooks/skill-install-vetting.md`.

---

## 0. Decide whether this tenant should have a channel at all

JamBot agents are **owner-facing, not customer-facing**. A tenant's OpenClaw serves the business owner; it does not talk to the owner's customers. Adding a public channel to a tenant gateway is a product decision, not a config task — confirm it before wiring anything.

Also note the split already in place: **SMS/email identity runs through InkBox** (`/inkbox-expert`) and **voice through Telnyx** (`/telnyx-expert`), not through OpenClaw channel plugins. Do not duplicate a lane that already has an owner.

---

## 1. Know where the channel code lives (anchor #12)

v2026.5.2 moved most channels out of the core bundle into **external plugins**: ACPX, OTel, Discord, WhatsApp, Voice Call, Brave, Codex, Memory LanceDB, Teams, Diffs, Lobster, BlueBubbles, Mattermost, Matrix, Tlon, Google Chat, LINE, Nextcloud Talk, Nostr, Zalo, QQ Bot, Synology Chat, Twitch, Feishu, Google Meet, Yuanbao.

Consequences:
- The channel may need an explicit plugin install; it is not present just because the docs describe it.
- **BlueBubbles is fully removed as of v2026.5.12** (breaking). iMessage goes through the bundled `imsg` path on a signed-in Mac or an SSH wrapper. Any `channels.bluebubbles` config must migrate to `channels.imessage`.
- On ≥7.x the per-plugin reference pages live under `plugins/reference/<name>` — look there, not under `channels/`, for config keys.

```bash
bash scripts/lookup.sh section:Channels
bash scripts/lookup.sh <channel-name>
```

---

## 2. Vet the plugin before it touches a tenant (anchor #18)

The ClawHavoc campaign caught 1,467 malicious ClawHub skills, including a 35k-install flagship exfiltrating data. In a multi-tenant deployment a single bad artifact in `/mnt/system/base/skills/` reaches every tenant at once.

Run `playbooks/skill-install-vetting.md` for anything from ClawHub. For official channel plugins, still pin the version and check the integrity hash — the changelog repeatedly bumps "official external channel catalog" specs and integrity pins, which means those pins are load-bearing.

---

## 3. Install + configure — from inside the container, never by hand-editing

```bash
T=<tenant>
sg docker -c "docker exec openclaw-$T openclaw plugins list"
sg docker -c "docker exec openclaw-$T openclaw plugins registry --refresh"     # v4.25+
sg docker -c "docker exec openclaw-$T openclaw plugins deps"                   # v4.27+

# Config: openclaw config set ONLY (anchors #19/#25, CLAUDE.md non-negotiable)
sg docker -c "docker exec openclaw-$T openclaw config set channels.telegram.enabled true"
sg docker -c "docker restart openclaw-$T"
```

**Secrets never go inline.** Use the SecretRef / secrets surface (`openclaw secrets`), and in the mesh use pointers, never values. Token-shaped values passed via `--env` are visible to any host admin through `docker inspect` (anchor #28's trust-boundary note).

---

## 4. The allowlist trap (anchor #3)

From v5.2, if a tool is in an explicit tool allowlist and the plugin providing it is disabled, the gateway **hard-errors**: `No callable tools remain after resolving explicit tool allowlist`. Adding or removing a channel plugin changes which tools resolve. If a tenant fails to start right after a channel change, check the allowlist before anything else.

---

## 5. Verify

```bash
sg docker -c "docker exec openclaw-$T openclaw channels status --probe"
sg docker -c "docker logs --tail 200 openclaw-$T" | grep -iE "channel|plugin|allowlist|pair"
```

`--probe` actually talks to the provider; plain `status` only reports local belief. Probe, then send one real message in each direction. A channel that reports connected and delivers nothing is the normal failure — test frames, not handshakes.

---

## 6. Version-dependent notes

- **≥2026.5.19** — Gateway WS protocol v4 is required; protocol-mismatch errors now name the stale side (anchor #26B).
- **≥2026.7.1** — replies carrying only rich presentation / buttons are no longer dropped as empty; several channels changed how tool-progress and draft bubbles render. If a channel's output looks different after an upgrade, that is expected, not a regression.
- **Access control** — `channels/access-groups` (reusable sender allowlists) and `channels/bot-loop-protection` are new-ish pages worth reading before exposing any channel where more than one human can post.
