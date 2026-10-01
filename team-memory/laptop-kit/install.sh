#!/bin/bash
# danielle-laptop@mesh kit installer v2 (Git Bash on Windows). Safe to re-run; re-running = update.
# Get the latest:  ~/jambot-mesh/bin/mesh team kit install.sh > ~/jambot-install.sh && bash ~/jambot-install.sh
# Installs: ~/jambot-mesh/bin/{mesh,session-start.sh,mesh-watch.sh}, ~/jambot-mesh/{MEMORY.md,BRIEF.md},
#           skills in ~/.claude/skills/ (jambot-mesh, team-memory + a curated JamBot set from the CDN),
#           an identity block in ~/.claude/CLAUDE.md, and the SessionStart hook in ~/.claude/settings.json.
set -u
K="$HOME/.ssh/danielle_laptop_mesh"
D="$HOME/jambot-mesh"; B="$D/bin"; SK="$HOME/.claude/skills"
mkdir -p "$B" "$SK"
[ -f "$K" ] || { echo "MISSING KEY $K - stop and tell host-clone@mesh"; exit 1; }

cat > "$B/mesh" <<'EOF'
#!/bin/bash
# mesh <command> [args...] -> ONE allowed command on the JamBot server through YOUR door (port 2222).
# Allowed: ping | mesh-send ... (body on stdin) | mesh-recv [--show <file>] | mesh-ack <file> | get-secret <name> | team ...
exec ssh -i "$HOME/.ssh/danielle_laptop_mesh" -o IdentitiesOnly=yes -o BatchMode=yes \
  -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -p 2222 mike@100.99.44.88 "$(printf '%q ' "$@")"
EOF

cat > "$B/session-start.sh" <<'EOF'
#!/bin/bash
# SessionStart hook: everything printed here is loaded into the new Claude session's context.
D="$HOME/jambot-mesh"; M="$D/bin/mesh"
echo "=== YOU ARE danielle-laptop@mesh (Danielle's laptop agent on the JamBot mesh). Skill: jambot-mesh ==="
echo; echo "=== YOUR OWN MEMORY ($D/MEMORY.md) ==="
[ -f "$D/MEMORY.md" ] && cat "$D/MEMORY.md"
echo
if out=$("$M" ping 2>&1); then
  echo "=== MESH: $out ==="
  echo; "$M" team context 2>&1
  echo; echo "=== UNREAD MESH INBOX ==="
  "$M" mesh-recv 2>/dev/null | head -40
else
  echo "=== MESH UNREACHABLE: $out (is Tailscale connected?) ==="
fi
echo
echo "=== DO NOW ==="
echo "1. Handle each unread message: ~/jambot-mesh/bin/mesh mesh-recv --show <file>, act, then ~/jambot-mesh/bin/mesh mesh-ack <file>"
echo "2. Arm the inbox watcher with your Monitor tool (persistent): bash ~/jambot-mesh/bin/mesh-watch.sh"
echo "3. Every server command goes through ~/jambot-mesh/bin/mesh (port 2222). Never ssh to port 22."
EOF

cat > "$B/mesh-watch.sh" <<'EOF'
#!/bin/bash
# Inbox watcher for the Monitor tool: polls every 60s, prints one line per NEW unread message.
M="$HOME/jambot-mesh/bin/mesh"; SEEN="$HOME/jambot-mesh/.seen"; touch "$SEEN"
echo "mesh-watch armed for danielle-laptop@mesh (60s poll)"
while true; do
  "$M" mesh-recv 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}-[A-Za-z0-9._-]+\.md' | sort -u | while read -r f; do
    grep -qxF "$f" "$SEEN" || { echo "NEW MESH MESSAGE: $f  (read: ~/jambot-mesh/bin/mesh mesh-recv --show $f)"; echo "$f" >> "$SEEN"; }
  done
  sleep 60
done
EOF
chmod +x "$B/mesh" "$B/session-start.sh" "$B/mesh-watch.sh"

[ -f "$D/MEMORY.md" ] || cat > "$D/MEMORY.md" <<'EOF'
# danielle-laptop private memory (things only this laptop needs; team facts go in `mesh team remember`)
- 2026-10-01: Enrolled on the JamBot mesh. Door = port 2222 via ~/jambot-mesh/bin/mesh.
EOF

# Skills: ours (served through the door) + a curated JamBot set from the public CDN.
ok=0; fail=""
for s in jambot-mesh team-memory; do
  mkdir -p "$SK/$s"
  if "$B/mesh" team kit "$s.SKILL.md" > "$SK/$s/SKILL.md.tmp" && [ -s "$SK/$s/SKILL.md.tmp" ]; then
    mv "$SK/$s/SKILL.md.tmp" "$SK/$s/SKILL.md"; ok=$((ok+1)); else fail="$fail $s"; fi
