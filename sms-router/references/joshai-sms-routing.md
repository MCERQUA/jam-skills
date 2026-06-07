# joshai SMS Routing — Runbook

**Last updated:** 2026-06-06
**Author:** sms-host@mesh

Per-agent InkBox identity so Mike texts Josh's agent directly and receives a reply from that
agent's own number (+19286986125) rather than the shared admin line.

---

## Numbers & IDs

| Item | Value |
|------|-------|
| joshai FROM number | `+19286986125` |
| InkBox phone_id | `f9f18067-c34f-43ea-a785-ed6d82191b2e` |
| Creds file | `/mnt/clients/josh/openclaw/workspace/.inkbox-joshai.env` (gitignored) |
| Webhook subscription | `b5110c34-…` (text.received, filter_mode=whitelist) |
| Whitelist | Mike's `+14374559131` only |
| Admin line (Mike) | `+15204341343` (reference profile — CA already enabled) |

---

## Inbound path

1. Mike texts `+19286986125`
2. InkBox fires webhook → `POST /inkbox-inbound/<secret>` on port 6450
3. `app.py::identity_for_local_phone("+19286986125")` matches → returns `"joshai"`
4. Inbox file written to `/mnt/system/josh-host/sms-inbox/` (NOT josh-host's FIFO `inbox/`)
5. `scripts/josh-host-sms-drain.sh` (cron `* * * * *`) processes FIFO and replies

## Outbound path

Agent (or drain script) POSTs:
```json
{"identity": "joshai", "to": "+14374559131", "body": "..."}
```
to `http://127.0.0.1:6450/send` → `inkbox_send_as("joshai", to, body)` → InkBox API →
reply lands on Mike's phone FROM `+19286986125`.

---

## Country whitelist (CA) — the critical gotcha

**New InkBox numbers are US-only by default.**
Sending to a Canadian number (`+1437…` = Mike) returns `409 carrier_rejected`.

### Symptom
```
{"error": "carrier_rejected", "status": 409}
```
or the carrier_rejected code propagated through host inbox and relayed to Mike by sms-host.

### Fix — one-time, done in InkBox dashboard (no API)

The joshai API key has **no privilege** over messaging-profile or opt-in endpoints (returns 403).
Fix requires Mike's login to the InkBox dashboard:

1. Log in to InkBox dashboard
2. Navigate to the `+19286986125` number → **Messaging Profile**
3. Reference the admin line `+15204341343` — that profile has **Canada** enabled; copy those settings
4. Add **CA** to the country allowlist on joshai's profile
5. Save — no restart needed; change is live immediately

To verify after Mike's fix:
```bash
# From sms-host, ask Mike to trigger a joshai→+14374559131 test text, then check:
curl -s -X POST http://127.0.0.1:6450/send \
  -H "Content-Type: application/json" \
  -d '{"identity":"joshai","to":"+14374559131","body":"joshai CA routing test"}'
# Expect: {"sid":"...","status":"queued"} — NOT carrier_rejected
```

---

## HUP-reload (no sudo)

When creds change (`/mnt/clients/josh/openclaw/workspace/.inkbox-joshai.env`), the module reads
them at import time. Reload without a sudo systemd restart:

```bash
# gunicorn master is owned by mike (ppid 1)
pkill -HUP -f 'gunicorn.*sms-router'
# or find PID first:
pgrep -f 'gunicorn.*sms-router' | head -1 | xargs kill -HUP
```

A full restart (`sudo systemctl restart sms-router`) is only needed if you change
`EnvironmentFile` vars in the unit file itself — creds loaded via file-read at import bypass
this.

---

## Adding another agent identity

Same pattern as joshai. Steps:

1. Provision an InkBox number (Mike does via dashboard)
2. Create `INKBOX_API_KEY` + `INKBOX_PHONE` in `/mnt/clients/<user>/openclaw/workspace/.inkbox-<agent>.env`
3. Add a registry entry in `app.py::INKBOX_IDENTITIES` (pattern: copy joshai block, adjust paths)
4. Create InkBox webhook subscription + whitelist contact-rule via API (see `inkbox-api-discovery-2026-05-27.md`)
5. Create `<agent>-host-sms-drain.sh` cron (copy `josh-host-sms-drain.sh`, adjust INBOX/SYSTEM_PROMPT)
6. HUP-reload gunicorn
7. **Add CA to new number's messaging profile in InkBox dashboard before testing with Mike's +1437 number**

---

## See also

- `sms-router.md` — full architecture (the §CURRENT-STATE 2026-05-30 section is the definitive reference)
- `inkbox-api-discovery-2026-05-27.md` — webhook subscription + whitelist creation via API
- `/mnt/system/josh-host/scripts/josh-host-sms-drain.sh` — joshai's drain script
