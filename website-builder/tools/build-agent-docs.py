#!/usr/bin/env python3
"""
build-agent-docs.py — Produce everything a voice/text agent needs to edit the
site without searching or guessing.

Outputs (all under <project>/):
  AGENTS.md                          ← single-page primer (read first)
  docs/site-map.json                 ← every page: route, file, type, sections, h1
  docs/content-registry.json         ← intake values + every file they appear in
  docs/design-tokens.json            ← Tailwind theme + Stitch palette + fonts
  tools/site-tools/find.py           ← project-local grep helper
  tools/site-tools/swap-phone.py     ← bulk-replace phone, idempotent
  tools/site-tools/swap-email.py     ← bulk-replace email
  tools/site-tools/swap-business-name.py
  tools/site-tools/page-summary.py   ← inspect any page's section list + h1/h2

Idempotent. Safe to re-run. No project-state mutations beyond writing these files.

Usage:
  build-agent-docs.py --project <project-root> --intake <intake.json>
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from textwrap import dedent


# ─── Page classification ─────────────────────────────────────────────────────
SERVICE_PAT = re.compile(
    r"^(pvc|composite|cedar|membrane|custom-curved|deck-railing|"
    r"pergolas?|deck-repair|outdoor-living|trex|vinyl|wood)",
    re.IGNORECASE,
)
LEGAL_SLUGS = {"privacy", "terms"}
INTAKE_SLUGS = {"about", "services", "gallery", "contact", "faq"}
SYSTEM_SLUGS = {"api", "og", "sitemap", "robots", "blog"}


def classify(slug: str, intake: dict) -> str:
    if slug == "home":
        return "home"
    if slug in INTAKE_SLUGS:
        return "intake"
    if slug in LEGAL_SLUGS:
        return "legal"
    if slug == "blog":
        return "blog"
    if SERVICE_PAT.match(slug):
        return "service"
    target_markets = [
        m.strip().lower().replace(" ", "-")
        for m in (intake.get("targetMarkets") or [])
    ]
    slow = slug.lower()
    for city in sorted(target_markets, key=len, reverse=True):
        if slow == city or f"-{city}" in f"-{slow}-" or f"-{city}-" in f"-{slow}-":
            return "location"
    if slug.startswith("deck-cost-") or slug.endswith("-cost") or "cost" in slug:
        return "cost-guide"
    return "other"


# ─── Page introspection ──────────────────────────────────────────────────────
def extract_h1(text: str) -> str:
    m = re.search(r"<h1[^>]*>([^<]+)</h1>", text)
    return m.group(1).strip() if m else ""


def extract_h2_list(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"<h2[^>]*>([^<]+)</h2>", text)]


def extract_metadata_title(text: str) -> str:
    m = re.search(r'metadata\s*=\s*\{[^}]*?title:\s*"([^"]+)"', text, re.DOTALL)
    return m.group(1) if m else ""


def page_route(slug: str) -> str:
    return "/" if slug == "home" else f"/{slug}"


def page_file(project: Path, slug: str) -> Path:
    return (
        project / "src" / "app" / "page.tsx"
        if slug == "home"
        else project / "src" / "app" / slug / "page.tsx"
    )


def section_count(text: str) -> int:
    return len(re.findall(r"<section\b", text))


# ─── Content-registry: where every intake value appears ──────────────────────
def find_value_occurrences(value: str, project: Path) -> list[dict]:
    """Return [{path, line, snippet}] across src/. Empty list if value blank."""
    if not value or len(value) < 4:
        return []
    src = project / "src"
    if not src.exists():
        return []
    occ = []
    for f in src.rglob("*.tsx"):
        try:
            for i, line in enumerate(f.read_text().splitlines(), 1):
                if value in line:
                    snip = line.strip()[:120]
                    occ.append({"path": str(f.relative_to(project)), "line": i, "snippet": snip})
        except Exception:
            continue
    return occ


def normalize_phone_variants(phone: str) -> list[str]:
    """Generate searchable phone forms (formatted, digits-only, tel: form)."""
    if not phone:
        return []
    digits = re.sub(r"\D", "", phone)
    out = {phone, digits}
    if len(digits) >= 10:
        d = digits[-10:]
        out.add(f"({d[:3]}) {d[3:6]}-{d[6:]}")
        out.add(f"{d[:3]}-{d[3:6]}-{d[6:]}")
        out.add(f"{d[:3]}.{d[3:6]}.{d[6:]}")
        out.add(f"+1{d}")
    return [v for v in out if v]


# ─── Outputs ─────────────────────────────────────────────────────────────────
def write_site_map(project: Path, intake: dict) -> dict:
    pages = []
    app_dir = project / "src" / "app"
    if not app_dir.exists():
        return {"pages": [], "totalCount": 0}

    if (app_dir / "page.tsx").exists():
        text = (app_dir / "page.tsx").read_text()
        pages.append({
            "slug": "home",
            "route": "/",
            "file": "src/app/page.tsx",
            "type": "home",
            "h1": extract_h1(text),
            "h2_list": extract_h2_list(text),
            "section_count": section_count(text),
            "title_metadata": extract_metadata_title(text),
        })

    for sub in sorted(app_dir.iterdir()):
        if not sub.is_dir():
            continue
        page_tsx = sub / "page.tsx"
        if not page_tsx.exists():
            continue
        slug = sub.name
        text = page_tsx.read_text()
        pages.append({
            "slug": slug,
            "route": page_route(slug),
            "file": str(page_tsx.relative_to(project)),
            "type": classify(slug, intake),
            "h1": extract_h1(text),
            "h2_list": extract_h2_list(text)[:8],
            "section_count": section_count(text),
            "title_metadata": extract_metadata_title(text),
        })

    out = {
        "businessName": intake.get("businessName"),
        "devUrl": intake.get("devUrl"),
        "domain": intake.get("domain"),
        "totalCount": len(pages),
        "byType": {},
        "pages": pages,
    }
    for p in pages:
        out["byType"].setdefault(p["type"], []).append(p["slug"])

    docs = project / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "site-map.json").write_text(json.dumps(out, indent=2))
    return out


def write_content_registry(project: Path, intake: dict) -> dict:
    biz = (intake.get("businessName") or "").strip()
    phone = (intake.get("phone") or "").strip()
    email = (intake.get("email") or "").strip()
    address = (intake.get("address") or "").strip()
    tagline = (intake.get("tagline") or "").strip()

    registry = {
        "businessName": {
            "value": biz,
            "occurrences": find_value_occurrences(biz, project) if biz else [],
        },
        "phone": {
            "value": phone,
            "variants": normalize_phone_variants(phone),
            "occurrences": [],
        },
        "email": {
            "value": email,
            "occurrences": find_value_occurrences(email, project) if email else [],
        },
        "address": {
            "value": address,
            "occurrences": find_value_occurrences(address, project) if address else [],
        },
        "tagline": {
            "value": tagline,
            "occurrences": find_value_occurrences(tagline, project) if tagline else [],
        },
        "services": list(intake.get("services") or []),
        "hours": intake.get("hours"),
        "socialLinks": intake.get("socialLinks") or {},
    }

    # Phone occurrences over all variants
    seen = set()
    for variant in registry["phone"]["variants"]:
        for occ in find_value_occurrences(variant, project):
            key = (occ["path"], occ["line"])
            if key in seen:
                continue
            seen.add(key)
            registry["phone"]["occurrences"].append(occ)

    docs = project / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "content-registry.json").write_text(json.dumps(registry, indent=2))
    return registry


def write_design_tokens(project: Path) -> dict:
    """Read tailwind.config.ts + globals.css and emit a canonical token map.
    Handles both quoted-key (`"primary": "#fff"`) and unquoted-key
    (`primary: '#fff'`) Tailwind theme objects, plus single + double quotes."""
    tokens: dict = {"colors": {}, "fonts": {}, "fontSizes": {}, "source": []}

    tw = project / "tailwind.config.ts"
    if tw.exists():
        text = tw.read_text()
        tokens["source"].append("tailwind.config.ts")
        # Color values: hex, rgb(), hsl(), CSS var()
        color_val = r"(?:#[0-9A-Fa-f]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\)|var\([^)]+\))"
        for cm in re.finditer(
            r'(?:"(\w+)"|\'(\w+)\'|(\w[\w-]*))\s*:\s*[\'"](' + color_val + r')[\'"]',
            text,
        ):
            key = cm.group(1) or cm.group(2) or cm.group(3)
            val = cm.group(4)
            # Skip non-color keys that happen to point at hex-looking strings
            if key.lower() in {"version", "id", "name", "type"}:
                continue
            tokens["colors"][key] = val
        # Font family arrays: `manrope: ["Manrope", "sans-serif"]`
        for fm in re.finditer(
            r'(?:"(\w+)"|\'(\w+)\'|(\w[\w-]*))\s*:\s*\[\s*[\'"]([^\'"]+)[\'"]',
            text,
        ):
            key = fm.group(1) or fm.group(2) or fm.group(3)
            val = fm.group(4)
            # Heuristic: only treat as font if value looks like a font family name
            if any(c in val for c in ("-", "/", "px", "%")) and not val[0].isupper():
                continue
            if key.lower() in {"manrope", "inter", "roboto", "sans", "serif", "mono",
                               "display", "body", "heading"} or val[0].isupper():
                tokens["fonts"][key] = val

    css = project / "src" / "app" / "globals.css"
    if css.exists():
        text = css.read_text()
        tokens["source"].append("src/app/globals.css")
        # Tailwind v4 @theme tokens, classic CSS vars, and bare --color-/--font-
        for cm in re.finditer(r"--color-([\w-]+)\s*:\s*([^;\n]+);", text):
            tokens["colors"][cm.group(1).strip()] = cm.group(2).strip()
        for fm in re.finditer(r"--font-([\w-]+)\s*:\s*([^;\n]+);", text):
            tokens["fonts"][fm.group(1).strip()] = fm.group(2).strip()

    docs = project / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "design-tokens.json").write_text(json.dumps(tokens, indent=2))
    return tokens


# ─── AGENTS.md (the human-readable primer the agent reads first) ─────────────
def derive_dev_url(intake: dict, project: Path) -> str:
    """devUrl is preferred from intake; otherwise infer from project parent path
    (`.../<client>/openclaw/workspace/Websites/<project>` → `https://dev-<client>.jam-bot.com`)."""
    dev_url = (intake.get("devUrl") or "").strip()
    if dev_url:
        return dev_url
    parts = project.parts
    try:
        idx = parts.index("clients")
        client = parts[idx + 1]
        return f"https://dev-{client}.jam-bot.com"
    except (ValueError, IndexError):
        return ""


def write_agents_md(project: Path, intake: dict, site_map: dict,
                    registry: dict, tokens: dict) -> Path:
    biz = intake.get("businessName") or "(unknown)"
    domain = intake.get("domain") or "(none)"
    dev_url = derive_dev_url(intake, project) or "(none)"
    phone = registry["phone"]["value"] or "(unset)"
    email = registry["email"]["value"] or "(unset)"

    by_type = site_map.get("byType", {})
    type_lines = []
    for t in ["home", "intake", "service", "location", "cost-guide", "blog", "legal", "other"]:
        slugs = by_type.get(t, [])
        if slugs:
            paths = ", ".join(f"`/{s if s != 'home' else ''}`" for s in slugs)
            type_lines.append(f"- **{t}** ({len(slugs)}): {paths}")
    type_block = "\n".join(type_lines) if type_lines else "(no pages discovered)"

    color_lines = "\n".join(
        f"  - `{k}`: `{v}`" for k, v in sorted(tokens.get("colors", {}).items())
    ) or "  - (none extracted — see `tailwind.config.ts` directly)"
    font_lines = "\n".join(
        f"  - `{k}`: `{v}`" for k, v in sorted(tokens.get("fonts", {}).items())
    ) or "  - (none extracted — see `tailwind.config.ts` directly)"

    proj_name = project.name

    sections = []
    sections.append(f"# AGENTS.md — Edit Guide for {biz}")
    sections.append(
        "**You are an agent editing this Next.js site.** Read this whole file before "
        "making changes. Then use `docs/site-map.json`, `docs/content-registry.json`, "
        "and `docs/design-tokens.json` as machine-readable references."
    )
    sections.append("---")
    sections.append("## Identity\n\n"
                    f"- **Business:** {biz}\n"
                    f"- **Production domain:** `{domain}`\n"
                    f"- **Dev URL (live, hot-reload):** `{dev_url}`\n"
                    f"- **Phone:** `{phone}`\n"
                    f"- **Email:** `{email}`\n\n"
                    "Source intake lives at `.intake.json`. Treat it as the canonical brief.")
    sections.append("---")
    sections.append(f"## Site Map ({site_map.get('totalCount', 0)} pages)\n\n"
                    f"{type_block}\n\n"
                    "Full machine-readable map: `docs/site-map.json` — every page's "
                    "`slug`, `route`, `file`, `type`, `h1`, `h2_list`, `section_count`, "
                    "`title_metadata`.")
    sections.append("---")
    sections.append("## Content Registry\n\n"
                    "Every value in `.intake.json` is indexed in `docs/content-registry.json` "
                    "with every file path + line number where it appears. **Never hand-edit "
                    "those files one-by-one** — use the bulk-swap tools (below). They are "
                    "idempotent and guaranteed not to leave the site half-changed.")
    sections.append("---")
    sections.append(f"## Design Tokens\n\n"
                    f"- **Colors:**\n{color_lines}\n"
                    f"- **Fonts:**\n{font_lines}\n\n"
                    "Defined in `tailwind.config.ts` and `src/app/globals.css`. Re-read "
                    "`docs/design-tokens.json` after any palette/font change.")
    sections.append("---")
    sections.append(
        "## How to make a change\n\n"
        "### 1. Change the phone / email / business name (everywhere)\n"
        "```\n"
        'python3 tools/site-tools/swap-phone.py "(425) 555-1234"\n'
        "python3 tools/site-tools/swap-email.py info@example.com\n"
        'python3 tools/site-tools/swap-business-name.py "New Name LLC"\n'
        "```\n"
        "These rewrite every variant (formatted, digits-only, `tel:` / `mailto:` "
        "hrefs) across `src/`. Always re-run `build-agent-docs.py` after to refresh "
        "the registry.\n\n"
        "### 2. Find any string in the site\n"
        "```\n"
        'python3 tools/site-tools/find.py "exact phrase to locate"\n'
        "```\n"
        "Returns JSON of `[{path, line, snippet}, ...]`.\n\n"
        "### 3. Inspect a single page\n"
        "```\n"
        "python3 tools/site-tools/page-summary.py services\n"
        "python3 tools/site-tools/page-summary.py home   # (use 'home' for /)\n"
        "```\n"
        "Returns: file, h1, h2 list, section count, title metadata, line count.\n\n"
        "### 4. Edit copy on a specific page\n"
        "- Find the file: `docs/site-map.json` → `pages[].file`.\n"
        "- Make a focused `Edit` (small `old_string` / `new_string`).\n"
        "- **Don't reformat the file** — Stitch-converted pages preserve class "
        "signatures other tools key off of (logo wordmark, services dropdown, etc).\n\n"
        "### 5. Add a new article to the blog\n"
        "- Append a record to `src/app/blog/articles.ts`.\n"
        "- The dynamic route `src/app/blog/[slug]/page.tsx` reads from there.\n\n"
        "### 6. Add a new service or location page\n"
        "- Clone an existing service page (`src/app/<existing-service>/page.tsx`).\n"
        "- Update H1/H2/intro to match the new keyword from "
        "`ai/research/keywords.md`.\n"
        "- Re-run `build-agent-docs.py` so the new page appears in the site map.\n"
        "- Re-run `stitch-finalize.py` so the new page appears in the dropdown.\n\n"
        "### 7. Update the logo or palette\n"
        "- Drop a new logo at `public/images/intake/<filename>.<ext>`.\n"
        "- Update the `<img src=...>` in any single page.tsx — navbar logo is "
        "identical across pages.\n"
        "- To recolor: edit `src/app/globals.css` `--color-*` variables, OR "
        "`tailwind.config.ts` theme.extend.colors."
    )
    sections.append("---")
    sections.append(
        "## Requesting a deploy / PR review\n\n"
        "**You do NOT push to production.** When the user is satisfied with the dev "
        "URL and wants the changes live, run:\n\n"
        "```\n"
        'python3 tools/site-tools/request-deploy.py --note "what changed in plain English"\n'
        "```\n\n"
        "This script:\n"
        "1. Commits any uncommitted edits on the current dev branch with a "
        "`voice-edit:` prefix.\n"
        "2. Detects whether this is a **first-deploy** (site has never been live) "
        "or a **PR review** (subsequent edits). Mike does the first deploy "
        "manually; subsequent edits go through a PR review flow.\n"
        "3. Drops a structured ticket at "
        "`/mnt/clients/<client>/tickets/deploy-requests/<ts>-<project>.json` and "
        "appends to the global queue at "
        "`/mnt/system/base/queue/deploy-requests.jsonl`.\n"
        "4. Sends a mesh message to `mike-host@mesh` and `admin@mesh` with a "
        "summary so the request shows up in the next-session inbox.\n"
        "5. Stamps `.build-status.json` with the deployRequest entry.\n\n"
        "After running it, **stop editing**. Tell the user the request is queued "
        "and Mike will review it. Don't push, don't merge, don't email."
    )
    sections.append("---")
    sections.append(
        "## Verifying changes\n\n"
        "The webdev container hot-reloads. You usually don't need to rebuild.\n\n"
        "```\n"
        f"cd /home/node/Websites/{proj_name}\n"
        "pnpm tsc --noEmit          # type-check only (fast)\n"
        "pnpm build                 # full prod build (slower, catches more)\n\n"
        f"curl -sk {dev_url}/ -o /tmp/home.html   # confirm live\n"
        "```\n\n"
        "Hot reload usually picks copy edits up in ~2-5 seconds. Tell the user to "
        "refresh."
    )
    sections.append("---")
    sections.append(
        "## What NOT to do\n\n"
        "- **Don't edit `layout.tsx` metadata directly** when changing the business "
        "name. Run `swap-business-name.py` instead — it rewrites layout metadata, "
        "footer copy, and content references in one pass.\n"
        "- **Don't run `pnpm install` from openclaw** — its pnpm store differs from "
        "webdev's. Builds + hot reload happen in webdev. Edit files from openclaw, "
        "let webdev rebuild.\n"
        "- **Don't delete `.archive-failed-runs/`** — preserves prior build outputs "
        "(project policy: never delete).\n"
        "- **Don't change `next.config.ts`** without checking webdev still hot-reloads.\n"
        "- **Don't reformat or auto-rewrite Stitch-converted pages.** The class "
        "signatures matter for downstream tools."
    )
    sections.append("---")
    sections.append(
        "## Top-level files\n\n"
        "- `.intake.json` — canonical project brief (form-submitted)\n"
        "- `ai/research/` — DataForSEO keywords, topical map, page recommendations\n"
        "- `.stitch-pages/` — original Stitch HTMLs (design source of truth)\n"
        "- `.brand/colors.json` — sampled logo palette\n"
        "- `src/app/` — every page (`page.tsx`) + `layout.tsx` + `globals.css`\n"
        "- `src/app/blog/articles.ts` — blog article list\n"
        "- `tailwind.config.ts` — Tailwind theme (Stitch palette baked in)\n"
        "- `tools/site-tools/` — bulk-swap + grep helpers\n"
        "- `docs/site-map.json`, `content-registry.json`, `design-tokens.json` — "
        "auto-generated machine reference"
    )
    sections.append("---")
    sections.append(
        "## Refresh this guide\n\n"
        "Re-run any time pages, intake, or tokens change:\n"
        "```\n"
        "python3 /mnt/system/base/skills/website-builder/tools/build-agent-docs.py \\\n"
        "    --project . --intake .intake.json\n"
        "```"
    )

    body = "\n\n".join(sections) + "\n"
    target = project / "AGENTS.md"
    target.write_text(body)

    # CLAUDE.md alias — same content + a one-line note. Some agents look for
    # CLAUDE.md by convention; both names should resolve to the same guide.
    claude_md = project / "CLAUDE.md"
    claude_md.write_text(
        "<!-- This file is an alias for AGENTS.md (same content). Both names point\n"
        "     at the same edit guide so agents can find it under either convention. -->\n\n"
        + body
    )
    return target


# ─── Project-local site-tools ────────────────────────────────────────────────
SITE_TOOL_FIND = '''#!/usr/bin/env python3
"""find.py — Grep across src/ for a string. Returns [(path, line, snippet)].
Usage: python3 tools/site-tools/find.py "<text>"
"""
import sys, json
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("usage: find.py <text>")
needle = sys.argv[1]
project = Path(__file__).resolve().parents[2]
src = project / "src"
hits = []
for f in src.rglob("*.tsx"):
    try:
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if needle in line:
                hits.append({"path": str(f.relative_to(project)), "line": i,
                             "snippet": line.strip()[:160]})
    except Exception:
        pass
print(json.dumps(hits, indent=2))
'''

SITE_TOOL_SWAP_PHONE = '''#!/usr/bin/env python3
"""swap-phone.py — Bulk-replace phone (every variant) across src/.
Usage: python3 tools/site-tools/swap-phone.py "(425) 555-1234"
Idempotent: subsequent runs with the same target are no-ops.
"""
import json, re, sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("usage: swap-phone.py <new-phone>")
new_phone = sys.argv[1]
new_digits = re.sub(r"\\D", "", new_phone)
if len(new_digits) < 10:
    sys.exit(f"new phone has fewer than 10 digits: {new_digits!r}")

project = Path(__file__).resolve().parents[2]
intake_path = project / ".intake.json"
intake = json.loads(intake_path.read_text()) if intake_path.exists() else {}
old_phone = (intake.get("phone") or "").strip()
old_digits = re.sub(r"\\D", "", old_phone)
if not old_phone or len(old_digits) < 10:
    sys.exit(f"can't find old phone in .intake.json")

def variants(digits, formatted):
    d = digits[-10:]
    return list({
        formatted, digits, f"+1{d}",
        f"({d[:3]}) {d[3:6]}-{d[6:]}",
        f"{d[:3]}-{d[3:6]}-{d[6:]}",
        f"{d[:3]}.{d[3:6]}.{d[6:]}",
    })

old_variants = variants(old_digits, old_phone)
new_variants_map = {
    old_phone: new_phone,
    old_digits: new_digits,
    f"+1{old_digits[-10:]}": f"+1{new_digits[-10:]}",
    f"({old_digits[-10:][:3]}) {old_digits[-10:][3:6]}-{old_digits[-10:][6:]}": f"({new_digits[-10:][:3]}) {new_digits[-10:][3:6]}-{new_digits[-10:][6:]}",
    f"{old_digits[-10:][:3]}-{old_digits[-10:][3:6]}-{old_digits[-10:][6:]}": f"{new_digits[-10:][:3]}-{new_digits[-10:][3:6]}-{new_digits[-10:][6:]}",
    f"{old_digits[-10:][:3]}.{old_digits[-10:][3:6]}.{old_digits[-10:][6:]}": f"{new_digits[-10:][:3]}.{new_digits[-10:][3:6]}.{new_digits[-10:][6:]}",
}

count = {"files": 0, "replacements": 0}
for f in (project / "src").rglob("*.tsx"):
    text = f.read_text()
    new = text
    file_replacements = 0
    for old_v, new_v in new_variants_map.items():
        if not old_v or old_v == new_v: continue
        n = new.count(old_v)
        if n > 0:
            new = new.replace(old_v, new_v)
            file_replacements += n
    if new != text:
        f.write_text(new)
        count["files"] += 1
        count["replacements"] += file_replacements

intake["phone"] = new_phone
intake_path.write_text(json.dumps(intake, indent=2))
print(json.dumps(count, indent=2))
'''

SITE_TOOL_SWAP_EMAIL = '''#!/usr/bin/env python3
"""swap-email.py — Bulk-replace email across src/. Updates .intake.json.
Usage: python3 tools/site-tools/swap-email.py info@example.com
"""
import json, sys
from pathlib import Path

if len(sys.argv) < 2: sys.exit("usage: swap-email.py <new-email>")
new_email = sys.argv[1].strip()
if "@" not in new_email: sys.exit(f"not a valid email: {new_email!r}")

project = Path(__file__).resolve().parents[2]
intake_path = project / ".intake.json"
intake = json.loads(intake_path.read_text()) if intake_path.exists() else {}
old_email = (intake.get("email") or "").strip()
if not old_email: sys.exit("no old email in .intake.json")

count = {"files": 0, "replacements": 0}
for f in (project / "src").rglob("*.tsx"):
    text = f.read_text()
    n = text.count(old_email)
    if n > 0:
        f.write_text(text.replace(old_email, new_email))
        count["files"] += 1; count["replacements"] += n
intake["email"] = new_email
intake_path.write_text(json.dumps(intake, indent=2))
print(json.dumps(count, indent=2))
'''

SITE_TOOL_SWAP_BUSINESS_NAME = '''#!/usr/bin/env python3
"""swap-business-name.py — Bulk-replace business name across src/ and intake.
Usage: python3 tools/site-tools/swap-business-name.py "New Name LLC"
"""
import json, sys
from pathlib import Path

if len(sys.argv) < 2: sys.exit("usage: swap-business-name.py <new-name>")
new_name = sys.argv[1].strip()
project = Path(__file__).resolve().parents[2]
intake_path = project / ".intake.json"
intake = json.loads(intake_path.read_text()) if intake_path.exists() else {}
old_name = (intake.get("businessName") or "").strip()
if not old_name: sys.exit("no old businessName in .intake.json")

count = {"files": 0, "replacements": 0}
for f in (project / "src").rglob("*.tsx"):
    text = f.read_text()
    n = text.count(old_name)
    if n > 0:
        f.write_text(text.replace(old_name, new_name))
        count["files"] += 1; count["replacements"] += n
intake["businessName"] = new_name
intake_path.write_text(json.dumps(intake, indent=2))
print(json.dumps(count, indent=2))
'''

SITE_TOOL_REQUEST_DEPLOY = '''#!/usr/bin/env python3
"""request-deploy.py — Stage edits for Mike's review and queue a deploy/PR ticket.