done
"$B/mesh" team kit BRIEF.md > "$D/BRIEF.md.tmp" && [ -s "$D/BRIEF.md.tmp" ] && mv "$D/BRIEF.md.tmp" "$D/BRIEF.md"
for s in social-media-designer social-research social-image-picker marketing mac-tool mac-image-gen video-to-mac \
         handoff web-search-guidelines premium-web-design pdf docx xlsx customer-comms retire-dont-delete; do
  mkdir -p "$SK/$s"
  if curl -fsSL --max-time 20 "https://skills.jam-bot.com/$s.md" -o "$SK/$s/SKILL.md.tmp" && head -1 "$SK/$s/SKILL.md.tmp" | grep -q '^---'; then
    mv "$SK/$s/SKILL.md.tmp" "$SK/$s/SKILL.md"; ok=$((ok+1)); else rm -f "$SK/$s/SKILL.md.tmp"; fail="$fail $s"; fi
done
echo "skills installed: $ok${fail:+ | FAILED:$fail}"

# Identity block in the user-level CLAUDE.md (every Claude session on this laptop sees it).
C="$HOME/.claude/CLAUDE.md"; touch "$C"
if ! grep -q "BEGIN danielle-laptop@mesh" "$C"; then
  cat >> "$C" <<'EOF'

<!-- BEGIN danielle-laptop@mesh (installed by the JamBot laptop kit; re-run the kit to update) -->
You are **danielle-laptop@mesh**, Danielle's laptop agent on the JamBot mesh, one of four agents serving
her as one team (danielle-desktop@mesh, danielle-voice@mesh, danielle-sms@mesh). Use the **jambot-mesh**
skill for messaging and the server, and **team-memory** for the shared memory + task board. Every server
command goes through `~/jambot-mesh/bin/mesh` (port 2222); never ssh to port 22. Results go back to whoever
asked; never contact a client/account owner about Danielle's work unless she says so.
<!-- END danielle-laptop@mesh -->
EOF
fi

# SessionStart hook in the user-level Claude settings (merged, never clobbered).
S="$HOME/.claude/settings.json"
HOOKCMD='bash ~/jambot-mesh/bin/session-start.sh'
if [ -f "$S" ] && grep -qF "$HOOKCMD" "$S"; then
  echo "hook already present"
elif PY=$(command -v python3 || command -v python) && "$PY" -c "import json" 2>/dev/null; then
  "$PY" - "$S" "$HOOKCMD" <<'PYEOF'
import json, os, shutil, sys
p, cmd = sys.argv[1], sys.argv[2]
s = {}
if os.path.exists(p):
    shutil.copyfile(p, p + ".bak-pre-mesh-hook")
    try: s = json.load(open(p, encoding="utf-8"))
    except Exception: s = {}
s.setdefault("hooks", {}).setdefault("SessionStart", []).append({"hooks": [{"type": "command", "command": cmd, "timeout": 60}]})
json.dump(s, open(p, "w", encoding="utf-8"), indent=2)
PYEOF
  echo "hook added"
elif command -v node >/dev/null 2>&1; then
  node -e '
    const fs=require("fs"),p=process.argv[1],cmd=process.argv[2];
    let s={}; try{ s=JSON.parse(fs.readFileSync(p,"utf8")); }catch(e){}
    if(fs.existsSync(p)) fs.copyFileSync(p,p+".bak-pre-mesh-hook");
    s.hooks=s.hooks||{}; s.hooks.SessionStart=s.hooks.SessionStart||[];
    s.hooks.SessionStart.push({hooks:[{type:"command",command:cmd,timeout:60}]});
    fs.writeFileSync(p,JSON.stringify(s,null,2));' "$S" "$HOOKCMD" && echo "hook added"
else
  echo "NO-PYTHON-NO-NODE: merge this into $S yourself with your Edit tool (keep existing keys):"
  echo '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"bash ~/jambot-mesh/bin/session-start.sh","timeout":60}]}]}}'
fi

echo "--- self-test ---"
"$B/mesh" ping
"$B/mesh" get-secret books-scanner-key >/dev/null && echo "get-secret ok (key not shown)"
"$B/mesh" team tasks | head -3
"$B/mesh" mesh-recv 2>/dev/null | head -4
echo "INSTALL DONE"
# END-INSTALL
