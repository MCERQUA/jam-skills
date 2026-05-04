#!/usr/bin/env python3
"""
stitch-to-next.py — Convert a Stitch HTML page into a Next.js App Router page.

Generic. No client/project/color/font hardcoding. Reads any Stitch HTML and emits:
  - <out>/src/app/<slug>/page.tsx     (or src/app/page.tsx for slug='home')
  - <out>/tailwind.config.ts          (extracted from <script id="tailwind-config">)
  - <out>/src/app/globals.css         (merged: stitch <style> + font imports)
  - <out>/.stitch-assets.json         (manifest of remote URLs to download)

Usage:
  stitch-to-next.py --input <stitch.html> --slug <home|about|services|...> --out <project-root>
  stitch-to-next.py --input <dir-of-stitch-htmls> --out <project-root>   (batch: filename = slug)

Smoke-test:
  stitch-to-next.py --input .stitch-pages/home.html --slug home --out /tmp/stitch-test
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup, NavigableString, Tag, Comment
except ImportError:
    sys.stderr.write("ERROR: pip install beautifulsoup4\n")
    sys.exit(2)


# ---------------------------------------------------------------------------
# JSX attribute name remap (HTML -> JSX). Anything not in this map passes through.
# ---------------------------------------------------------------------------
JSX_ATTR_MAP = {
    "class": "className",
    "for": "htmlFor",
    "tabindex": "tabIndex",
    "readonly": "readOnly",
    "maxlength": "maxLength",
    "minlength": "minLength",
    "autocomplete": "autoComplete",
    "autofocus": "autoFocus",
    "spellcheck": "spellCheck",
    "contenteditable": "contentEditable",
    "crossorigin": "crossOrigin",
    "enctype": "encType",
    "novalidate": "noValidate",
    "formnovalidate": "formNoValidate",
    "frameborder": "frameBorder",
    "hreflang": "hrefLang",
    "marginwidth": "marginWidth",
    "marginheight": "marginHeight",
    "rowspan": "rowSpan",
    "colspan": "colSpan",
    "usemap": "useMap",
    "accept-charset": "acceptCharset",
    "http-equiv": "httpEquiv",
    "srcset": "srcSet",
    "srclang": "srcLang",
    "fill-rule": "fillRule",
    "clip-rule": "clipRule",
    "stroke-width": "strokeWidth",
    "stroke-linecap": "strokeLinecap",
    "stroke-linejoin": "strokeLinejoin",
    "stroke-miterlimit": "strokeMiterlimit",
    "stroke-dasharray": "strokeDasharray",
    "stop-color": "stopColor",
    "stop-opacity": "stopOpacity",
    "viewbox": "viewBox",
    "preserveaspectratio": "preserveAspectRatio",
    "xmlns:xlink": "xmlnsXlink",
    "xlink:href": "xlinkHref",
}

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# Elements/attributes to STRIP entirely (Stitch-specific scaffolding we don't want in JSX).
STRIP_TAGS = {"script"}  # we extract tailwind-config separately and drop the rest

# data-* attributes are valid JSX, keep them.


def style_attr_to_jsx(value: str) -> str:
    """Convert `color: red; padding: 5px` → JSX style object literal as a STRING."""
    parts = []
    for chunk in value.split(";"):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        k, v = chunk.split(":", 1)
        k = k.strip()
        v = v.strip()
        # Convert kebab-case property → camelCase
        camel = re.sub(r"-([a-z])", lambda m: m.group(1).upper(), k)
        # Numeric pixel-less values: keep as quoted string (safest)
        # Wrap value in JSON-safe double-quoted string with embedded escaping
        v_escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f'"{camel}": "{v_escaped}"')
    return "{{ " + ", ".join(parts) + " }}"


def escape_jsx_text(text: str) -> str:
    """Escape `{` and `}` so React doesn't try to interpret them. Keep entities readable."""
    return text.replace("{", "&#123;").replace("}", "&#125;")


def widen_nav_breakpoint(class_str: str) -> str:
    """Stitch templates use Tailwind `md:` for the nav/hamburger split (768px).
    With our injected Services + Locations dropdowns + Blog link the nav
    overflows in the 768-1024px range. Move the nav split to `lg:` (1024px)
    so the hamburger kicks in earlier on tablets. Only rewrites the two
    nav-specific patterns — leaves layout-grid `md:flex-row` etc. alone."""
    if "md:flex" in class_str and "hidden" in class_str:
        class_str = class_str.replace("md:flex", "lg:flex")
    if "md:hidden" in class_str:
        class_str = class_str.replace("md:hidden", "lg:hidden")
    return class_str


