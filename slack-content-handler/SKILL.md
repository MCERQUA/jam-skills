---
name: slack-content-handler
description: Download files/images from Slack, process them, and present results on canvas pages
---

# Slack Content Handler

When users share files, images, or videos in Slack and ask you to do something with them — download the content, process it, and deliver results as a canvas page.

## When to Use This Skill

- User shares images in Slack and asks you to organize, edit, review, or present them
- User shares documents and asks you to analyze, summarize, or display them
- User asks you to "download" or "grab" files from Slack
- User shares project photos and wants a gallery, before/after comparison, or presentation
- User shares a video and wants edits, thumbnails, or a review page
- Any request where Slack-shared content needs to become a deliverable on canvas

## Environment Variables (already in your container)

| Variable | Purpose |
|----------|---------|
| `SLACK_BOT_TOKEN` | Bot auth token (`xoxb-...`) — used for all Slack API calls |
| `SLACK_CHANNEL_COMPANY` | Main company channel ID |
| `SLACK_CHANNEL_AI_UPDATES` | AI updates channel ID |
| `SLACK_CHANNEL_LEADS` | Leads channel ID |

## Step 1: Find Files in Slack

List recent files shared in the workspace:

```bash
curl -s -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  "https://slack.com/api/files.list?count=20&types=images" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not data.get('ok'):
    print('ERROR:', data.get('error'))
    sys.exit(1)
for f in data.get('files', []):
    print(f'{f[\"id\"]}|{f[\"name\"]}|{f[\"size\"]}|{f[\"mimetype\"]}|{f[\"url_private_download\"]}')
"
```

**Filter by type:** Change `types=` parameter:
- `images` — photos, screenshots, graphics
- `videos` — video files
- `pdfs` — PDF documents
- `all` — everything

**Filter by channel:** Add `&channel=CHANNEL_ID`
**Filter by user:** Add `&user=USER_ID`

## Step 2: Download Files

Download using the bot token for auth:

```bash
curl -s -o "/app/runtime/uploads/slack-files/FILENAME" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  "DOWNLOAD_URL"
```

**Rules:**
- Always save to `/app/runtime/uploads/slack-files/` (create the directory first)
- Use `mkdir -p /app/runtime/uploads/slack-files/` before downloading
- Preserve original filenames
- Files saved here are accessible via `/uploads/slack-files/FILENAME` in canvas pages

## Step 3: Convert Formats

Browsers cannot display HEIC files (iPhone photos). Convert to JPG:

```bash
convert "INPUT.heic" -quality 90 -auto-orient "OUTPUT.jpg"
```

**Available converters:**
| Tool | Use For |
|------|---------|
| `convert` (ImageMagick) | HEIC→JPG, resize, crop, thumbnails, format conversion |
| `ffmpeg` | Video conversion, thumbnails from video, audio extraction |
| `python3` | PDF text extraction, data processing |

**Common conversions:**
```bash
# HEIC to JPG (iPhone photos)
convert photo.heic -quality 90 -auto-orient photo.jpg

# Create thumbnail (400px wide)
convert photo.jpg -resize 400x -quality 80 thumb_photo.jpg

# Extract frame from video as thumbnail
ffmpeg -i video.mp4 -ss 00:00:05 -vframes 1 thumbnail.jpg

# Resize for web (max 1200px wide, keep aspect ratio)
convert photo.jpg -resize 1200x\> -quality 85 photo_web.jpg
```

## Step 4: Build Canvas Page

Create an HTML page to present the content. Write to `/app/runtime/canvas-pages/`.

