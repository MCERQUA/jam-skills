#!/usr/bin/env python3
# qa-audit-engine.py — Deterministic Playwright DOM audit of ONE brand-report HTML file
# Part of the QA audit runner for the JamBot mesh.
#
# Usage:
#   python3 qa-audit-engine.py <html_path> [--client <name>] [--date <YYYY-MM-DD>]
#
# Outputs (all written):
#   /mnt/agent-mesh/mesh/QUALITY/<stem>-audit-<date>/audit-report.json  — full findings
#   /mnt/agent-mesh/mesh/QUALITY/<stem>-audit-<date>/audit-report.md    — human readable
#   /mnt/agent-mesh/mesh/QUALITY/<stem>-audit-<date>/screenshots/<vp>_<theme>_<page>.png
#   /mnt/agent-mesh/mesh/QUALITY/<stem>-audit-<date>.json               — summary (watcher reads this)
#
# Exit codes: 0=SHIP, 1=NO-SHIP, 2=error
# Prints summary JSON to stdout.
#
# Env overrides:
#   QUALITY_DIR  — override default /mnt/agent-mesh/mesh/QUALITY
#   QA_TIMEOUT   — ms per page.goto (default 30000)

import argparse
import json
import math
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# ── Constants ──────────────────────────────────────────────────────────────────
QUALITY_DIR = Path(os.environ.get("QUALITY_DIR", "/mnt/agent-mesh/mesh/QUALITY"))
QA_TIMEOUT = int(os.environ.get("QA_TIMEOUT", "30000"))
AUDITOR = "quality-assurance-manager@mesh"

VIEWPORTS = [
    {"name": "mobile",  "width": 375,  "height": 812},
    {"name": "tablet",  "width": 768,  "height": 1024},
    {"name": "desktop", "width": 1440, "height": 900},
]

# Badge selectors for WCAG contrast check (per audit-cadence.md)
BADGE_SELECTORS = [".pill", ".sev-critical", ".sev-high", ".sev-medium", ".sev-low",
                   ".sev", ".status", ".mention", ".badge", ".tag"]


# ── WCAG luminance helpers ──────────────────────────────────────────────────────

def _parse_rgb(css: str) -> tuple[float, float, float] | None:
    """Parse rgb/rgba CSS string into (r, g, b) 0-255 floats. Returns None on failure."""
    m = re.search(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)", css or "")
    if not m:
        return None
    return float(m.group(1)), float(m.group(2)), float(m.group(3))


def _relative_luminance(r: float, g: float, b: float) -> float:
    """WCAG 2.1 relative luminance from 0-255 components."""
    def channel(c: float) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(rgb1: tuple, rgb2: tuple) -> float:
    """WCAG contrast ratio between two (r,g,b) pairs."""
    l1 = _relative_luminance(*rgb1)
    l2 = _relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ── DOM checks (run inside page.evaluate) ─────────────────────────────────────

# These JS snippets return serialisable data so all post-processing stays in Python.

_JS_HOVERFLOW = """() => {
    const de = document.documentElement;
    return {
        scrollWidth: de.scrollWidth,
        clientWidth: de.clientWidth,
        overflows: de.scrollWidth > de.clientWidth
    };
}"""

_JS_ELEMENT_OVERFLOW = """() => {
    const results = [];
    const all = document.querySelectorAll('*');
    for (const el of all) {
        const style = window.getComputedStyle(el);
        const ov = style.overflow + ' ' + style.overflowX;
        if (/auto|scroll/.test(ov)) continue;
        if (el.scrollWidth > el.clientWidth && el.clientWidth > 0) {
            const tag = el.tagName + (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().replace(/\\s+/g, ' ') : '');
            results.push({
                tag: tag.substring(0, 120),
                scrollWidth: el.scrollWidth,
                clientWidth: el.clientWidth
            });
            if (results.length >= 20) break;  // cap to avoid enormous reports
        }
    }
    return results;
}"""

_JS_OFFSCREEN_TEXT = """() => {
    const W = window.innerWidth;
    // Text inside a horizontally-scrollable ancestor (overflow-x:auto|scroll — e.g. a
    // scrollable tab/nav bar) is REACHABLE, not cut off, so it is not a bug. Mirror the
    // element-overflow check's scroll-container skip. Also skip text in hidden ancestors.
    function inScrollableOrHidden(el) {
        let node = el;
        while (node && node.nodeType === 1 && node !== document.body) {
            const cs = window.getComputedStyle(node);
            if (cs.display === 'none' || cs.visibility === 'hidden') return true;
            if (/auto|scroll/.test(cs.overflowX + ' ' + cs.overflow)) return true;
            node = node.parentElement;
        }
        return false;
    }
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const found = [];
    const seen = new Set();
    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (!node.textContent.trim()) continue;
        if (node.parentElement && inScrollableOrHidden(node.parentElement)) continue;
        const range = document.createRange();
        range.selectNode(node);
        const rect = range.getBoundingClientRect();
        if (rect.right > W + 1 && rect.width > 0) {
            const text = node.textContent.trim().substring(0, 60);
            if (seen.has(text)) continue;
            seen.add(text);
            found.push({text: text, right: Math.round(rect.right), innerWidth: W});
            if (found.length >= 10) break;
        }
    }
    return found;
}"""