def serialize_attrs(tag: Tag, asset_manifest: list) -> str:
    """Serialize a tag's attributes as JSX attribute string."""
    out = []
    for name, value in tag.attrs.items():
        # multi-value attrs (class) come back as a list
        if isinstance(value, list):
            value = " ".join(value)

        lower = name.lower()
        # JSX rename
        jsx_name = JSX_ATTR_MAP.get(lower, name)

        # Widen the nav breakpoint at conversion time so future builds don't
        # need post-fixup. Only touches `class` / `className` values.
        if lower in ("class", "classname") and isinstance(value, str):
            value = widen_nav_breakpoint(value)

        # style= needs to be a JS object
        if lower == "style":
            out.append(f"style={style_attr_to_jsx(value)}")
            continue

        # boolean attrs (no value or empty string and HTML-boolean-style)
        if value is None or value == "":
            out.append(jsx_name)
            continue

        # collect remote image/asset URLs
        if lower in ("src", "href") and isinstance(value, str) and value.startswith(("http://", "https://")):
            # Only collect <img>/<source>/<video> srcs as assets, not <link>/<a>
            if tag.name in ("img", "source", "video", "audio"):
                asset_manifest.append({"tag": tag.name, "url": value})

        # Escape the value for JSX (string in double quotes)
        v_escaped = (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', "&quot;")
        )
        out.append(f'{jsx_name}="{v_escaped}"')

    if not out:
        return ""
    return " " + " ".join(out)


def is_material_icon_span(tag: Tag) -> bool:
    """True for <span class="material-symbols-outlined ...">name</span>."""
    if tag.name != "span":
        return False
    classes = tag.get("class") or []
    return any(c in classes for c in ("material-symbols-outlined", "material-icons", "material-symbols-rounded", "material-symbols-sharp"))


def serialize_node(node, asset_manifest: list, depth: int = 0) -> str:
    """Recursively convert a BeautifulSoup node to a JSX string."""
    # HTML comments — re-emit as JSX comments so they don't show as raw text.
    if isinstance(node, Comment):
        body = str(node).replace("*/", "* /")
        return f"{{/* {body} */}}"
    if isinstance(node, NavigableString):
        text = str(node)
        # Preserve whitespace-only nodes (they matter for JSX text spacing)
        return escape_jsx_text(text)

    if not isinstance(node, Tag):
        return ""

    name = node.name
    if name in STRIP_TAGS:
        return ""
    if name == "style":
        # extracted separately, skip
        return ""

    attrs = serialize_attrs(node, asset_manifest)

    if name in VOID_ELEMENTS:
        return f"<{name}{attrs} />"

    # Material Symbols icon: ligature substitution requires the span's text to be
    # exactly the icon name with no surrounding whitespace/newlines. JSX whitespace
    # rules will inject newlines via our pretty-printing, so collapse to bare text.
    if is_material_icon_span(node):
        icon_name = node.get_text(strip=True)
        return f"<{name}{attrs}>{escape_jsx_text(icon_name)}</{name}>"

    # Render children
    inner = "".join(
        serialize_node(child, asset_manifest, depth + 1) for child in node.children
    )

    return f"<{name}{attrs}>{inner}</{name}>"


def extract_tailwind_config(soup: BeautifulSoup) -> str | None:
    """Pull the JS object literal from <script id='tailwind-config'>."""
    script = soup.find("script", id="tailwind-config")
    if not script or not script.string:
        return None
    raw = script.string
    # The script body is `tailwind.config = { ... };`
    m = re.search(r"tailwind\.config\s*=\s*(\{[\s\S]*?\});?\s*$", raw.strip())
    if not m:
        # Try without trailing semicolon
        m = re.search(r"tailwind\.config\s*=\s*(\{[\s\S]*\})", raw.strip())
    if not m:
        return None
    return m.group(1)


def extract_styles(soup: BeautifulSoup) -> str:
    """Concatenate every <style> block into one CSS string."""
    blocks = []
    for s in soup.find_all("style"):
        if s.string:
            blocks.append(s.string)
    return "\n\n".join(blocks)


def extract_font_links(soup: BeautifulSoup) -> list[str]:
    """Return the href of every Google Fonts (or other font CDN) link tag."""
    fonts = []
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href", "")
        if "fonts.googleapis.com" in href or "fonts.gstatic.com" in href:
            fonts.append(href)
    return fonts


