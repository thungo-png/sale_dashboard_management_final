#!/usr/bin/env python3
"""Gọn v2.2 = Gọn v2.1 + menu dọc bên trái thu gọn/mở rộng khi rê chuột (thay thanh tab ngang), bỏ nút "Bản tóm tắt". Không đổi id/data-p của tab, không đụng `const D`.
Dùng: python3 make_gon_v2_2.py <gon_v2_1.html> <ra.html>"""
import re, sys
SRC, DST = sys.argv[1], sys.argv[2]
t = open(SRC, encoding="utf-8").read()
def once(pat, flags=0):
    m = list(re.finditer(pat, t, flags)); assert len(m) == 1, (pat, len(m)); return m[0]
d_before = [l for l in t.split("\n") if l.startswith("const D = ")]

def ic(path):  # icon nét mảnh 24x24 -> data URI để tô bằng currentColor (mask)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.8" '
           'stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>')
    return "url(\"data:image/svg+xml;utf8," + svg.replace('"', "'").replace("<", "%3C").replace(">", "%3E").replace("#", "%23") + "\")"
ICONS = {
 "ov":  '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
 "gr":  '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
 "mg":  '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
 "dt":  '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 4v16"/>',
 "cp":  '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
 "inv": '<path d="M3 8l9-5 9 5v12H3z"/><path d="M8 20v-7h8v7"/>',
 "bb":  '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.3"/>',
}
css_icons = "".join(f'.tab[data-p="{k}"]::before{{-webkit-mask-image:{ic(v)};mask-image:{ic(v)}}}\n' for k, v in ICONS.items())