_JS_BG_COLOR = """() => {
    return window.getComputedStyle(document.body).backgroundColor;
}"""

_JS_TOUCH_TARGETS = """() => {
    const issues = [];
    const els = document.querySelectorAll('button, .chip, .tab-btn, a.btn');
    for (const el of els) {
        const rect = el.getBoundingClientRect();
        if (rect.height > 0 && rect.height < 44) {
            const label = (el.textContent || '').trim().substring(0, 40);
            const cls = typeof el.className === 'string' ? el.className.trim().replace(/\\s+/g, ' ') : '';
            issues.push({
                tag: el.tagName + (cls ? '.' + cls : ''),
                height: Math.round(rect.height),
                label: label
            });
            if (issues.length >= 20) break;
        }
    }
    return issues;
}"""

_JS_CHARTS = """() => {
    // Only audit VISIBLE canvases. A canvas in a display:none tab is 0×0 / blank by design
    // (Chart.js collapses hidden containers) — flagging those was the bulk of the false
    // "empty chart" findings. A chart only needs to render when its tab is actually shown.
    const results = [];
    const canvases = document.querySelectorAll('canvas');
    for (let i = 0; i < canvases.length; i++) {
        const c = canvases[i];
        const cs = window.getComputedStyle(c);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        if (!c.offsetParent && cs.position !== 'fixed') continue;   // hidden ancestor (inactive tab)
        const r = c.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) continue;                  // not laid out / hidden
        let dataURL = '';
        try { dataURL = c.toDataURL(); } catch(e) { dataURL = 'error:' + e.message; }
        results.push({
            index: i,
            id: c.id || '',
            width: c.width,
            height: c.height,
            dataURLLength: dataURL.length,
            dataURL: dataURL.substring(0, 100)
        });
    }
    return results;
}"""

_JS_TAB_INVARIANT = """() => {
    const active = document.querySelectorAll('.report-page.is-active');
    const all = document.querySelectorAll('.report-page');
    const hidden = [];
    for (const p of all) {
        if (!p.classList.contains('is-active')) {
            const s = window.getComputedStyle(p).display;
            if (s !== 'none') hidden.push({id: p.id, display: s});
        }
    }
    return {activeCount: active.length, totalPages: all.length, nonHiddenInactive: hidden};
}"""

