"""Gọn v4 – lần 16 (phản biện nội dung):
   A. Nhãn/ngày theo kỳ: bỏ nhãn cứng W39/W38, hạn xử lý tính từ ngày mở báo cáo (không quá hạn ngay), tồn kho tính theo BQ 4 tuần.
   B-F. Phần DOM/logic nằm ở p16/fix.js (nạp cùng thư mục).
   Dùng: python3 make_gon_v4_16.py vào.html ra.html (đã áp make_gon_v4_15). Cần server có invnorm.py (chuẩn hoá D)."""
import sys,os
here=os.path.dirname(os.path.abspath(__file__))
s=open(sys.argv[1],encoding="utf-8").read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(a[:70],s.count(a))
    s=s.replace(a,b)
# --- A1: nhãn cứng theo tuần
rep('<title>Sale Report — Tuần 2026-W39</title>','<title>Sale Report</title>')
rep('<span class="hint">tuần W39 · so tuần W38 · so với FC</span>','<span class="hint">tuần báo cáo · so tuần trước · so với FC</span>')
rep('<th>SL tuần W39</th>','<th>SL tuần báo cáo</th>')
rep('bình quân tuần W38, giữ nguyên cho W39 để số các kỳ cũ không đổi','bình quân tuần W38, giữ nguyên cho các tuần sau để số các kỳ cũ không đổi')
rep('bình quân tuần W38, giữ nguyên cho W39 (1 CAD','bình quân tuần W38, giữ nguyên cho các tuần sau (1 CAD')
# --- A2: hạn xử lý tính từ ngày mở báo cáo nếu đã qua cuối kỳ
rep('const hlab=days=>{const dt=new Date(D.meta.d1);dt.setDate(dt.getDate()+days);',
    'const hlab=days=>{const b0=new Date(D.meta.d1),t0=new Date(),dt=t0>b0?t0:b0;dt.setDate(dt.getDate()+days);')
# --- A3: tồn kho theo BQ 4 tuần (D đã chuẩn hoá ở server: invnorm.py)
rep('Tốc độ bán = SL bán tuần W39 ÷ 7 × 7 (tức chính SL bán trong tuần)','Tốc độ bán = bình quân 4 tuần gần nhất · số tuần tồn = tồn ÷ tốc độ bán · SL của tuần báo cáo ghi nhỏ bên cạnh')
rep('<th>SL bán tuần W39</th>','<th>SL bán BQ 4 tuần</th>')
old='<td>${N(x.sold_month)}</td>'
new='<td>${(Math.round((x.sold_month||0)*10)/10).toLocaleString("de-DE")}<small class="muted"> · tuần này ${N(x.sold_cur==null?x.sold_month:x.sold_cur)}</small></td>'
rep(old,new,2)
old='D.sku.forEach(x=>{const k=x.sku+"|"+x.cty; soldByCtySku[k]=(soldByCtySku[k]||0)+x.q;});'
new='if(D.invdet.avg4_cty){Object.assign(soldByCtySku,D.invdet.avg4_cty);}else D.sku.forEach(x=>{const k=x.sku+"|"+x.cty; soldByCtySku[k]=(soldByCtySku[k]||0)+x.q;});'
rep(old,new,3)
# --- F: thẻ chất lượng — nhãn đúng bản chất (phí hoàn trả / doanh thu), bỏ nhóm doanh thu quá nhỏ; sửa chính tả hiển thị tên nhóm
rep('<div class="ql">% doanh thu</div>','<div class="ql">Phí hoàn trả / doanh thu</div>')
rep('<div class="ql" style="margin:8px 0 6px">Nhóm có tỷ lệ hoàn trả cao nhất</div>','<div class="ql" style="margin:8px 0 6px">Nhóm có phí hoàn trả / doanh thu cao nhất</div>')
rep('.filter(x=>x.r>=500).sort((a,b)=>b.p-a.p).slice(0,5);','.filter(x=>x.r>=1000).sort((a,b)=>b.p-a.p).slice(0,5);')
rep('const short=g=>String(g).replace(/^Acacia - /,"")','const short=g=>String(g).replace(/Dinning/g,"Dining").replace(/^Acacia - /,"")')
# --- SKU ngưng kinh doanh: trạng thái riêng trong bảng tồn kho
rep('function invStatusOf(w,qty){\n  if(w===null)','function invStatusOf(w,qty,x){\n  if(x&&x.disc) return "Ngưng KD";\n  if(w===null)')
rep('invStatusOf(x.weeks,x.qty)','invStatusOf(x.weeks,x.qty,x)',3)
rep('const order=["Over","Health","Low","PO","Chưa bán","Hết tồn"];','const order=["Over","Health","Low","PO","Chưa bán","Hết tồn","Ngưng KD"];')
rep('const statusChip=(w,qty)=>{','const statusChip=(w,qty,x)=>{\n    if(x&&x.disc) return \'<span class="chip">ngưng KD</span>\';')
rep('${statusChip(x.weeks,x.qty)}','${statusChip(x.weeks,x.qty,x)}')
exec(open(os.path.join(here,"p16","ads.py"),encoding="utf-8").read())
js=open(os.path.join(here,"p16","fix.js"),encoding="utf-8").read()
k=s.rfind("</script>"); assert k>0; s=s[:k]+"\n"+js+"\n"+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
