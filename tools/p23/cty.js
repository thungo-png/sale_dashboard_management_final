/* ===== Gọn v4.3 – Đợt 1: tách theo quốc gia ===== */
(function(){
  const CTYS=(D.meta&&D.meta.ctys)||["US","CAN","AUS"];
  window.CTYF="";                                     // "" = tất cả quốc gia
  const F=v=>(v<0?"−":"")+N(Math.abs(v));
  const FU=v=>(v<0?"−":"")+"$"+N(Math.abs(v));
  const P1=v=>(v<0?"−":"")+pc0(Math.abs(v));
  const sum=(a,f)=>a.reduce((s,x)=>s+(+f(x)||0),0);

  /* 1) Thanh chọn quốc gia dùng chung */
  let BAR=null;
  function bar(){
    let h=BAR;
    if(!h){BAR=h=document.createElement("div"); h.id="ctybar"; h.className="ctyseg"; h.setAttribute("role","group"); h.setAttribute("aria-label","Lọc theo quốc gia");}
    h.innerHTML=[""].concat(CTYS).map(c=>
      `<button type="button" class="pick" data-c="${c}" aria-pressed="${c===CTYF}">${c||"All"}</button>`).join("");
    h.querySelectorAll(".pick").forEach(b=>b.addEventListener("click",()=>setCty(b.dataset.c)));
    place();
  }
  /* bộ lọc nằm cùng hàng với ô chọn thời gian (Tổng quan: ngay trước ô "7 ngày qua"); các tab khác: góc phải tiêu đề mục đầu tiên */
  function place(){
    const h=BAR; if(!h)return;
    const rng=document.getElementById("rng"), pn=document.querySelector(".panel.on");
    if(rng&&pn&&pn.contains(rng)){const m=rng.parentElement; if(h.parentElement!==m||h.nextElementSibling!==rng)m.insertBefore(h,rng); h.classList.remove("alone"); return}
    const sh=pn&&[...pn.querySelectorAll(".shead")].find(e=>e.offsetParent);
    if(sh){if(h.parentElement!==sh)sh.appendChild(h); h.classList.add("alone")}
    else if(!h.isConnected){const w=document.querySelector(".wrap");if(w){w.insertBefore(h,w.firstChild);h.classList.add("alone")}}
  }
  document.addEventListener("click",e=>{if(e.target.closest&&e.target.closest(".tab,nav,[role=tab]"))setTimeout(place,60)},true);
  window.addEventListener("hashchange",()=>setTimeout(place,60));
  setInterval(place,1500);
  function rebuildAll(){      // dựng lại từng tab đã mở; một tab lỗi không chặn các tab còn lại (rebuild() gốc dừng ở lỗi đầu tiên)
    Object.keys(built).forEach(k=>{try{
      if(k==="mk"){const p=document.getElementById("p-mk"),keep=window.__mkMoved||[];if(p)[...p.children].forEach(ch=>{if(!keep.includes(ch))ch.remove()})}   // tab Thị trường tự nối thêm khi dựng lại → dọn trước
      builders[k]()}catch(e){if(!/ovcurcap|innerHTML/.test(String(e)))console.warn("rebuild",k,e)}});
    try{window.__dashRebuild&&window.__dashRebuild()}catch(e){}   // Tổng quan của gói Pro
  }
  function setCty(c){
    CTYF=(c===CTYF?"":c);
    try{DTF3.cty=CTYF;}catch(e){}
    try{INVCTY=CTYF||"ALL";}catch(e){}
    try{LTF.cty=CTYF;}catch(e){}
    try{GCMP_CTY=CTYF||null;}catch(e){}
    try{CMPCTY=CTYF||null;}catch(e){}
    try{applyCty(CTYF)}catch(e){console.error("applyCty",e)}
    try{BMP=null;BGRP=null}catch(e){}
    bar(); rebuildAll(); place(); ctyOv(); ctyPl(); (window.CTYHOOK||[]).forEach(f=>{try{f()}catch(e){}});
  }
  window.setCty=setCty;

  /* 2) Thẻ tóm tắt theo quốc gia (Tổng quan) */
  function ctyStats(c){
    const S0=window.D0||D, cells=S0.cell.filter(x=>x.cty===c), prev=S0.cell_prev.filter(x=>x.cty===c);
    const r=sum(cells,x=>x.r), rfc=sum(cells,x=>x.rfc), pr=sum(prev,x=>x.r);
    const pm=(S0.pl5&&S0.pl5.by_mpcty)||{}, pk=Object.keys(pm).filter(k=>k.endsWith("|"+c));
    const plr=sum(pk,k=>pm[k].r), plp=sum(pk,k=>pm[k].profit);
    const spend=sum((S0.adsum||[]).filter(x=>x.cty===c),x=>x.spend);
    const inv=((D.invdet&&D.invdet.cty_totals)||[]).find(x=>x.cty===c);
    const bc=((S0.pl5&&S0.pl5.below_cogs)||[]).filter(x=>x.cty===c);
    let worst=null; pk.forEach(k=>{if(!worst||pm[k].profit<pm[worst].profit)worst=k});
    const lowFc=cells.filter(x=>x.rfc>0).map(x=>({k:x.mp,a:x.r/x.rfc*100,gap:x.rfc-x.r})).sort((a,b)=>b.gap-a.gap)[0];
    return {c,r,rfc,pr,plr,plp,spend,inv:inv?inv.qty:0,bc,worst,wp:worst?pm[worst]:null,lowFc,np:pk.length};
  }
  function ctyOv(){
    const host=document.getElementById("ctysum"); if(!host)return;
    const S=CTYS.map(ctyStats), tot=sum(S,x=>x.r), TT=sum((window.D0||D).cell,x=>x.r);
    host.innerHTML=S.map(s=>{
      const a=s.rfc?s.r/s.rfc*100:null, d=s.pr?(s.r/s.pr-1)*100:null, m=s.plr?s.plp/s.plr*100:null;
      let issue="", fix="";
      if(s.wp&&s.wp.profit<0){
        const mp=s.worst.split("|")[0], nb=s.bc.filter(x=>x.mp===mp).length;
        issue=`${mp} ${s.c}: Profit PL5 ${FU(s.wp.profit)} (biên ${P1(s.wp.margin)}).`;
        fix=nb?`Rà giá bán/khuyến mãi của ${nb} SKU đang thấp hơn giá vốn, và giảm quảng cáo ở các SKU này.`:"Rà giá vốn, phí kênh và quảng cáo của kênh này theo bảng Profit PL5 theo quốc gia × sàn.";
      } else if(s.lowFc&&s.lowFc.a<85){
        issue=`${s.lowFc.k} ${s.c}: doanh thu mới đạt ${pc0(s.lowFc.a)} so với FC (còn thiếu ${FU(s.lowFc.gap)}).`;
        fix="Xem tab Nhóm sản phẩm để biết SKU và nhóm kéo FC xuống, ưu tiên tồn kho và giá.";
      } else { issue="Chưa có điểm nào cần xử lý gấp trong tuần này."; fix="Giữ nhịp hiện tại và theo dõi tồn kho."; }
      const tacos=s.r?s.spend/s.r*100:null;
      return `<button type="button" class="ctyc${CTYF===s.c?" on":""}" data-c="${s.c}" aria-pressed="${CTYF===s.c}">
        <div class="ch"><b>${s.c}</b><span>${tot?pc0(s.r/tot*100):"—"} doanh thu toàn danh mục</span></div>
        <div class="cv">${FU(s.r)}</div>
        <div class="cs">${a===null?"không có FC":`<b class="${ach(a)}">${pc0(a)}</b> so với FC`}${d===null?"":` · <b class="${d>=0?"up":"dn"}">${d>=0?"↑":"↓"} ${pc0(Math.abs(d))}</b> so với tuần trước`}</div>
        <div class="cg">
          <span>Profit PL5</span><b class="${s.plp<0?"down":"up"}">${s.np?FU(s.plp):"chưa có"}${m===null?"":` <small>(${P1(m)})</small>`}</b>
          <span>Chi phí QC · TACoS</span><b>${FU(s.spend)}${tacos===null?"":` <small>(${pc0(tacos)})</small>`}</b>
          <span>Tồn kho</span><b>${N(s.inv)} <small>sản phẩm</small></b>
        </div>
        <div class="ci"><b>Vấn đề nằm ở đâu:</b> ${issue}<br><b>Hướng xử lý:</b> ${fix}</div></button>`;
    }).join("");
    host.querySelectorAll(".ctyc").forEach(b=>b.addEventListener("click",()=>setCty(b.dataset.c)));
    const cap=document.getElementById("ctysumcap");
    if(cap){const chk=Math.abs(tot-TT)<1;cap.innerHTML=`Mỗi thẻ là một thị trường (USD sau quy đổi; CAD và AUD theo tỷ giá cố định của kỳ). Bấm vào thẻ để lọc cả báo cáo theo quốc gia đó, bấm lần nữa để bỏ lọc. Tổng ba thị trường ${chk?"khớp":"<b>lệch</b> so với"} tổng doanh thu toàn danh mục (${FU(TT)}). Profit PL5 của AUS hiện chỉ gồm các kênh đã có công thức (Amazon, Shopify).`}
  }

  /* 3) Bảng Profit PL5 theo quốc gia × sàn */
  function ctyPl(){
    const tb=document.querySelector("#tbl-plmc tbody"), tf=document.querySelector("#tbl-plmc tfoot"); if(!tb)return;
    const rows=((window.D0||D).pl5&&(window.D0||D).pl5.rows)||[]; const keys=["r","cogs","ref_fee","sem","wh_fee","fulfill","profit","q"];
    const agg=(f)=>{const o={n:0};keys.forEach(k=>o[k]=0);rows.filter(f).forEach(x=>{keys.forEach(k=>o[k]+=(+x[k]||0));if(x.q>0&&x.cogs>x.r+0.005)o.n++});return o};
    const cs=CTYF?[CTYF]:CTYS; let html="";
    const line=(c,m,o,cls)=>`<tr class="${cls||""}"><td>${c}</td><td>${m}</td><td>${F(o.r)}</td><td>${F(o.cogs)}</td><td>${F(o.ref_fee)}</td><td>${F(o.sem)}</td><td>${F(o.wh_fee)}</td><td>${F(o.fulfill)}</td>
      <td class="${o.profit<0?"down":"up"}">${F(o.profit)}</td><td class="${o.profit<0?"down":"up"}">${o.r?P1(o.profit/o.r*100):"—"}</td><td>${N(o.q)}</td><td>${o.n?`<span class="chip w">${o.n} SKU</span>`:"—"}</td></tr>`;
    cs.forEach(c=>{
      const mps=MP.filter(m=>rows.some(x=>x.cty===c&&x.mp===m));
      mps.forEach(m=>{html+=line(c,m,agg(x=>x.cty===c&&x.mp===m))});
      if(mps.length>1&&!CTYF)html+=line(c,"<b>Tổng "+c+"</b>",agg(x=>x.cty===c),"sub");
    });
    const g=agg(x=>cs.includes(x.cty));
    const un=(!CTYF&&(window.D0||D).pl5&&(window.D0||D).pl5.total&&+(window.D0||D).pl5.total.sem_unalloc)||0;     // chi phí quảng cáo chưa gán được cho SKU nào: giữ riêng để tổng khớp Profit PL5 toàn danh mục
    if(un>0.5){html+=`<tr><td>—</td><td>QC chưa gán SKU</td><td>0</td><td>0</td><td>0</td><td>${F(un)}</td><td>0</td><td>0</td><td class="down">${F(-un)}</td><td>—</td><td>0</td><td>—</td></tr>`;g.sem+=un;g.profit-=un;}
    tb.innerHTML=html;
    tf.innerHTML=line(CTYF||"Tất cả","<b>Tổng</b>",g);
    const cap=document.getElementById("plmccap");
    if(cap){const t=(window.D0||D).pl5&&(window.D0||D).pl5.total, ok=!CTYF&&t&&Math.abs(g.profit-t.profit)<1;
      cap.innerHTML=`Cùng công thức Profit PL5 với bảng theo SKU phía dưới (Doanh thu − COGS − phí sàn − quảng cáo − Warehouse fee − Fulfillment FBA; không tính Return). Cột “giá &lt; COGS” đếm số SKU bán thấp hơn giá vốn.${CTYF?` Đang lọc riêng ${CTYF}.`:(ok?" Tổng khớp với Profit PL5 toàn danh mục.":"")}`}
  }

  /* 4) Top SKU theo quốc gia (bảng Top 10 ở tab Nhóm sản phẩm) */
  if(typeof grTop==="function"){
    const _g=grTop;
    grTop=function(){
      _g(); if(!CTYF||!D.sku)return;
      const nm={}; (D.sku_meta||[]).forEach(m=>nm[m.sku]=m.name);
      const A={}; D.sku.filter(x=>x.cty===CTYF).forEach(x=>{const a=A[x.sku]||(A[x.sku]={sku:x.sku,grp:x.grp,q:0,r:0,rfc:0});a.q+=x.q;a.r+=x.r;a.rfc+=(x.rfc||0)});
      const L=Object.values(A);
      const chip=g=>`<span class="chip" style="background:${css(GC(g))};color:#fff">${short(g)}</span>`;
      const best=L.filter(x=>x.r>0).sort((a,b)=>b.r-a.r).slice(0,10);
      const worst=L.filter(x=>x.rfc>0&&x.r<x.rfc).map(x=>({...x,ach:x.r/x.rfc*100,gap:x.rfc-x.r})).sort((a,b)=>b.gap-a.gap).slice(0,10);
      document.querySelector("#tbl-gbest tbody").innerHTML=best.map((x,i)=>{const a=x.rfc?x.r/x.rfc*100:null;
        return `<tr><td class="mono">${i+1}</td><td class="mono">${x.sku}<span class="sub-asin">${nm[x.sku]||""}</span></td><td>${chip(x.grp)}</td><td>${N(x.q)}</td><td>${N(x.r)}</td><td>${x.q?N(x.r/x.q):"—"}</td>
        <td class="${a===null?"":ach(a)}">${a===null?'<span class="chip w">không có FC</span>':pc0(a)}</td></tr>`}).join("")||`<tr><td colspan="7">Không có dữ liệu ${CTYF}</td></tr>`;
      document.querySelector("#tbl-gworst tbody").innerHTML=worst.map((x,i)=>
        `<tr><td class="mono">${i+1}</td><td class="mono">${x.sku}<span class="sub-asin">${nm[x.sku]||""}</span></td><td>${chip(x.grp)}</td><td>${N(x.q)}</td><td>${N(x.r)}</td><td>${N(x.rfc)}</td><td class="${ach(x.ach)}">${pc0(x.ach)}</td><td>${N(x.gap)}</td></tr>`).join("")||`<tr><td colspan="8">Không có SKU thiếu FC ở ${CTYF}</td></tr>`;
      const c=document.getElementById("gtopcap"); if(c)c.innerHTML=`Đang lọc quốc gia <b>${CTYF}</b>: ${N(L.length)} SKU có dữ liệu, gộp các sàn của quốc gia này. Tiền tệ: <b>USD sau quy đổi</b>.`;
    };
  }

  /* 5) Gắn vào vòng dựng của từng tab */
  const _b=builders;
  const wrap=(k,fn)=>{const o=_b[k];_b[k]=function(){o();fn()}};
  wrap("ov",ctyOv); wrap("dt",ctyPl);
  bar(); ctyOv(); try{ctyPl();}catch(e){}

  /* 6) Gói Pro chuyển mục "P&L PL5" sang tab Lợi nhuận: đưa bảng quốc gia × sàn đi cùng, đứng ngay trước */
  function moveSec(){
    const me=document.getElementById("plmc-sec"); if(!me)return;
    const t=[...document.querySelectorAll("section")].find(s=>{const h=s.querySelector("h2");return s!==me&&h&&/^P&L PL5/.test(h.textContent.trim())});
    if(t&&me.nextElementSibling!==t)t.parentNode.insertBefore(me,t);
  }
  const mo=new MutationObserver(moveSec); mo.observe(document.body,{childList:true,subtree:true}); moveSec();
  setTimeout(()=>{moveSec();try{mo.disconnect()}catch(e){}},15000);
})();
