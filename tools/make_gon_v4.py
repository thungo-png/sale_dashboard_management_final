#!/usr/bin/env python3
"""Gọn v4 = Gọn v3 + Tổng quan dạng bảng điều khiển (thẻ KPI có đường xu hướng nhỏ, biểu đồ vành khuyên, xu hướng 12 tuần,
top nhóm, hiệu quả quảng cáo, cảnh báo). Chỉ đọc dữ liệu có sẵn trong D và window.__PRO; không đụng `const D`, ETL, các id cũ.
Hàng KPI cũ (#ovkpi) và dải so với tuần trước (#wowstrip) vẫn được dựng nhưng ẩn, vì bảng điều khiển đã có thông tin tương đương.
Dùng: python3 make_gon_v4.py <gon_v3.html> <ra.html>"""
import re, sys
SRC, DST = sys.argv[1], sys.argv[2]
t = open(SRC, encoding="utf-8").read()
def rep1(a, b):
    global t
    assert t.count(a) == 1, (a[:70], t.count(a)); t = t.replace(a, b)
d_before = [l for l in t.split("\n") if l.startswith("const D = ")]
assert len(d_before) == 1

CSS = r'''<style>
/* ===== Gọn v4: Tổng quan dạng bảng điều khiển ===== */
#ovkpi,#wowstrip{display:none!important}
.dash{display:grid;gap:14px;margin:4px 0 16px}
.dash .row{display:grid;gap:14px}
.dash .r1{grid-template-columns:repeat(5,minmax(0,1fr))}
.dash .r2{grid-template-columns:minmax(0,1fr) minmax(0,1.55fr) minmax(0,1fr)}
.dash .r3{grid-template-columns:minmax(0,1fr) minmax(0,1.3fr) minmax(0,1fr)}
.dc{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow);min-width:0;display:flex;flex-direction:column}
.dc h3{margin:0 0 12px;font:700 12.5px/1.2 "Public Sans",system-ui,sans-serif;letter-spacing:.04em;text-transform:uppercase;color:var(--ink);display:flex;align-items:center;justify-content:space-between;gap:8px}
.dc h3 .pk{display:inline-flex;gap:4px;text-transform:none;letter-spacing:0;font-weight:500}
.dc h3 .pk button{appearance:none;border:1px solid var(--line);background:var(--chip);color:var(--ink-2);font:inherit;font-size:11px;padding:3px 9px;border-radius:999px;cursor:pointer}
.dc h3 .pk button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.dc .more{margin-top:auto;padding-top:12px;text-align:right;font-size:12.5px}
.dc .more a{color:var(--accent);text-decoration:none;font-weight:600;cursor:pointer}
.dc .more a:hover{text-decoration:underline}
.kd{gap:2px}
.kd .kh{display:flex;align-items:center;gap:10px}
.kd .ki{width:34px;height:34px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;flex:none;font-weight:700;font-size:15px}
.kd .ki svg{width:17px;height:17px;stroke:#fff;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.kd .kl{font-size:12.5px;color:var(--ink-2);line-height:1.25}
.kd .kv{font:700 23px/1.15 "Public Sans",system-ui,sans-serif;margin:8px 0 2px;letter-spacing:-.01em}
.kd .kv.neg{color:var(--bad-ink)}
.kd .ks{font-size:11.5px;color:var(--ink-2)}
.kd .ks b{font-weight:700}.kd .up{color:var(--good-ink)}.kd .dn{color:var(--bad-ink)}
.kd svg.sp{width:100%;height:34px;margin-top:8px;display:block}
.kd .bar{height:6px;border-radius:99px;background:var(--chip);margin-top:12px;overflow:hidden}
.kd .bar i{display:block;height:100%;border-radius:99px;background:var(--accent)}
.dnw{display:flex;align-items:center;gap:14px;flex:1}
.dnw svg{width:118px;height:118px;flex:none}
.dnw .ct{font:700 15px "Public Sans",system-ui,sans-serif;fill:var(--ink)}
.dnw .cs{font:500 9.5px "Public Sans",system-ui,sans-serif;fill:var(--muted)}
.lg2{flex:1;min-width:0;display:grid;gap:7px;font-size:12.5px}
.lg2 div{display:flex;align-items:center;gap:8px;min-width:0}
.lg2 i{width:9px;height:9px;border-radius:50%;flex:none}
.lg2 span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lg2 b{font-weight:600;font-variant-numeric:tabular-nums}
.dc .ln{width:100%;height:auto;flex:1}
.dc .ln text{font:500 10px "Public Sans",system-ui,sans-serif;fill:var(--muted)}
.hb{display:grid;gap:11px}
.hb .r{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:3px 10px;font-size:12.5px}
.hb .r .tr{grid-column:1/3;height:7px;border-radius:99px;background:var(--chip);overflow:hidden}
.hb .r .tr i{display:block;height:100%;border-radius:99px;background:var(--accent)}
.hb .r span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.hb .r b{font-variant-numeric:tabular-nums;font-weight:600}
table.dt2{width:100%;border-collapse:collapse;font-size:12.5px}
table.dt2 th{font-weight:500;font-size:11px;color:var(--muted);text-align:right;padding:0 0 8px}
table.dt2 th:first-child,table.dt2 td:first-child{text-align:left}
table.dt2 td{padding:8px 0;border-top:1px solid var(--line-2);text-align:right;font-variant-numeric:tabular-nums}
table.dt2 td:first-child{max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
table.dt2 .g{color:var(--good-ink);font-weight:700}.dt2 .m{color:var(--warn-ink);font-weight:700}.dt2 .b{color:var(--bad-ink);font-weight:700}
.dc .note{font-size:11.5px;color:var(--muted);margin-top:8px}
@media(max-width:1280px){.dash .r1{grid-template-columns:repeat(3,minmax(0,1fr))}.dash .r2,.dash .r3{grid-template-columns:repeat(2,minmax(0,1fr))}.dash .r2>:nth-child(2){grid-column:1/3;order:-1}}
@media(max-width:760px){.dash .r1{grid-template-columns:repeat(2,minmax(0,1fr))}.dash .r2,.dash .r3{grid-template-columns:minmax(0,1fr)}.dash .r2>:nth-child(2){grid-column:auto;order:0}.dnw{flex-direction:column;align-items:flex-start}}
.dash .tbtools,.dash .pro-csv{display:none!important}
table.matrix{display:block;max-width:100%;overflow-x:auto}
@media print{.dash .r1{grid-template-columns:repeat(5,1fr)}.dash{break-inside:avoid}}
</style>
'''