CSS = """<style>
/* ===== Gọn v2.2: menu dọc bên trái (thay thanh tab ngang) ===== */
:root{--sbw:70px;--sbw-open:244px;--sb-bg:#0c2461;--sb-bg2:#0a1d52;--sb-ink:#e6ecff;--sb-mut:#8fa3d6;--sb-act:#2f62f0}
body{padding-left:var(--sbw)}
.tabbar{position:fixed!important;left:0;top:0;bottom:0;width:var(--sbw);margin:0!important;z-index:40;background:linear-gradient(180deg,var(--sb-bg),var(--sb-bg2))!important;
  backdrop-filter:none!important;border:0!important;border-right:1px solid rgba(255,255,255,.06)!important;display:flex;flex-direction:column;overflow-y:auto;overflow-x:hidden;
  transition:width .22s cubic-bezier(.4,0,.2,1),box-shadow .22s;scrollbar-width:none}
.tabbar::-webkit-scrollbar{display:none}
.tabbar:hover,.tabbar:has(:focus-visible){width:var(--sbw-open);box-shadow:8px 0 32px rgba(8,20,60,.35)}
.tabbar .tabwrap{display:flex;flex-direction:column;flex:1;min-height:0;max-width:none;padding:0;width:100%}
.tabbar .tabarrow,.tabbar .tabfade{display:none!important}
.sbbrand{display:flex;align-items:center;gap:12px;padding:20px 16px 18px;color:#fff;font-weight:700;font-size:16px;letter-spacing:.01em;white-space:nowrap}
.sbbrand .lg{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#3b74ff,#2250d8);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;box-shadow:0 6px 16px rgba(34,80,216,.45);flex:none}
.sbbrand .tx{opacity:0;transition:opacity .15s}
.sbbrand small{display:block;font-weight:500;font-size:11px;color:var(--sb-mut);margin-top:1px;letter-spacing:0}
.tabbar .tabinner{display:flex!important;flex-direction:column;align-items:stretch;gap:3px;padding:6px 11px 18px!important;overflow:visible!important;width:auto}
.tabbar .tabgrp{align-self:stretch;margin:14px 10px 5px;font-size:9.5px;letter-spacing:.14em;color:transparent;white-space:nowrap;transition:color .15s;position:relative;overflow:hidden}
.tabbar .tabgrp::after{content:"";position:absolute;left:0;right:0;top:50%;height:1px;background:rgba(255,255,255,.16);opacity:1;transition:opacity .15s}
.tabbar:hover .tabgrp::after,.tabbar:has(:focus-visible) .tabgrp::after{opacity:0}
.tabbar .tabgrp:first-child{margin-top:4px}
.tabbar .tabdiv{display:none}
.tabbar .tab{display:flex;align-items:center;gap:13px;width:100%;text-align:left;padding:11px 14px;border-radius:11px;font-size:13.5px;font-weight:500;color:var(--sb-ink);background:none;white-space:nowrap;line-height:1.25;overflow:hidden;transition:background .18s,color .12s}
.tabbar:hover .tabgrp,.tabbar:has(:focus-visible) .tabgrp{color:var(--sb-mut);transition-delay:.08s}
.tabbar:hover .sbbrand .tx,.tabbar:has(:focus-visible) .sbbrand .tx{opacity:1;transition-delay:.08s}
.tabbar .tab::before{content:"";width:19px;height:19px;flex:none;background:var(--ic,#e6ecff);opacity:.85;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-position:center;mask-position:center;-webkit-mask-size:contain;mask-size:contain}
.tabbar .tab::after{display:none!important}
.tabbar:not(:hover):not(:has(:focus-visible)) .tab{color:transparent}
.tabbar .tab:hover{background:rgba(255,255,255,.08);color:#fff}
.tabbar .tab[aria-selected="true"]{--ic:#fff;background:var(--sb-act);color:#fff;font-weight:600;box-shadow:0 6px 16px rgba(47,98,240,.4)}
.tabbar .tab[aria-selected="true"]::before{opacity:1}
.tabbar .tab:focus-visible{outline:2px solid #9db8ff;outline-offset:1px}
""" + css_icons + """
.wrap{max-width:1240px}
body.brief{padding-left:0}
@media(max-width:900px){
  body{padding-left:0}
  .tabbar{position:sticky!important;top:0;bottom:auto;width:100%!important;max-width:100vw;overflow:visible;flex-direction:row}
  .tabbar .tabwrap{flex-direction:row;width:100%;min-width:0}
  .sbbrand{display:none}
  table.matrix{display:block;max-width:100%;overflow-x:auto}
  .tabbar .tabinner{flex-direction:row;overflow-x:auto!important;min-width:0;width:100%;padding:8px 10px!important;gap:4px;scrollbar-width:none}
  .tabbar .tabinner::-webkit-scrollbar{display:none}
  .tabbar .tabgrp{display:none}
  .tabbar .tab{color:var(--sb-ink)!important}.tabbar .tab[aria-selected="true"]{color:#fff!important}
  .tabbar .tabwrap{width:100%}
  .tabbar .tab{width:auto;flex:none;white-space:nowrap;padding:9px 13px;gap:8px;font-size:13px}
  .tabbar .tab::before{width:16px;height:16px}
}
@media print{body{padding-left:0}}
</style>
"""
brand = ('<div class="sbbrand"><span class="lg">SR</span><span class="tx">Sale Report<small>Báo cáo bán hàng đa sàn</small></span></div>')
m = once(r'<div class="tabwrap">\n'); t = t[:m.end()] + brand + "\n" + t[m.end():]
m = once(r'</nav>\n'); t = t[:m.end()] + CSS + t[m.end():]
m = once(r'Mẫu Gọn v2</div>'); t = t[:m.start()] + "Mẫu Gọn v2.2</div>" + t[m.end():]
m = once(r'[ \t]*<div class="mastact">.*?</div>\n'); t = t[:m.start()] + t[m.end():]      # bỏ nút "Bản tóm tắt" (tóm tắt để gửi vẫn có ở thanh công cụ nổi)
m = once(r'document\.getElementById\("briefbtn"\)\.addEventListener\('); t = t[:m.start()] + 'const _bb=document.getElementById("briefbtn");if(_bb)_bb.addEventListener(' + t[m.end():]
assert [l for l in t.split("\n") if l.startswith("const D = ")] == d_before
open(DST, "w", encoding="utf-8").write(t); print("OK", DST, len(t) // 1024, "KB")
