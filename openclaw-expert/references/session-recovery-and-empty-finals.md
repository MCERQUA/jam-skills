# Session Recovery, Empty-Finals, and Conversation-Flow Failures

Documented 2026-04-19 from a 10-hour investigation on josh.jam-bot.com. This is the playbook for debugging "agent returns nothing / agent loses context / conversation falls apart" — don't re-discover from scratch.

## The core failure mode: MiniMax empty-final

**Symptom:** user message → 200-500ms later → empty `text_done` → client shows "Sorry, I couldn't process that."

**Log signature (in openvoiceui container logs, NOT openclaw):**
```
WARNING:services.gateways.openclaw:### chat.final with no text (no subagent) — signaling retry
```

**What it means:** MiniMax-M2.7-highspeed completed the turn with `chat.final` but zero text output. Not a timeout. The LLM "finished" with no content. Observed 15+ times in a 30-minute window on josh. Pattern: fresh sessions often get ONE successful turn, then subsequent turns empty out.

**openclaw's server-side failover does NOT handle this.** Per `models-and-providers.md`, failover triggers on rate-limit, auth, or timeout — NOT on empty responses. So the empty-final reaches the OVU client directly.

**Why not raise it with the MiniMax vendor:** empty-final is intermittent and context-dependent. Specific session state + specific prompt accumulation triggers it. Can't reproduce on isolated test inputs.

**OVU's workaround:** `services/gateways/openclaw.py::_stream_events` returns `'empty-final'` to `_send_and_stream`, which retries `chat.send` once. If the retry also empties, emits null text_done and lets the upstream cascade handle it.

## The cascade architecture

Order of layers that fire when MiniMax empties:

1. **Gateway retry (Fix I)** — `_send_and_stream` catches `empty-final`, re-issues `chat.send` once.
2. **Fast-empty retry** — if llm_ms < 5000 and response empty, re-sends `message_with_context` on same session.
3. **Steer-recovery refire (Fix E)** — if there was a recent steer (<30s) on this session, re-fires that steer as a fresh turn.
4. **Double-empty → session recovery (Fix C)** — switches sessionKey from `main` to timestamped `recovery-<epoch>`, injects a context-replay prime, re-fires.
5. **Z.AI direct fallback** — standalone one-shot call to `api.z.ai/api/anthropic/v1/messages` with full context as a last-resort non-openclaw path.

Cascade takes 2-6s end-to-end when all layers fire. Client shows a "one moment..." SpeechSynthesis utterance at t=2s to cover silence.

## The recovery prime

`_build_recovery_prime()` pulls last 30 turns from `conversation_log` (both `session_id='default'` AND `session_id IS NULL` — most rows are NULL because the main conversation route passes request-scoped session_id). Renders them as a `[RECENT CONTEXT — ...]` prefix on the first turn of the recovery session.

**Phrasing matters.** Earlier prime text said "`[SESSION_RECOVERED]: Previous session was reset`" — agents interpreted this as a break and responded in fresh-chat register ("Yeah, I'm here. What are we working on?"). Current phrasing tells the agent to treat it as ongoing conversation, not a reset.

## Session poisoning pattern

Once `main` poisons (first double-empty), every subsequent user message also empties instantly. Openclaw's server-side session state for `main` has a corrupted message history that doesn't self-heal by WS reconnect. Recovery is STICKY: once we flip to `recovery-<epoch>`, we stay there for process lifetime. Manual `/api/session/reset` is the only way back to `main`.

## Related fixes (all in openvoiceui, not openclaw)

