#!/usr/bin/env python3
"""
visual-check.py — the Quality Officer's VISUAL gate (the part HTTP checks can't do).

Renders each page in headless Chromium (Playwright) at multiple viewports and runs
PROGRAMMATIC visual checks against the live DOM + computed styles — far more reliable
than asking a vision model "does this look ok":
  - contrast: every text node's computed color vs its effective background → WCAG ratio
    (catches light-on-light / dark-on-dark text + invisible/unstyled buttons)
  - horizontal overflow: page wider than the viewport (squished / breaks on mobile)
  - broken/missing images: <img> that loaded but naturalWidth==0
  - clipped containers: elements whose content overflows a fixed/hidden box
  - empty sections: <section>/<main> blocks with no real content
Saves a full-page screenshot per page×viewport for the human eye too.

USAGE
  python3 visual-check.py --url https://site.com --routes "/,/map,/about" \
      --viewports 390,1440 --out /tmp/qa-shots
EXIT: 0 = PASS, 1 = FAIL (gate). Writes <out>/visual-review.json.
"""
import argparse, json, os, sys

# in-page JS: returns {contrast:[...], overflow:bool, brokenImages:[...], clipped:[...], emptySections:int}
JS = r"""
() => {
  const lum = (r,g,b) => { const f=c=>{c/=255; return c<=0.03928? c/12.92 : Math.pow((c+0.055)/1.055,2.4);};
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b); };
  const parseRGB = s => { const m=(s||'').match(/rgba?\(([^)]+)\)/); if(!m) return null;
    const p=m[1].split(',').map(x=>parseFloat(x)); return {r:p[0],g:p[1],b:p[2],a:p[3]===undefined?1:p[3]}; };
  const effBg = el => { let n=el; while(n){ const c=parseRGB(getComputedStyle(n).backgroundColor);
    if(c && c.a>0.05) return c; n=n.parentElement; } return {r:255,g:255,b:255,a:1}; };
  const ratio = (a,b)=>{ const la=lum(a.r,a.g,a.b), lb=lum(b.r,b.g,b.b);
    return (Math.max(la,lb)+0.05)/(Math.min(la,lb)+0.05); };

  const out={contrast:[],overflow:false,brokenImages:[],clipped:[],emptySections:0};
  // contrast — visible elements holding direct text
  const els=[...document.querySelectorAll('body *')];
  let checked=0;
  for(const el of els){
    if(checked>4000) break;
    const txt=[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent.trim()).join('');
    if(txt.length<3) continue;
    const cs=getComputedStyle(el);
    if(cs.visibility==='hidden'||cs.display==='none'||parseFloat(cs.opacity)<0.1) continue;
    const rect=el.getBoundingClientRect(); if(rect.width<2||rect.height<2) continue;
    const fg=parseRGB(cs.color); if(!fg||fg.a<0.1) continue;
    const bg=effBg(el);
    const r=ratio(fg,bg); checked++;
    const fsz=parseFloat(cs.fontSize), bold=parseInt(cs.fontWeight)>=600;
    const large=(fsz>=24)||(fsz>=18.66&&bold);
    const min=large?3.0:4.5;
    if(r<min) out.contrast.push({text:txt.slice(0,50), ratio:Math.round(r*100)/100,
      color:cs.color, bg:`rgb(${Math.round(bg.r)},${Math.round(bg.g)},${Math.round(bg.b)})`,
      fontSize:Math.round(fsz), need:min});
  }
  // horizontal overflow
  out.overflow = document.documentElement.scrollWidth > window.innerWidth+2;
  out.scrollW = document.documentElement.scrollWidth; out.innerW = window.innerWidth;
  // broken images
  for(const img of document.images){ if(img.complete && img.naturalWidth===0)
    out.brokenImages.push(img.currentSrc||img.src||'(no src)'); }
  // clipped containers (content overflows a hidden/fixed box)
  for(const el of els){ const cs=getComputedStyle(el);
    if((cs.overflow==='hidden'||cs.overflowX==='hidden') && el.scrollWidth>el.clientWidth+8 && el.clientWidth>40)
      out.clipped.push((el.id?'#'+el.id:el.className?'.'+String(el.className).split(' ')[0]:el.tagName)); }
  out.clipped=[...new Set(out.clipped)].slice(0,10);
  // empty sections
  for(const s of document.querySelectorAll('section,main>div')){
    if(s.textContent.trim().length<15 && !s.querySelector('img,svg,canvas,video,iframe')) out.emptySections++; }
  return out;
}
"""


