(function(){
  /* Gọn v4.15: tái cấu trúc menu 9 mục + tab Lợi nhuận (A/B), Việc cần làm, Dữ liệu & Giả định */
  var P=window.__PRO||{};
  var ALIAS={dt:"gr",pl5:"mg"};
  var fmtN=function(n,d){return Number(n).toLocaleString("vi-VN",{maximumFractionDigits:d||0,minimumFractionDigits:d||0})};
  var USD=function(n){return (n<0?"−":"")+"$"+fmtN(Math.abs(n))};
  var PCT=function(n,d){return fmtN(n,d==null?1:d)+"%"};
  var esc=function(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
  var $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  function secTitle(sec){var h=sec.querySelector("h2");return h?h.textContent.replace(/\s+/g," ").trim():""}
  function findSec(paneId,re){var pn=document.getElementById(paneId);if(!pn)return null;var r=null;$$("section",pn).forEach(function(s){if(!r&&re.test(secTitle(s)))r=s});return r}
  function mk(html){var t=document.createElement("template");t.innerHTML=html.trim();return t.content.firstChild}
  function ensure(k){ /* chạy builder của tab k (nếu chưa) trong lúc panel được bật tạm để biểu đồ đo đúng kích thước */
    if(typeof built==="undefined"||built[k]||!builders[k])return;var p=document.getElementById("p-"+k),was=p&&p.classList.contains("on");
    if(p&&!was)p.classList.add("on");try{builders[k]();built[k]=1}catch(e){console.warn("reorg ensure",k,e)}
    if(p&&!was)p.classList.remove("on")}
  function subLabel(txt,before){var d=mk('<div class="sub-grp">'+txt+'</div>');before.parentNode.insertBefore(d,before);return d}

  function init(){
    var inner=document.getElementById("tabinner");if(!inner||!$("#p-ov")||window.__REORG)return;window.__REORG=1;
    /* 0) mg phải dựng xong để lấy các mục của nó */
    if(typeof builders!=="undefined"&&builders.mg&&!built.mg){var pm=$("#p-mg"),wasOn=pm&&pm.classList.contains("on");if(pm)pm.classList.add("on");try{builders.mg();built.mg=1}catch(e){console.warn("mg",e)}if(pm&&!wasOn)pm.classList.remove("on")}
    /* 1) panels mới */
    var anchor=$("#p-bb");
    ["fc","td","dd"].forEach(function(k){var p=mk('<div class="panel" id="p-'+k+'" role="tabpanel"></div>');anchor.after(p);anchor=p});
    var pFc=$("#p-fc"),pTd=$("#p-td"),pDd=$("#p-dd"),pGr=$("#p-gr"),pMg=$("#p-mg");
    /* 2) di chuyển các mục */
    [/^Ma trận sàn/,/^Diễn biến theo thời gian$/,/^Theo dõi FC theo tuần/,/^Cơ cấu và bảng KPI/].forEach(function(re){var s=findSec("p-ov",re);if(s)pFc.appendChild(s)});
    var par=findSec("p-mg",/^Mức độ tập trung doanh thu/);if(par)pFc.appendChild(par);
    var hl=findSec("p-mg",/^Sức khỏe dữ liệu/);
    var dts=$$("section",$("#p-dt")),firstDt=null;
    dts.forEach(function(s){var t=secTitle(s);if(/^P&L PL5/.test(t))return;pGr.appendChild(s);if(!firstDt)firstDt=s});
    var pl5=findSec("p-dt",/^P&L PL5/);
    /* nhãn nhóm trong tab Sản phẩm */
    var f1=$("section",pGr);if(f1)subLabel("Theo nhóm sản phẩm",f1);if(firstDt)subLabel("Theo SKU",firstDt);
    /* tab Lợi nhuận: nhóm A (kết quả kinh doanh) + PL5 + nhóm B (dòng tiền) */
    var mgSecs=$$("section",pMg).filter(function(s){return s.style.display!=="none"&&!/^Mô phỏng/.test(secTitle(s))&&secTitle(s)!==""});
    var sim=findSec("p-mg",/^Mô phỏng giá & quảng cáo/);
    var a1=mgSecs[0];if(a1)subLabel("A · Kết quả kinh doanh",a1);
    if(pl5)pMg.appendChild(pl5);if(sim)pMg.appendChild(sim);
    var cashSec=buildCash();if(cashSec){var lb=mk('<div class="sub-grp">B · Dòng tiền &amp; vốn lưu động</div>');pMg.appendChild(lb);pMg.appendChild(cashSec)}
    /* chuyển nhanh A/B */
    var nav=mk('<div class="pf-nav"><button type="button" data-t="a">A · Kết quả kinh doanh</button><button type="button" data-t="b">B · Dòng tiền &amp; vốn lưu động</button></div>');
    pMg.insertBefore(nav,pMg.firstChild);
    nav.addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;var tg=b.dataset.t==="b"?$("#pf-cash"):$$(".sub-grp",pMg)[0];if(tg)tg.scrollIntoView({behavior:"smooth",block:"start"})});
    /* 3) tab bar */
    var old={};$$(".tab",inner).forEach(function(b){old[b.dataset.p]=b});
    function nb(k,label){var b=old[k];if(!b){b=document.createElement("button");b.className="tab";b.setAttribute("role","tab");b.setAttribute("aria-selected","false");b.dataset.p=k;b.addEventListener("click",function(){activate(k)})}b.textContent=label;return b}
    var grp=function(t){var s=document.createElement("span");s.className="tabgrp";s.textContent=t;return s}, dv=function(){var s=document.createElement("span");s.className="tabdiv";return s};
    while(inner.firstChild)inner.removeChild(inner.firstChild);
    [grp("Điều hành"),nb("ov","Tổng quan"),nb("fc","Doanh thu & Kế hoạch"),nb("mg","Lợi nhuận"),dv(),grp("Vận hành"),nb("gr","Sản phẩm"),nb("cp","Quảng cáo"),nb("inv","Tồn kho & Cung ứng"),nb("bb","Listing & Giá"),dv(),grp("Quản trị"),nb("td","Việc cần làm"),nb("dd","Dữ liệu & Giả định")].forEach(function(x){inner.appendChild(x)});
    /* 4) builders & activate */
    var oGr=builders.gr,oDt=builders.dt;
    builders.gr=function(){oGr();oDt()};
    builders.fc=function(){};
    builders.td=function(){buildTasks(pTd)};
    builders.dd=function(){Object.keys(builders).forEach(function(k){if(k!=="dd"&&k!=="td")ensure(k)});buildData(pDd)};
    var _act=window.activate;
    window.activate=function(k){k=ALIAS[k]||k;if(k==="mg")ensure("gr");return _act(k)};
    /* các mục chứa số liệu của tab khác */
    pFc.addEventListener("click",function(e){var r=e.target.closest("[data-sku],[data-grp]");if(!r)return;r.dataset.sku?window.proDrillSku&&window.proDrillSku(r.dataset.sku):window.proDrillGrp&&window.proDrillGrp(r.dataset.grp)});
    /* phần dữ liệu sức khỏe giữ lại để dd dùng */
    window.__hlSec=hl;if(hl)hl.style.display="none";
    /* "Xem thêm" ở Điều cần chú ý → tab Việc cần làm */
    document.addEventListener("click",function(e){var b=e.target.closest&&e.target.closest("#pi-more");if(!b)return;e.stopImmediatePropagation();e.preventDefault();activate("td")},true);
    /* hash cũ */
    document.dispatchEvent(new Event("reorg-ready"));
  }

  /* ===== B. Dòng tiền & vốn lưu động ===== */
  function buildCash(){
    if(typeof D==="undefined"||!D.invdet||!D.pl5||!D.pl5.available)return null;
    var uc={},acc={};(D.pl5.rows||[]).forEach(function(r){var a=acc[r.sku]||(acc[r.sku]={c:0,q:0});a.c+=r.cogs||0;a.q+=r.q||0});
    Object.keys(acc).forEach(function(k){if(acc[k].q>0&&acc[k].c>0)uc[k]=acc[k].c/acc[k].q});
    var st=(D.invdet.sku_tot||[]).filter(function(x){return x.qty>0});
    var totQ=st.reduce(function(s,x){return s+x.qty},0), prQ=0,val=0,unp=[];
    var byGrp={},slow=[],slowV=0,slowQ=0;var SLOW_W=26;
    st.forEach(function(x){var u=uc[x.sku];if(u==null){unp.push(x);return}var v=x.qty*u;prQ+=x.qty;val+=v;
      var g=byGrp[x.grp]||(byGrp[x.grp]={v:0,q:0});g.v+=v;g.q+=x.qty;
      var isSlow=(x.sold_month===0||x.sold_month==null)||(x.weeks!=null&&x.weeks>SLOW_W);
      if(isSlow){slowV+=v;slowQ+=x.qty}
      slow.push({sku:x.sku,grp:x.grp,qty:x.qty,v:v,w:x.weeks,sm:x.sold_month,slow:isSlow})});
    var src={};(D.invdet.rows||[]).forEach(function(r){if(!(r.qty>0)||uc[r.sku]==null)return;var s=src[r.stlab]||(src[r.stlab]={v:0,q:0});s.v+=r.qty*uc[r.sku];s.q+=r.qty});
    var old271=0,old271q=0,old271u=0;["amz","wf"].forEach(function(k){var L=(D.lt&&D.lt[k]&&D.lt[k].sku)||[];L.forEach(function(x){var q=(x.buckets[3]||0)+(x.buckets[4]||0);old271q+=q;if(uc[x.sku]!=null)old271+=q*uc[x.sku];else old271u+=q})});
    var cogsW=D.pl5.total.cogs||0, wk=cogsW>0?val/cogsW:null;
    var unpQ=totQ-prQ;
    var tile=function(k,v,s,c){return '<div class="ptile" style="--tc:'+(c||"var(--accent)")+'"><div class="k">'+k+'</div><div class="v">'+v+'</div><div class="s">'+(s||"")+'</div></div>'};
    var whNow=D.pl5.total.wh_fee||0, whPrev=(D.pl5.prev_total||{}).wh_fee;
    var tiles='<div class="pro-grid g4">'
      +tile("Giá trị tồn kho (theo giá vốn)",USD(val),"đã định giá "+PCT(totQ?prQ/totQ*100:0,0)+" số lượng tồn; phần còn lại chưa có giá vốn")
      +tile("Số tuần tồn kho bình quân",wk==null?"—":fmtN(wk,1),wk==null?"":"≈ "+fmtN(wk*7,0)+" ngày · so với giá vốn bán ra "+USD(cogsW)+"/tuần","var(--s3)")
      +tile("Vốn nằm ở tồn chậm",USD(slowV),fmtN(slowQ)+" sản phẩm · chưa bán trong tháng hoặc đủ bán > "+SLOW_W+" tuần ("+PCT(val?slowV/val*100:0,0)+" giá trị tồn)","var(--warn)")
      +tile("Vốn nằm ở tồn ≥ 271 ngày",old271>0?"≥ "+USD(old271):"—",fmtN(old271q)+" sản phẩm ở FBA &amp; CastleGate"+(old271u?" · "+fmtN(old271u)+" chưa có giá vốn":""),"var(--bad)")
      +'</div>';
    /* nguồn kho */
    var sk=Object.keys(src).sort(function(a,b){return src[b].v-src[a].v}),mx=Math.max.apply(null,sk.map(function(k){return src[k].v}).concat([1]));
    var srcH='<div class="card"><h3>Vốn theo nguồn kho</h3><div class="hb">'+sk.map(function(k){return '<div class="r"><span>'+esc(k)+'</span><b>'+USD(src[k].v)+' <small style="font-weight:400;color:var(--muted)">· '+PCT(val?src[k].v/val*100:0,0)+' · '+fmtN(src[k].q)+' sp</small></b><div class="tr"><i style="width:'+src[k].v/mx*100+'%"></i></div></div>'}).join("")+'</div></div>';
    /* theo nhóm */
    var gk=Object.keys(byGrp).sort(function(a,b){return byGrp[b].v-byGrp[a].v}).slice(0,6),gm=Math.max.apply(null,gk.map(function(k){return byGrp[k].v}).concat([1]));
    var sh=function(g){return String(g).replace(/^Acacia\s*-\s*|^Arozu\s*-\s*/,"").replace(/\s*-\s*Wooden Bed Frame.*$/i,"")};
    var grpH='<div class="card"><h3>Vốn theo nhóm sản phẩm</h3><div class="hb">'+gk.map(function(k){return '<div class="r"><span title="'+esc(k)+'">'+esc(sh(k))+'</span><b>'+USD(byGrp[k].v)+' <small style="font-weight:400;color:var(--muted)">· '+PCT(val?byGrp[k].v/val*100:0,0)+'</small></b><div class="tr"><i style="width:'+byGrp[k].v/gm*100+'%"></i></div></div>'}).join("")+'</div></div>';
    /* top SKU giữ nhiều tiền */
    var top=slow.sort(function(a,b){return b.v-a.v}).slice(0,10);
    var topH='<div class="card" style="margin-top:14px"><h3>10 SKU đang giữ nhiều vốn nhất</h3><div class="scroll"><table><thead><tr><th>SKU</th><th>Nhóm</th><th>Tồn</th><th>Giá trị</th><th>Đủ bán (tuần)</th><th>Tình trạng</th></tr></thead><tbody>'
      +top.map(function(x){var tg=x.slow?(x.sm?'<span class="sev s2">Dư tồn</span>':'<span class="sev s3">Chưa bán</span>'):'<span class="sev s1">Bình thường</span>';return '<tr><td><b>'+esc(x.sku)+'</b></td><td>'+esc(sh(x.grp))+'</td><td>'+fmtN(x.qty)+'</td><td>'+USD(x.v)+'</td><td>'+(x.w==null?"—":fmtN(x.w,1))+'</td><td>'+tg+'</td></tr>'}).join("")+'</tbody></table></div></div>';
    /* chi phí giữ hàng + chưa định giá */
    var cost='<div class="card"><h3>Chi phí giữ hàng</h3><table><thead><tr><th>Khoản</th><th>Tuần này</th><th>Tuần trước</th></tr></thead><tbody>'
      +'<tr><td>Phí kho (warehouse fee)</td><td>'+USD(whNow)+(whNow===0&&whPrev>0?' <span class="sev s2">cần kiểm tra</span>':'')+'</td><td>'+(whPrev==null?"—":USD(whPrev))+'</td></tr>'
      +'<tr><td>Phí vận hành (op fee)</td><td>'+USD(D.pl5.total.op_fee||0)+'</td><td>'+(D.pl5.prev_total&&D.pl5.prev_total.op_fee!=null?USD(D.pl5.prev_total.op_fee):"—")+'</td></tr>'
      +'<tr><td>Phụ phí tồn lâu (long-term storage)</td><td colspan="2"><span class="muted">chưa có số thật từ báo cáo phí của sàn</span></td></tr></tbody></table></div>';
    var unpH='<div class="card"><h3>Tồn chưa có giá vốn ('+fmtN(unpQ)+' sản phẩm · '+unp.length+' SKU)</h3><p class="cap" style="margin:0 0 6px">Thường là SKU không có đơn trong tuần nên P&amp;L không có giá vốn. Đây cũng là nhóm dễ nằm lâu nhất, nên giá trị vốn thực tế <b>cao hơn</b> con số trên.</p>'
      +'<div class="scroll"><table><thead><tr><th>SKU</th><th>Nhóm</th><th>Tồn</th></tr></thead><tbody>'+unp.sort(function(a,b){return b.qty-a.qty}).slice(0,8).map(function(x){return '<tr><td><b>'+esc(x.sku)+'</b></td><td>'+esc(sh(x.grp))+'</td><td>'+fmtN(x.qty)+'</td></tr>'}).join("")+'</tbody></table></div></div>';
    var soon='<div class="card"><h3>Tiền sắp ra · tiền sắp vào</h3><p class="cap" style="margin:0">Cần thêm: hóa đơn và điều khoản thanh toán nhà cung cấp, đơn nhập đang về và cước vận chuyển, báo cáo thanh toán của Amazon và Wayfair, số dư tiền. Xem mục "Dữ liệu còn thiếu" ở tab Dữ liệu &amp; Giả định.</p></div>';
    var html='<section class="pro-sec" id="pf-cash"><details class="fold" open><summary><div class="shead"><span class="snum">06</span><h2>Dòng tiền &amp; vốn lưu động</h2><span class="hint">tiền đang nằm trong tồn kho · chi phí giữ hàng · tiền sắp ra/vào</span></div></summary><div class="foldbody">'
      +tiles+'<div class="pro-grid g2" style="margin-top:14px">'+srcH+grpH+'</div>'+topH+'<div class="pro-grid g2" style="margin-top:14px">'+cost+unpH+'</div><div style="margin-top:14px">'+soon+'</div></div></details></section>';
    return mk(html);
  }

  /* ===== Việc cần làm ===== */
  function buildTasks(pn){
    var IS=(P.issues||[]),TK=(P.tasks||[]),tk={};TK.forEach(function(t){if(t.key)tk[t.key]=t});
    var SEV={3:"Ưu tiên cao",2:"Ưu tiên vừa",1:"Theo dõi"},DUE={3:7,2:14,1:28};
    var STA={todo:"Chưa làm",doing:"Đang làm",done:"Xong",dismissed:"Bỏ qua"};
    var cnt={todo:0,doing:0,done:0};TK.forEach(function(t){if(cnt[t.status]!=null)cnt[t.status]++});
    var today=new Date().toISOString().slice(0,10),late=TK.filter(function(t){return(t.status==="todo"||t.status==="doing")&&t.due&&t.due<today}).length;
    var tile=function(k,v,s,c){return '<div class="ptile" style="--tc:'+(c||"var(--accent)")+'"><div class="k">'+k+'</div><div class="v">'+v+'</div><div class="s">'+(s||"")+'</div></div>'};
    var by=(P.summary&&P.summary.by_sev)||{};
    var head='<div class="pro-grid g4">'+tile("Điểm cần xử lý",fmtN(IS.length),"ưu tiên cao "+(by[3]||0)+" · vừa "+(by[2]||0)+" · theo dõi "+(by[1]||0))
      +tile("Đang làm / chưa làm",fmtN(cnt.doing)+" / "+fmtN(cnt.todo),TK.length?"theo bảng công việc của ứng dụng":"chưa có công việc nào được tạo từ ứng dụng","var(--s3)")
      +tile("Quá hạn",fmtN(late),"hạn đã qua mà chưa xong","var(--bad)")+tile("Đã xong",fmtN(cnt.done),"trong kỳ báo cáo","var(--good,var(--accent))")+'</div>';
    var short=function(w){var x=String(w||"").replace(/^Nhóm sản phẩm:\s*|^Nhóm:\s*|^Kênh:\s*/,"");(D.meta.groups||[]).forEach(function(g){x=x.split(g).join(g.replace(/^Acacia\s*-\s*|^Arozu\s*-\s*/,"").replace(/\s*-\s*Wooden Bed Frame.*$/i,""))});return x};
    var rows=IS.slice().sort(function(a,b){return b.sev-a.sev||(b.impact||0)-(a.impact||0)}).map(function(i){var t=tk[i.key]||{};var st=t.status&&STA[t.status]?STA[t.status]:"Chưa giao";
      var due=t.due?t.due:"";var dueH=due?(due<today&&t.status!=="done"?'<span style="color:var(--bad-ink)">'+esc(due)+' · quá hạn</span>':esc(due)):'<span class="muted" title="Hạn đề xuất theo mức ưu tiên">≤ '+DUE[i.sev]+' ngày (đề xuất)</span>';
      return '<tr><td><span class="sev s'+i.sev+'">'+SEV[i.sev]+'</span></td><td>'+esc(i.area)+'</td><td><b>'+esc(i.title)+'</b><div class="muted" style="font-size:12px">'+esc(short(i.where))+'</div>'+(i.impact_note?'<div class="muted" style="font-size:12px">Ảnh hưởng ước tính: '+esc(i.impact_note)+'</div>':'')+'</td><td>'+(i.fix&&i.fix.length?i.fix.slice(0,2).map(function(x){return '<div style="margin-bottom:4px">'+esc(x)+'</div>'}).join(""):"—")+'</td><td>'+(t.owner?esc(t.owner):'<span class="muted">Chưa phân công</span>')+'</td><td>'+dueH+'</td><td>'+st+'</td></tr>'}).join("");
    var qs=(P.questions||[]);
    pn.innerHTML='<section class="pro-sec" style="margin-top:0"><div class="shead"><span class="snum">01</span><h2>Bảng việc cần làm</h2><span class="hint">gộp từ các điểm cần chú ý · phụ trách và hạn lấy từ bảng công việc của ứng dụng</span></div>'+head
      +'<div class="card" style="margin-top:14px"><div class="scroll"><table id="tbl-td" class="tl"><thead><tr><th>Mức</th><th>Khu vực</th><th>Vấn đề · nằm ở</th><th>Giải pháp trước mắt</th><th>Phụ trách</th><th>Hạn</th><th>Trạng thái</th></tr></thead><tbody>'+(rows||'<tr><td colspan="7">Không có điểm cần xử lý.</td></tr>')+'</tbody></table></div></div></section>'
      +(qs.length?'<section class="pro-sec"><div class="shead"><span class="snum">02</span><h2>Cần chốt trong buổi họp</h2></div><div class="card"><ol style="margin:0 0 0 18px;padding:0;line-height:1.7">'+qs.map(function(q){return '<li>'+esc(q)+'</li>'}).join("")+'</ol></div></section>':"");
    if(typeof TBL!=="undefined")TBL["tbl-td"]={n:12};
  }

  /* ===== Dữ liệu & Giả định ===== */
  function buildData(pn){
    var m=D.meta||{},fx=(D.fx&&D.fx.rates)||{};
    var rowsK=[["Kỳ dữ liệu",esc(m.d0||"")+" → "+esc(m.d1||"")+" (tuần "+esc(m.week_no||"")+")"],
      ["Tỷ giá quy đổi USD",(fx.CAD?"1 CAD = "+fx.CAD+" USD · ":"")+(fx.AUD?"1 AUD = "+fx.AUD+" USD · ":"")+"tham chiếu ECB, một tỷ giá cố định cho mọi kỳ (constant-currency) để so sánh không bị nhiễu tỷ giá"],
      ["Độ phủ PL5",(D.pl5&&D.pl5.coverage_pct!=null?PCT(D.pl5.coverage_pct,1):"—")+" doanh thu đã tính được lợi nhuận"],
      ["Cách tính PL5",D.pl5&&typeof D.pl5.why==="string"?esc(D.pl5.why):"—"],
      ["Giá vốn","Giá vốn trong file P&amp;L đã gồm cước nhập hàng và một số chi phí khác"],
      ["Chi phí quảng cáo trong PL5","Cột SEM trong file P&amp;L là số tạm tính theo tỷ lệ %; khi có chi phí thực tế sẽ tính theo thực tế"],
      ["Số liệu giả lập","Mục 'Sản phẩm bán không đạt' (nhãn nguyên nhân MOCK) chưa phải số thật"]];
    var need=[["Giá vốn chuẩn của toàn bộ SKU","Bảng COGS đơn vị (sheet COGS chuẩn trong file P&amp;L) cho cả SKU không có đơn trong tuần","Định giá đủ tồn kho, vốn bị chôn thật"],
      ["Hóa đơn và điều khoản thanh toán nhà cung cấp","Tiền cọc, đơn đang sản xuất, kỳ hạn trả","Tiền sắp ra"],
      ["Báo cáo thanh toán Amazon và Wayfair","Settlement / remittance theo ngày","Tiền sắp vào, chu kỳ thu tiền"],
      ["Hàng đang vận chuyển và cước nhập hàng","Container, PO đang về, chi phí vận chuyển","Vốn đang trên đường, cước nhập"],
      ["Báo cáo phí lưu kho và phụ phí tồn lâu","Storage fee / long-term storage fee thật","Chi phí giữ hàng thực tế"],
      ["Phí kho (warehouse fee) tuần này","Tuần này đang ghi $0 trong khi tuần trước có phí","Biên lợi nhuận có thể đang đẹp hơn thực tế"],
      ["Đánh giá sao, lý do trả hàng, khiếu nại","Amazon Returns/Reviews, Wayfair Returns","Chất lượng sản phẩm thật (hiện chỉ đo gián tiếp)"],
      ["Buy Box, đối thủ","Báo cáo Buy Box, dữ liệu giá đối thủ","Mục Listing &amp; Giá, Đối thủ"],
      ["Báo cáo quảng cáo Shopify và Walmart","File chi tiêu theo ngày · theo SKU của hai sàn","TACoS phủ đủ các sàn"],
      ["Báo cáo quảng cáo Amazon cấp SKU (Advertised Product)","Hiện PL5 Amazon đang chia đều chi phí quảng cáo theo nhóm × quốc gia","Biên theo SKU của Amazon chính xác hơn"],
      ["Chi phí quảng cáo thực tế để thay cột SEM tạm tính","Số thực tế theo kênh/SKU (xem đối chiếu ở Quảng cáo › mục 02)","Biên PL5 phản ánh đúng chi phí quảng cáo"],
      ["Phí sàn thực tế Shopify CAN/AUS và Walmart","Sheet tính phí tương ứng trong file P&amp;L","PL5 của các kênh này"]];
    pn.innerHTML='<section class="pro-sec" style="margin-top:0"><div class="shead"><span class="snum">01</span><h2>Nguồn &amp; phương pháp</h2><span class="hint">để kiểm chứng số liệu</span></div><div class="card"><table class="tl"><tbody>'+rowsK.map(function(r){return '<tr><td style="width:200px"><b>'+r[0]+'</b></td><td>'+r[1]+'</td></tr>'}).join("")+'</tbody></table></div></section>'
     +'<div id="dd-health"></div>'
     +'<section class="pro-sec"><div class="shead"><span class="snum">03</span><h2>Dữ liệu còn thiếu</h2><span class="hint">bổ sung để các mục "đang phát triển" hoàn chỉnh</span></div><div class="card"><div class="scroll"><table class="tl"><thead><tr><th>Cần bổ sung</th><th>Chi tiết file</th><th>Giúp được</th></tr></thead><tbody>'+need.map(function(r){return '<tr><td><b>'+r[0]+'</b></td><td>'+r[1]+'</td><td>'+r[2]+'</td></tr>'}).join("")+'</tbody></table></div></div></section>'
     +'<section class="pro-sec"><div class="shead"><span class="snum">04</span><h2>Chú thích theo từng mục</h2><span class="hint">gom về một chỗ</span></div><div id="dd-notes"></div></section>';
    var hl=window.__hlSec;if(hl){hl.style.display="";var hd=hl.querySelector("details");if(hd)hd.open=true;$("#dd-health",pn).appendChild(hl)}
    var gs=findSec("p-inv",/^Giả định/);if(gs){gs.style.display="";pn.appendChild(gs)}
    /* chú thích gập: gom về đây (không gồm Chi tiết từng mục của Điều cần chú ý) */
    var nm={ov:"Tổng quan",fc:"Doanh thu & Kế hoạch",mg:"Lợi nhuận",gr:"Sản phẩm",dt:"Sản phẩm",cp:"Quảng cáo",inv:"Tồn kho",bb:"Listing & Giá"},box=$("#dd-notes",pn);
    $$("details.capfold").forEach(function(d){if(d.closest("#pro-ins")||d.closest("#p-dd"))return;
      var txt=d.textContent.replace(/\s+/g," ").trim();if(txt.length<40)return;
      var pane=d.closest(".panel"),k=pane?pane.id.replace("p-",""):"",sec=d.closest("section"),t=sec?secTitle(sec):"";
      var w=mk('<div class="nt-item"><div class="nt-h">'+esc((nm[k]||"")+(t?" › "+t:""))+'</div></div>');w.appendChild(d);box.appendChild(w)});
  }

  setTimeout(init,0);
})();
