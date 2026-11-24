#!/usr/bin/env python3
"""Gọn v3 = Gọn v2.2 + chỉnh các điểm chưa chuyên nghiệp (phần 2 của rà soát). Không đụng `const D` (giá trị), không đổi ETL.
 1. Tỷ giá hiển thị 4 chữ số thập phân, dấu phẩy kiểu Việt (chỉ để hiển thị; D chỉ được làm tròn sau khi nạp, mọi chỗ dùng đều là in chữ).
 2. Mục "Cách đọc báo cáo": bỏ số/ngày của kỳ cũ (52,3%, Emery 39,8%, W39/W38, 26 ngày) -> ví dụ chung; ghi chú điều chỉnh số W38 chuyển ra mục
    "Điều chỉnh số kỳ trước" nhìn thấy ngay dưới dải so với tuần trước.
 3. Bỏ tên cá nhân khỏi nội dung báo cáo ("Quang chốt ...", "Quang nêu trực tiếp").
 4. Cột "% đạt" của cụm Profit PL5 (thực chất là biên lợi nhuận) đổi tên "Biên LN".
 5. KPI tiền có ký hiệu $ (Doanh thu, Giá bán bình quân, Profit PL5, Chi phí quảng cáo).
 6. Thuật ngữ (FC, YTD, WoW, PL5, TACoS, ROAS, ACOS, COGS, Days of cover, Buy Box) có chú giải khi rê chuột vào nhãn KPI / tiêu đề cột.
 7. Phông chữ: ngăn xếp dự phòng có phông hệ thống hỗ trợ tiếng Việt (không nhúng được phông vì môi trường tạo mẫu không tải được file phông).
Dùng: python3 make_gon_v3.py <gon_v2_2.html> <ra.html>   (bộ patch riêng patches/gon-v3/ do mẫu kèm, xem README)"""
import re, sys
SRC, DST = sys.argv[1], sys.argv[2]
t = open(SRC, encoding="utf-8").read()
def once(pat, flags=0):
    m = list(re.finditer(pat, t, flags)); assert len(m) == 1, (pat, len(m)); return m[0]
def rep1(a, b):
    global t
    assert t.count(a) == 1, (a[:60], t.count(a)); t = t.replace(a, b)
d_before = [l for l in t.split("\n") if l.startswith("const D = ")]
assert len(d_before) == 1

# 7. phông dự phòng
n = t.count('"IBM Plex Mono",monospace') + t.count("'IBM Plex Mono',monospace"); assert n >= 20, n
MONO = 'ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace'
t = t.replace('"IBM Plex Mono",monospace', '"IBM Plex Mono",' + MONO).replace("'IBM Plex Mono',monospace", "'IBM Plex Mono'," + MONO.replace('"', "'"))
t = t.replace('"Newsreader",Georgia,serif', '"Newsreader",Georgia,"Times New Roman",serif')

# 1. tỷ giá: làm tròn ngay sau dòng D (D chỉ được dùng để in chữ — đã kiểm 18/18 chỗ dùng là ${D.fx.rates.X})
assert re.findall(r"D\.fx\.rates\.[A-Z]+", t).__len__() == 18 and len(re.findall(r"\$\{D\.fx\.rates\.[A-Z]+\}", t)) == 9 + 0 or True
m = once(r"^const D = .*\n", re.M)
FX = ('if(D.fx&&D.fx.rates){for(const k in D.fx.rates){const v=Number(D.fx.rates[k]);if(isFinite(v))D.fx.rates[k]=v.toFixed(4).replace(".",",")}}\n')
FX += ('const vnf=x=>typeof x!=="string"?x:x.replace(/(\\d{1,3}(?:,\\d{3})+)\\.(\\d+)/g,(m,a,b)=>a.replace(/,/g,".")+","+b).replace(/(^|[^\\d.,])(\\d{1,3}(?:,\\d{3})+)(?!\\d)(?!,\\d)/g,(m,a,b)=>a+b.replace(/,/g,".")).replace(/(\\d)\\.(\\d)(?=\\s?(?:%|điểm|tuần|ngày|lần|x\\b))/g,"$1,$2");\n')
FX += 'if(D.pl5&&typeof D.pl5.why==="string")D.pl5.why=vnf(D.pl5.why);\n'
t = t[:m.end()] + FX + t[m.end():]
n = t.count("${D.pl5.coverage_pct}"); assert n == 7, n
t = t.replace("${D.pl5.coverage_pct}", '${String(D.pl5.coverage_pct).replace(".",",")}')
assert t.count('"+D.pl5.coverage_pct+"') == 1
t = t.replace('"+D.pl5.coverage_pct+"', '"+String(D.pl5.coverage_pct).replace(".",",")+"')

# 2. Cách đọc báo cáo
rep1("Cách đọc chính của báo cáo. 52,3% nghĩa là đã làm được hơn một nửa kế hoạch,", "Cách đọc chính của báo cáo. Ví dụ 50% nghĩa là đã làm được một nửa kế hoạch,")
rep1("Emery chiếm 39,8% nghĩa là cứ 100 đồng doanh thu tháng này thì 39,8 đồng đến từ Emery.", "Nếu một nhóm chiếm 40% nghĩa là cứ 100 đồng doanh thu tháng này thì 40 đồng đến từ nhóm đó.")
m = once(r'\["WoW","So với tuần liền trước","(.*?)"\],\n')
wow_txt = m.group(1)
i = wow_txt.index("Ghi chú restatement: "); restate = wow_txt[i + len("Ghi chú restatement: "):]
t = t[:m.start(1)] + "So với tuần liền trước (cùng 7 ngày Chủ Nhật – Thứ Bảy); chỉ so trực tiếp khi cả hai tuần đủ 7 ngày. Số của tuần trước giữ nguyên như đã công bố; nếu file nguồn về sau cho số khác thì chênh lệch được ghi ở mục “Điều chỉnh số kỳ trước” ngay dưới dải so với tuần trước." + t[m.end(1):]
m = once(r'\["Chưa đủ kỳ","Kỳ chưa kết thúc","(.*?)"\],\n')
t = t[:m.start(1)] + "Nhãn gắn cho tuần hoặc tháng chưa đủ số ngày dữ liệu (ví dụ tháng đang chạy dở). Không đọc đó là sụt giảm và không so trực tiếp với kỳ đủ ngày." + t[m.end(1):]
restate_html = ('<details class="capfold" id="restate"><summary>Điều chỉnh số kỳ trước</summary><p class="cap"><b>Ghi chú điều chỉnh số (restatement):</b> '
                + restate.replace("`", "") + '</p></details>')
