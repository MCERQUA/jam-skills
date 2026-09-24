#!/usr/bin/env python3
"""Re-audit visual artifacts per visual-artifact-qa-workflow.md.
Usage: qa-reaudit-2026-09-06.py <artifact.html> <client> <outdir>
"""
import json, sys, os, re
from playwright.sync_api import sync_playwright

VIEWPORTS = [(375, 812, "mobile"), (768, 1024, "tablet"), (1440, 900, "desktop")]

def static_text_chars(html_path):
    # Second instrument for render health: count visible chars with no JS at
    # all. innerText===0 from a failed harness load is indistinguishable from a
    # blank page by runtime read alone (2026-09-21 storehouse false-CRITICAL).
    try:
        html = open(html_path, encoding="utf-8", errors="replace").read()
    except OSError:
        return 0
    html = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return len(re.sub(r"\s+", " ", text).strip())

CHECK_JS = """
() => {
  const out = {};
  out.body_text_len = (document.body.innerText || '').length;
  const de = document.documentElement;
  out.doc_overflow = { scrollWidth: de.scrollWidth, clientWidth: de.clientWidth,
                       bodyScrollWidth: document.body.scrollWidth, bodyClientWidth: document.body.clientWidth };
  const visible = el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  // nearest scrollable-x ancestor (overflow-x auto/scroll) — content within is reachable by design
  const inScrollRail = el => {
    let c = el.parentElement;
    while (c && c !== document.body) {
      const cs = getComputedStyle(c);
      if (cs.overflowX === 'auto' || cs.overflowX === 'scroll') return true;
      c = c.parentElement;
    }
    return false;
  };
  // element overflow (skip intentional hiders)
  out.elem_overflow = [];
  const seen = new Set();
  document.querySelectorAll('*').forEach(el => {
    if (!visible(el)) return;
    const ovs = getComputedStyle(el).overflowX;
    if (ovs === 'auto' || ovs === 'scroll') return;
    const tag = el.tagName;
    if (['HTML','BODY','SCRIPT','STYLE','LINK','META','HEAD'].includes(tag)) return;
    const cs = getComputedStyle(el);
    if (el.scrollWidth > el.clientWidth + 2) {
      const sel = tag.toLowerCase() + (el.id ? '#'+el.id : '') + (el.className && typeof el.className === 'string' ? '.'+el.className.trim().split(/\\s+/).slice(0,2).join('.') : '');
      if (!seen.has(sel)) { seen.add(sel);
        out.elem_overflow.push({selector: sel, scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, overflowX: cs.overflowX}); }
    }
  });
  out.elem_overflow = out.elem_overflow.slice(0, 25);
  // off-screen visible text nodes
  out.offscreen_text = [];
  const w = window.innerWidth;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const offseen = new Set();
  let n;
  while ((n = walker.nextNode())) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement;
    if (!el) continue;
    if (inScrollRail(el)) continue;
    let hidden = false, cur = el;
    while (cur && cur !== document.body) {
      const cs = getComputedStyle(cur);
      if (cs.display === 'none' || cs.visibility === 'hidden') { hidden = true; break; }
      cur = cur.parentElement;
    }
    if (hidden) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    const r = range.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (r.right > w + 1 || r.left < -1) {
      let anc = el, found = false;
      for (const o of out.offscreen_text) { /* dedupe by ancestor */ }
      const key = el.tagName + ':' + (el.className && typeof el.className === 'string' ? el.className : '').slice(0,40) + ':' + n.textContent.trim().slice(0,30);
      if (offseen.has(key)) continue;
      offseen.add(key);
      out.offscreen_text.push({selector: el.tagName.toLowerCase() + (el.id ? '#'+el.id : '') + (el.className && typeof el.className === 'string' ? '.'+el.className.trim().split(/\\s+/).slice(0,2).join('.') : ''), text: n.textContent.trim().slice(0,60), left: Math.round(r.left), right: Math.round(r.right), viewport: w});
      if (out.offscreen_text.length >= 25) break;
    }
  }
  // contrast on badge-like elements
  const lum = (r,g,b) => {
    const f = c => { c/=255; return c <= 0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4); };
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b);
  };
  const parseA = s => { const m = s.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/); return m ? [+m[1],+m[2],+m[3], m[4] === undefined ? 1 : +m[4]] : null; };
  const ratio = (fg, bg) => { const l1 = lum(...fg), l2 = lum(...bg); return (Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05); };
  // composite translucent ancestor backgrounds up the chain until opaque
  const bgOf = el => { let acc = null; let c = el.parentElement || el; while (c) { const bg = parseA(getComputedStyle(c).backgroundColor); if (bg && bg[3] > 0) { if (acc === null) acc = bg.slice(); else { const a = bg[3]; for (let i=0;i<3;i++) acc[i] = Math.round(a*bg[i] + (1-a)*acc[i]); acc[3] = Math.min(1, acc[3] + a*(1-acc[3])); } if (acc[3] >= 0.99) return acc.slice(0,3); } if (c === document.documentElement) break; c = c.parentElement; } if (acc === null) return [255,255,255]; return acc.slice(0,3); };
  out.contrast = [];
  const cseen = new Set();
  document.querySelectorAll('.pill,.tag,.badge,.status,.mention,[class*="sev-"],.chip').forEach(el => {
    if (!visible(el)) return;
    const fg = parseA(getComputedStyle(el).color), bg = bgOf(el);
    if (!fg) return;
    const r = ratio(fg, bg);
    if (r < 4.5) {
      const key = el.tagName + '.' + (typeof el.className === 'string' ? el.className : '') + ':' + Math.round(r*10);
      if (cseen.has(key)) return;
      cseen.add(key);
      out.contrast.push({selector: el.tagName.toLowerCase() + (typeof el.className === 'string' ? '.'+el.className.trim().split(/\\s+/).join('.') : ''), text: el.textContent.trim().slice(0,40), ratio: Math.round(r*100)/100, fg: getComputedStyle(el).color, bg: 'rgb('+bg.join(',')+')'});
    }
  });
  out.contrast = out.contrast.slice(0, 20);
  // touch targets (mobile only caller decides)
  out.touch = [];
  const tseen = new Set();
  document.querySelectorAll('button, a.btn, .btn, .chip, .tab-btn, [role="button"]').forEach(el => {
    if (!visible(el)) return;
    const r = el.getBoundingClientRect();
    if (r.height < 44 || r.width < 44) {
      const key = el.tagName + '.' + (typeof el.className === 'string' ? el.className : '') + ':' + Math.round(r.height);
      if (tseen.has(key)) return;
      tseen.add(key);
      out.touch.push({selector: el.tagName.toLowerCase() + (typeof el.className === 'string' ? '.'+el.className.trim().split(/\\s+/).slice(0,2).join('.') : ''), text: el.textContent.trim().slice(0,30), w: Math.round(r.width), h: Math.round(r.height)});
    }
  });
  out.touch = out.touch.slice(0, 20);
  // canvas health
  out.canvas = [];
  document.querySelectorAll('canvas').forEach((c, i) => {
    let hashOk = false, hashLen = 0;
    try { const d = c.toDataURL(); hashLen = d.length; hashOk = d.length > 500; } catch(e) {}
    out.canvas.push({index: i, w: c.width, h: c.height, cssW: Math.round(c.getBoundingClientRect().width), dataLen: hashLen, ok: c.width>0 && c.height>0 && hashOk});
  });
  // tab invariant
  const pages = document.querySelectorAll('.report-page, .tab-page, [class*="tab-panel"]');
  if (pages.length) {
    const active = [...pages].filter(p => p.classList.contains('is-active') || getComputedStyle(p).display !== 'none');
    out.tabs = {total: pages.length, active: active.length};
  }
  // purple detection — hue-based: purple/violet hue 255-305 with real saturation (excludes pink/magenta ~310-340 and desaturated near-whites)
  out.purple = [];
  const isPurple = rgb => { if (!rgb) return false; const [r,g,b] = rgb; const mx = Math.max(r,g,b), mn = Math.min(r,g,b); const d = mx - mn; if (mx === 0 || d / mx < 0.12) return false; let hue; if (mx === r) hue = 60 * (((g - b) / d) % 6); else if (mx === g) hue = 60 * ((b - r) / d + 2); else hue = 60 * ((r - g) / d + 4); if (hue < 0) hue += 360; if (!(hue >= 255 && hue <= 305)) return false; const f = c => { c/=255; return c <= 0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4); }; const L = 0.2126*f(r)+0.7152*f(g)+0.0722*f(b); return L >= 0.04; };
  // emoji detection — astral-plane emoji, FE0F emoji-presentation, and default-emoji dingbats (NOT text dingbats like ✔ ✖)
  out.emoji = [];
  const emojiCore = /[\\u{1F000}-\\u{1FAFF}\\u{2B50}\\u{2728}\\u{2795}\\u{2796}\\u{274C}\\u{274E}\\u{2705}\\u{2764}]/u;
  const emojiFE0F = /[\\u{2600}-\\u{27BF}\\u{2190}-\\u{21FF}\\u{2B00}-\\u{2BFF}]\\u{FE0F}/u;
  document.querySelectorAll('body *').forEach(el => {
    if (el.children.length > 0) return;
    if (!visible(el)) return;
    const t = el.textContent;
    if (t && (emojiCore.test(t) || emojiFE0F.test(t))) {
      out.emoji.push({selector: el.tagName.toLowerCase() + (typeof el.className === 'string' ? '.'+el.className.trim().split(/\\s+/).slice(0,2).join('.') : ''), text: t.trim().slice(0,50)});
      if (out.emoji.length >= 10) return;
    }
  });
  const pseen = new Set();
  document.querySelectorAll('body *').forEach(el => {
    if (!visible(el)) return;
    const cs = getComputedStyle(el);
    const fg = parseA(cs.color), bg = parseA(cs.backgroundColor);
    const fgp = isPurple(fg), bgp = bg && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' ? isPurple(bg) : false;
    if (fgp || bgp) {
      const key = el.tagName + (typeof el.className === 'string' ? '.'+el.className : '') + (fgp?':fg':'') + (bgp?':bg':'');
      if (pseen.has(key)) return;
      pseen.add(key);
      out.purple.push({selector: el.tagName.toLowerCase() + (typeof el.className === 'string' ? '.'+el.className.trim().split(/\\s+/).slice(0,2).join('.') : ''), fg: fgp ? cs.color : null, bg: bgp ? cs.backgroundColor : null});
      if (out.purple.length >= 10) return;
    }
  });
  return out;
}
"""

