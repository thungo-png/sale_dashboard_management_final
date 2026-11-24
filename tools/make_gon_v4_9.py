"""Gọn v4 – chỉnh nhỏ (lần 9): bấm vào từng ô màu (hoặc dòng chú giải) của 3 vòng tròn "Doanh thu theo sàn / thị trường / nhóm sản phẩm"
   để mở khung chi tiết: doanh thu, số lượng, % đạt FC, so với kỳ trước, biểu đồ theo ngày, bảng phân rã chéo (sàn ↔ thị trường ↔ nhóm) và top SKU của nhóm.
   Theo ô chọn khoảng ngày; bấm lại ô đang chọn hoặc nút × để đóng.
   Dùng: python3 make_gon_v4_9.py vào.html ra.html (đã áp make_gon_v4_8). Không đụng dòng const D, không xoá id."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
dl_=[l for l in s.split("\n") if l.startswith("const D = ")]
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]); s=s.replace(a,b)
rep1('let first=true;','window.__FULLD=FULLD;let first=true;')
# ---- donut + legend: ô bấm được khi item có k
rep1('const s=`<circle r="${R}" cx="70" cy="70" fill="none" style="stroke:${x.c}"','const s=`<circle r="${R}" cx="70" cy="70" fill="none"${x.k!=null?` class="seg" data-k="${String(x.k).replace(/"/g,"&quot;")}"`:""} style="stroke:${x.c}"')
rep1('`<div class="lg2">${items.map(x=>`<div title="${x.l}: ${x.t||N(x.v)}">','`<div class="lg2">${items.map(x=>`<div${x.k!=null?` class="lgi" data-k="${String(x.k).replace(/"/g,"&quot;")}"`:""} title="${x.l}: ${x.t||N(x.v)}">')
i=s.index('  function build(force){'); j=s.index('    host.innerHTML=h;\n',i)
seg=s[i:j]
def r(a,b,cnt=1):
    global seg
    assert seg.count(a)==cnt,(seg.count(a),a[:80]); seg=seg.replace(a,b,cnt)
r('.map((k,i)=>({l:k,v:byMp[k],','.map((k,i)=>({k:k,l:k,v:byMp[k],')
r('.map((k,i2)=>({l:CTYN[k]||k,','.map((k,i2)=>({k:k,l:CTYN[k]||k,')
r('.map((k,i2)=>({l:short(k),','.map((k,i2)=>({k:k,l:short(k),')
r('gi.push({l:"Nhóm khác (','gi.push({k:"__other",l:"Nhóm khác (')
r('<div class="dnw">${donut(cti','<div class="dnw" data-dim="cty">${donut(cti')
r('<div class="dnw">${donut(gi','<div class="dnw" data-dim="grp">${donut(gi')
r('<div class="dc"><h3>Doanh thu theo sàn</h3><div class="dnw">','<div class="dc"><h3>Doanh thu theo sàn</h3><div class="dnw" data-dim="mp">')
r("    h+='</div><div class=\"row r2 r2b\">';","    h+='</div><div id=\"ddp\"></div><div class=\"row r2 r2b\">';")
s=s[:i]+seg+s[j:]; j=i+len(seg)
code='''    host.innerHTML=h;
    // ---- khung chi tiết khi bấm vào ô màu
    const drawDD=()=>{
      const sel=window.__DSEL,el=host.querySelector("#ddp");if(!el)return;
      host.querySelectorAll("[data-k]").forEach(x=>{const w=x.closest("[data-dim]");x.classList.toggle("on",!!(sel&&w&&w.dataset.dim===sel.dim&&x.dataset.k===sel.k))});
      host.querySelectorAll(".dnw[data-dim]").forEach(w=>w.classList.toggle("hasSel",!!(sel&&w.dataset.dim===sel.dim)));
      if(!sel){el.innerHTML="";return}
      const FD=window.__FULLD||[],nL=L||FD.slice(-7);
      if(!nL.length||!D.ts_grpcell||!D.ts_grp){el.innerHTML='<div class="dd"><div class="note">Kỳ này chưa có dữ liệu theo ngày để xem chi tiết.</div></div>';return}
      const n=nL.length,a0=FD.indexOf(nL[0]),PL=a0-n>=0?FD.slice(a0-n,a0):null;
      const agg=(ser,labs)=>{let rr=0,qq=0,ff=0;labs.forEach(d=>{const c=(ser||{})[d];if(c){rr+=c.r||0;qq+=c.q||0;ff+=c.rfc||0}});return{r:rr,q:qq,f:ff}};
      const GCC=D.ts_grpcell.D,OV=D.ts_ov.D,KEYS={mp:Object.keys(OV.mp),cty:Object.keys(OV.cty),grp:Object.keys(D.ts_grp.D)};
      const S1=(dim,k)=>dim==="mp"?OV.mp[k]:(dim==="cty"?OV.cty[k]:D.ts_grp.D[k]);
      const X=(dim,k,od,ok)=>dim==="mp"&&od==="cty"?OV.mpcty[k+" · "+ok]:dim==="cty"&&od==="mp"?OV.mpcty[ok+" · "+k]:dim==="mp"&&od==="grp"?GCC.grp_mp[ok+" · "+k]:dim==="grp"&&od==="mp"?GCC.grp_mp[k+" · "+ok]:dim==="cty"&&od==="grp"?GCC.grp_cty[ok+" · "+k]:GCC.grp_cty[k+" · "+ok];
      const NM={mp:k=>k,cty:k=>CTYN[k]||k,grp:k=>short(k)},DN={mp:"sàn",cty:"thị trường",grp:"nhóm sản phẩm"};
      const other=sel.k==="__other",oth=other?gs.slice(5):null;
      const mix=(sers)=>{const o={};nL.concat(PL||[]).forEach(d=>{let rr=0,qq=0,ff=0;sers.forEach(sv=>{const c=(sv||{})[d];if(c){rr+=c.r||0;qq+=c.q||0;ff+=c.rfc||0}});o[d]={r:rr,q:qq,rfc:ff}});return o};
      const ser=other?mix(oth.map(k=>D.ts_grp.D[k])):S1(sel.dim,sel.k);
      const cur2=agg(ser,nL),pv=PL?agg(ser,PL):null,tot=sum(KEYS[sel.dim],k=>agg(S1(sel.dim,k),nL).r)||1;
      const title=other?"Nhóm khác ("+oth.length+" nhóm)":NM[sel.dim](sel.k);
      const dlt=(a,b)=>b?arrow(dl(a,b)):"<span class=\\"mu\\">—</span>";
      const kpi=(l,v,sb)=>`<div class="ddk"><span>${l}</span><b>${v}</b><small>${sb||""}</small></div>`;
      const bars=(rows,tt)=>rows.map(x=>`<tr><td title="${x.name}">${x.name}</td><td>${U(x.r)}</td><td><div class="tr"><i style="width:${Math.min(x.r/(tt||1)*100,100)}%"></i></div><span class="sh">${pc0(x.r/(tt||1)*100,1)}</span></td><td>${N(x.q)}</td><td>${x.f?pc0(x.r/x.f*100):"—"}</td><td>${dlt(x.r,x.pr)}</td></tr>`).join("");
      const tbl=(ttl,rows)=>rows.length?`<div class="ddt"><h4>${ttl}</h4><div class="ddw"><table class="dt2"><thead><tr><th>Tên</th><th>Doanh thu</th><th>Tỷ trọng</th><th>SL</th><th>% FC</th><th>So kỳ trước</th></tr></thead><tbody>${bars(rows,cur2.r)}</tbody></table></div></div>`:"";
      const mk=(od,sl)=>{const rows=[];KEYS[od].forEach(ok=>{
          const sv=other?mix(oth.map(g=>X("grp",g,od,ok))):X(sel.dim,sel.k,od,ok),a=agg(sv,nL);if(!a.r&&!a.q)return;
          rows.push({name:NM[od](ok),r:a.r,q:a.q,f:a.f,pr:PL?agg(sv,PL).r:0})});
        rows.sort((p,q)=>q.r-p.r);return rows.slice(0,sl||8)};
      let tb="";
      if(other){const rows=oth.map(g=>{const a=agg(D.ts_grp.D[g],nL);return{name:short(g),r:a.r,q:a.q,f:a.f,pr:PL?agg(D.ts_grp.D[g],PL).r:0}}).sort((p,q)=>q.r-p.r);tb=tbl("Các nhóm trong mục này",rows);
        tb+=tbl("Theo sàn",mk("mp"))+tbl("Theo thị trường",mk("cty"))}
      else{const ods=["mp","cty","grp"].filter(x=>x!==sel.dim);ods.forEach(od=>{tb+=tbl("Theo "+DN[od],mk(od))});
        if(sel.dim==="grp"&&D.ts_sku&&D.ts_sku.D&&D.ts_sku.D.l1&&D.sku_meta){const sk=D.sku_meta.filter(x=>x.grp===sel.k).map(x=>{const sv=D.ts_sku.D.l1[x.sku],a=agg(sv,nL);return{name:x.sku+" · "+String(x.name||"").slice(0,34),r:a.r,q:a.q,f:a.f,pr:PL?agg(sv,PL).r:0}}).filter(x=>x.r||x.q).sort((p,q)=>q.r-p.r).slice(0,8);tb+=tbl("Top SKU của nhóm",sk)}}
      const lab=nL.map(d=>d.slice(8)+"/"+d.slice(5,7)),vals=nL.map(d=>(ser[d]||{}).r||0);
      const rng=nL.length>1?lab[0]+" – "+lab[lab.length-1]:lab[0];
      el.innerHTML=`<div class="dd"><div class="ddh"><div><b>${title}</b><span> · chi tiết ${n} ngày (${rng})</span></div><button type="button" class="ddx" data-close aria-label="Đóng">×</button></div>
        <div class="ddb"><div class="ddl"><div class="ddks">${kpi("Doanh thu",U(cur2.r),pv?dlt(cur2.r,pv.r)+" so với "+n+" ngày trước":"")}${kpi("Số lượng",N(cur2.q),pv?dlt(cur2.q,pv.q)+" so với "+n+" ngày trước":"")}${kpi("Đạt kế hoạch",cur2.f?pc0(cur2.r/cur2.f*100):"—","FC "+U(cur2.f))}${kpi("Tỷ trọng",pc0(cur2.r/tot*100,1),"trên tổng "+DN[sel.dim])}</div>
        <div class="ddc">${lineChart(lab,[{n:"Doanh thu",v:vals,c:"var(--s1)"}],(v,d)=>d?U(v):(v>=1000?N(v/1000)+"K":N(v)))}</div></div><div class="ddr">${tb}</div></div></div>`;
    };
    host.__draw=drawDD;
    if(!host.dataset.dd){host.dataset.dd="1";host.addEventListener("click",ev=>{
      if(ev.target.closest("[data-close]")){window.__DSEL=null;host.__draw();return}
      const t=ev.target.closest("[data-k]");if(!t)return;const w=t.closest("[data-dim]");if(!w)return;
      const dim=w.dataset.dim,k=t.dataset.k,c=window.__DSEL;window.__DSEL=(c&&c.dim===dim&&c.k===k)?null:{dim:dim,k:k};host.__draw();
      if(window.__DSEL){const p=host.querySelector("#ddp");if(p&&p.getBoundingClientRect().bottom>window.innerHeight)p.scrollIntoView({behavior:"smooth",block:"nearest"})}})}
    drawDD();
'''
s=s[:j]+code+s[j+len('    host.innerHTML=h;\n'):]
rep1('.xc{}\n','''.xc{}
circle.seg{cursor:pointer;transition:opacity .15s,stroke-width .15s}.lgi{cursor:pointer;border-radius:6px}.lgi:hover{background:color-mix(in srgb,var(--accent) 8%,transparent)}
.dnw.hasSel circle.seg:not(.on){opacity:.3}.dnw.hasSel .lgi:not(.on){opacity:.55}circle.seg.on{stroke-width:25}.lgi.on{font-weight:700;background:color-mix(in srgb,var(--accent) 10%,transparent)}
#ddp:empty{display:none}#ddp .dd{border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:14px;background:var(--card);padding:16px 18px;box-shadow:var(--sh,none)}
#ddp .ddh{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:15px}#ddp .ddh span{color:var(--muted);font-size:12.5px}
#ddp .ddx{border:1px solid var(--line);background:var(--card);border-radius:8px;width:30px;height:30px;font-size:18px;line-height:1;cursor:pointer;color:var(--muted)}
#ddp .ddb{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.5fr);gap:18px;margin-top:12px}
#ddp .ddks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
#ddp .ddk{border:1px solid var(--line);border-radius:10px;padding:9px 12px;display:flex;flex-direction:column;gap:2px;background:var(--card2,transparent)}
#ddp .ddk span{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}#ddp .ddk b{font-size:19px}#ddp .ddk small{font-size:11.5px;color:var(--muted)}
#ddp .ddc{margin-top:12px}#ddp .ddc svg{width:100%;height:auto}
#ddp .ddr{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:14px}#ddp .ddt h4{margin:0 0 6px;font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
#ddp .ddw{overflow-x:auto}#ddp table.dt2 td:first-child{max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#ddp .tr{display:inline-block;width:46px;height:6px;border-radius:4px;background:var(--line);vertical-align:middle;margin-right:6px;overflow:hidden}#ddp .tr i{display:block;height:100%;background:var(--accent)}#ddp .sh{font-size:11.5px;color:var(--muted)}
@media(max-width:900px){#ddp .ddb{grid-template-columns:minmax(0,1fr)}#ddp .ddr{grid-template-columns:minmax(0,1fr)}}
''')
assert [l for l in s.split("\n") if l.startswith("const D = ")]==dl_
open(sys.argv[2],"w",encoding="utf-8").write(s)
