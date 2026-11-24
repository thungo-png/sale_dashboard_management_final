"""Gọn v4 – chỉnh nhỏ: gọn khối kỳ/thời gian ở đầu report, ẩn mục "Cách đọc báo cáo".
   Dùng: python3 make_gon_v4_2.py vào.html ra.html   (không đụng dòng const D, không xoá id nào)"""
import sys,re
s=open(sys.argv[1],encoding="utf-8").read()
dl=[l for l in s.split("\n") if l.startswith("const D = ")]
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:60]); s=s.replace(a,b)
# 1) khối kỳ / thời gian: 5 chip một hàng thay cho 6 cột có nhãn
i=s.index('document.getElementById("mmeta").innerHTML=`'); j=s.index('`;',i)+2
new='''document.getElementById("mmeta").innerHTML=`
 <span class="mchip m1" title="Kỳ báo cáo: tuần Chủ Nhật–Thứ Bảy, đã đủ 7 ngày"><b>W${D.meta.week_no}</b> ${D.meta.d0.split("-").reverse().slice(0,2).join("/")} – ${D.meta.d1.split("-").reverse().join("/")}</span>
 <span class="mchip" title="Lũy kế từ đầu năm">Lũy kế ${D.meta.ytd0.split("-").reverse().slice(0,2).join("/")} – ${D.meta.ytd1.split("-").reverse().slice(0,2).join("/")} · ${D.meta.months.length} tháng</span>
 <span class="mchip" title="Sàn bán hàng">${MP.join(" · ")}</span>
 <span class="mchip" title="Thị trường">${CO.join(" · ")}</span>
 <span class="mchip" title="Phạm vi: danh mục Thu Ngo, số SKU có bán trong tuần">Thu Ngo · ${GR.length} nhóm · ${D.meta.nsku} SKU</span>`;'''
s=s[:i]+new+s[j:]
rep1('.xc{}\n','.xc{}\n.meta{display:flex;flex-wrap:wrap;gap:6px 8px;margin-top:10px}.meta .mchip{display:inline-flex;align-items:center;gap:6px;padding:4px 11px;border:1px solid var(--line);border-radius:999px;background:var(--card);font-size:12.5px;font-weight:500;color:var(--ink-2,var(--ink));white-space:nowrap}.meta .mchip.m1{background:color-mix(in srgb,var(--accent) 9%,var(--card));border-color:color-mix(in srgb,var(--accent) 35%,var(--line));color:var(--ink)}.meta .mchip b{font-weight:700}@media(max-width:560px){.meta .mchip{white-space:normal}}\n')
# 2) ẩn "Cách đọc báo cáo" (giữ phần tử để script cũ không lỗi)
rep1('<section class="bh">\n    <details class="howto">','<section class="bh" hidden style="display:none!important">\n    <details class="howto">')
assert [l for l in s.split("\n") if l.startswith("const D = ")]==dl
open(sys.argv[2],"w",encoding="utf-8").write(s)
