#!/usr/bin/env python3
"""render_master.py — render a JSON intermediate (from harvest.py) into ONE
standalone searchable master page.

Features proven on the Cortez caption library: dark theme, inline CSS/JS only
(no CDN — pages must work on a phone over a canvas route), live search,
per-section TOC chips, per-item Copy button (copies plain text from embedded
JS data, never innerHTML), Select-Text modal, source-page tag, per-section
Copy All, lightbox for item images.

Usage:
  render_master.py captions.json --out master.html --title "Caption Library" \
    [--banned-words "graco,fusion"]
"""
import argparse, html, json, re, sys

# JS template: NB use only String.fromCharCode for newlines inside JS string
# literals, and helper functions in onclick attributes — no backslash escapes,
# they get mangled between Python and JS quoting layers.
PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#0a0a0a;--fg:#e2e8f0;--amber:#f59e0b;--dim:#94a3b8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
header{position:sticky;top:0;background:var(--bg);padding:12px 16px;
border-bottom:1px solid #1e293b;z-index:9}
h1{font-size:1.15rem;margin:0 0 8px}
#q{width:100%;padding:10px 12px;border-radius:8px;border:1px solid #334155;
background:#0f172a;color:var(--fg);font-size:1rem}
#toc{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
#toc a{color:var(--amber);text-decoration:none;font-size:.8rem;border:1px solid
#334155;border-radius:99px;padding:2px 10px}
section{padding:8px 16px}section h2{color:var(--amber);font-size:1rem;
border-bottom:1px solid #1e293b;padding-bottom:4px}
.meta{color:var(--dim);font-size:.75rem}
.card{border:1px solid #1e293b;border-radius:10px;padding:12px;margin:10px 0;
background:#0f172a}
.card img{max-width:90px;max-height:90px;border-radius:6px;margin:4px 6px 0 0;
cursor:zoom-in;vertical-align:top}
pre{white-space:pre-wrap;word-break:break-word;font:inherit;margin:8px 0}
button{background:var(--amber);color:#000;border:0;border-radius:8px;
padding:6px 14px;font-weight:600;cursor:pointer;margin-right:6px}
button.ghost{background:transparent;color:var(--amber);border:1px solid var(--amber)}
button:active{transform:scale(.97)}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.9);display:none;
align-items:center;justify-content:center;z-index:99;cursor:zoom-out}
#lb img{max-width:96vw;max-height:96vh}
#modal{position:fixed;inset:0;background:rgba(0,0,0,.7);display:none;z-index:98;
align-items:center;justify-content:center}
#modal textarea{width:92vw;height:60vh;background:#fff;color:#000;padding:12px;
font:15px/1.5 monospace;border-radius:8px}
</style></head><body>
<header><h1>__TITLE__</h1>
<input id="q" placeholder="Search… (__COUNT__ items)" autocomplete="off">
<div id="toc"></div></header>
<div id="sections"></div>
<div id="lb" onclick="this.style.display='none'"><img></div>
<div id="modal" onclick="if(event.target===this)this.style.display='none'">
<textarea id="mtext" readonly></textarea></div>
<script>
const DATA=__DATA__;
const NL=String.fromCharCode(10,10)+'---'+String.fromCharCode(10,10);
const bySec=id=>DATA.sections.find(x=>x.id===id);
const byItem=(sid,iid)=>bySec(sid).items.find(x=>x.id===iid);
function copyText(t,btn){navigator.clipboard.writeText(t).then(()=>{
  const o=btn.textContent;btn.textContent='Copied!';
  setTimeout(()=>btn.textContent=o,1200);});}
function copyItem(sid,iid,btn){copyText(byItem(sid,iid).text,btn);}
function copySection(sid,btn){copyText(bySec(sid).items.map(i=>i.text).join(NL),btn);}
function showText(t){const m=document.getElementById('modal');
  document.getElementById('mtext').value=t;m.style.display='flex';
  document.getElementById('mtext').select();}
function lbImg(src){const l=document.getElementById('lb');
  l.querySelector('img').src=src;l.style.display='flex';}
function esc(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function render(q){q=(q||'').toLowerCase();const root=document.getElementById('sections');
  root.innerHTML='';const toc=document.getElementById('toc');toc.innerHTML='';
  let shown=0;
  for(const sec of DATA.sections){
    const items=sec.items.filter(i=>!q||i.text.toLowerCase().includes(q)||sec.name.toLowerCase().includes(q));
    if(!items.length)continue;shown+=items.length;
    const s=document.createElement('section');s.id=sec.id;
    const srcPages=[...new Set(items.map(i=>i.source))].join(', ');
    s.innerHTML='<h2>'+esc(sec.name)+' <span class="meta">('+items.length+')</span></h2>'
      +'<div class="meta">'+esc(srcPages)+'</div>'
      +'<button class="ghost" onclick="copySection(this.dataset.s,this)" data-s="'+sec.id+'">Copy all in section</button>';
    for(const it of items){
      const d=document.createElement('div');d.className='card';
      d.innerHTML='<div class="meta">'+esc(it.id)+' &middot; '+esc(it.source)+'</div><pre>'+esc(it.text)+'</pre>'
        +'<button onclick="copyItem(this.dataset.s,this.dataset.i,this)" data-s="'+sec.id+'" data-i="'+it.id+'">Copy</button>'
        +'<button class="ghost" onclick="showText(byItem(this.dataset.s,this.dataset.i).text)" data-s="'+sec.id+'" data-i="'+it.id+'">Select text</button>'
        +(it.images||[]).map(im=>'<img loading="lazy" src="'+esc(im)+'" onclick="lbImg(this.src)">').join('');
      s.appendChild(d);}
    root.appendChild(s);
    const a=document.createElement('a');a.href='#'+sec.id;a.textContent=sec.name+' ('+items.length+')';toc.appendChild(a);}
  if(!shown)root.innerHTML='<p style="padding:24px" class="meta">No matches.</p>';}
document.getElementById('q').addEventListener('input',e=>render(e.target.value));
render('');
</script></body></html>"""


def esc(s):
    return html.escape(s, quote=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Master Library")
    ap.add_argument("--banned-words", default="",
                    help="comma list; run a compliance grep on rendered text, fail if any hit")
    args = ap.parse_args()

    items = json.load(open(args.json, encoding="utf-8"))
    sections, order = {}, []
    for it in items:
        s = it.get("section") or "Unsorted"
        if s not in sections:
            sections[s] = []
            order.append(s)
        sections[s].append(it)

    def sid(s):
        return "sec" + re.sub(r"\W+", "-", s.lower())[:30]

    data = {"sections": [{"id": sid(s), "name": s, "items": sections[s]} for s in order]}

    if args.banned_words:
        blob = json.dumps(data).lower()
        hits = [w for w in args.banned_words.split(",") if w.strip() and w.strip().lower() in blob]
        if hits:
            sys.exit(f"COMPLIANCE FAIL — banned words found in rendered text: {hits}")
        print(f"compliance: 0 hits for banned words [{args.banned_words}]")

    doc = (PAGE.replace("__TITLE__", esc(args.title))
               .replace("__COUNT__", str(len(items)))
               .replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    open(args.out, "w", encoding="utf-8").write(doc)
    print(f"rendered {len(items)} items in {len(order)} sections -> {args.out}")


if __name__ == "__main__":
    main()
