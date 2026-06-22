---
name: peekaboo-click-patterns
description: "Click Mac UI elements by stable element IDs using Peekaboo — the correct default for all Mac desktop automation. Covers see→extract→click, not-found handling, and when NOT to use coordinates or osascript."
version: 1.0.0
---

# Peekaboo Click Patterns

Use Peekaboo element IDs for **all** Mac UI interaction. Never default to pixel coordinates or osascript keystrokes — both fail silently when layouts shift or Secure Input is active.

## The three-step pattern

```bash
# 1. Capture the current AX tree
peekaboo see

# 2. Find your target in the output — look for role + label
#    Output lines look like: elem_42  AXButton "Cancel"  [pos: 400,300 size: 80,30]

# 3. Click by element ID — stable across resolution and dialog reflows
peekaboo click --on elem_42
```

That's it. The element ID is resolved from the AX tree, not screen coordinates.

---

## When the element isn't visible yet

Dialogs animate in. If `peekaboo see` returns nothing useful, wait and retry:

```bash
for i in 1 2 3; do
  peekaboo see | grep -i "cancel\|dismiss\|ok" && break
  sleep 1
done
peekaboo click --on elem_N   # use the ID from the grep hit
```

---

## Extracting IDs from `peekaboo see` output

```bash
# Get IDs for all buttons
peekaboo see | grep AXButton

# Get ID for a specific label (case-insensitive)
peekaboo see | grep -i "sign in"

# Full see output to a file for inspection
peekaboo see > /tmp/ax-tree.txt
```

Output format:
```
elem_113  AXButton "Cancel"        [pos: 520,410 size: 80,32]
elem_114  AXButton "Sign In"       [pos: 614,410 size: 80,32]
elem_115  AXTextField ""           [pos: 400,320 size: 300,28]
```

---

## Typing into fields

```bash
# Click the field first, then type
peekaboo click --on elem_115
peekaboo type "my text here"

# Or use fill if Peekaboo supports it
peekaboo fill --on elem_115 --text "value"
```

---

## Not-found handling

```bash
TARGET=$(peekaboo see | grep -i "cancel" | awk '{print $1}' | head -1)
if [ -z "$TARGET" ]; then
  echo "cancel button not found — dialog may not be visible yet"
  exit 1
fi
peekaboo click --on "$TARGET"
```

---

## When to use coordinates instead

Only when:
- The target has no AX role (e.g. a canvas, game window, or custom-drawn UI)
- `peekaboo see` returns no elements at all (accessibility off for that app)

In those cases, use `peekaboo screenshot` + measure coordinates from the image. Still prefer Peekaboo's click command over pyautogui.

---

## Anti-patterns to avoid

| Anti-pattern | Why it breaks | Use instead |
|---|---|---|
| `osascript -e 'tell application ... to click button "OK"'` | Blocked by Secure Input on lock screen / auth dialogs; brittle to UI changes | `peekaboo click --on elem_N` |
| `pyautogui.click(400, 300)` | Coordinate-brittle; fails if display resolution or dialog position changes | `peekaboo click --on elem_N` |
| Clicking without `peekaboo see` first | No element reference — you're guessing | Always `see` first |
| Hard-coding elem_N across sessions | IDs are session-scoped, not persistent | Always call `peekaboo see` fresh |

---

## Dialogs that commonly need this

- iCloud sign-in sheet (blocks Desktop)
- iPhone passcode pairing dialog
- macOS Software Update prompts
- Safari/Chrome permission dialogs
- App Store sign-in sheets
- Accessibility permission requests

---

## Peekaboo commands reference

```bash
peekaboo see                    # AX tree of frontmost app (or all apps with --all)
peekaboo see --app Safari       # scope to specific app
peekaboo see --all              # all apps (slower, more complete)
peekaboo click --on elem_N      # click by element ID
peekaboo type "text"            # type into focused element
peekaboo screenshot             # capture screen
peekaboo screenshot --app Foo   # capture specific app window
```

---

## Dialog-dismissal time benchmark

| Approach | Typical time | Failure modes |
|---|---|---|
| osascript → pyautogui coords → Peekaboo | ~20 min | Two failed pivots before correct tool |
| Peekaboo element IDs from start | ~3 min | None (element IDs are stable) |

**Always start with Peekaboo.**