**Photo Gallery Template:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PAGE TITLE</title>
<meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f1117; color: #e2e8f0; min-height: 100vh;
  }
  .header {
    background: linear-gradient(135deg, #1a1d2e 0%, #0f1117 100%);
    border-bottom: 1px solid #2a3040; padding: 24px 32px;
  }
  .header h1 { font-size: 1.5rem; font-weight: 700; color: #f1f5f9; }
  .header p { font-size: 0.9rem; color: #94a3b8; margin-top: 4px; }
  .gallery {
    padding: 24px 32px;
    display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px; max-width: 1400px; margin: 0 auto;
  }
  .photo-card {
    background: #1a1d2e; border: 1px solid #2a3040;
    border-radius: 12px; overflow: hidden; cursor: pointer;
    transition: transform 0.2s, border-color 0.2s;
  }
  .photo-card:hover { transform: translateY(-2px); border-color: #3b82f6; }
  .photo-card img { width: 100%; height: 300px; object-fit: cover; display: block; }
  .photo-card .info { padding: 12px 16px; font-size: 0.85rem; color: #94a3b8; }
  /* Lightbox */
  .lightbox {
    display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.95); z-index: 1000;
    justify-content: center; align-items: center; padding: 40px;
  }
  .lightbox.active { display: flex; }
  .lightbox img { max-width: 95vw; max-height: 90vh; object-fit: contain; border-radius: 8px; }
  .lb-close {
    position: fixed; top: 16px; right: 24px; font-size: 2rem;
    color: #94a3b8; cursor: pointer; background: none; border: none; z-index: 1001;
  }
  .lb-nav {
    position: fixed; top: 50%; transform: translateY(-50%);
    font-size: 2.5rem; color: #94a3b8; cursor: pointer;
    background: rgba(0,0,0,0.5); border: none; padding: 8px 16px;
    border-radius: 8px; z-index: 1001;
  }
  .lb-nav:hover { color: #fff; background: rgba(59,130,246,0.4); }
  .lb-nav.prev { left: 16px; }
  .lb-nav.next { right: 16px; }
  .lb-count {
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    color: #94a3b8; font-size: 0.9rem; z-index: 1001;
  }
  @media (max-width: 600px) {
    .gallery { grid-template-columns: 1fr; padding: 12px; }
    .photo-card img { height: 240px; }
  }
</style>
</head>
<body>

<div class="header">
  <h1>PAGE TITLE</h1>
  <p>SUBTITLE — DATE</p>
</div>

<div class="gallery">
  <!-- Repeat for each image -->
  <div class="photo-card" onclick="openLB(INDEX)">
    <img src="/uploads/slack-files/FILENAME.jpg" alt="Description" loading="lazy">
    <div class="info">FILENAME — INDEX / TOTAL</div>
  </div>
</div>

<div class="lightbox" id="lb">
  <button class="lb-close" onclick="closeLB()">&times;</button>
  <button class="lb-nav prev" onclick="navLB(-1)">&lsaquo;</button>
  <img id="lb-img" src="">
  <button class="lb-nav next" onclick="navLB(1)">&rsaquo;</button>
  <div class="lb-count" id="lb-count"></div>
</div>

<script>
const imgs = [/* '/uploads/slack-files/photo1.jpg', '/uploads/slack-files/photo2.jpg' */];
let ci = 0;
function openLB(i) {
  ci = i; document.getElementById('lb-img').src = imgs[i];
  document.getElementById('lb-count').textContent = (i+1)+' / '+imgs.length;
  document.getElementById('lb').classList.add('active');
  document.body.style.overflow = 'hidden';
}
function closeLB() {
  document.getElementById('lb').classList.remove('active');
  document.body.style.overflow = '';
}
function navLB(d) {
  ci = (ci+d+imgs.length)%imgs.length;
  document.getElementById('lb-img').src = imgs[ci];
  document.getElementById('lb-count').textContent = (ci+1)+' / '+imgs.length;
}
document.addEventListener('keydown', e => {
  if (!document.getElementById('lb').classList.contains('active')) return;
  if (e.key==='Escape') closeLB();
  if (e.key==='ArrowLeft') navLB(-1);
  if (e.key==='ArrowRight') navLB(1);
});
document.getElementById('lb').addEventListener('click', function(e) { if (e.target===this) closeLB(); });
</script>
</body>
</html>
```

## Step 5: Open the Canvas Page

After writing the HTML file, embed the canvas tag in your response:

```
Here are your project photos. [CANVAS:page-name] Click any image to view full size.
```

## Step 6: Provide the Link

The public URL for any canvas page is:

```
https://DOMAIN/pages/PAGE-NAME.html
```

Use the `DOMAIN` environment variable if available, otherwise use the domain from the user's Slack workspace context.

## Complete Workflow Example

User says in Slack: "Download all these photos and put them on a page for me"

1. **List files:** `curl` the `files.list` API filtered to recent images
2. **Create directory:** `mkdir -p /app/runtime/uploads/slack-files/`
3. **Download each file:** `curl` with bot token auth to the `url_private_download` URL
4. **Convert if needed:** HEIC→JPG with `convert`, auto-orient
5. **Write canvas page:** Photo gallery HTML to `/app/runtime/canvas-pages/project-photos.html`
6. **Open it:** Include `[CANVAS:project-photos]` in your response
7. **Verify:** `curl -s http://openvoiceui:5001/api/canvas/context` to confirm it opened
8. **Share link:** Tell the user the URL they can share

## Important Rules

- **Always download to server immediately** — never hold files only in memory
- **Convert HEIC to JPG** — browsers cannot display HEIC natively
- **Use `-auto-orient`** with ImageMagick — iPhone photos have EXIF rotation data
- **Dark theme only** — background `#0f1117`, text `#e2e8f0`, accent `#3b82f6`
- **No emojis** in page headers, labels, or UI elements
- **No external CDN** — all CSS/JS inline
- **No localStorage** — everything on the server
- **Set permissions** after creating directories: files need to be readable by the web server

## Uploading Files TO Slack

To share a file back to a Slack channel:

```bash
curl -s -X POST "https://slack.com/api/files.uploadV2" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -F "channel_id=$SLACK_CHANNEL_COMPANY" \
  -F "file=@/path/to/file.png" \
  -F "title=File Title" \
  -F "initial_comment=Here's the deliverable"
```

## Posting a Link to Slack

```bash
curl -s -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL_COMPANY\",
    \"text\": \"Your project photos are ready: https://DOMAIN/pages/project-photos.html\"
  }"
```