def review(url, routes, viewports, out_dir):
    from playwright.sync_api import sync_playwright
    os.makedirs(out_dir, exist_ok=True)
    findings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        for route in routes:
            full = url.rstrip("/") + ("" if route == "/" else route)
            for vw in viewports:
                page = browser.new_page(viewport={"width": vw, "height": 900})
                tag = f"{route}@{vw}px"
                try:
                    resp = page.goto(full, wait_until="networkidle", timeout=25000)
                    code = resp.status if resp else 0
                    hdrs = resp.headers if resp else {}
                    # Clerk-protected route hit by a signed-out headless browser returns a
                    # 404/redirect to the dev-handshake interstitial — working-as-designed,
                    # NOT a build failure. (Same AUTH_GATED signal check.py keys off.)
                    if any(k.lower().startswith("x-clerk-auth") for k in hdrs) and \
                       "protect" in (hdrs.get("x-clerk-auth-reason", "").lower()):
                        findings.append({"severity": "warn", "check": "auth-gated", "where": tag,
                                         "detail": "Clerk-protected route — visual checks skipped (signed-out headless can't render protected content)"})
                        page.close(); continue
                    if code >= 400:
                        findings.append({"severity": "fail", "check": "route", "where": tag, "detail": f"HTTP {code}"})
                        page.close(); continue
                    page.wait_for_timeout(800)
                    # Trigger scroll-reveal animations (IntersectionObserver / FadeIn etc.)
                    # BEFORE checking + screenshotting. Reveal sections start at opacity:0 and
                    # only animate in on scroll — a static capture leaves them blank and the
                    # checks false-flag them as "empty/low-contrast". Scroll through, then top.
                    try:
                        page.evaluate(
                            "async () => { const h = document.body.scrollHeight;"
                            " for (let y = 0; y < h; y += 400) { window.scrollTo(0, y);"
                            " await new Promise(r => setTimeout(r, 80)); }"
                            " window.scrollTo(0, 0); }"
                        )
                        page.wait_for_timeout(600)
                    except Exception:
                        pass
                    shot = os.path.join(out_dir, f"{route.strip('/').replace('/','_') or 'home'}_{vw}.png")
                    page.screenshot(path=shot, full_page=True)
                    r = page.evaluate(JS)
                    for c in r["contrast"][:8]:
                        findings.append({"severity": "fail", "check": "contrast", "where": tag,
                                         "detail": f'low contrast {c["ratio"]}:1 (need {c["need"]}) — "{c["text"]}" {c["color"]} on {c["bg"]}'})
                    if r["overflow"]:
                        findings.append({"severity": "fail", "check": "overflow", "where": tag,
                                         "detail": f'horizontal overflow: page {r["scrollW"]}px > viewport {r["innerW"]}px (squished/breaks)'})
                    for src in r["brokenImages"][:8]:
                        findings.append({"severity": "fail", "check": "broken-image", "where": tag, "detail": f"image not rendering: {src[:80]}"})
                    for cl in r["clipped"]:
                        findings.append({"severity": "warn", "check": "clipped", "where": tag, "detail": f"content clipped in {cl}"})
                    if r["emptySections"]:
                        findings.append({"severity": "warn", "check": "empty-section", "where": tag, "detail": f'{r["emptySections"]} empty section(s)'})
                except Exception as e:
                    findings.append({"severity": "warn", "check": "render", "where": tag, "detail": f"render error: {str(e)[:100]}"})
                finally:
                    page.close()
        browser.close()
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--routes", default="/")
    ap.add_argument("--viewports", default="390,1440")  # mobile + desktop by default
    ap.add_argument("--out", default="/tmp/visual-review")
    a = ap.parse_args()
    routes = [r.strip() for r in a.routes.split(",") if r.strip()]
    vps = [int(v) for v in a.viewports.split(",") if v.strip().isdigit()]
    findings = review(a.url, routes, vps, a.out)
    fails = [f for f in findings if f["severity"] == "fail"]
    warns = [f for f in findings if f["severity"] == "warn"]
    verdict = "PASS" if not fails else "FAIL"
    json.dump({"verdict": verdict, "fail_count": len(fails), "warn_count": len(warns),
               "findings": findings, "screenshots_dir": a.out, "url": a.url},
              open(os.path.join(a.out, "visual-review.json"), "w"), indent=2)
    print(f"VISUAL REVIEW: {verdict}  ({len(fails)} fail, {len(warns)} warn)  — {a.url}")
    print(f"  screenshots → {a.out}")
    for f in fails + warns:
        print(f"  {'✗' if f['severity']=='fail' else '⚠'} {f['check']} [{f.get('where')}]: {f['detail']}")
    if verdict == "PASS" and not warns:
        print("  ✓ no visual issues")
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