THEME_TOGGLE_JS = """
() => {
  const cands = document.querySelectorAll('#themeToggle, [class*="theme-toggle"], [class*="themeToggle"], [aria-label*="theme" i], [data-action*="theme"], .toggle-theme, #theme-toggle');
  for (const el of cands) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 || getComputedStyle(el).display !== 'none') return {found: true, desc: el.tagName + ':' + (el.id || el.className || el.getAttribute('aria-label'))};
  }
  return {found: false};
}
"""

def click_theme(page):
    page.evaluate("""() => {
      const el = document.querySelector('#themeToggle, [class*="theme-toggle"], [class*="themeToggle"], [aria-label*="theme" i], [data-action*="theme"], .toggle-theme, #theme-toggle');
      if (el) el.click();
    }""")
    page.wait_for_timeout(400)

def classify(res, viewport_name, is_mobile, static_chars):
    bugs = []
    observations = []
    def add(sev, kind, detail, selector, extra=None):
        bugs.append({"severity": sev, "kind": kind, "viewport": viewport_name, "selector": selector, "detail": detail, **(extra or {})})
    # render health: two instruments must BOTH read zero before calling a page
    # blank. Zero from one instrument = CANNOT-TELL (harness failure), never a bug.
    if res.get("body_text_len", 0) == 0:
        if static_chars == 0:
            add("CRITICAL", "blank-page", "body innerText 0 AND static text 0 — page is genuinely empty", "body")
        else:
            observations.append({"kind": "render-health-cannot-tell", "viewport": viewport_name,
                                 "detail": f"runtime innerText 0 but static text {static_chars} chars — harness did not see the page; re-run before reporting render failure"})
    o = res["doc_overflow"]
    if o["scrollWidth"] > o["clientWidth"] or o["bodyScrollWidth"] > o["bodyClientWidth"]:
        add("CRITICAL", "doc-horizontal-overflow",
            f"documentElement scrollWidth {o['scrollWidth']} > clientWidth {o['clientWidth']} (body {o['bodyScrollWidth']}/{o['bodyClientWidth']})",
            "html/body")
    for e in res["elem_overflow"]:
        add("HIGH", "element-overflow", f"scrollWidth {e['scrollWidth']} > clientWidth {e['clientWidth']} (overflow-x: {e['overflowX']})", e["selector"])
    for t in res["offscreen_text"]:
        add("HIGH", "offscreen-text", f"text '{t['text']}' spans {t['left']}..{t['right']} vs viewport {t['viewport']}", t["selector"])
    for c in res["contrast"]:
        add("HIGH", "contrast-fail", f"WCAG {c['ratio']}:1 < 4.5:1 on '{c['text']}' (fg {c['fg']} on bg {c['bg']})", c["selector"])
    if is_mobile:
        for t in res["touch"]:
            add("HIGH", "touch-target", f"{t['w']}x{t['h']}px < 44px minimum on '{t['text']}'", t["selector"])
    for cv in res["canvas"]:
        if not cv["ok"]:
            add("HIGH", "canvas-dead", f"canvas {cv['index']} dims {cv['w']}x{cv['h']} cssW {cv['cssW']} dataLen {cv['dataLen']}", f"canvas[{cv['index']}]")
    if "tabs" in res and res["tabs"]["active"] != 1:
        add("CRITICAL", "tab-invariant", f"{res['tabs']['active']} of {res['tabs']['total']} tab pages active, expected exactly 1", ".report-page")
    for p in res["purple"]:
        add("HIGH", "purple-rule", f"purple color detected fg={p['fg']} bg={p['bg']}", p["selector"])
    for e in res.get("emoji", []):
        add("HIGH", "emoji-rule", f"emoji character in UI text: '{e['text']}'", e["selector"])
    return bugs, observations

