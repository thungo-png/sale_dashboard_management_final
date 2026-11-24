/* ===== v4_16: sửa nội dung theo phản biện (A–F). Chạy sau reorg.js (setTimeout) ===== */
(function(){
  try{ if(D.meta&&D.meta.curm) document.title="Sale Report — "+D.meta.curm; }catch(e){}
  var $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var esc=function(x){return String(x==null?"":x).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
  var fN=function(n,d){return Number(n).toLocaleString("vi-VN",{maximumFractionDigits:d||0,minimumFractionDigits:d||0})};
  var USD=function(n){return (n<0?"−":"")+"$"+fN(Math.abs(n))};
  var PC=function(n,d){return (n<0?"−":"")+fN(Math.abs(n),d==null?1:d)+"%"};
  var mk=function(h){var t=document.createElement("div");t.innerHTML=h.trim();return t.firstChild};
  var sum=function(a,f){return a.reduce(function(s,x){return s+(+f(x)||0)},0)};
  var plRows=(D.pl5&&D.pl5.rows)||[];

  /* ---------- B. đối chiếu chi phí quảng cáo: báo cáo QC ↔ file P&L (SEM) ---------- */
  function adRecon(){
    var sem={},cell={};plRows.forEach(function(x){var k=x.mp+"|"+x.cty;sem[k]=(sem[k]||0)+(x.sem||0)});
    (D.cell||[]).forEach(function(c){cell[c.mp+"|"+c.cty]=c.r});
    var rows=(D.adsum||[]).map(function(a){var k=a.mp+"|"+a.cty,s=sem[k]||0;
      return {k:a.mp+" · "+a.cty,sp:a.spend,sem:s,diff:a.spend-s,rev:a.rev,rch:cell[k]||0}}).sort(function(a,b){return b.sp-a.sp});
    var t={sp:sum(rows,function(r){return r.sp}),sem:sum(rows,function(r){return r.sem}),rev:sum(rows,function(r){return r.rev}),rch:sum(rows,function(r){return r.rch})};
    t.diff=t.sp-t.sem;
    var plr=D.pl5&&D.pl5.total?D.pl5.total.r:0;
    return {rows:rows,t:t,pp:plr>0?t.diff/plr*100:0};
  }
  function adRecHtml(R){
    var tr=R.rows.map(function(r){return '<tr><td>'+esc(r.k)+'</td><td>'+USD(r.sp)+'</td><td>'+USD(r.sem)+'</td><td>'+USD(r.diff)+'</td><td>'+USD(r.rev)+'</td><td>'+USD(r.rch)+'</td><td>'+(r.rev>0?PC(r.sp/r.rev*100):"—")+'</td><td>'+(r.rch>0?PC(r.sp/r.rch*100):"—")+'</td></tr>'}).join("");
    var t=R.t;
    return '<div class="card" id="adrec" style="margin:0 0 13px"><h3 style="margin:0 0 4px">Đối chiếu chi phí quảng cáo</h3>'
      +'<div class="muted" style="font-size:12.5px;margin-bottom:8px">Báo cáo quảng cáo ghi chi phí thực tế '+USD(t.sp)+'; cột SEM trong file P&amp;L (dùng tính PL5) đang là số tạm tính theo tỷ lệ % và ghi '+USD(t.sem)+'. Phần chênh '+USD(t.diff)+' sẽ được phản ánh khi file P&amp;L cập nhật chi phí thực tế; với mức chi như tuần này, biên PL5 sẽ thấp hơn khoảng '+fN(R.pp,1)+' điểm %.</div>'
      +'<div class="scroll"><table><thead><tr><th>Kênh</th><th>Chi QC (báo cáo QC)</th><th>Chi QC (file P&amp;L)</th><th>Chênh</th><th>Doanh thu nhóm có chiến dịch</th><th>Doanh thu toàn kênh</th><th>TACoS (nhóm có chiến dịch)</th><th>TACoS (toàn kênh)</th></tr></thead><tbody>'+tr
      +'<tr><td><b>Tổng</b></td><td><b>'+USD(t.sp)+'</b></td><td><b>'+USD(t.sem)+'</b></td><td><b>'+USD(t.diff)+'</b></td><td><b>'+USD(t.rev)+'</b></td><td><b>'+USD(t.rch)+'</b></td><td><b>'+(t.rev>0?PC(t.sp/t.rev*100):"—")+'</b></td><td><b>'+(t.rch>0?PC(t.sp/t.rch*100):"—")+'</b></td></tr></tbody></table></div>'
      +'<div class="muted" style="font-size:12px;margin-top:6px">TACoS ở các bảng khác tính trên doanh thu của nhóm có chiến dịch; cột cuối tính trên toàn bộ doanh thu kênh nên thấp hơn. Amazon · AUS có chi quảng cáo nhưng chưa có doanh thu nên chưa vào PL5.</div></div>';
  }
  function adRec(){var h=$("#tacoskpi");if(!h||$("#adrec"))return;h.insertAdjacentElement("afterend",mk(adRecHtml(adRecon())))}

  /* ---------- B. ghi chú đối chiếu ngay dưới cầu lợi nhuận ---------- */
  function mgNote(){
    var pane=$("#p-mg");if(!pane||$("#mg-recon"))return;
    var sec=$$("section",pane).filter(function(s){var h=$("h2",s);return h&&/^Cầu lợi nhuận/.test(h.textContent.trim())})[0];if(!sec)return;
    var R=adRecon();if(!(R.t.diff>1))return;
    sec.appendChild(mk('<p class="cap" id="mg-recon" style="margin:10px 0 0">Đối chiếu: chi phí quảng cáo trong PL5 là số tạm tính theo tỷ lệ % ('+USD(R.t.sem)+'), chi phí thực tế theo báo cáo quảng cáo là '+USD(R.t.sp)+' (chênh '+USD(R.t.diff)+', khoảng '+fN(R.pp,1)+' điểm % biên). Xem chi tiết ở Quảng cáo › mục 02.</p>'));
  }

  /* ---------- E. Kết luận tuần ---------- */
  function conclusions(){
    var ins=$("#pro-ins");if(!ins||$("#wk-concl"))return;
    var items=[];
    // 1. Lợi nhuận theo sàn
    var byMp={};Object.keys((D.pl5&&D.pl5.by_mpcty)||{}).forEach(function(k){var mp=k.split("|")[0],v=D.pl5.by_mpcty[k];var o=byMp[mp]||(byMp[mp]={p:0,r:0});o.p+=v.profit||0;o.r+=v.r||0});
    var revMp={};(D.cell||[]).forEach(function(c){revMp[c.mp]=(revMp[c.mp]||0)+c.r});var revT=sum(Object.keys(revMp),function(k){return revMp[k]});
    var neg=Object.keys(byMp).filter(function(k){return byMp[k].p<0}).sort(function(a,b){return byMp[a].p-byMp[b].p});
    if(neg.length&&revT>0){
      var lead=neg[0],pos=Object.keys(byMp).filter(function(k){return byMp[k].p>=0});
      items.push(['Lợi nhuận PL5 tập trung ở '+lead+', các sàn còn lại ổn hơn',
        lead+' chiếm '+PC((revMp[lead]||0)/revT*100,0)+' doanh thu tuần, lợi nhuận PL5 '+USD(byMp[lead].p)+(pos.length?'; '+pos.map(function(k){return k+' '+(byMp[k].p>=0?"+":"")+USD(byMp[k].p)}).join(" · "):"")+' (độ phủ PL5 '+PC(D.pl5.coverage_pct,0)+((D.pl5.no_formula_mpcty||[]).length?'; chưa tính được PL5 cho '+Array.from(new Set(D.pl5.no_formula_mpcty.map(function(x){return Array.isArray(x)?x[0]+" "+x[1]:String(x)}))).join(", "):"")+').',
        'Rà cơ cấu chi phí của '+lead+' trước: giá bán sỉ so với giá vốn, chi phí vận chuyển/fulfill và các khoản phí kho; chưa cần can thiệp lớn ở các sàn còn lại.']);
    }
    // 2. Xu hướng doanh thu
    var W=((D.weekfc&&D.weekfc.all)||[]).filter(function(w){return w.nd===7});
    if(W.length>=12){
      var l3=W.slice(-3),pr=W.slice(-11,-3),a3=sum(l3,function(w){return w.r})/3,a8=sum(pr,function(w){return w.r})/8;
      var lastW=W[W.length-1],prevW=W[W.length-2],wow=prevW.r>0?(lastW.r/prevW.r-1)*100:null;
      if(a8>0&&a3<a8*0.9)
        items.push(['Doanh thu đang đi ngang ở nền thấp hơn các tuần trước',
          'Bình quân 3 tuần gần nhất '+USD(a3)+', thấp hơn '+PC((1-a3/a8)*100,0)+' so với bình quân 8 tuần trước đó ('+USD(a8)+'); tuần này '+(wow==null?"":(wow>=0?"+":"")+PC(wow)+" so với tuần trước, ")+'là ổn định ở nền thấp chứ chưa phải phục hồi.',
          'Xác định nguyên nhân giảm theo từng nhóm × sàn (tồn kho, quảng cáo, listing) ở mục Điều cần chú ý bên dưới, bắt đầu từ cụm có mức giảm lớn nhất.']);
    }
    // 3. FC
    if(W.length>=8){
      var ach=function(w){return w.rfc>0?w.r/w.rfc*100:0},cur=ach(W[W.length-1]),a4=sum(W.slice(-4),ach)/4,ay=sum(W,ach)/W.length,mx=Math.max.apply(null,W.map(ach));
      if(cur<ay-5)
        items.push(['Mức đạt kế hoạch (FC) thấp hơn nền cả năm',
          'Tuần này đạt '+PC(cur)+' FC; bình quân 4 tuần gần nhất '+PC(a4)+', bình quân cả năm '+PC(ay)+'; tuần cao nhất mới đạt '+PC(mx,0)+'.',
          'Rà lại cách lập FC theo năng lực bán thực tế (FC cuốn chiếu theo hệ số thực tế/FC từng sàn) để mục tiêu bám sát và phản ánh đúng tiến độ.']);
    }
    // 4. Tồn kho (BQ 4 tuần)
    var sk=((D.invdet&&D.invdet.sku_tot)||[]);
    var vel=sum(sk,function(s){return s.sold_month});
    if(sk.length&&vel>0){
      var tq=(D.invdet&&D.invdet.qty_total)!=null?D.invdet.qty_total:sum(sk,function(s){return s.qty}),wk=tq/vel,low=sk.filter(function(s){return s.qty>0&&!s.disc&&s.weeks!=null&&s.weeks<4}),dq=sum(sk.filter(function(s){return s.disc&&s.qty>0}),function(s){return s.qty});
      items.push(['Tồn kho đủ bán khoảng '+fN(wk,1)+' tuần (theo số lượng), nhưng phân bổ chưa đều',
        fN(tq)+' sản phẩm tồn, tốc độ bán bình quân 4 tuần '+fN(vel)+' sản phẩm/tuần; '+low.length+' SKU còn dưới 4 tuần bán'+(low.length?' ('+low.slice(0,5).map(function(s){return s.sku}).join(", ")+(low.length>5?" …":"")+')':"")+(dq>0?'; '+fN(dq)+' sản phẩm thuộc SKU ngưng kinh doanh cần kế hoạch thanh lý':"")+'.',
        'Chốt lịch nhập cho các SKU còn kinh doanh sắp hết hàng (lead time đang là số giả lập, cần nhập số thật); thanh lý hàng ngưng kinh doanh và xử lý phần tồn chậm bằng giá, khuyến mãi hoặc listing.']);
    }
    if(!items.length)return;
    var li=items.map(function(it){return '<li><div><div class="t">'+esc(it[0])+'</div><div class="m"><em>Số liệu:</em> '+esc(it[1])+' · <em>Hướng xử lý:</em> '+esc(it[2])+'</div></div></li>'}).join("");
    ins.insertAdjacentElement("beforebegin",mk('<section class="pro-sec" id="wk-concl"><div class="shead"><span class="snum">★</span><h2>Kết luận tuần</h2><span class="hint">bốn điều đáng nhớ nhất, tính tự động từ số liệu</span></div><div class="sol" style="margin-top:0"><ol class="act">'+li+'</ol></div></section>'));
  }

  /* ---------- tồn kho: nhãn số liệu tuổi tồn kho nếu là số kỳ trước ---------- */
  function ltBanner(){
    var pane=$("#p-inv");if(!pane||$("#lt-stale"))return;
    var m=/THẬT của tuần W(\d+)/.exec((D.lt&&D.lt.note)||""),wk=D.meta&&D.meta.week_no;
    if(!m||!wk||+m[1]>=wk)return;
    var sec=$$("section",pane).filter(function(s){var h=$("h2",s);return h&&/Long-term Storage/.test(h.textContent)})[0];if(!sec)return;
    var sh=$(".shead",sec);
    sh.insertAdjacentElement("afterend",mk('<div class="card" id="lt-stale" style="margin:0 0 10px;padding:10px 14px;font-size:13px;border-left:3px solid var(--warn)"><b>Số liệu tuổi tồn kho đang là của tuần W'+esc(m[1])+'</b> (file xuất 27–28/09). Kỳ này chưa có file FBA Inventory Age nên hệ thống giữ số kỳ trước cho cả FBA và CastleGate, dù đã có file CastleGate mới. Tổng tồn ở mục này và ô "so với tuần trước" vì vậy chưa phản ánh W'+esc(wk)+'. Bổ sung file FBA Inventory Age để cập nhật. Ngoài ra, bảng theo tài khoản bên dưới là toàn tài khoản (gồm cả hàng ngoài danh mục Thu Ngo), trong khi ô tổng ở trên chỉ tính SKU của danh mục.</div>'));
  }

  /* ---------- dữ liệu cần làm sạch (tab Dữ liệu & Giả định) ---------- */
  function hygiene(){
    var pane=$("#p-dd");if(!pane||$("#dd-hyg"))return;
    var iv=D.invdet||{},neg=iv.neg_rows||[],dup=iv.dup_sku_grp||[],nm=(D.sku_meta||[]).filter(function(m){return m.name===m.sku});
    var rows=[];
    if(neg.length)rows.push(['Tồn kho âm ở '+neg.length+' vị trí kho (tổng '+fN(sum(neg,function(r){return r.qty}))+' sản phẩm)',neg.slice(0,5).map(function(r){return r.sku+" "+r.qty+" ("+r.loc.replace(/-?\s*Available/,"").trim()+")"}).join(" · ")+(neg.length>5?" …":""),'Đối chiếu số tồn thật với kho, vì số âm làm tổng tồn bị thấp hơn thực tế.']);
    if(dup.length)rows.push([dup.length+' SKU nằm ở hai nhóm khác nhau trong file tồn kho',dup.map(function(d){return d.sku+": "+d.qty_by_group.map(function(g){return g.grp.replace(/^Acacia - /,"")+" ("+g.qty+")"}).join(" + ")}).join(" · "),'Chốt nhóm chuẩn cho các SKU này để số theo nhóm không bị tách đôi.']);
    if(nm.length)rows.push([nm.length+' SKU chưa có tên sản phẩm (tên đang trùng mã)',nm.map(function(m){return m.sku}).join(", "),'Bổ sung tên vào sheet Listing/master để bảng SKU dễ đọc.']);
    var lm=/THẬT của tuần W(\d+)/.exec((D.lt&&D.lt.note)||"");
    if(lm&&D.meta.week_no&&+lm[1]<D.meta.week_no)rows.push(['Tuổi tồn kho FBA và CastleGate đang là số tuần W'+lm[1],'Kỳ này thiếu file FBA Inventory Age nên giữ số kỳ trước','Bổ sung file FBA Inventory Age của kỳ này.']);
    var R=adRecon();if(R.t.diff>1)rows.push(['Cột SEM trong file P&L đang tạm tính theo tỷ lệ % (thấp hơn chi phí thực tế '+USD(R.t.diff)+')','SEM '+USD(R.t.sem)+' so với báo cáo quảng cáo '+USD(R.t.sp),'Cập nhật chi phí quảng cáo thực tế vào file P&L khi có để PL5 chính xác.']);
    if(!rows.length)return;
    var tr=rows.map(function(r){return '<tr><td><b>'+esc(r[0])+'</b></td><td>'+esc(r[1])+'</td><td>'+esc(r[2])+'</td></tr>'}).join("");
    var sec=mk('<section class="pro-sec" id="dd-hyg"><div class="shead"><span class="snum">0</span><h2>Dữ liệu cần làm sạch</h2><span class="hint">phát hiện tự động từ số liệu kỳ này</span></div><div class="card"><div class="scroll"><table class="tl"><thead><tr><th>Vấn đề</th><th>Chi tiết</th><th>Cách xử lý</th></tr></thead><tbody>'+tr+'</tbody></table></div></div></section>');
    var after=$$("section",pane).filter(function(s){var h=$("h2",s);return h&&/^Dữ liệu còn thiếu/.test(h.textContent.trim())})[0];
    if(after)after.insertAdjacentElement("afterend",sec);else pane.appendChild(sec);
    $$(".snum",pane).forEach(function(n,i){n.textContent=String(i+1).padStart(2,"0")});
  }


  function quality(){
    var Q=D.quality;if(!Q||!Q.total)return;
    var card=$$(".dc").filter(function(c){var h=$("h3",c);return h&&/^Chất lượng sản phẩm/.test(h.textContent.trim())})[0];
    if(card&&!card.getAttribute("data-q")){
      var T=Q.total,pc=function(v){return v==null?"—":String(v).replace(".",",")+"%"};
      var bad=Q.rows.filter(function(r){return r.flag_inc||r.flag_ret}).length;
      var gl=Q.by_grp.filter(function(g){return g.adj>=100}).sort(function(a,b){return (b.inc_rate-b.inc_bench)-(a.inc_rate-a.inc_bench)}).slice(0,5);
      var tr=gl.map(function(g){var hi=g.inc_rate>g.inc_bench,hr=g.ret_rate>g.ret_bench;
        return '<tr><td>'+esc(g.grp.replace(/^Acacia - /,"").replace(/ - Wooden Bed Frame.*/i,"").replace("Dinning","Dining"))+'</td><td style="text-align:right;color:'+(hi?"var(--bad-ink)":"inherit")+'">'+pc(g.inc_rate)+'<small> / '+pc(g.inc_bench)+'</small></td><td style="text-align:right;color:'+(hr?"var(--bad-ink)":"inherit")+'">'+pc(g.ret_rate)+'<small> / '+pc(g.ret_bench)+'</small></td></tr>'}).join("");
      card.setAttribute("data-q","1");
      card.innerHTML='<h3 title="Nguồn: báo cáo Wayfair Summary-data (Incidents và Buyer\'s Remorse Returns), số tích luỹ 6 tháng">Chất lượng sản phẩm <span class="pk" style="font-weight:400">Wayfair · tích luỹ đến '+esc(Q.as_of)+'</span></h3>'
       +'<div class="note">Tỷ lệ sự cố <b>'+pc(T.inc_rate)+'</b> (chuẩn Wayfair '+pc(T.inc_bench)+') · tỷ lệ hoàn do đổi ý <b>'+pc(T.ret_rate)+'</b> (chuẩn '+pc(T.ret_bench)+'). '
       +(bad?bad+' listing đang cao hơn chuẩn ngành hàng ở ít nhất một chỉ số — nên xem nguyên nhân (đóng gói, mô tả, kích thước) và xử lý ở nhóm có tỷ lệ cao nhất.':'Các listing đều trong ngưỡng chuẩn.')+'</div>'
       +'<table class="tbl" style="margin-top:8px"><thead><tr><th>Nhóm</th><th style="text-align:right">Sự cố / chuẩn</th><th style="text-align:right">Hoàn đổi ý / chuẩn</th></tr></thead><tbody>'+tr+'</tbody></table>'
       +'<div class="note" style="margin-top:6px"><small>Phạm vi: '+Q.scope_n+' trên '+Q.all_n+' listing trong file thuộc danh mục đang theo dõi (phần còn lại chưa gắn được vào nhóm). Số liệu tích luỹ nên không so theo tuần.</small></div>';
    }
    $$("td").forEach(function(td){if(/hiện chỉ đo gián tiếp/.test(td.textContent)&&td.children.length===0)td.textContent="Đã có Summary-data (sự cố, hoàn đổi ý); chưa có đánh giá sao và lý do trả hàng"});
  }

  function init(){
    try{
      if(typeof builders!=="undefined"){
        var oc=builders.cp;if(oc)builders.cp=function(){var r=oc.apply(this,arguments);try{adRec()}catch(e){console.warn("adRec",e)}return r};
        var oi=builders.inv;if(oi)builders.inv=function(){var r=oi.apply(this,arguments);try{ltBanner()}catch(e){console.warn("ltBanner",e)}return r};
        var od=builders.dd;if(od)builders.dd=function(){var r=od.apply(this,arguments);try{hygiene()}catch(e){console.warn("hygiene",e)}return r};
      }
      mgNote();conclusions();quality();
    }catch(e){console.warn("v4_16",e)}
  }
  setTimeout(init,0);
})();