| Fix | File | Purpose |
|-----|------|---------|
| A | `src/app.js` | `_textDoneReceived` flag — post-text_done messages abort + fresh path instead of orphan steer |
| B | `routes/conversation.py` | Uncommitted-promise auto-continue when assistant promises work but emits zero tool_use |
| C | `routes/conversation.py` | `_build_recovery_prime()` + first-turn injection on recovery session |
| D | `routes/message_classifier.py` | Steer patterns for `naw/nah/nuh-uh` + scope-refinement ("X only", "just X", "not Y") |
| E | `routes/conversation.py` | `record_recent_steer`/`consume_recent_steer` — re-fires lost steers on empty |
| F | `routes/conversation.py` | Recovery idle-timeout (10min, activity-bumped) not elapsed-entry-time |
| G | `routes/conversation.py` | Prime pulls NULL session_id rows + 30 turn depth (was 'default' only + 6) |
| H | `routes/conversation.py` | Cooldown against last-exited not last-entered — allows re-entry when main re-poisons |
| I | `services/gateways/openclaw.py` | Empty-final retry in `_send_and_stream` — catches MiniMax empty-finals |
| J | `src/app.js` | Stop double-processing `data.actions` in text_done (already streamed live) |
| K | `src/app.js` | No more "Sorry, I couldn't process that" in transcript — silent mic-resume |
| L | `src/app.js` | Persistent cascade filler via SpeechSynthesis — "one moment / still working / almost there" |
| M | `routes/conversation.py` | Removed `time.sleep(1/2)` padding from retry paths — tighter cascade |

## Triage checklist when user reports "agent silent / responds with wrong context"

1. **Check for empty-final cluster.** In the openvoiceui container: `grep "chat.final with no text" logs | wc -l`. Three or more in 5 min = MiniMax degraded. The `minimax_empty_cluster` alert fires automatically from the session-monitor.

2. **Check if stuck in recovery.** `grep "SESSION RECOVERY" logs | tail -5`. If recent recovery entries + no `RECOVERY CLEARED`, the session is persistently on `recovery-<epoch>`.

3. **Check if `main` is the poisoned side.** If always empty on main but first recovery turn succeeds → main is the broken one. Don't auto-exit recovery; let it stay.

4. **Container restart is NOT a fix.** MEMORY rule: never restart openclaw to "reset" a poisoned session — kills in-progress work. Session reset via `/api/session/reset` is the proper path.

5. **Prime size.** `grep "Injecting session-recovery prime" logs`. If prime is <500 chars, the conversation_log has very few rows — may need to rebuild context manually.

## What NOT to do

- Do NOT flip primary to GLM as a first reaction. MiniMax is primary for good reasons (rate limits, cache behavior, speed). Use Fix I retry + recovery cascade instead. Only flip if MiniMax is down >1 hour consistently.
- Do NOT add more `time.sleep()` "to let things settle" in retry paths. Every sleep is dead silence for the user. Fix M removed all of them.
- Do NOT restart the openvoiceui container mid-session to deploy fixes. Shows "⚠️ Task interrupted — agent restarted" to the user. Hot-swap Python files with `docker cp` and restart during idle windows.
- Do NOT treat `data.actions` in `text_done` as new. Every action is already streamed via individual `type:'action'` events — re-processing duplicates in the action panel.

## Session-monitor signals to watch

| Event | What it means |
|-------|---------------|
| `empty_final` | Single MiniMax no-text return. Normal noise at low rate. |
| `empty_final_retry_failed` | Fix I's second attempt also empty. About to fall to upstream cascade. |
| `minimax_empty_cluster` alert | 3+ empty-finals in 5 min — provider degraded, investigate. |
| `session_poisoned` alert | Double-empty fired. Recovery activating. |
| `recovery_prime_injected` | Fresh recovery session started. Count chars to verify prime size. |
| `recovery_cooldown` | Recovery blocked by 10s cooldown from last exit. Should be rare. |
| `recovery_timeout` | Recovery session idle >10min. Cleared. |
| `uncommitted_promise` | Fix B caught "I'll do X" with zero tool use. Auto-continuing. |
| `auto_continue` | Fix B sent the continue-steer. Expect tools on the next turn. |
| `steer_recovery_refire` | Fix E caught a lost steer and refiring as fresh turn. |