def write_tailwind_config(out_dir: Path, tw_config_obj: str | None):
    """Write tailwind.config.ts using the extracted theme.extend block (if found)."""
    path = out_dir / "tailwind.config.ts"
    if tw_config_obj is None:
        # Nothing to do — leave whatever scaffold wrote.
        return False

    content = f"""import type {{ Config }} from "tailwindcss";

// Generated from Stitch HTML <script id="tailwind-config">.
// DO NOT EDIT BY HAND — re-run stitch-to-next.py to regenerate.
// Typed as `any` because Stitch fontFamily entries are tuples that
// Tailwind's strict type wants as mutable string[].
const stitch: any = {tw_config_obj};

const config: Config = {{
  content: [
    "./src/app/**/*.{{js,ts,jsx,tsx,mdx}}",
    "./src/components/**/*.{{js,ts,jsx,tsx,mdx}}",
  ],
  darkMode: stitch.darkMode ?? "class",
  theme: {{
    extend: {{
      ...(stitch.theme?.extend ?? {{}}),
    }},
  }},
  plugins: [],
}};

export default config;
"""
    path.write_text(content)
    return True


def write_globals_css(out_dir: Path, stitch_styles: str):
    """Write src/app/globals.css. Font <link> tags go in layout.tsx, not @import here
    (PostCSS may strip/process external @imports inconsistently)."""
    css_path = out_dir / "src" / "app" / "globals.css"
    css_path.parent.mkdir(parents=True, exist_ok=True)

    parts = ['@tailwind base;', '@tailwind components;', '@tailwind utilities;', ""]

    if stitch_styles.strip():
        parts.append("/* ── Stitch <style> blocks (verbatim) ── */")
        parts.append(stitch_styles.strip())
        parts.append("")

    # Stitch's <style> usually only sets font-variation-settings on the icon class;
    # the font-family + ligature substitution rule is needed for the icons to render.
    parts.append("/* ── stitch-to-next: Material Symbols icon rendering ── */")
    parts.append(
        ".material-symbols-outlined, .material-symbols-rounded, .material-symbols-sharp, .material-icons {\n"
        "  font-family: 'Material Symbols Outlined', 'Material Icons';\n"
        "  font-weight: normal;\n"
        "  font-style: normal;\n"
        "  line-height: 1;\n"
        "  letter-spacing: normal;\n"
        "  text-transform: none;\n"
        "  display: inline-block;\n"
        "  white-space: nowrap;\n"
        "  word-wrap: normal;\n"
        "  direction: ltr;\n"
        "  font-feature-settings: 'liga';\n"
        "  -webkit-font-feature-settings: 'liga';\n"
        "  -webkit-font-smoothing: antialiased;\n"
        "}"
    )
    parts.append("")

    css_path.write_text("\n".join(parts))


def write_layout_tsx(out_dir: Path, font_links: list[str], title: str = "Site", description: str = "Site"):
    """Write/overwrite src/app/layout.tsx with Stitch's font <link> tags in <head>.
    Pulls title/description from intake.json when available — falls back to 'Site'
    only when the converter is run without intake context (e.g. ad-hoc smoke test)."""
    target = out_dir / "src" / "app" / "layout.tsx"
    target.parent.mkdir(parents=True, exist_ok=True)

    # JSON-safe escape — title/description go inside double-quoted JS strings.
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()

    link_tags = "\n".join(
        f'        <link href="{h}" rel="stylesheet" />' for h in font_links
    )
    head_block = f"""      <head>
{link_tags}
      </head>""" if font_links else ""

    content = f"""// Generated by stitch-to-next.py — font <link>s come from Stitch <head>.
import "./globals.css";

export const metadata = {{
  title: "{esc(title)}",
  description: "{esc(description)}",
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en">
{head_block}
      <body>{{children}}</body>
    </html>
  );
}}
"""
    target.write_text(content)


def write_page_tsx(out_dir: Path, slug: str, body_jsx: str, html_attrs: dict):
    """Write src/app/<slug>/page.tsx (or src/app/page.tsx for home)."""
    if slug == "home":
        target = out_dir / "src" / "app" / "page.tsx"
    else:
        target = out_dir / "src" / "app" / slug / "page.tsx"

    target.parent.mkdir(parents=True, exist_ok=True)

    # Body classes from the original <body>: keep them as a wrapper div.
    body_class = html_attrs.get("body_class", "")
    body_attr = f' className="{body_class}"' if body_class else ""

    content = f"""// Generated from Stitch HTML by stitch-to-next.py.
// DO NOT EDIT BY HAND — re-run the converter to regenerate.
// Component is a Server Component; add "use client" + handlers later if needed.

export default function Page() {{
  return (
    <div{body_attr}>
{body_jsx}
    </div>
  );
}}
"""
    target.write_text(content)
    return target


