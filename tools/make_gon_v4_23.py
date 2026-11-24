"""Gọn v4.3 = Gọn v4.2 + Đợt 1 "tách theo quốc gia":
 - Thanh chọn quốc gia dùng chung (Tất cả/US/CAN/AUS) dưới thanh tab: đổi các bộ lọc quốc gia sẵn có (SKU & P&L, Tồn kho, Long-term Storage, So với kỳ trước, Phân rã nhóm) và bảng Top 10 SKU.
 - Tổng quan: 3 thẻ tóm tắt theo quốc gia (doanh thu, %FC, so tuần trước, Profit PL5, QC/TACoS, tồn kho, vấn đề + hướng xử lý).
 - SKU & P&L: bảng Profit PL5 theo quốc gia × sàn (có tổng từng quốc gia), đứng trước bảng theo SKU.
Chạy: python tools/make_gon_v4_23.py <gon-v4-2.html> <file ra>. Không đổi dữ liệu."""
import os, sys
s = open(sys.argv[1], encoding="utf-8").read()
here = os.path.dirname(os.path.abspath(__file__))

def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:70], s.count(a))
    s = s.replace(a, b)

CSS = '''<style>
.ctyseg{display:inline-flex;align-items:center;gap:2px;padding:3px;margin-right:10px;border:1px solid var(--line);border-radius:10px;background:var(--card,#fff);vertical-align:middle}
.ctyseg .pick{border:0;background:transparent;border-radius:7px;padding:6px 12px;font-size:13px;font-weight:600;color:var(--muted);cursor:pointer;line-height:1.2}
.ctyseg .pick:hover{color:var(--ink,inherit)}.ctyseg .pick[aria-pressed="true"]{background:var(--accent);color:#fff}
.ctyseg{flex-direction:row!important;flex-wrap:nowrap}.ctyseg .pick{display:inline-block;width:auto;margin:0;white-space:nowrap}
#mmeta:has(>.ctyseg){display:flex;flex-direction:row;align-items:center;flex-wrap:nowrap;gap:10px}#mmeta>.ctyseg{margin-right:0}
.ctyseg.alone{margin:0 0 0 auto}.shead:has(>.ctyseg){display:flex;align-items:center;flex-wrap:wrap;gap:8px}
body.brief .ctyseg{display:none}
.ctysum{display:grid;gap:14px;grid-template-columns:repeat(3,minmax(0,1fr));margin-bottom:6px}
.ctyc{appearance:none;text-align:left;font:inherit;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;cursor:pointer;display:flex;flex-direction:column;gap:6px;transition:border-color .18s,box-shadow .18s}
.ctyc:hover{border-color:var(--accent)}.ctyc.on{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent) inset}
.ctyc .ch{display:flex;justify-content:space-between;align-items:baseline;gap:8px}.ctyc .ch b{font-size:15px;letter-spacing:.04em}.ctyc .ch span{font-size:11.5px;color:var(--muted)}
.ctyc .cv{font-size:28px;font-weight:700;line-height:1.1}.ctyc .cs{font-size:12.5px;color:var(--ink-2)}
.ctyc .cg{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:12.5px;margin-top:4px;padding-top:8px;border-top:1px solid var(--line)}.ctyc .cg span{color:var(--muted)}.ctyc .cg b{text-align:right}.ctyc small{font-weight:400;color:var(--muted)}
.ctyc .ci{font-size:12.5px;line-height:1.55;color:var(--ink-2);margin-top:6px;padding-top:8px;border-top:1px solid var(--line)}
#tbl-plmc tr.sub td{font-weight:600;background:var(--card2,rgba(127,127,127,.07))}
@media(max-width:1000px){.ctysum{grid-template-columns:minmax(0,1fr)}}
</style>
'''

# thanh quốc gia: ngay sau thanh tab
rep('</div></nav>\n<style>', '</div></nav>\n' + CSS + '<style>')   # thanh quốc gia được JS chèn đầu .wrap (không đụng chuỗi neo của patch pro)

# Tổng quan: thẻ theo quốc gia, đứng trước "Ma trận sàn × thị trường"
rep('''<section>
    <div class="shead"><span class="snum">03</span><h2>Ma trận sàn × thị trường</h2>''',
    '''<section>
    <div class="shead"><span class="snum">02b</span><h2>Tóm tắt theo quốc gia</h2><span class="hint">doanh thu · FC · Profit PL5 · quảng cáo · tồn kho · vấn đề chính</span></div>
    <div class="ctysum" id="ctysum"></div>
    <details class="capfold"><summary>Chú thích</summary><p class="cap" id="ctysumcap"></p></details>
  </section>

<section>
    <div class="shead"><span class="snum">03</span><h2>Ma trận sàn × thị trường</h2>''')

# FC cả năm: chèn cạnh bảng PL5 quốc gia (sau đó JS chuyển về trước "Ma trận sàn × thị trường" ở tab Doanh thu & Kế hoạch)
FCSEC = '''<section id="fcyr-sec">
    <div class="shead"><span class="snum">FC</span><h2>FC cả năm 2026 — thực tế so với FC</h2><span class="hint">theo tháng · quý · quốc gia</span></div>
    <div id="fcyr"></div>
    <details class="capfold"><summary>Chú thích</summary><p class="cap" id="fcyrcap"></p></details>
  </section>

'''
rep('''<section>
    <div class="shead"><span class="snum">02</span><h2>P&amp;L PL5 — khung tính lợi nhuận theo SKU</h2>''', FCSEC + '''<section>
    <div class="shead"><span class="snum">02</span><h2>P&amp;L PL5 — khung tính lợi nhuận theo SKU</h2>''')

# SKU & P&L: bảng Profit PL5 theo quốc gia × sàn, trước bảng theo SKU
rep('''<section>
    <div class="shead"><span class="snum">02</span><h2>P&amp;L PL5 — khung tính lợi nhuận theo SKU</h2>''',
    '''<section id="plmc-sec">
    <div class="shead"><span class="snum">01b</span><h2>Profit PL5 theo quốc gia × sàn</h2><span class="hint">bảng tổng trước khi xuống từng SKU</span></div>
    <div class="scroll"><table id="tbl-plmc">
      <thead><tr><th>Quốc gia</th><th>Sàn</th><th>Doanh thu</th><th>COGS</th><th>Ref. Fee</th><th>SEM Fee</th><th>Warehouse Fee</th><th>Phí fulfillment</th><th>Profit PL5</th><th>Biên</th><th>SL</th><th>Giá &lt; COGS</th></tr></thead>
      <tbody></tbody><tfoot></tfoot>
    </table></div>
    <details class="capfold"><summary>Chú thích</summary><p class="cap" id="plmccap"></p></details>
  </section>

<section>
    <div class="shead"><span class="snum">02</span><h2>P&amp;L PL5 — khung tính lợi nhuận theo SKU</h2>''')

# script: ngay trước </body> cuối
i = s.rindex("</script>")      # mẫu là mảnh HTML (không có </body>): chèn vào cuối script cuối; patch pro.js được nối sau
s = s[:i] + "\n" + open(os.path.join(here, "p23", "cview.js"), encoding="utf-8").read() + "\n" + open(os.path.join(here, "p23", "cty.js"), encoding="utf-8").read() + "\n" + open(os.path.join(here, "p23", "fc.js"), encoding="utf-8").read() + "\n" + s[i:]
open(sys.argv[2], "w", encoding="utf-8").write(s)
print("built", len(s))
