---
name: ubuntu-desktop
description: "Control the KDE Ubuntu webtop via 8 ovui-desktop plugin tools — screenshot, list windows, launch apps, move/resize windows, type text, send key combos, click at coordinates, and create desktop launchers."
version: 1.0.0
---

# Ubuntu Desktop Control

You have 8 tools to drive the KDE desktop via the ovui-desktop plugin. Use them to automate the desktop, run apps, take screenshots, type, click, and manage windows.

---

## Tools

| Tool | What it does |
|------|-------------|
| `ovui_screenshot` | Capture the current desktop as JPEG. Returns base64 image. Use before clicking to confirm state. |
| `ovui_list_windows` | List all open windows with title, class, position, size. Use to find window IDs before placing. |
| `ovui_launch_app` | Launch any app by command (e.g. `chromium`, `konsole`, `dolphin`, `kate`). |
| `ovui_place_window` | Move/resize a window. Match by title substring. |
| `ovui_type_text` | Type text into the focused window. Sends keystrokes. |
| `ovui_key_press` | Send a key combo (e.g. `ctrl+t`, `ctrl+l`, `Return`, `Escape`, `super`). |
| `ovui_mouse_click` | Click at absolute screen coordinates `{x, y}`. Left/right/middle. |
| `ovui_create_desktop_icon` | Create a `.desktop` launcher on the KDE desktop. |

---

## Core Workflow Patterns

### 1. See before you act
Always take a screenshot first when unsure of current state:
```
ovui_screenshot() → look at result → then act
```

### 2. Open a URL in Chrome
```
ovui_launch_app("chromium https://example.com")
# wait ~2s for window
ovui_list_windows()  # find the chrome window
ovui_key_press("ctrl+l")  # focus address bar
ovui_type_text("https://new-url.com")
ovui_key_press("Return")
```

### 3. Open a terminal and run a command
```
ovui_launch_app("konsole")
# wait ~1s
ovui_type_text("your command here")
ovui_key_press("Return")
ovui_screenshot()  # verify output
```

### 4. Click a UI element
```
ovui_screenshot()  # find coordinates from screenshot
ovui_mouse_click({x: 640, y: 400, button: "left"})
```

### 5. Focus a specific window
```
ovui_list_windows()  # get window titles
ovui_place_window({match: "Firefox", x: 0, y: 0, width: 1280, height: 800})
```

### 6. Type into a form field
```
ovui_mouse_click({x: <field x>, y: <field y>})  # click the field first
ovui_type_text("text to enter")
ovui_key_press("Tab")  # advance to next field
```

---

## Tested Workflows

### Open the voice app in Chrome
```
ovui_launch_app("chromium --app=https://test-dev.jam-bot.com")
```

### Open a canvas page
```
ovui_key_press("ctrl+l")
ovui_type_text("https://test-dev.jam-bot.com/pages/desktop.html")
ovui_key_press("Return")
```

### Copy text from terminal output
```
ovui_key_press("ctrl+a")  # select all in terminal
ovui_key_press("ctrl+c")  # copy
```

### Tile two windows side by side
```
ovui_list_windows()  # get titles
ovui_place_window({match: "Window A", x: 0, y: 0, width: 960, height: 1080})
ovui_place_window({match: "Window B", x: 960, y: 0, width: 960, height: 1080})
```

---

## Limitations & Gotchas

- **Wayland panel clicks don't work** — KDE taskbar, system tray, and panel items use Wayland surfaces that ignore xdotool clicks. Use keyboard shortcuts instead (e.g. `super` to open launcher, `alt+F4` to close).
- **`ovui_screenshot` is expensive** — base64 JPEG is ~200KB = many tokens. Take one screenshot to orient, then act. Don't screenshot after every keystroke.
- **App launch is async** — apps take 1-3s to appear. After `ovui_launch_app`, wait before calling `ovui_list_windows` or clicking.
- **`ovui_type_text` needs focus** — the target window must be focused first. Click into it or use `ovui_place_window` to bring it forward.
- **Coordinates are absolute** — `ovui_mouse_click` uses screen pixels from top-left. Get coordinates from a screenshot.
- **Selkies stream must be active** — if no browser is connected to desktop.jam-bot.com, screenshots will be stale/frozen.

---

## Adding New Workflows

When you discover a reliable multi-step workflow, add it to the **Tested Workflows** section above with:
1. A short name
2. The exact tool call sequence
3. Any timing notes or gotchas

This skill is the evolving library. Refine it as you learn what works.