_JS_BADGE_CONTRAST = """(selectors) => {
    // Only VISIBLE elements (a badge in a display:none tab has unrendered/garbage style
    // and is not a real user-facing contrast issue), and resolve the EFFECTIVE background
    // by walking ancestors — a badge with a transparent own-bg (rgba(...,0)) inherits its
    // parent's bg; treating transparent as black (the old bug) flagged every fine badge.
    function isVisible(el) {
        const cs = window.getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
        if (!el.offsetParent && cs.position !== 'fixed') return false;  // in a display:none ancestor
        const r = el.getBoundingClientRect();
        return r.width >= 1 && r.height >= 1;
    }
    function alpha(css) {
        const m = (css || '').match(/rgba?\\(([^)]+)\\)/);
        if (!m) return 1;
        const p = m[1].split(',').map(s => parseFloat(s));
        return p.length >= 4 ? p[3] : 1;
    }
    function rgbaParts(css) {
        const m = (css || '').match(/rgba?\\(([^)]+)\\)/);
        if (!m) return null;
        const p = m[1].split(',').map(s => parseFloat(s));
        if (p.length < 3 || p.slice(0, 3).some(isNaN)) return null;
        return [p[0], p[1], p[2], p.length >= 4 ? p[3] : 1];
    }
    function effectiveBg(el) {
        // 2026-08-22 FIX — COMPOSITE semi-transparent layers, do not return the first one.
        // Old behaviour returned the first bg with alpha>0 verbatim, and the Python side
        // parses only r,g,b — so a 10% tint like rgba(59,130,246,0.1) was scored as if it
        // were SOLID rgb(59,130,246). Where the text is that same hue (the standard tinted
        // badge pattern), that yields ratio 1.00:1 and a false CRITICAL. It blocked
        // catalyst-deck.html (client nick) at NO-SHIP for 8 days with 16 such CRITICALs;
        // the real composited ratios were 4.93:1 and 8.07:1 — both PASSING AA.
        // The earlier alpha===0 fix was the same bug one step less far: transparent was
        // handled, translucent was not.
        const layers = [];                     // top-most first
        let node = el;
        while (node && node.nodeType === 1) {
            const c = rgbaParts(window.getComputedStyle(node).backgroundColor);
            if (c && c[3] > 0) {
                layers.push(c);
                if (c[3] >= 1) break;          // opaque: nothing below it can show through
            }
            node = node.parentElement;
        }
        let base = null;
        if (layers.length && layers[layers.length - 1][3] >= 1) {
            base = layers.pop();               // the opaque backstop we found
        } else {
            const b = rgbaParts(window.getComputedStyle(document.body).backgroundColor);
            base = (b && b[3] >= 1) ? b : [255, 255, 255, 1];   // page default is white
        }
        // composite bottom-up: each translucent layer over what is already beneath it
        let out = [base[0], base[1], base[2]];
        for (let i = layers.length - 1; i >= 0; i--) {
            const L = layers[i], a = L[3];
            out = [0, 1, 2].map(k => L[k] * a + out[k] * (1 - a));
        }
        return 'rgb(' + out.map(v => Math.round(v)).join(', ') + ')';
    }
    const results = [];
    const seen = new Set();
    for (const sel of selectors) {
        for (const el of document.querySelectorAll(sel)) {
            if (!isVisible(el)) continue;
            const style = window.getComputedStyle(el);
            const color = style.color;
            const text = (el.textContent || '').trim().substring(0, 40);
            if (!color || !text) continue;
            if (alpha(color) === 0) continue;        // invisible text — not a contrast bug
            const bg = effectiveBg(el);
            const cls = typeof el.className === 'string' ? el.className.trim().replace(/\\s+/g, ' ') : '';
            const key = cls + '|' + color + '|' + bg + '|' + text;
            if (seen.has(key)) continue;             // dedup identical badges within one scan
            seen.add(key);
            results.push({selector: sel, className: cls, color: color, bg: bg, text: text});
            if (results.length >= 60) return results;
        }
    }
    return results;
}"""

_JS_PAGES = """() => {
    const pages = document.querySelectorAll('.report-page');
    const names = [];
    for (const p of pages) {
        names.push(p.id || p.dataset.page || ('page-' + (names.length + 1)));
    }
    return names;
}"""

_JS_ACTIVATE_PAGE = """(pageId) => {
    // Prefer the report's OWN tab mechanism: click the matching tab BUTTON and let the
    // report's JS switch pages. This is faithful to real user behavior and never fights
    // the report's own state. The previous version manually toggled .report-page display
    // AND looked up the target by [data-page=...] unscoped — which matched the same-
    // data-page tab BUTTON (first in document order), so it deactivated every page and
    // activated none → a FALSE "0 active pages" CRITICAL on every tabbed report.
    const btn = document.querySelector('.tab-btn[data-page="' + pageId + '"]')
             || document.querySelector('[data-tab="' + pageId + '"]')
             || document.querySelector('.tab-btn[onclick*="' + pageId + '"]');
    if (btn) { btn.click(); return true; }
    // Fallback (no button): activate the .report-page element directly, SCOPED so we never
    // grab a tab button that happens to share the data-page value.
    let target = null;
    try { target = document.querySelector('.report-page#' + (window.CSS && CSS.escape ? CSS.escape(pageId) : pageId)); } catch (e) {}
    if (!target) target = document.querySelector('.report-page[data-page="' + pageId + '"]');
    if (!target) { const byId = document.getElementById(pageId); if (byId && byId.classList.contains('report-page')) target = byId; }
    if (!target) return false;
    for (const p of document.querySelectorAll('.report-page')) {
        p.classList.toggle('is-active', p === target);
        p.style.display = (p === target) ? '' : 'none';
    }
    return true;
}"""

_JS_HAS_THEME_TOGGLE = """() => {
    return !!document.getElementById('themeToggle');
}"""

_JS_BLANK_DATA_URL = """() => {
    // Generate a blank same-size canvas and return its dataURL for comparison
    const c = document.createElement('canvas');
    c.width = 1; c.height = 1;
    return c.toDataURL();
}"""


# ── Finding builder ────────────────────────────────────────────────────────────

