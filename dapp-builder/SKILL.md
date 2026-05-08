---
name: dapp-builder
description: Build decentralized apps, web apps, or Python apps with live preview using the dApp Builder canvas page. Read when the user asks to build/preview an app or wants Web3/dApp prototyping.
---

# dApp Builder — Build Apps with Live Preview

The dApp Builder is a code editor + live preview canvas page. You send code to it, the user sees it render live.

## How to use

1. Write project files as JSON to `/app/runtime/canvas-pages/_data/dapp-project.json` with:
   - `_ts` — set to `$(date +%s)`, **update on each change**
   - `files` — keys are filenames with extensions, values are file content
2. Open the builder: `[CANVAS:dapp-builder]` — auto-loads files, polls for `_ts` changes every 5s
3. User clicks **Run** (or enables Auto-run) to preview

## Web3 dApps

Include ethers.js via script tag in your HTML files. The preview iframe supports MetaMask injection.

## Example file write

```bash
exec("cat > /app/runtime/canvas-pages/_data/dapp-project.json <<EOF
{
  \"_ts\": $(date +%s),
  \"files\": {
    \"index.html\": \"<!DOCTYPE html>...\",
    \"style.css\": \"body { ... }\",
    \"app.js\": \"...\"
  }
}
EOF")
```

After writing, emit `[CANVAS:dapp-builder]` in your spoken reply.
