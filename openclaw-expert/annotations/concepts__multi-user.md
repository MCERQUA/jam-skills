---
upstream: https://docs.openclaw.ai/concepts/multi-user
relevance: jambot-critical
last-verified: 2026-07-25
audit_anchors: [28]
related_pages: [gateway__multi-tenant-hosting, concepts__main-session, concepts__session, gateway__security__exposure-runbook]
---

# Multi-user mode — JamBot annotation

New page in the 2026-07-25 catalog rebuild. **Read this before answering any "can my client's team share the agent?" question** — it is the upstream doctrine for exactly that, and the answer is more nuanced than yes/no.

## The load-bearing sentence

> *"Everyone who can operate an agent can make it do anything that agent can do. Session ownership, visibility in the sidebar, and presence indicators are **usability features, not security boundaries**."*

And the consequence upstream draws:

> *"If people must not access each other's sessions, tools, credentials, or files, give them separate agents or separate gateway/host trust boundaries. Do not rely on owner avatars or filters for isolation."*

This is the same doctrine as anchor #28 (`gateway/multi-tenant-hosting`), stated for the within-one-tenant case: **session-level attribution is never an authorization boundary.**

## Why this matters for JamBot specifically

The realistic request is a client with employees — "can my office manager use the agent too?" Multi-user mode makes that *pleasant* (you can see who started what, who is watching) but it does not partition anything. Everyone who can operate that tenant's agent can reach:

- every tool the agent has (and per `annotations/tools__permission-modes.md`, our tenants run `security=full, ask=off` — **unguarded host exec**)
- the tenant's workspace, memory, and business files
- every credential available to that agent

So the decision rule for JamBot:

| Request | Answer |
|---|---|
| Several people at the same company, all trusted with the whole business | Multi-user mode is fine — it is a coordination feature |
| People who must not see each other's work, or a contractor/temp | **Separate tenant.** Not a second agent in the same gateway, not a session filter |
| The client's *customers* | **No.** JamBot agents are owner-facing, never customer-facing — that is a standing rule, and this page's trust boundary is the technical reason it exists |

## Mechanics worth knowing

- **`createdActor`** is write-once, recorded at session creation when the path can prove who caused it. Authenticated humans use their durable Gateway profile id; requesting agents and system paths use the same field. **Sessions created without a proven actor stay unattributed** — which is most of ours, since tenant sessions originate from the OVU container rather than a logged-in Control UI human.
- Display names resolve live from the Gateway profile; nothing is stored on the session row, so renaming a profile updates history retroactively rather than rewriting it.
- **Ownership UI hides itself entirely below two distinct creators** — a single-operator gateway looks unchanged. So the absence of ownership chrome in a tenant is not evidence the feature is off.
- **Drafts are not private.** Admins see other people's drafts with a ghost marker. Upstream says plainly: "a coordination feature, not a security boundary."
- **Turn attribution is best-effort.** Steering can merge one person's input into another's active turn, so the transcript cannot always separate contributions. Do not build anything that treats the transcript as a per-person audit record — for that, `gateway/audit` is the surface.

## Not verified at our pin

This page describes 7.x behavior. Whether the ownership/presence surface exists at `2026.5.7` was **not** confirmed — the doctrine is version-independent and is what this annotation is for; the UI mechanics are not. Check before promising a client the feature.