def make_finding(severity: str, title: str, detail: str, selector: str,
                 viewport: str, theme: str, page: str, fix: str) -> dict:
    return {
        "severity": severity,
        "title": title,
        "detail": detail,
        "selector": selector,
        "viewport": viewport,
        "theme": theme,
        "page": page,
        "fix": fix,
    }


# ── Phase 0 oracles (Quality Council deterministic bandage, 2026-07-23) ────────
# docs/jambot/quality-council-system.md §"Phase 0 — The Oracle Bandage": the three
# recurring real client-facing incidents (Acme Spray Foam template leak, 18
# brand-report no-ships, voice bare-responses) were each catchable by a CHEAP
# deterministic check that was simply never wired into the ship path — not review
# depth failures. These two run once per artifact (not per viewport×theme×page
# combination; they don't vary by breakpoint) and produce CRITICAL findings, same
# severity tier as the existing overflow/contrast checks — a leaked demo string or
# a genuinely-unrendered page is exactly as ship-blocking as a layout bug.

# Generic placeholder/demo markers a real client deliverable must NEVER contain.
# Deliberately narrow and literal (grep, not fuzzy-matched) — false positives here
# would train agents to ignore this check, defeating its purpose. Named client
# examples are the OTHER tenants' own template placeholders seen in the wild
# (the "Acme Spray Foam" incident this Phase was built to catch), not real client
# names — safe to hardcode since these strings should NEVER appear in ANY real
# client deliverable regardless of which tenant it's for.
PLACEHOLDER_MARKERS = [
    "acme spray foam", "acme corp", "acme inc", "acme company",
    "example company", "example business", "example client",
    "your company name", "your business name", "company name here",
    "sample business", "sample company", "demo company", "demo client",
    "lorem ipsum", "your text here", "insert text here", "placeholder text",
    "[insert ", "[company name]", "[client name]", "[business name]",
    "123 main street", "john doe", "jane doe", "555-0100", "555-0123",
]


def check_placeholder_leaks(raw_html: str, page_name: str) -> list[dict]:
    """Phase 0 oracle #1 — template/placeholder-leak grep (the Acme class). Runs
    ONCE per artifact against the raw HTML source (cheap text search, no
    Playwright/DOM needed — a leaked placeholder string is present in the markup
    regardless of viewport/theme, so per-combination repetition would just be
    redundant CRITICAL findings for the same root string)."""
    bugs = []
    hay = raw_html.lower()
    for marker in PLACEHOLDER_MARKERS:
        if marker in hay:
            bugs.append(make_finding(
                severity="CRITICAL",
                title="Template/placeholder text leaked into client deliverable",
                detail=f"Found literal placeholder marker {marker!r} in the page source — "
                       "this is demo/template content that must never reach a real client.",
                selector="(page source)",
                viewport="all", theme="all", page=page_name,
                fix=f"Search the source for {marker!r} and replace with this client's real "
                    "content. Verify no other template placeholders remain nearby.",
            ))
    return bugs


def check_render_succeeded(page_pw, vp_name: str, theme: str, page_name: str) -> list[dict]:
    """Phase 0 oracle #2 — output-exists / render-succeeded assertion (the no-ship
    class: a page that technically loads but rendered nothing real). Runs once per
    viewport (content doesn't vary by theme at this coarse a check). Flags: near-empty
    body text (a blank/broken render), and visible raw error tokens that indicate a
    template failed to interpolate (undefined/NaN/[object Object] rendered as text)."""
    bugs = []
    try:
        info = page_pw.evaluate("""() => {
            const text = (document.body && document.body.innerText || '').trim();
            return {len: text.length, sample: text.slice(0, 4000)};
        }""")
    except Exception:
        return bugs
    text_len = info.get("len", 0)
    if text_len < 40:
        bugs.append(make_finding(
            severity="CRITICAL",
            title="Page rendered with near-empty body text",
            detail=f"document.body.innerText is only {text_len} chars — this looks like a "
                   "failed render (blank page, JS error before content painted, or a "
                   "template that produced no output) rather than real content.",
            selector="body",
            viewport=vp_name, theme=theme, page=page_name,
            fix="Open the page directly and check the browser console for JS errors during "
                "load; verify the template/data pipeline actually produced content.",
        ))
    sample = info.get("sample", "")
    for token in ("undefined", "NaN", "[object Object]", "null" ):
        # word-boundary-ish check: these tokens are legitimate substrings of real
        # words (e.g. "nullify") so require them standalone-ish (surrounded by
        # whitespace/punctuation) to avoid false positives on real content.
        if re.search(rf"(?:^|[\s:,\[({{]){re.escape(token)}(?:$|[\s.,\]\)}}])", sample):
            bugs.append(make_finding(
                severity="HIGH",
                title="Unrendered template token visible in page text",
                detail=f"Found the literal string {token!r} visible in rendered body text — "
                       "this is almost always a template variable that failed to interpolate.",
                selector="body",
                viewport=vp_name, theme=theme, page=page_name,
                fix=f"Find where {token!r} is rendered and fix the data binding/template that "
                    "produced it instead of a real value.",
            ))
            break  # one finding per token type is enough signal; don't spam duplicates
    return bugs