The agent does NOT push to production. The flow:

  FIRST DEPLOY (site has never been live):
    - Confirm `firstDeployedAt` is unset in .build-status.json
    - Commit any uncommitted changes on the current dev branch
    - Drop ticket: type=first-deploy
    - Mesh-notify Mike + admin: "first-time deploy needed for <project>"
    - Mike does the manual first push to production himself

  SUBSEQUENT EDIT (site is live, agent is making refinements):
    - Commit changes on the dev branch (current branch — typically `web-dev`)
    - Drop ticket: type=pr-request, with commit SHA + summary + files changed
    - Mesh-notify Mike + admin: "PR ready for review"
    - Host-side automation pushes the branch + opens a GitHub PR
    - Mike reviews + merges to `main` himself, then triggers prod deploy

Side effects (all best-effort, all logged in the JSON output):
  1. `git add -A && git commit` on the current branch with a structured message
     (skipped if there are no uncommitted changes).
  2. Per-project ticket JSON at:
        /mnt/clients/<client>/tickets/deploy-requests/<ts>-<project>.json
  3. One-line summary appended to:
        /mnt/system/base/queue/deploy-requests.jsonl
  4. Mesh message to mike-host@mesh + admin@mesh (best-effort).
  5. Stamps the project's .build-status.json with deployRequest metadata.