def main():
    artifact, client, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(os.path.join(outdir, "screenshots"), exist_ok=True)
    name = os.path.basename(artifact)
    s_chars = static_text_chars(artifact)
    all_bugs = []
    all_observations = []
    combos = []
    theme_skip = None
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for (w, h, vname) in VIEWPORTS:
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto("file://" + artifact)
            page.wait_for_timeout(700)
            base_bg = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
            tgl = page.evaluate(THEME_TOGGLE_JS)
            themes = []
            if tgl.get("found"):
                click_theme(page)
                light_bg = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
                if light_bg != base_bg:
                    themes = [("light", light_bg), ("dark", base_bg)]
                else:
                    themes = [("dark", base_bg)]
                    theme_skip = "Theme toggle found but clicking it did not change body background"
                click_theme(page)  # back to default
                if themes and themes[0][0] == "light":
                    themes = list(reversed(themes))
            else:
                themes = [("dark", base_bg)]
                theme_skip = "No theme toggle found; light theme skipped."
            for (tname, tbg) in themes:
                if tname == "light":
                    click_theme(page)
                page.wait_for_timeout(300)
                res = page.evaluate(CHECK_JS)
                shot = f"{vname}_{tname}.png"
                page.screenshot(path=os.path.join(outdir, "screenshots", shot), full_page=True)
                is_mobile = vname == "mobile"
                bugs_c, obs_c = classify(res, f"{vname}/{tname}", is_mobile, s_chars)
                all_bugs.extend(bugs_c)
                all_observations.extend(obs_c)
                combos.append({"viewport": vname, "theme": tname, "body_bg": tbg,
                               "doc_overflow": res["doc_overflow"], "checks": res})
                if tname == "light":
                    click_theme(page)  # restore
            page.close()
        browser.close()

    # dedupe by (kind, selector, detail)
    seen = set()
    bugs = []
    for b in all_bugs:
        k = (b["kind"], b["selector"], b["detail"])
        if k in seen:
            continue
        seen.add(k)
        bugs.append(b)
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for b in bugs:
        counts[b["severity"]] += 1
    verdict = "SHIP" if counts["CRITICAL"] == 0 and counts["HIGH"] == 0 else "NO-SHIP"
    report = {
        "artifact": name, "artifact_path": artifact, "client": client,
        "audit_date": "2026-09-06", "auditor": "quality-assurance-manager@mesh",
        "audit_type": "re-audit after root-cause fix",
        "viewports": [v[2] for v in VIEWPORTS], "combinations": combos,
        "bug_counts": counts, "total_bugs": len(bugs), "verdict": verdict,
        "bugs": bugs,
        "render_health": {"static_text_chars": s_chars,
                          "observations": all_observations},
        **({"theme_skip_reason": theme_skip} if theme_skip else {}),
    }
    with open(os.path.join(outdir, "audit-report.json"), "w") as f:
        json.dump(report, f, indent=1)
    lines = [f"# Re-audit — {name} ({client}) — 2026-09-06", "",
             f"**Verdict: {verdict}** — {counts['CRITICAL']} critical / {counts['HIGH']} high / {counts['MEDIUM']} medium / {counts['LOW']} low",
             ""]
    for b in bugs:
        lines.append(f"- [{b['severity']}] {b['kind']} @ {b['viewport']} — `{b['selector']}`: {b['detail']}")
    with open(os.path.join(outdir, "audit-report.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{name}: {verdict} — {counts['CRITICAL']}C/{counts['HIGH']}H/{counts['MEDIUM']}M/{counts['LOW']}L — {outdir}")
    # compact combo summary for triage
    for c in combos:
        print(f"  {c['viewport']}/{c['theme']}: doc {c['doc_overflow']['scrollWidth']}/{c['doc_overflow']['clientWidth']}")

if __name__ == "__main__":
    main()