def convert_one(input_html: Path, slug: str, out_dir: Path, write_shared: bool,
                meta_title: str = "Site", meta_description: str = "Site") -> dict:
    """Convert a single Stitch HTML file. Returns a small report dict.
    meta_title/meta_description go into layout.tsx — pass them from intake on first call."""
    soup = BeautifulSoup(input_html.read_text(), "html.parser")

    # Extract the design system bits (only write on first call — they're shared).
    tw_obj = extract_tailwind_config(soup)
    stitch_css = extract_styles(soup)
    fonts = extract_font_links(soup)

    if write_shared:
        write_tailwind_config(out_dir, tw_obj)
        write_globals_css(out_dir, stitch_css)
        write_layout_tsx(out_dir, fonts, meta_title, meta_description)

    # Convert <body> → JSX
    body = soup.find("body")
    if body is None:
        raise RuntimeError(f"{input_html}: no <body> found")

    asset_manifest = []
    inner_jsx = "".join(
        serialize_node(child, asset_manifest) for child in body.children
    )
    # Indent by 6 spaces so it sits inside `return (...)`.
    inner_jsx_indented = "\n".join(
        ("      " + line) if line.strip() else line
        for line in inner_jsx.splitlines()
    )

    body_class = " ".join(body.get("class", [])) if body.get("class") else ""

    page_path = write_page_tsx(out_dir, slug, inner_jsx_indented, {"body_class": body_class})

    return {
        "input": str(input_html),
        "slug": slug,
        "page": str(page_path),
        "tailwind_config_extracted": tw_obj is not None,
        "stitch_styles_bytes": len(stitch_css),
        "font_links": fonts,
        "asset_count": len(asset_manifest),
        "assets": asset_manifest,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Stitch HTML file OR directory")
    ap.add_argument("--slug", help="Page slug (required when --input is a single file)")
    ap.add_argument("--out", required=True, help="Project root (must already be scaffolded)")
    ap.add_argument("--intake", help="Path to .intake.json — used to populate layout.tsx metadata")
    args = ap.parse_args()

    src = Path(args.input).resolve()
    out = Path(args.out).resolve()
    if not src.exists():
        sys.exit(f"--input not found: {src}")
    out.mkdir(parents=True, exist_ok=True)

    # Pull title/description from intake when supplied. Tries .intake.json next
    # to --out as a fallback so the converter does the right thing even when the
    # caller forgot to pass --intake.
    meta_title = "Site"
    meta_description = "Site"
    intake_path = Path(args.intake) if args.intake else (out / ".intake.json")
    if intake_path.exists():
        try:
            intake = json.loads(intake_path.read_text())
            biz = (intake.get("businessName") or "").strip()
            tagline = (intake.get("tagline") or "").strip()
            desc = (intake.get("description") or "").strip()
            if biz:
                meta_title = f"{biz} — {tagline}" if tagline else biz
            if desc:
                meta_description = desc[:160]
            elif tagline:
                meta_description = tagline
            elif biz:
                meta_description = biz
        except Exception as e:
            sys.stderr.write(f"intake parse warn: {e}\n")

    reports = []
    asset_manifest_all = []

    if src.is_file():
        if not args.slug:
            sys.exit("--slug is required when --input is a single file")
        reports.append(convert_one(src, args.slug, out, write_shared=True,
                                   meta_title=meta_title, meta_description=meta_description))
    else:
        files = sorted(src.glob("*.html"))
        if not files:
            sys.exit(f"--input dir contains no .html files: {src}")
        for i, f in enumerate(files):
            slug = f.stem  # filename → slug (home.html → home)
            reports.append(convert_one(f, slug, out, write_shared=(i == 0),
                                       meta_title=meta_title, meta_description=meta_description))

    for r in reports:
        asset_manifest_all.extend(r.get("assets", []))

    manifest = {
        "generated_by": "stitch-to-next.py",
        "pages": [
            {k: v for k, v in r.items() if k != "assets"} for r in reports
        ],
        "assets": asset_manifest_all,
    }
    (out / ".stitch-assets.json").write_text(json.dumps(manifest, indent=2))

    # Summary to stdout
    print(json.dumps({
        "ok": True,
        "out_dir": str(out),
        "pages_converted": len(reports),
        "shared_assets_written": ["tailwind.config.ts", "src/app/globals.css"],
        "remote_assets_pending_download": len(asset_manifest_all),
    }, indent=2))


if __name__ == "__main__":
    main()