# ── Per-combination audit ──────────────────────────────────────────────────────

def audit_combination(page_pw, vp_name: str, theme: str, page_name: str) -> list[dict]:
    """Run all deterministic checks for one viewport×theme×page combination."""
    bugs = []

    # 1. Horizontal overflow (document level)
    try:
        hov = page_pw.evaluate(_JS_HOVERFLOW)
        if hov.get("overflows"):
            bugs.append(make_finding(
                severity="HIGH",
                title="Horizontal overflow on document",
                detail=f"scrollWidth={hov['scrollWidth']} > clientWidth={hov['clientWidth']}",
                selector="document",
                viewport=vp_name, theme=theme, page=page_name,
                fix="Check for fixed-width elements exceeding viewport. Add overflow-x:hidden on body or max-width:100% constraints.",
            ))
    except Exception as e:
        pass  # non-fatal

    # 2. Per-element overflow
    try:
        elem_ovs = page_pw.evaluate(_JS_ELEMENT_OVERFLOW)
        for ov in elem_ovs:
            tag = ov.get("tag", "?")
            # Build a readable selector from the tag string
            sel_parts = tag.split(".")
            sel = sel_parts[0] if sel_parts else tag
            class_part = " ".join(sel_parts[1:]) if len(sel_parts) > 1 else ""
            display_sel = f"{sel}.{class_part}" if class_part else sel
            bugs.append(make_finding(
                severity="HIGH",
                title=f"Element overflow: {display_sel[:60]}",
                detail=f"scrollWidth={ov['scrollWidth']} > clientWidth={ov['clientWidth']}",
                selector=display_sel[:120],
                viewport=vp_name, theme=theme, page=page_name,
                fix="Add min-width:0 on flex/grid children; use repeat(N, minmax(0, 1fr)) for grids; max-width:100% on imgs/canvas.",
            ))
    except Exception:
        pass

    # 3. Off-screen text
    try:
        texts = page_pw.evaluate(_JS_OFFSCREEN_TEXT)
        for t in texts:
            bugs.append(make_finding(
                severity="HIGH",
                title="Off-screen text node",
                detail=f"text='{t['text']}' rect.right={t['right']} > innerWidth={t['innerWidth']}",
                selector="text-node",
                viewport=vp_name, theme=theme, page=page_name,
                fix="Wrap text in overflow-hidden container or ensure parent has max-width:100%.",
            ))
    except Exception:
        pass

    # 5. WCAG contrast on badge elements
    try:
        badges = page_pw.evaluate(_JS_BADGE_CONTRAST, BADGE_SELECTORS)
        for b in badges:
            color_rgb = _parse_rgb(b.get("color", ""))
            bg_rgb = _parse_rgb(b.get("bg", ""))
            if not color_rgb or not bg_rgb:
                continue
            try:
                ratio = _contrast_ratio(color_rgb, bg_rgb)
            except ZeroDivisionError:
                continue
            if ratio < 4.5:
                cls = b.get("className", "")
                sel = b.get("selector", "")
                text = b.get("text", "")
                bugs.append(make_finding(
                    severity="CRITICAL",
                    title=f"WCAG contrast fail on badge: {cls[:40] or sel}",
                    detail=f"ratio={ratio:.2f}:1 < 4.5:1 | color={b['color']} bg={b['bg']} text='{text}'",
                    selector=sel,
                    viewport=vp_name, theme=theme, page=page_name,
                    fix=f"Increase contrast to ≥4.5:1 by adjusting text color or background. Current: {ratio:.2f}:1",
                ))
    except Exception:
        pass

    # 6. Touch targets (mobile only)
    if vp_name == "mobile":
        try:
            targets = page_pw.evaluate(_JS_TOUCH_TARGETS)
            for t in targets:
                tag = t.get("tag", "?")
                h = t.get("height", 0)
                label = t.get("label", "")
                bugs.append(make_finding(
                    severity="HIGH",
                    title=f"Touch target too small: {tag[:40]}",
                    detail=f"height={h}px < 44px | label='{label}'",
                    selector=tag[:100],
                    viewport=vp_name, theme=theme, page=page_name,
                    fix="Set min-height:44px; min-width:44px on interactive elements for touch accessibility.",
                ))
        except Exception:
            pass

    # 7. Chart health
    try:
        blank_url = page_pw.evaluate(_JS_BLANK_DATA_URL)
        # blank 1x1 canvas has a known short dataURL (~70 chars starting with data:image/png;base64)
        # Length <= 400 is a reliable proxy for blank/transparent
        BLANK_LEN_THRESHOLD = 400
        charts = page_pw.evaluate(_JS_CHARTS)
        for ch in charts:
            idx = ch.get("index", 0)
            cid = ch.get("id", "")
            w = ch.get("width", 0)
            h = ch.get("height", 0)
            data_len = ch.get("dataURLLength", 0)
            sel = f"canvas#{cid}" if cid else f"canvas:nth-child({idx + 1})"
            # CRITICAL if 0x0 or blank dataURL
            is_blank = data_len <= BLANK_LEN_THRESHOLD
            if w == 0 or h == 0 or is_blank:
                bugs.append(make_finding(
                    severity="CRITICAL",
                    title=f"Chart 0×0 or empty: canvas#{idx} {cid}",
                    detail=f"width={w} height={h} dataURL.length={data_len}",
                    selector=sel,
                    viewport=vp_name, theme=theme, page=page_name,
                    fix="Call chart.resize() on tab activation. Add min-width:0 to flex/grid parent.",
                ))
    except Exception:
        pass

    # 8. Tab invariant
    try:
        ti = page_pw.evaluate(_JS_TAB_INVARIANT)
        active_count = ti.get("activeCount", 0)
        total = ti.get("totalPages", 0)
        non_hidden = ti.get("nonHiddenInactive", [])
        if total > 0 and active_count != 1:
            bugs.append(make_finding(
                severity="CRITICAL",
                title=f"Tab invariant violated: {active_count} active pages (expected 1)",
                detail=f"activeCount={active_count} totalPages={total}",
                selector=".report-page",
                viewport=vp_name, theme=theme, page=page_name,
                fix="Ensure exactly one .report-page has class is-active at any time; others must have display:none.",
            ))
        for nh in non_hidden[:5]:
            bugs.append(make_finding(
                severity="CRITICAL",
                title=f"Inactive page not hidden: #{nh.get('id', '?')}",
                detail=f"display={nh.get('display', '?')} (expected none)",
                selector=f".report-page#{nh.get('id', '?')}",
                viewport=vp_name, theme=theme, page=page_name,
                fix="Set display:none on all inactive .report-page elements; only the active one should be visible.",
            ))
    except Exception:
        pass

    return bugs


