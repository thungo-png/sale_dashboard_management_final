"""Gọn v4.1: Profit PL5 theo khoảng thời gian — thẻ KPI Tổng quan và 4 biểu đồ xu hướng (Tổng quan 03, Nhóm SP 02/03, SKU 02) đọc D.pl5ts.
Chạy: python tools/make_gon_v4_21.py <gon-v4-f20a98.html> <file ra>. Không đổi dữ liệu nào khác; không có pl5ts thì hành vi như Gọn v4."""
import os, sys
s = open(sys.argv[1], encoding="utf-8").read()
here = os.path.dirname(os.path.abspath(__file__))

def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:70], s.count(a))
    s = s.replace(a, b)

# 1) metricVal hiểu PL5
rep('function metricVal(rec,k){\n  if(!rec) return 0;\n  if(k==="q") return rec.q;',
    'function metricVal(rec,k){\n  if(!rec) return 0;\n  if(k==="pl5") return rec.p||0;\n  if(k==="q") return rec.q;')

# 2) pl5Panel mới (có đọc pl5ts); các hàm trợ giúp đặt ngay trước nó
i = s.index("function pl5Panel(hostId,capId){")
tail = '  const c=document.getElementById(capId); if(c) c.innerHTML="";\n}\n'
j = s.index(tail, i) + len(tail)
s = s[:i] + open(os.path.join(here, "p21", "pl5ts.js"), encoding="utf-8").read() + s[j:]

# 3) bốn biểu đồ
rep('''  if(OVM==="pl5"){pl5Panel("ovtrend","ovtrendcap");
    cap.innerHTML='<b>Profit PL5 chưa có dữ liệu</b> — biểu đồ sẽ tự lên khi bộ dữ liệu có giá vốn và phí sàn thực tế theo kênh.';
    return;}''',
    '''  if(OVM==="pl5"){pl5Panel("ovtrend","ovtrendcap",{g:OVG,fam:OVDIM,tip:"ovtrendtip",colorOf:OVDIM==="mp"?(k=>MPC[k]||"--s1"):(OVDIM==="cty"?(k=>COC[k]||"--s1"):null),what:", tách "+OVDIMS.find(d=>d.k===OVDIM).lab.toLowerCase()});
    return;}''')
rep('''  if(GRM==="pl5"){pl5Panel("grtrend","grtrendcap");
    cap.innerHTML='<b>Profit PL5 chưa có dữ liệu</b> — biểu đồ sẽ tự lên khi có giá vốn và phí sàn thực tế theo kênh.';return;}''',
    '''  if(GRM==="pl5"){pl5Panel("grtrend","grtrendcap",{g:GRG,fam:"grp",tip:"grtrendtip",colorOf:GC,mr:150,what:" của từng nhóm sản phẩm"});return;}''')
rep('''  if(GDM==="pl5"){pl5Panel("gdtrend","gdtrendcap");
    cap.innerHTML='<b>Profit PL5 chưa có dữ liệu</b> cho biểu đồ này.';return;}''',
    '''  if(GDM==="pl5"){pl5Panel("gdtrend","gdtrendcap",{g:GDG,fam:GDDIM,tip:"gdtrendtip",colorOf:GDDIM==="grp_mp"?(k=>MPC[k]||"--s1"):(k=>COC[k]||"--s1"),
      pick:all=>{const sm={};Object.keys(all).forEach(k=>{if(k.startsWith(g+" · "))sm[k.slice(g.length+3)]=all[k]});return sm},
      what:" của nhóm "+short(g)+(GDDIM==="grp_mp"?", tách theo sàn":", tách theo thị trường")});return;}''')
rep('''  if(SKM==="pl5"){pl5Panel("sktrend","sktrendcap");
    cap.innerHTML='<b>Profit PL5 chưa có dữ liệu</b> cho biểu đồ SKU.';return;}''',
    '''  if(SKM==="pl5"){pl5Panel("sktrend","sktrendcap",{g:SKG,fam:SKLV,tip:"sktrendtip",mr:150,
      pick:all=>{const sm={};Object.keys(all).forEach(k=>{if(k===SKSEL)sm["Tổng"]=all[k];else if(k.startsWith(SKSEL+" · "))sm[k.slice(SKSEL.length+3)]=all[k]});return sm},
      what:" của SKU "+(SKSEL||"—")});return;}''')

