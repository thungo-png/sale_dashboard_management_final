/* ===== Gọn v4.2 (nâng cấp): FC cả năm + tách Phí tồn kho khỏi Cầu lợi nhuận ===== */
(function(){
  const CT=(D.meta&&D.meta.ctys)||["US","CAN","AUS"];
  const F=v=>(v<0?"−":"")+N(Math.abs(v)), FU=v=>(v<0?"−":"")+"$"+N(Math.abs(v));
  const GC2=((window.D0&&window.D0.ts_grpcell)||D.ts_grpcell)||{};
  let LV="M", MT="r";   // MT: r = doanh thu, q = số lượng

  /* ---- 1) Cầu lợi nhuận: tách Warehouse fee (phí tồn kho) ra dòng riêng ---- */
  (function(){
    const P=window.__PRO, B=P&&P.bridge, t=D.pl5&&D.pl5.total; if(!B||!B.items||!t||!(+t.wh_fee>0))return;
    const it=B.items, f=it.find(x=>/Phí sàn/.test(x.k)); if(!f||it.some(x=>/tồn kho/i.test(x.k)))return;
    const wh=+t.wh_fee, inc=(+t.ref_fee||0)+(+t.return_fee||0)+(+t.op_fee||0)+wh;
    if(Math.abs(f.v-inc)>2)return;               // dòng phí hiện tại không chứa Warehouse fee → không tự ý tách
    f.v=+(f.v-wh).toFixed(2); f.pct=B.r?+(f.v/B.r*100).toFixed(1):0;
    it.splice(it.indexOf(f)+1,0,{k:"Phí tồn kho (Warehouse fee 6%)",v:+wh.toFixed(2),pct:B.r?+(wh/B.r*100).toFixed(1):0});
  })();
  const COL={"Giá vốn":"--s2","Phí sàn":"--s4","Phí tồn kho":"--s6","Vận chuyển":"--s5","Quảng cáo":"--s7"};
  function recolor(){
    document.querySelectorAll("#p-mg .hl").forEach(r=>{const s=r.querySelector("span"),i=r.querySelector("i"); if(!s||!i)return;
      const k=Object.keys(COL).find(k=>s.textContent.replace(/^[−-]\s*/,"").startsWith(k)); if(k&&/^[−-]/.test(s.textContent.trim()))i.style.background=`var(${COL[k]})`});
  }
  let wrapped=false;
  const iv=setInterval(()=>{
    if(!wrapped&&typeof builders!=="undefined"&&builders.mg){wrapped=true;const o=builders.mg;builders.mg=function(){try{o()}finally{recolor()}};
      if(document.querySelector("#p-mg .hl"))recolor();}
  },200); setTimeout(()=>clearInterval(iv),15000);

  /* ---- 2) FC cả năm: thực tế so với FC theo tháng/quý và quốc gia ---- */
  function agg(lv){
    const src=(GC2[lv]&&GC2[lv].grp_cty)||{}, o={};
    Object.keys(src).forEach(k=>{const c=k.split(" · ").pop(), v=src[k];
      Object.keys(v).forEach(p=>{const a=((o[p]||(o[p]={}))[c]||(o[p][c]={r:0,rfc:0,q:0,qfc:0}));a.r+=v[p].r||0;a.rfc+=v[p].rfc||0;a.q+=v[p].q||0})});
    /* Số lượng FC theo quốc gia không có sẵn trong file: lấy số lượng FC toàn cầu của kỳ (có thật) chia theo tỷ trọng doanh thu FC của từng quốc gia → ước tính */
    const G0=window.D0||D, gq={};
    if(lv==="M")(G0.monthly||[]).forEach(x=>{gq[x.M]=(gq[x.M]||0)+(x.qfc||0)});
    else if(lv==="Q")(G0.quarterly||[]).forEach(x=>{gq[x.Q]=(gq[x.Q]||0)+(x.qfc||0)});
    else((G0.weekfc&&G0.weekfc.all)||[]).forEach(x=>{gq[String(x.wk)]=(x.qfc||0)});
    Object.keys(o).forEach(p=>{const tot=Object.keys(o[p]).reduce((s,c)=>s+o[p][c].rfc,0);
      Object.keys(o[p]).forEach(c=>{o[p][c].qfc=tot?(gq[p]||0)*o[p][c].rfc/tot:0})});
    return o;
  }
  /* Profit PL5 theo kỳ: PL5 chỉ có theo tuần (các tuần đã có báo cáo phí/QC) → gộp tuần vào tháng/quý theo ngày cuối tuần */
  function plAgg(c){
    const P0=(window.D0||D).pl5ts, src=(P0&&P0.W&&P0.W.cty&&P0.W.cty[c])||{}, lab=(D.meta&&D.meta.weeklab)||{}, yr=((D.meta&&D.meta.d1)||"").slice(0,4), o={};
    Object.keys(src).forEach(w=>{const v=src[w]; if(!Array.isArray(v))return; const m=String(lab[w]||"").match(/–\s*(\d\d)\/(\d\d)/);
      const mo=m?m[2]:null; let k=w; if(LV==="M"){if(!mo)return;k=yr+"-"+mo}else if(LV==="Q"){if(!mo)return;k=yr+"Q"+(Math.floor((+mo-1)/3)+1)}
      const a=o[k]||(o[k]={p:0,r:0,n:0}); a.p+=+v[0]||0; a.r+=+v[1]||0; a.n++});
    return o;
  }
  function lastDate(){
    const d=(GC2.D&&GC2.D.grp_cty)||{}; let m="";
    Object.keys(d).forEach(k=>Object.keys(d[k]).forEach(p=>{if(p>m)m=p})); return m||(D.meta&&D.meta.d1)||"";
  }
  const dm=s=>s?s.slice(8,10)+"/"+s.slice(5,7):"";
  function lab(p,end){
    if(LV==="W"){const l=(D.meta&&D.meta.weeklab||{})[p];return "W"+p+(l?" · "+l:"")}
    if(LV==="M"){const part=end&&p===end.slice(0,7)&&end.slice(8)!==String(new Date(+end.slice(0,4),+end.slice(5,7),0).getDate()).padStart(2,"0");
      return "Tháng "+(+p.slice(5))+(part?` (đến ${dm(end)})`:"")}
    const q=p.slice(5), qe=end?(+end.slice(5,7)-1)/3|0:-1, part=end&&p===end.slice(0,4)+"Q"+(qe+1)&&!/-(03-31|06-30|09-30|12-31)$/.test(end);
    return "Quý "+q+(part?` (đến ${dm(end)})`:"");
  }
  function chart(rows){
    const W=900,H=250,L=52,R=10,T=20,Bm=40, n=rows.length||1, mx=Math.max(1,...rows.map(x=>Math.max(x.r,x.rfc)))*1.12;
    const gw=(W-L-R)/n, bw=Math.min(30,gw*.32), Y=v=>T+(H-T-Bm)*(1-v/mx);
    const K=v=>v>=1e6?(v/1e6).toFixed(1).replace(".",",")+"M":v>=1000?Math.round(v/1000)+"K":Math.round(v);
    const g=[0,.5,1].map(f=>{const v=mx/1.12*f;return `<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${L-6}" y="${Y(v)+3}" text-anchor="end" fill="var(--muted)" font-size="11">${K(v)}</text>`}).join("");
    const b=rows.map((x,i)=>{const cx=L+gw*i+gw/2, a=x.rfc?x.r/x.rfc*100:null;
      return `<rect x="${cx-bw-1}" y="${Y(x.rfc)}" width="${bw}" height="${Y(0)-Y(x.rfc)}" rx="2" fill="var(--muted)" opacity=".4"/>
        <rect x="${cx+1}" y="${Y(x.r)}" width="${bw}" height="${Y(0)-Y(x.r)}" rx="2" fill="var(--accent)"/>
        <text x="${cx}" y="${Y(Math.max(x.r,x.rfc))-6}" text-anchor="middle" font-size="11" font-weight="600" class="${a===null?"":ach(a)}">${a===null?"":pc0(a)}</text>
        <text x="${cx}" y="${H-Bm+16}" text-anchor="middle" font-size="11" fill="var(--muted)">${x.s}</text>`}).join("");
    return `<svg class="svgc" viewBox="0 0 ${W} ${H}" role="img" aria-label="Doanh thu thực tế so với FC theo kỳ" style="width:100%;height:auto">${g}${b}</svg>
      <div style="display:flex;gap:16px;font-size:12px;color:var(--muted);margin-top:4px"><span><i style="display:inline-block;width:10px;height:10px;border-radius:2px;background:var(--accent);margin-right:6px"></i>Thực tế</span><span><i style="display:inline-block;width:10px;height:10px;border-radius:2px;background:var(--muted);opacity:.4;margin-right:6px"></i>FC</span><span>Số trên đầu cột: % đạt FC</span></div>`;
  }
  function render(){
    const host=document.getElementById("fcyr"); if(!host)return;
    const A=agg(LV), ps=Object.keys(A).sort((x,y)=>LV==="W"?x-y:(x<y?-1:1)), end=lastDate(), cs=(window.CTYF?[window.CTYF]:CT), PL={}; cs.forEach(c=>PL[c]=plAgg(c));
    const rows=ps.map(p=>{const o={p,s:LV==="M"?"T"+(+p.slice(5)):LV==="W"?"W"+p:"Q"+p.slice(5),lab:lab(p,end),c:{}};let r=0,f=0;
      cs.forEach(c=>{const a=(A[p]&&A[p][c])||{r:0,rfc:0};const q=PL[c][p]||null;const Rk=MT==="q"?"q":"r",Fk=MT==="q"?"qfc":"rfc";o.c[c]={r:a[Rk],rfc:a[Fk],pp:q?q.p:null,pr:q?q.r:0};r+=a[Rk];f+=a[Fk]});o.r=r;o.rfc=f;const ks=cs.filter(c=>PL[c][p]);o.pp=ks.length?ks.reduce((s,c)=>s+PL[c][p].p,0):null;o.pr=ks.reduce((s,c)=>s+PL[c][p].r,0);return o});
    const T=rows.reduce((s,x)=>({r:s.r+x.r,rfc:s.rfc+x.rfc}),{r:0,rfc:0}), a=T.rfc?T.r/T.rfc*100:null;
    const cT={}; cs.forEach(c=>cT[c]=rows.reduce((s,x)=>({r:s.r+x.c[c].r,rfc:s.rfc+x.c[c].rfc,pp:s.pp+(x.c[c].pp||0),pr:s.pr+(x.c[c].pr||0)}),{r:0,rfc:0,pp:0,pr:0}));
    T.pp=rows.reduce((s,x)=>s+(x.pp||0),0); T.pr=rows.reduce((s,x)=>s+(x.pr||0),0);
    const plw=[...new Set(cs.reduce((s,c)=>s.concat(Object.keys((((window.D0||D).pl5ts||{}).W||{}).cty&&((window.D0||D).pl5ts.W.cty[c])||{})),[]))].filter(w=>cs.some(c=>{const v=(((window.D0||D).pl5ts.W.cty||{})[c]||{})[w];return Array.isArray(v)})).map(Number).sort((x,y)=>x-y);
    const pcell=(pp,pr)=>MT==="q"?"":pp===null||pp===undefined||!pr?'<td>—</td><td>—</td>':`<td class="${pp<0?"neg":""}">${FU(pp)}</td><td class="${pp<0?"neg":""}">${(pp/pr*100).toFixed(1).replace(".",",")}%</td>`;
    const cell=(x)=>{const p=x.rfc?x.r/x.rfc*100:null;return `<td>${F(Math.round(x.r))}</td><td>${F(Math.round(x.rfc))}</td><td class="${p===null?"":ach(p)}">${p===null?"—":pc0(p)}</td>${pcell(x.pp===undefined?null:x.pp,x.pr)}`};
    const multi=cs.length>1;
    const head=`<tr><th rowspan="2">Kỳ</th>${cs.map(c=>`<th colspan="${MT==="q"?3:5}" style="text-align:center">${c}</th>`).join("")}${multi?'<th colspan="${MT==="q"?3:5}" style="text-align:center">Tổng</th>':""}</tr>
      <tr>${(multi?cs.concat(["T"]):cs).map(()=>(MT==="q"?"<th>Số lượng</th><th>FC (ước tính)</th><th>% đạt</th>":"<th>Revenue</th><th>FC</th><th>% đạt</th><th>Profit PL5</th><th>Biên PL5</th>")).join("")}</tr>`;
    const body=rows.map(x=>`<tr><td>${x.lab}</td>${cs.map(c=>cell(x.c[c])).join("")}${multi?cell(x):""}</tr>`).join("")
      +`<tr class="sub"><td><b>Lũy kế đến ${dm(end)}</b></td>${cs.map(c=>cell(cT[c])).join("")}${multi?cell(T):""}</tr>`;
    const gap=T.rfc-T.r;
    host.innerHTML=`<div class="fck" style="display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));margin-bottom:12px">
      <div class="card"><div class="cap">${MT==="q"?"Số lượng":"Doanh thu"} thực tế lũy kế${window.CTYF?" · "+window.CTYF:""}</div><div style="font-size:26px;font-weight:700">${MT==="q"?F(Math.round(T.r)):FU(T.r)}</div><div class="cap">từ 01/01 đến ${dm(end)}</div></div>
      <div class="card"><div class="cap">FC lũy kế cùng kỳ</div><div style="font-size:26px;font-weight:700">${MT==="q"?F(Math.round(T.rfc)):FU(T.rfc)}</div><div class="cap">${MT==="q"?"số lượng FC ước tính theo tỷ trọng doanh thu FC":"tổng các tháng đã có FC"}</div></div>
      ${MT==="q"?"":`<div class="card"><div class="cap">Profit PL5 (các tuần đã có PL5)${window.CTYF?" · "+window.CTYF:""}</div><div style="font-size:26px;font-weight:700" class="${T.pp<0?"neg":""}">${T.pr?FU(T.pp):"—"}</div><div class="cap">${T.pr?"biên "+(T.pp/T.pr*100).toFixed(1).replace(".",",")+"% trên doanh thu "+FU(T.pr)+" · "+plw.map(w=>"W"+w).join(", "):"chưa có tuần nào có PL5"}</div></div>`}
      <div class="card"><div class="cap">Đạt so với FC</div><div style="font-size:26px;font-weight:700" class="${a===null?"":ach(a)}">${a===null?"—":pc0(a)}</div><div class="cap">${gap>0?"chênh "+(MT==="q"?F(Math.round(gap))+" sp":FU(gap))+" so với FC":"vượt FC "+(MT==="q"?F(Math.round(-gap))+" sp":FU(-gap))}</div></div></div>
      <div class="pickrow" style="display:flex;gap:8px;margin-bottom:8px">${[["M","Theo tháng"],["Q","Theo quý"],["W","Theo tuần"]].map(([k,t])=>`<button class="pick" data-lv="${k}" aria-pressed="${k===LV}">${t}</button>`).join("")}<span style="flex:1"></span>${[["r","Doanh thu"],["q","Số lượng"]].map(([k,t])=>`<button class="pick" data-mt="${k}" aria-pressed="${k===MT}">${t}</button>`).join("")}</div>
      <div class="chartbox">${chart(rows)}</div>
      <div class="scroll" style="margin-top:12px"><table id="tbl-fcyr"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
    host.querySelectorAll(".pick").forEach(b=>b.addEventListener("click",()=>{if(b.dataset.lv)LV=b.dataset.lv;if(b.dataset.mt)MT=b.dataset.mt;render()}));
    const cap=document.getElementById("fcyrcap");
    if(cap)cap.innerHTML=`FC trong file hiện có <b>đến ${dm(end)}</b>${end?"/"+end.slice(0,4):""}; các tháng còn lại của năm chưa có FC nên chưa hiển thị. Khi có file FC đủ cả năm, mục này tự thêm các kỳ đó. Profit PL5 chỉ tính cho các tuần đã có báo cáo phí/quảng cáo (nêu ở thẻ Profit PL5); tuần chưa có PL5 hiển thị “—”, tuần vắt qua hai tháng được gộp vào tháng chứa ngày cuối tuần; biên PL5 tính trên doanh thu của chính các tuần có PL5. Doanh thu quy đổi USD. Kỳ cuối chưa trọn tháng/quý chỉ so với phần FC của các ngày đã có.`;
  }
  (window.CTYHOOK=window.CTYHOOK||[]).push(render);
  render();

  /* mục này đứng ngay trước "Ma trận sàn × thị trường" (tab Doanh thu & Kế hoạch) */
  function moveSec(){
    const me=document.getElementById("fcyr-sec"); if(!me)return;
    const t=[...document.querySelectorAll("section")].find(s=>{const h=s.querySelector("h2");return s!==me&&h&&/^Ma trận sàn/.test(h.textContent.trim())});
    if(t&&me.nextElementSibling!==t)t.parentNode.insertBefore(me,t);
  }
  const mo=new MutationObserver(moveSec); mo.observe(document.body,{childList:true,subtree:true}); moveSec();
  setTimeout(()=>{moveSec();try{mo.disconnect()}catch(e){}},15000);
})();