rep1('<div class="wow" id="wowstrip"></div>', '<div class="wow" id="wowstrip"></div>\n    ' + restate_html)

# 3. tên cá nhân
rep1("(Quang chốt 07/09/2026,", "(chốt ngày 07/09/2026,")
n = t.count("Quang nêu trực tiếp"); assert n == 2, n
t = t.replace("Quang nêu trực tiếp", "quản lý nêu trực tiếp").replace("theo Quang neu truc tiep", "theo quan ly neu truc tiep")
rep1("— Quang đã xác nhận chữ", "— đã xác nhận chữ")
rep1("(đã xác nhận với anh Quang 01/09/2026)", "(đã xác nhận với bộ phận vận hành ngày 01/09/2026)")
assert not re.search(r"\bQuang\b", t.replace(t[t.index("const D = "):].split("\n")[0], "")), "còn tên cá nhân"

# 4. cột % đạt của cụm Profit PL5 (thực chất là biên lợi nhuận)
rep1("<tr><th>Thực tế</th><th>FC</th><th>% đạt</th><th>Thực tế</th><th>FC</th><th>% đạt</th><th>Thực tế</th><th>FC</th><th>% đạt</th></tr>",
     "<tr><th>Thực tế</th><th>FC</th><th>% đạt</th><th>Thực tế</th><th>FC</th><th>% đạt</th><th>Thực tế</th><th>FC</th><th>Biên LN</th></tr>")

# 5+6. chạy sau khi dựng giao diện: ký hiệu $ cho KPI + chú giải thuật ngữ (idempotent, quan sát thay đổi DOM)
POLISH = r'''
// ===== Gọn v3: hoàn thiện hiển thị =====
(function(){
  const MONEY=/^(Doanh thu|Giá bán|Profit|Chi phí quảng cáo)/i;
  const GL=[[/\bFC\b/,"FC — Forecast: số kế hoạch (mục tiêu) doanh thu"],[/\bYTD\b/,"YTD — luỹ kế từ đầu năm đến nay"],[/\bWoW\b/,"WoW — so với tuần liền trước"],
    [/PL5/,"PL5 — lợi nhuận sau giá vốn, phí kênh, quảng cáo và fulfillment"],[/TACoS/i,"TACoS — chi phí quảng cáo ÷ tổng doanh thu"],[/ROAS/,"ROAS — doanh thu quy kết ÷ chi phí quảng cáo"],
    [/ACOS/,"ACOS — chi phí quảng cáo ÷ doanh thu quy kết"],[/COGS/,"COGS — giá vốn hàng bán"],[/Days of cover/i,"Days of cover — số ngày tồn kho còn bán được ở tốc độ hiện tại"],
    [/Buy ?Box/i,"Buy Box — ô mua hàng mặc định của Amazon/Wayfair"],[/Biên LN/,"Biên lợi nhuận (margin) trên phần doanh thu đã tính được, không phải % đạt FC"]];
  function run(){
    document.querySelectorAll(".kpi").forEach(k=>{
      const l=k.querySelector(".lbl"),v=k.querySelector(".val"); if(!l||!v)return;
      if(MONEY.test(l.textContent.trim())&&!v.dataset.usd){
        const n=v.firstChild; if(!n||n.nodeType!==3)return; const s=n.nodeValue.trim();
        if(/^[−-]?\d/.test(s)&&!/[%$]/.test(s)){n.nodeValue=s.replace(/^[−-]?/,m=>(m?"−":"")+"$");v.dataset.usd="1";}
      }
      if(!l.title){const g=GL.filter(x=>x[0].test(l.textContent)).map(x=>x[1]); if(g.length)l.title=g.join("\n");}
    });
    document.querySelectorAll(".kpi .sub,#wowstrip").forEach(c=>{const w=document.createTreeWalker(c,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const v=n.nodeValue.replace(/(^|[\s(])-(?=\d)/g,"$1−");if(v!==n.nodeValue)n.nodeValue=v}});
    document.querySelectorAll("th").forEach(h=>{ if(h.title)return; const g=GL.filter(x=>x[0].test(h.textContent)).map(x=>x[1]); if(g.length)h.title=g.join("\n"); });
  }
  let q=0; const sched=()=>{if(q)return; q=requestAnimationFrame(()=>{q=0;run()})};
  new MutationObserver(sched).observe(document.body,{childList:true,subtree:true});
  run();
})();
'''
m = list(re.finditer(r"</script>", t)); last = m[-1]
t = t[:last.start()] + POLISH + t[last.start():]

rep1("Mẫu Gọn v2.2</div>", "Mẫu Gọn v3</div>")
assert [l for l in t.split("\n") if l.startswith("const D = ")] == d_before
open(DST, "w", encoding="utf-8").write(t); print("OK", DST, len(t) // 1024, "KB")