# ── Main audit ─────────────────────────────────────────────────────────────────

def run_audit(html_path: Path, client: str, audit_date: str) -> dict:
    stem = html_path.stem
    artifact_name = html_path.name

    report_dir = QUALITY_DIR / f"{stem}-audit-{audit_date}"
    screenshots_dir = report_dir / "screenshots"
    report_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    url = html_path.resolve().as_uri()

    all_bugs: list[dict] = []
    themes_used: list[str] = []
    pages_used: list[str] = []
    combinations_run = 0
    theme_skip_reason: str | None = None

    # Phase 0 oracle #1 (placeholder-leak grep) — once per artifact, raw source,
    # before the browser even launches. Cheapest possible check, zero Playwright cost.
    try:
        raw_html = html_path.read_text(encoding="utf-8", errors="replace")
        all_bugs.extend(check_placeholder_leaks(raw_html, artifact_name))
    except Exception:
        pass  # non-fatal — a source-read failure shouldn't kill the whole audit

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )

        for vp in VIEWPORTS:
            vp_name = vp["name"]
            context = browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                device_scale_factor=1,
            )
            page_pw = context.new_page()

            try:
                page_pw.goto(url, wait_until="networkidle", timeout=QA_TIMEOUT)
            except PWTimeoutError:
                page_pw.goto(url, wait_until="domcontentloaded", timeout=QA_TIMEOUT)

            # Wait briefly for JS to settle
            page_pw.wait_for_timeout(800)

            # Phase 0 oracle #2 (render-succeeded) — once per viewport, on the
            # freshly-loaded page before any tab/theme switching. Content doesn't
            # vary by theme at this coarse a check, so per-theme repetition would
            # just duplicate the same finding.
            all_bugs.extend(check_render_succeeded(page_pw, vp_name, "dark", "main"))

            # Discover pages/tabs
            discovered_pages = page_pw.evaluate(_JS_PAGES)
            if not discovered_pages:
                discovered_pages = ["main"]
            if not pages_used:
                pages_used = list(discovered_pages)

            # Detect theme toggle
            has_toggle = page_pw.evaluate(_JS_HAS_THEME_TOGGLE)

            # Determine themes to test
            themes_to_test = ["dark"]
            if has_toggle:
                themes_to_test = ["dark", "light"]
            else:
                if not theme_skip_reason:
                    theme_skip_reason = f"No #themeToggle found in {artifact_name}; light theme skipped."

            for theme in themes_to_test:
                if theme not in themes_used:
                    themes_used.append(theme)

                # Reset to dark first (reload)
                try:
                    page_pw.goto(url, wait_until="networkidle", timeout=QA_TIMEOUT)
                except PWTimeoutError:
                    page_pw.goto(url, wait_until="domcontentloaded", timeout=QA_TIMEOUT)
                page_pw.wait_for_timeout(600)

                # Switch to light if needed
                bg_dark: str | None = None
                bg_light: str | None = None

                if theme == "dark":
                    bg_dark = page_pw.evaluate(_JS_BG_COLOR)
                elif theme == "light" and has_toggle:
                    bg_dark = page_pw.evaluate(_JS_BG_COLOR)
                    page_pw.click("#themeToggle")
                    page_pw.wait_for_timeout(400)
                    bg_light = page_pw.evaluate(_JS_BG_COLOR)

                for pg_name in discovered_pages:
                    # Activate the right page/tab
                    if pg_name != "main" and len(discovered_pages) > 1:
                        activated = page_pw.evaluate(_JS_ACTIVATE_PAGE, pg_name)
                        page_pw.wait_for_timeout(300)

                    # Screenshot
                    ss_path = screenshots_dir / f"{vp_name}_{theme}_{pg_name}.png"
                    try:
                        page_pw.screenshot(path=str(ss_path), full_page=False)
                    except Exception:
                        pass  # non-fatal

                    bugs = audit_combination(page_pw, vp_name, theme, pg_name)
                    all_bugs.extend(bugs)
                    combinations_run += 1

            # Theme propagation check (once per viewport, only if we tested both themes)
            if has_toggle and "dark" in themes_used and "light" in themes_used:
                try:
                    # Re-open fresh for clean bg comparison
                    page_pw.goto(url, wait_until="domcontentloaded", timeout=QA_TIMEOUT)
                    page_pw.wait_for_timeout(400)
                    bg_d = page_pw.evaluate(_JS_BG_COLOR)
                    page_pw.click("#themeToggle")
                    page_pw.wait_for_timeout(400)
                    bg_l = page_pw.evaluate(_JS_BG_COLOR)

                    if bg_d and bg_l and bg_d == bg_l:
                        all_bugs.append(make_finding(
                            severity="CRITICAL",
                            title="Theme toggle does not change body background",
                            detail=f"dark='{bg_d}' light='{bg_l}' — identical",
                            selector="body",
                            viewport=vp_name, theme="light", page=pages_used[0] if pages_used else "main",
                            fix="Ensure #themeToggle toggles a class (e.g. body.light-mode) and that CSS vars/selectors change background-color.",
                        ))
                except Exception:
                    pass

            context.close()

        browser.close()

    # ── De-duplicate across combinations ──────────────────────────────────────
    # The biggest over-count driver: contrast / chart-health / tab-invariant / theme are
    # DOM/CSS properties that DON'T vary by viewport — but audit_combination runs once per
    # viewport×theme×page (~48 combos for a tabbed report), so the SAME finding was counted
    # ~48×. Collapse on finding identity (title + selector + detail). Viewport-dependent
    # layout findings (overflow / off-screen text) embed the viewport's clientWidth/innerWidth
    # in `detail`, so they remain distinct per viewport (correct — those ARE different bugs).
    # We keep the FIRST occurrence's viewport/theme/page for the surviving record.
    _seen = set()
    _deduped = []
    for b in all_bugs:
        key = (b.get("title", ""), b.get("selector", ""), b.get("detail", ""))
        if key in _seen:
            continue
        _seen.add(key)
        _deduped.append(b)
    pre_dedup_total = len(all_bugs)
    all_bugs = _deduped

    # ── Count bugs ───────────────────────────────────────────────────────────
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for b in all_bugs:
        sev = b.get("severity", "LOW")
        if sev in counts:
            counts[sev] += 1

    total_bugs = sum(counts.values())
    verdict = "NO-SHIP" if (counts["CRITICAL"] > 0 or counts["HIGH"] > 0) else "SHIP"

    # ── Write audit-report.json ───────────────────────────────────────────────
    full_report = {
        "artifact": artifact_name,
        "artifact_path": str(html_path.resolve()),
        "audit_date": audit_date,
        "auditor": AUDITOR,
        "viewports": [v["name"] for v in VIEWPORTS],
        "themes": themes_used,
        "pages": pages_used,
        "combinations": combinations_run,
        "screenshots_dir": str(screenshots_dir),
        "bug_counts": counts,
        "total_bugs": total_bugs,
        "raw_findings_pre_dedup": pre_dedup_total,
        "bugs": all_bugs,
    }
    if theme_skip_reason:
        full_report["theme_skip_reason"] = theme_skip_reason

    report_json_path = report_dir / "audit-report.json"
    report_json_path.write_text(json.dumps(full_report, indent=2, ensure_ascii=False))

    # ── Write audit-report.md ─────────────────────────────────────────────────
    md_lines = [
        f"# QA Audit: {artifact_name}",
        f"",
        f"**Artifact:** `{artifact_name}`",
        f"**Client:** {client}",
        f"**Date:** {audit_date}",
        f"**Auditor:** {AUDITOR}",
        f"**Verdict:** {verdict}",
        f"",
        f"## Bug Summary",
        f"",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| CRITICAL | {counts['CRITICAL']} |",
        f"| HIGH     | {counts['HIGH']} |",
        f"| MEDIUM   | {counts['MEDIUM']} |",
        f"| LOW      | {counts['LOW']} |",
        f"| **TOTAL**| **{total_bugs}** |",
        f"",
    ]
    if theme_skip_reason:
        md_lines += [f"> Note: {theme_skip_reason}", ""]
    if verdict == "NO-SHIP":
        md_lines += [
            f"**NO-SHIP**: {counts['CRITICAL']} CRITICAL + {counts['HIGH']} HIGH bugs must be fixed before delivery.",
            "",
        ]
    else:
        md_lines += [f"**SHIP**: No blocking bugs found.", ""]

    if all_bugs:
        md_lines += ["## Findings", ""]
        for bug in all_bugs:
            sev = bug["severity"]
            md_lines += [
                f"### [{sev}] {bug['title']}",
                f"",
                f"- **Selector:** `{bug['selector']}`",
                f"- **Viewport / Theme / Page:** {bug['viewport']} / {bug['theme']} / {bug['page']}",
                f"- **Detail:** {bug['detail']}",
                f"- **Fix:** {bug['fix']}",
                f"",
            ]
    else:
        md_lines += ["## Findings", "", "_No bugs found._", ""]

    (report_dir / "audit-report.md").write_text("\n".join(md_lines))

    # ── Write QUALITY/<stem>-audit-<date>.json (summary the watcher reads) ───
    summary = {
        "artifact": artifact_name,   # bare filename — watcher matches on this
        "client": client,
        "audit_date": audit_date,
        "auditor": AUDITOR,
        "bug_counts": counts,
        "total_bugs": total_bugs,
        "verdict": verdict,
        "report_path": str(report_json_path),
        "screenshots_dir": str(screenshots_dir),
    }
    if theme_skip_reason:
        summary["theme_skip_reason"] = theme_skip_reason

    summary_path = QUALITY_DIR / f"{stem}-audit-{audit_date}.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    return summary


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deterministic Playwright DOM audit of ONE brand-report HTML file."
    )
    parser.add_argument("html_path", help="Path to the HTML file to audit")
    parser.add_argument("--client", default=None, help="Client name (derived from path if omitted)")
    parser.add_argument("--date", default=None, help="Audit date YYYY-MM-DD (defaults to today UTC)")
    args = parser.parse_args()

    html_path = Path(args.html_path).resolve()
    if not html_path.exists():
        print(json.dumps({"error": f"File not found: {html_path}"}), file=sys.stderr)
        sys.exit(2)
    if not html_path.suffix.lower() == ".html":
        print(json.dumps({"error": f"Expected .html file, got: {html_path}"}), file=sys.stderr)
        sys.exit(2)

    # Derive client from path /mnt/clients/<client>/...
    client = args.client
    if not client:
        parts = html_path.parts
        try:
            idx = parts.index("clients")
            client = parts[idx + 1]
        except (ValueError, IndexError):
            client = "unknown"

    audit_date = args.date or date.today().isoformat()

    try:
        summary = run_audit(html_path, client, audit_date)
    except Exception as e:
        import traceback
        print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}), file=sys.stderr)
        sys.exit(2)

    print(json.dumps(summary, indent=2))

    verdict = summary.get("verdict", "NO-SHIP")
    sys.exit(0 if verdict == "SHIP" else 1)


if __name__ == "__main__":
    main()