JS = r'''
// ===== Gọn v4: bảng điều khiển Tổng quan =====
(function(){
  const $$=(s,r=document)=>r.querySelector(s);
  const U=n=>(n<0?"−":"")+"$"+N(Math.abs(n));
  const sum=(a,f)=>a.reduce((s,x)=>s+(+f(x)||0),0);
  const arrow=d=>d==null?"":`<b class="${d>=0?"up":"dn"}">${d>=0?"↑":"↓"} ${pc0(Math.abs(d))}</b>`;
  const SERIES=["--s1","--s2","--s3","--s4","--s5","--s6","--s7","--s8"];
  const IC={usd:'<span>$</span>',box:'<svg viewBox="0 0 24 24"><path d="M3 8l9-5 9 5v12H3z"/><path d="M8 20v-7h8v7"/></svg>',tgt:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg>',
    pct:'<span>%</span>',tag:'<svg viewBox="0 0 24 24"><path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.3"/></svg>'};

  function spark(vals){
    if(!vals||vals.length<2)return"";
    const w=140,h=34,p=3,mn=Math.min(...vals),mx=Math.max(...vals),rg=(mx-mn)||1;
    const pts=vals.map((v,i)=>[p+i*(w-2*p)/(vals.length-1),h-p-((v-mn)/rg)*(h-2*p-2)]);
    const d=pts.map((q,i)=>(i?"L":"M")+q[0].toFixed(1)+" "+q[1].toFixed(1)).join(" ");
    const last=pts[pts.length-1];
    return `<svg class="sp" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><path d="${d} L${last[0]} ${h} L${pts[0][0]} ${h}Z" style="fill:var(--accent);opacity:.12"/><path d="${d}" style="fill:none;stroke:var(--accent);stroke-width:1.8;vector-effect:non-scaling-stroke"/><circle cx="${last[0]}" cy="${last[1]}" r="2.6" style="fill:var(--accent)"/></svg>`;
  }
  function donut(items,top,sub){
    const tot=sum(items,x=>x.v)||1,R=52,C=2*Math.PI*R; let off=0;
    const seg=items.filter(x=>x.v>0).map(x=>{const len=x.v/tot*C,gap=items.length>1?1.5:0;const s=`<circle r="${R}" cx="70" cy="70" fill="none" style="stroke:${x.c}" stroke-width="20" stroke-dasharray="${Math.max(len-gap,0.1).toFixed(2)} ${(C-len+gap).toFixed(2)}" stroke-dashoffset="${(-off).toFixed(2)}"><title>${x.l}: ${x.t||N(x.v)}</title></circle>`;off+=len;return s}).join("");
    return `<svg viewBox="0 0 140 140" role="img" aria-label="${top}"><g transform="rotate(-90 70 70)">${seg}</g><text class="ct" x="70" y="68" text-anchor="middle">${top}</text><text class="cs" x="70" y="83" text-anchor="middle">${sub}</text></svg>`;
  }
  const legend=(items,tot)=>`<div class="lg2">${items.map(x=>`<div title="${x.l}: ${x.t||N(x.v)}"><i style="background:${x.c}"></i><span>${x.l}</span><b>${tot?pc0(x.v/tot*100,1):(x.t||N(x.v))}</b></div>`).join("")}</div>`;
  const more=(txt,fn)=>`<div class="more"><a data-go="${fn}">${txt} ›</a></div>`;

  function lineChart(labels,series,fmt){
    const W=560,H=210,l=46,r=22,t=12,b=26,all=series.flatMap(s=>s.v),mx=Math.max(...all,1)*1.1,n=labels.length;
    const X=i=>l+(n>1?i*(W-l-r)/(n-1):0),Y=v=>t+(1-v/mx)*(H-t-b);
    const grid=[0,1,2,3,4].map(k=>{const v=mx*k/4,y=Y(v);return `<line x1="${l}" x2="${W-r}" y1="${y}" y2="${y}" style="stroke:var(--line-2)"/><text x="${l-6}" y="${y+3}" text-anchor="end">${fmt(v)}</text>`}).join("");
    const xl=labels.map((x,i)=>`<text x="${X(i)}" y="${H-8}" text-anchor="middle">${x}</text>`).join("");
    const body=series.map((s,si)=>{
      const d=s.v.map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1)).join(" ");
      const area=si===0?`<path d="${d} L${X(n-1)} ${Y(0)} L${X(0)} ${Y(0)}Z" style="fill:${s.c};opacity:.10"/>`:"";
      const dots=s.v.map((v,i)=>`<circle cx="${X(i)}" cy="${Y(v)}" r="${si===0?3.6:2.4}" style="fill:${si===0?"var(--card)":s.c};stroke:${s.c};stroke-width:2"><title>${labels[i]} · ${s.n}: ${fmt(v,1)}</title></circle>`).join("");
      return area+`<path d="${d}" style="fill:none;stroke:${s.c};stroke-width:${si===0?2.4:1.6}" ${s.dash?'stroke-dasharray="5 4"':""} />`+dots}).join("");
    return `<svg class="ln" viewBox="0 0 ${W} ${H}" role="img" aria-label="Xu hướng">${grid}${xl}${body}</svg>`;
  }

  function build(){
    const host=$$("#dash"); if(!host||host.dataset.built)return; host.dataset.built="1";
    const P=window.__PRO||{};
    const wk=(D.ts_labels&&D.ts_labels.W)||[], mps=Object.keys((D.ts_ov&&D.ts_ov.W&&D.ts_ov.W.mp)||{});
    const wsum=k=>wk.map(w=>sum(mps,m=>((D.ts_ov.W.mp[m]||{})[w]||{})[k]));
    const wr=wsum("r"),wq=wsum("q"),wl=wk.map(w=>"W"+w);
    const ach=wk.map(w=>{const x=(D.weekfc.all||[]).find(a=>a.wk===w);return x?x.ach:null}).map(v=>v==null?0:v);
    const cur={r:sum(D.cell,c=>c.r),q:sum(D.cell,c=>c.q),rfc:sum(D.cell,c=>c.rfc)}, prev={r:sum(D.cell_prev||[],c=>c.r),q:sum(D.cell_prev||[],c=>c.q),rfc:sum(D.cell_prev||[],c=>c.rfc)};
    const dl=(a,b)=>b?(a/b-1)*100:null, achC=cur.rfc?cur.r/cur.rfc*100:0, achP=prev.rfc?prev.r/prev.rfc*100:null;
    const pl=D.pl5&&D.pl5.available?D.pl5.total:null, spend=sum(D.adsum||[],a=>a.spend), arev=sum(D.adsum||[],a=>a.rev), tac=arev?spend/arev*100:null;
    const kp=(ic,lab,val,neg,sub,extra)=>`<div class="dc kd"><div class="kh"><div class="ki">${ic}</div><div class="kl">${lab}</div></div><div class="kv${neg?" neg":""}">${val}</div><div class="ks">${sub}</div>${extra||""}</div>`;
    let h='<div class="row r1">';
    h+=kp(IC.usd,"Doanh thu tuần",U(cur.r),0,`${arrow(dl(cur.r,prev.r))} so với tuần trước`,spark(wr));
    h+=kp(IC.box,"Số lượng bán",N(cur.q),0,`${arrow(dl(cur.q,prev.q))} so với tuần trước`,spark(wq));
    h+=kp(IC.tgt,"Đạt kế hoạch (FC)",pc0(achC),0,achP==null?"":`<b class="${achC>=achP?"up":"dn"}">${achC>=achP?"↑":"↓"} ${pc0(Math.abs(achC-achP))}</b> điểm so với tuần trước`,spark(ach));
    h+=pl?kp(IC.pct,"Profit PL5",U(pl.profit),pl.profit<0,`biên <b class="${pl.margin>=0?"up":"dn"}">${(pl.margin<0?"−":"")+pc0(Math.abs(pl.margin))}</b> · độ phủ ${String(D.pl5.coverage_pct).replace(".",",")}%`,`<div class="bar" title="Độ phủ dữ liệu P&L"><i style="width:${Math.min(D.pl5.coverage_pct,100)}%"></i></div>`)
         :kp(IC.pct,"Profit PL5","—",0,"chưa có dữ liệu P&L");
    h+=kp(IC.tag,"Chi phí quảng cáo",U(spend),0,tac==null?"":`TACoS <b class="${tac>15?"dn":"up"}">${pc0(tac)}</b> · ngưỡng 15%`,tac==null?"":`<div class="bar" title="TACoS so với ngưỡng 15%"><i style="width:${Math.min(tac/15*100,100)}%;background:${tac>15?"var(--bad)":"var(--accent)"}"></i></div>`);
    h+='</div><div class="row r2">';
    // doanh thu theo sàn
    const byMp={}; D.cell.forEach(c=>{byMp[c.mp]=(byMp[c.mp]||0)+c.r});
    const mpi=Object.keys(byMp).filter(k=>byMp[k]>0).sort((a,b)=>byMp[b]-byMp[a]).map((k,i)=>({l:k,v:byMp[k],c:`var(${SERIES[i%8]})`,t:U(byMp[k])}));
    h+=`<div class="dc"><h3>Doanh thu theo sàn</h3><div class="dnw">${donut(mpi,U(cur.r),"doanh thu tuần")}${legend(mpi,cur.r)}</div>${more("Xem theo nhóm","gr")}</div>`;
    // xu hướng
    h+=`<div class="dc"><h3>Xu hướng ${wk.length} tuần<span class="pk" id="dtrkp"><button type="button" data-m="r" aria-pressed="true">Doanh thu</button><button type="button" data-m="a" aria-pressed="false">% đạt FC</button></span></h3><div id="dtrk"></div></div>`;
    // tồn kho & cảnh báo
    const st=(D.invdet&&D.invdet.st_totals)||[], sti=st.map((x,i)=>({l:x.stlab,v:x.qty,c:`var(${SERIES[i%8]})`}));
    const iv=P.inv||{};
    h+=`<div class="dc"><h3>Tồn kho &amp; cảnh báo</h3><div class="dnw">${donut(sti,N(sum(st,x=>x.qty)),"sản phẩm tồn")}${legend(sti)}</div>`
      +(iv.n_low!=null?`<div class="note"><b style="color:var(--bad-ink)">${iv.n_low}</b> SKU sắp hết hàng · <b style="color:var(--warn-ink)">${iv.dead_n||0}</b> SKU tồn chậm${iv.dead_units?` (${N(iv.dead_units)} sp)`:""}</div>`:"")+more("Xem chi tiết tồn kho","inv")+'</div>';
    h+='</div><div class="row r3">';
    // top nhóm
    const g=[...D.bygrp].sort((a,b)=>b.r-a.r).slice(0,5), gm=Math.max(...g.map(x=>x.r),1);
    h+=`<div class="dc"><h3>Top nhóm sản phẩm</h3><div class="hb">${g.map(x=>`<div class="r"><span title="${x.grp}">${short(x.grp)}</span><b>${U(x.r)}</b><div class="tr"><i style="width:${x.r/gm*100}%"></i></div></div>`).join("")}</div>${more("Xem tất cả","gr")}</div>`;
    // quảng cáo
    const ad=[...(D.adsum||[])].sort((a,b)=>b.spend-a.spend).slice(0,5);
    h+=`<div class="dc"><h3>Hiệu quả quảng cáo theo kênh</h3>`+(ad.length?`<table class="dt2"><thead><tr><th>Kênh</th><th>Chi phí</th><th>TACoS</th><th>ROAS</th></tr></thead><tbody>${ad.map(a=>`<tr><td title="${a.mp} ${a.cty}">${a.mp} · ${a.cty}</td><td>${U(a.spend)}</td><td class="${a.tacos==null?"":(a.tacos>15?"b":(a.tacos>10?"m":"g"))}">${a.tacos==null?"—":pc0(a.tacos)}</td><td class="${a.roas>=5?"g":(a.roas>=3?"m":"b")}">${a.roas?String(a.roas.toFixed(1)).replace(".",","):"—"}</td></tr>`).join("")}</tbody></table>`:'<div class="note">Chưa có dữ liệu quảng cáo.</div>')+more("Xem tất cả","cp")+'</div>';
    // cảnh báo
    const sv=(P.summary&&P.summary.by_sev)||null;
    if(sv){const it=[{l:"Ưu tiên cao",v:sv[3]||0,c:"var(--bad)"},{l:"Ưu tiên vừa",v:sv[2]||0,c:"var(--warn)"},{l:"Theo dõi",v:sv[1]||0,c:"var(--muted)"}];
      h+=`<div class="dc"><h3>Điều cần chú ý</h3><div class="dnw">${donut(it,String(P.summary.n),"cảnh báo")}${legend(it)}</div>${more("Xem chi tiết","ins")}</div>`;}
    else h+='<div class="dc"><h3>Điều cần chú ý</h3><div class="note">Chưa có dữ liệu cảnh báo.</div></div>';
    h+='</div>';
    host.innerHTML=h;
    // xu hướng (chuyển chế độ)
    const fm=(v,d)=>d?U(v):(v>=1000?N(v/1000)+"K":N(v)), fa=(v,d)=>pc0(v,d?1:0);
    const fcw=wk.map(w=>{const x=(D.weekfc.all||[]).find(a=>a.wk===w);return x?x.rfc:0});
    function paint(m){ $$("#dtrk").innerHTML=m==="r"?lineChart(wl,[{n:"Doanh thu",v:wr,c:"var(--s1)"},{n:"FC",v:fcw,c:"var(--muted)",dash:1}],fm)+'<div class="note">Đường liền: doanh thu thực tế · đường nét đứt: kế hoạch (FC) của từng tuần.</div>':lineChart(wl,[{n:"% đạt FC",v:ach,c:"var(--s1)"}],fa)+'<div class="note">Tỷ lệ doanh thu thực tế so với kế hoạch của từng tuần.</div>';
      host.querySelectorAll("#dtrkp button").forEach(b=>b.setAttribute("aria-pressed",b.dataset.m===m))}
    paint("r"); host.querySelectorAll("#dtrkp button").forEach(b=>b.addEventListener("click",()=>paint(b.dataset.m)));
    host.querySelectorAll("[data-go]").forEach(a=>a.addEventListener("click",()=>{const k=a.dataset.go; if(k==="ins"){const e=document.getElementById("pro-ins")||document.getElementById("pro-slot");if(e)e.scrollIntoView({behavior:"smooth",block:"start"});}else{activate(k);window.scrollTo({top:0,behavior:"smooth"})}}));
  }
  const _ov=builders.ov; builders.ov=function(){_ov.apply(this,arguments);try{build()}catch(e){console.warn("dash",e)}};
  if(typeof built!=="undefined"&&built.ov){try{build()}catch(e){console.warn("dash",e)}}
})();
'''
# 1) CSS vào cuối <head> (cùng chỗ với các khối <style> khác): chèn trước </nav>…? -> ngay sau khối CSS Gọn v3 đầu tiên là chắc chắn có trong <body>
m = list(re.finditer(r"</nav>\n", t)); assert len(m) == 1
t = t[:m[0].end()] + CSS + t[m[0].end():]
# 2) khung bảng điều khiển: ngay sau tiêu đề mục "Tóm tắt điều hành"
m = re.search(r'(<div class="shead"><span class="snum">01</span><h2>Tóm tắt điều hành</h2>.*?</div>)\n', t)
assert m, "không thấy tiêu đề Tóm tắt điều hành"
t = t[:m.end()] + '    <div class="dash" id="dash" aria-label="Bảng điều khiển tổng quan"></div>\n' + t[m.end():]
# 3) JS: cuối script cuối cùng, sau khi `builders` đã khai báo
last = list(re.finditer(r"</script>", t))[-1]
t = t[:last.start()] + JS + t[last.start():]
rep1("Mẫu Gọn v3</div>", "Mẫu Gọn v4</div>")
assert [l for l in t.split("\n") if l.startswith("const D = ")] == d_before
open(DST, "w", encoding="utf-8").write(t); print("OK", DST, len(t) // 1024, "KB")
