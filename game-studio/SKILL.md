---
name: game-studio
description: "Autonomous game development studio. Use when user wants to make a game, build a game, create a game, game development, game design, or anything game-related. Supports Godot, Unity, Unreal Engine, Love2D, Pygame, Bevy. Handles full pipeline: concept design, architecture, implementation, testing, build."
metadata:
  version: 1.0.0
---

# Game Studio — Autonomous Game Development Pipeline

You have access to a full autonomous game development pipeline powered by z-code. When a user wants to make a game, you help them define the concept and then kick off the pipeline that builds it.

## How It Works

The game studio is a 6-phase autonomous pipeline:
1. **Concept & Design** — Game Design Documents, core loop, systems mapping, scope
2. **Systems Design** — Detailed GDDs for every system with real formulas and balance
3. **Architecture** — Technical architecture, class design, ADRs, scene structure
4. **Implementation** — Full game code, all systems, UI, AI, playable level, tests
5. **Testing & Review** — QA, comprehensive testing, code review, fix list
6. **Fix & Polish** — Bug fixes, polish pass, release notes

Each phase spawns z-code (autonomous Claude Code) inside the user's openclaw container. z-code has 48 specialized game development agent definitions (Creative Director, Game Designer, Lead Programmer, QA Lead, etc.) and 11 coding rule sets loaded automatically.

## Supported Engines
- **Godot** (GDScript) — recommended for indie/2D games
- **Unity** (C#) — recommended for 3D games
- **Unreal** (C++/Blueprint) — recommended for AAA-quality
- **Love2D** (Lua) — lightweight 2D
- **Pygame** (Python) — beginner-friendly
- **Bevy** (Rust) — ECS-based
- **Custom** — bring your own engine/framework

## What You Need From the User

Before starting, gather these details conversationally:

1. **Game concept** — What's the game about? What makes it fun? (1-3 sentences minimum)
2. **Engine preference** — Which engine? If unsure, recommend Godot for 2D indie, Unity for 3D
3. **Genre** — roguelike, platformer, rpg, puzzle, shooter, strategy, tower-defense, survival, adventure, racing, fighting, simulation, sandbox, rhythm, card-game, etc.
4. **Platform** — pc, web, mobile, console, cross-platform

## How to Launch the Pipeline

Once you have the concept, engine, genre, and platform, execute this command using the exec tool:

```bash
bash /mnt/system/base/tools/game-studio/scripts/game-init.sh {{USERNAME}} "{{GAME_NAME}}" {{ENGINE}} {{GENRE}} {{PLATFORM}} "{{GAME_CONCEPT}}"
```

Where:
- `{{USERNAME}}` — the JamBot username (from your container context)
- `{{GAME_NAME}}` — a slug for the project (lowercase, hyphens, no spaces). Generate from the concept (e.g., "space-raiders", "dungeon-crawl", "pixel-farm")
- `{{ENGINE}}` — godot, unity, unreal, love2d, pygame, bevy, or custom
- `{{GENRE}}` — the game genre (lowercase)
- `{{PLATFORM}}` — pc, web, mobile, console, or cross-platform
- `{{GAME_CONCEPT}}` — the full game concept text (quoted)

Then immediately start the pipeline:

```bash
nohup bash /mnt/system/base/tools/game-studio/scripts/game-pipeline.sh {{USERNAME}} "{{GAME_NAME}}" > /mnt/clients/{{USERNAME}}/openclaw/workspace/Games/{{GAME_NAME}}/logs/pipeline-launch.log 2>&1 &
```

## Checking Progress

To check on a running pipeline:

```bash
bash /mnt/system/base/tools/game-studio/scripts/game-status.sh {{USERNAME}} "{{GAME_NAME}}"
```

Or check the status file directly:
```bash
cat /home/node/workspace/Games/{{GAME_NAME}}/.pipeline-status
```

Or check the game's own progress tracking:
```bash
cat /home/node/workspace/Games/{{GAME_NAME}}/production/status.json
```

## Conversation Flow

Here's how to handle the conversation:

**User says something like "I want to make a game" / "let's build a game" / "can you make me a game":**

1. Get excited! This is a big project. Ask them:
   - "What kind of game are you thinking? Tell me about the concept — what's the gameplay, what makes it fun?"
   - If they're vague: "No worries! What genre interests you? Roguelike? Platformer? RPG? Puzzle? Tower defense?"

2. Once you have the concept, confirm details:
   - "Great concept! For the engine, I'd recommend Godot for a 2D game like this [or Unity for 3D]. Sound good?"
   - "And this would be for PC? Or web/mobile too?"

3. Summarize and launch:
   - "Here's what I'm building: [summary]. I'm starting the game studio pipeline now. This runs in 6 phases — design, architecture, implementation, testing, and polish. It'll take a few hours to complete."
   - Run `game-init.sh` then `game-pipeline.sh`

4. Report back:
   - "Phase 1 (Concept & Design) is done — created the Game Design Documents, core loop, systems index, and milestone plan."
   - Check status periodically if the user asks

**User asks about progress on an existing game:**
- Run `game-status.sh` and report the results
- If a phase failed, offer to restart it

**User wants to modify a game that's already built:**
- The game files are in `~/workspace/Games/<game-name>/`
- You can read and edit them directly
- For major changes, you could re-run specific phases

## Important Notes

- Each phase takes 15-60 minutes depending on complexity
- The full pipeline takes 2-6 hours
- A watchdog cron runs every 15 minutes to catch failures and retry (up to 3 times)
- All game files are in the user's workspace at `~/workspace/Games/<game-name>/`
- The pipeline creates real, runnable game code — not just documentation
- Design docs follow an 8-section GDD standard (Overview, Player Fantasy, Rules, Formulas, Edge Cases, Dependencies, Tuning Knobs, Acceptance Criteria)
- All gameplay values are data-driven (no hardcoding) — designers can tune without code changes

## Error Handling

If the pipeline fails:
1. Check the log: `cat ~/workspace/Games/<game-name>/logs/phase-<N>-*.log | tail -50`
2. The watchdog will auto-retry up to 3 times
3. To manually retry a phase: `bash /mnt/system/base/tools/game-studio/scripts/game-phase.sh {{USERNAME}} "{{GAME_NAME}}" <phase-number>`
4. To resume the pipeline from a specific phase: `bash /mnt/system/base/tools/game-studio/scripts/game-pipeline.sh {{USERNAME}} "{{GAME_NAME}}" <start-phase>`