# 5) tsChart vẽ được số ÂM (Profit PL5 thường âm): trục y đi từ mốc âm đến dương, có đường 0 đậm. Khi không có số âm thì y hệt cũ.
rep("""  max=Math.max(max,1); const st=Math.pow(10,Math.floor(Math.log10(max)))/2; max=Math.ceil(max/st)*st;
  const n=labels.length,x=i=>ML+(W-ML-MR)*i/Math.max(n-1,1),y=v=>MT+(H-MT-MB)*(1-v/max);
  let o="";
  for(let g=0;g<=max+0.0001;g+=max/4){
    const lb=metricKey==="ach"?Math.round(g)+"%":(g>=1000?Math.round(g/1000)+"k":Math.round(g));""",
"""  max=Math.max(max,1); const span=Math.max(max,-min), st=Math.pow(10,Math.floor(Math.log10(span)))/2; max=Math.ceil(max/st)*st;
  const lo=min<0?-Math.ceil(-min/st)*st:0, rg=max-lo;
  const n=labels.length,x=i=>ML+(W-ML-MR)*i/Math.max(n-1,1),y=v=>MT+(H-MT-MB)*(1-(v-lo)/rg);
  let o="";
  for(let g=lo;g<=max+0.0001;g+=rg/4){
    const lb=metricKey==="ach"?Math.round(g)+"%":(Math.abs(g)>=1000?Math.round(g/1000)+"k":Math.round(g));""")
rep("""  if(metricKey==="ach"&&max>=100)
    o+=`<line x1="${ML}" x2="${W-MR}" y1="${y(100)}" y2="${y(100)}" """,
"""  if(lo<0)o+=`<line x1="${ML}" x2="${W-MR}" y1="${y(0)}" y2="${y(0)}" stroke="${css('--ink-2')}" stroke-width="1.2" opacity=".7"/>`;
  if(metricKey==="ach"&&max>=100)
    o+=`<line x1="${ML}" x2="${W-MR}" y1="${y(100)}" y2="${y(100)}" """)

# 4) thẻ KPI PL5 ở Tổng quan theo khoảng ngày đang chọn
rep('''    h+=pl?kp(IC.pct,"Profit PL5"+PW,U(pl.profit),pl.profit<0,''',
    '''    const PLR=(RG&&L&&window.__pl5r)?window.__pl5r(L,RG.a-L.length>=0?window.__FULLD.slice(RG.a-L.length,RG.a):null):null;
    h+=PLR?kp(IC.pct,"Profit PL5 · "+rngLab,U(PLR.p),PLR.p<0,
        `biên <b class="${PLR.p>=0?"up":"dn"}">${(PLR.p<0?"−":"")+pc0(Math.abs(PLR.r?PLR.p/PLR.r*100:0))}</b> · trên ${U(PLR.r)} doanh thu`
        +(PLR.prev?`<br><small><b class="${PLR.p>=PLR.prev.p?"up":"dn"}">${PLR.p>=PLR.prev.p?"↑":"↓"} ${U(Math.abs(PLR.p-PLR.prev.p))}</b> so với ${TT}</small>`:"")
        +`<br><small>chi phí QC thật · có số ${PLR.n}/${PLR.tot} ngày${PLR.n<PLR.tot?" (ngày còn lại chưa đủ file quảng cáo)":""}</small>`,
        `<div class="bar" title="Số ngày có PL5 trong khoảng chọn"><i style="width:${Math.min(PLR.n/PLR.tot*100,100)}%"></i></div>`)
    :pl?kp(IC.pct,"Profit PL5"+PW,U(pl.profit),pl.profit<0,''')
rep('''if(/^Profit PL5/.test(l))ks.insertAdjacentHTML("beforeend","<br><small>không có số theo ngày — giữ theo kỳ báo cáo</small>");''',
    '''if(/^Profit PL5 · W/.test(l))ks.insertAdjacentHTML("beforeend","<br><small>"+(D.pl5ts?"khoảng ngày chọn chưa đủ số PL5 (cần phủ ≥ 50% số ngày) — đang giữ theo kỳ báo cáo":"không có số theo ngày — giữ theo kỳ báo cáo")+"</small>");''')
open(sys.argv[2], "w", encoding="utf-8").write(s)
print("built", len(s))