Usage:
  python3 tools/site-tools/request-deploy.py
  python3 tools/site-tools/request-deploy.py --note "removed old testimonial section"
  python3 tools/site-tools/request-deploy.py --type first-deploy
  python3 tools/site-tools/request-deploy.py --type pr-request
"""
import argparse, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--note", default="", help="Free-text note describing what changed (visible to Mike)")
ap.add_argument("--type", default="auto", choices=["auto", "first-deploy", "pr-request"],
                help="auto = detect from .build-status.json (default)")
args = ap.parse_args()

project = Path(__file__).resolve().parents[2]
project_name = project.name
ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

intake_path = project / ".intake.json"
status_path = project / ".build-status.json"
intake = json.loads(intake_path.read_text()) if intake_path.exists() else {}
status = json.loads(status_path.read_text()) if status_path.exists() else {}

# Derive client from path
parts = project.parts
client = next((parts[i+1] for i, p in enumerate(parts) if p == "clients" and i+1 < len(parts)), None)

# Detect ticket type
if args.type == "auto":
    request_type = "pr-request" if status.get("firstDeployedAt") else "first-deploy"
else:
    request_type = args.type

# ── Step 1: commit any uncommitted changes (skipped if working tree clean) ──
def git(*cmd_args, check=False):
    return subprocess.run(["git"] + list(cmd_args), cwd=project, capture_output=True, text=True, check=check)

git_branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "(detached)"
git_status_short = git("status", "--porcelain").stdout.strip()
files_changed = [line[3:] for line in git_status_short.splitlines() if line.strip()]
commit_sha = None
commit_made = False

if files_changed:
    # Stage and commit
    git("add", "-A")
    msg_lines = [
        f"voice-edit: {args.note}" if args.note else "voice-edit: refinement pass",
        "",
        f"Project: {project_name}",
        f"Client: {client}",
        f"Files changed: {len(files_changed)}",
        "",
        f"Submitted via tools/site-tools/request-deploy.py at {ts}",
    ]
    r = git("commit", "-m", "\\n".join(msg_lines), "--no-verify")
    if r.returncode == 0:
        commit_made = True
        commit_sha = git("rev-parse", "HEAD").stdout.strip()[:12]

# Always grab the latest commit SHA (even if we didn't commit this run)
if not commit_sha:
    r = git("rev-parse", "HEAD")
    commit_sha = r.stdout.strip()[:12] if r.returncode == 0 else None

ticket = {
    "ticketId": f"deploy-{ts}-{project_name}",
    "type": request_type,
    "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "client": client,
    "project": project_name,
    "businessName": intake.get("businessName"),
    "domain": intake.get("domain"),
    "devUrl": intake.get("devUrl") or status.get("devUrl"),
    "branch": git_branch,
    "commitSha": commit_sha,
    "commitMadeThisRun": commit_made,
    "filesChanged": files_changed,
    "note": args.note.strip(),
    "buildStatus": status.get("status"),
    "firstDeployedAt": status.get("firstDeployedAt"),  # null until first deploy
    "agentRequester": os.environ.get("USER") or os.environ.get("AGENT_URI") or "agent",
    "actionRequired": (
        "Mike: review changes, manually push the first production deploy."
        if request_type == "first-deploy"
        else f"Host automation: push branch '{git_branch}' to origin and open PR vs main. Mike: review and merge."
    ),
}

# ── Step 2: per-project ticket (preserved per never-delete policy) ──
client_root = Path("/mnt/clients") / (client or "_unknown")
tickets_dir = client_root / "tickets" / "deploy-requests"
tickets_dir.mkdir(parents=True, exist_ok=True)
ticket_file = tickets_dir / f"{ts}-{project_name}.json"
ticket_file.write_text(json.dumps(ticket, indent=2))

# ── Step 3: global queue (host-watched) ──
queue_dir = Path("/mnt/system/base/queue")
try:
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_file = queue_dir / "deploy-requests.jsonl"
    with open(queue_file, "a") as f:
        f.write(json.dumps(ticket) + "\\n")
    queue_written = True
    queue_path_str = str(queue_file)
except Exception as e:
    queue_written = False
    queue_path_str = f"(queue write failed: {e})"

# ── Step 4: mesh notify (mike-host + admin) ──
mesh_results = []
if shutil.which("mesh-send"):
    if request_type == "first-deploy":
        subj = f"FIRST-DEPLOY needed: {ticket['businessName'] or project_name}"
    else:
        subj = f"PR REVIEW: {ticket['businessName'] or project_name}"
    body = (
        f"Type: {request_type}\\n"
        f"Project: {project_name} (client: {client})\\n"
        f"Branch: {git_branch}, commit: {commit_sha}\\n"
        f"Dev URL: {ticket['devUrl']}\\n"
        f"Domain: {ticket['domain']}\\n"
        f"Files changed this commit: {len(files_changed)}\\n"
        f"Note: {ticket['note'] or '(none)'}\\n"
        f"Action: {ticket['actionRequired']}\\n"
        f"Ticket: {ticket_file}"
    )
    for recipient in ["mike-host@mesh", "admin@mesh"]:
        try:
            r = subprocess.run(
                ["mesh-send", recipient, subj, "--body", body],
                capture_output=True, text=True, timeout=15,
            )
            mesh_results.append({
                "recipient": recipient,
                "ok": r.returncode == 0,
                "err": (r.stderr or r.stdout or "").strip()[:200] if r.returncode != 0 else None,
            })
        except Exception as e:
            mesh_results.append({"recipient": recipient, "ok": False, "err": str(e)[:200]})
else:
    mesh_results.append({"recipient": "(none)", "ok": False, "err": "mesh-send not on PATH"})

# ── Step 5: stamp .build-status.json with deployRequest ──
if status_path.exists():
    status.setdefault("deployRequests", []).append({
        "ticketId": ticket["ticketId"],
        "type": request_type,
        "createdAt": ticket["createdAt"],
        "commitSha": commit_sha,
        "branch": git_branch,
        "note": args.note.strip(),
    })
    status_path.write_text(json.dumps(status, indent=2))

# ── Final report ──
print(json.dumps({
    "ticketId": ticket["ticketId"],
    "type": request_type,
    "branch": git_branch,
    "commitSha": commit_sha,
    "commitMadeThisRun": commit_made,
    "filesChanged": len(files_changed),
    "ticketFile": str(ticket_file),
    "queueFile": queue_path_str,
    "queueWritten": queue_written,
    "meshResults": mesh_results,
    "next": ticket["actionRequired"],
}, indent=2))
'''


SITE_TOOL_PAGE_SUMMARY = '''#!/usr/bin/env python3
"""page-summary.py — Show H1, H2 list, section count, file path for a page.
Usage: python3 tools/site-tools/page-summary.py <slug>   (use 'home' for /)
"""
import json, re, sys
from pathlib import Path

if len(sys.argv) < 2: sys.exit("usage: page-summary.py <slug>")
slug = sys.argv[1]
project = Path(__file__).resolve().parents[2]
target = (project / "src" / "app" / "page.tsx") if slug == "home" else (project / "src" / "app" / slug / "page.tsx")
if not target.exists(): sys.exit(f"not found: {target}")
text = target.read_text()
out = {
    "slug": slug,
    "file": str(target.relative_to(project)),
    "h1": (re.search(r"<h1[^>]*>([^<]+)</h1>", text) or [None, ""])[1].strip() if re.search(r"<h1[^>]*>([^<]+)</h1>", text) else "",
    "h2_list": [m.group(1).strip() for m in re.finditer(r"<h2[^>]*>([^<]+)</h2>", text)],
    "section_count": len(re.findall(r"<section\\b", text)),
    "title_metadata": (re.search(r'metadata\\s*=\\s*\\{[^}]*?title:\\s*"([^"]+)"', text, re.DOTALL) or [None, ""])[1] if re.search(r'metadata\\s*=\\s*\\{[^}]*?title:\\s*"([^"]+)"', text, re.DOTALL) else "",
    "lines": text.count("\\n"),
}
print(json.dumps(out, indent=2))
'''


def write_site_tools(project: Path) -> list[Path]:
    tools_dir = project / "tools" / "site-tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in [
        ("find.py", SITE_TOOL_FIND),
        ("swap-phone.py", SITE_TOOL_SWAP_PHONE),
        ("swap-email.py", SITE_TOOL_SWAP_EMAIL),
        ("swap-business-name.py", SITE_TOOL_SWAP_BUSINESS_NAME),
        ("page-summary.py", SITE_TOOL_PAGE_SUMMARY),
        ("request-deploy.py", SITE_TOOL_REQUEST_DEPLOY),
    ]:
        target = tools_dir / name
        target.write_text(content)
        target.chmod(0o755)
        written.append(target)
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--intake", required=True)
    args = ap.parse_args()

    project = Path(args.project).resolve()
    intake = json.loads(Path(args.intake).read_text())

    site_map = write_site_map(project, intake)
    registry = write_content_registry(project, intake)
    tokens = write_design_tokens(project)
    agents_md = write_agents_md(project, intake, site_map, registry, tokens)
    tools = write_site_tools(project)

    print(json.dumps({
        "project": str(project),
        "site_map_pages": site_map.get("totalCount"),
        "registry_intake_keys": list(registry.keys()),
        "design_tokens_colors": len(tokens.get("colors", {})),
        "agents_md": str(agents_md.relative_to(project)),
        "site_tools": [str(t.relative_to(project)) for t in tools],
    }, indent=2))


if __name__ == "__main__":
    main()
