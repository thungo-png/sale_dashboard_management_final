(function(){
  /* Gọn v4.17: menu "Thị trường & Đối thủ" — theo dõi thứ hạng ngành hàng, thị phần tìm kiếm, chất lượng so với chuẩn ngành để ứng phó kịp thời */
  var $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var esc=function(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
  var fN=function(n,d){return Number(n).toLocaleString("vi-VN",{maximumFractionDigits:d||0,minimumFractionDigits:d||0})};
  var pc=function(v,d){return v==null?"—":fN(v,d==null?1:d)+"%"};
  var sg=function(g){return String(g||"").replace(/Dinning/g,"Dining").replace(/^Acacia - /,"").replace(/ - Wooden Bed Frame.*/i,"")};
  function mk(html){var t=document.createElement("template");t.innerHTML=html.trim();return t.content.firstChild}

  /* dữ liệu: ưu tiên D.market (có so tuần trước); nếu kỳ cũ chưa có thì dựng từ D.ads, không có so sánh */
  function market(){
    if(D.market)return D.market;
    var A=D.ads||{},rank=[],st=[];
    Object.keys(A.rank||{}).forEach(function(a){A.rank[a].forEach(function(r){rank.push({acct:a,listing:r.Listing,grp:r.grp,cls:r["Class Name"],status:r.status,first:r.first,last:r.last,best:r.best,prev_last:null})})});
    Object.keys(A.st||{}).forEach(function(a){A.st[a].forEach(function(r){st.push({acct:a,term:r.term,cls:r.cls,impr:r.impr,sh:r.sh_search,p1:r.sh_p1,top8:r.sh_top8,prev_sh:null})})});
    return {has_prev:false,rank:rank,st:st};
  }

  function alerts(M){
    var out=[];
    /* 1) listing tụt hạng so với tuần trước */
    var rk=M.rank.filter(function(r){return r.prev_last!=null&&r.last!=null&&r.status==="ACTIVE"}).map(function(r){r.d=r.last-r.prev_last;return r})
      .filter(function(r){return r.d>=20&&r.d/r.prev_last>=0.1}).sort(function(a,b){return b.d-a.d});
    if(rk.length)out.push({lv:2,area:"Thứ hạng ngành hàng",where:rk.length+" listing đang xuống hạng so với tuần trước: "+rk.slice(0,4).map(function(r){return r.listing+" ("+r.acct+", "+r.cls+") "+fN(r.prev_last)+"→"+fN(r.last)}).join(" · "),
      act:"Kiểm tồn kho, giá và ảnh của các listing này; nếu đang tạm ngưng quảng cáo hoặc hết hàng thì xử lý trước, vì thứ hạng sẽ hồi lại khi listing bán đều trở lại."});
    /* 2) thị phần tìm kiếm giảm ở cụm từ lớn */
    var sd=M.st.filter(function(r){return r.prev_sh!=null&&r.impr>=5000&&r.sh-r.prev_sh<=-2}).sort(function(a,b){return b.impr*(b.prev_sh-b.sh)-a.impr*(a.prev_sh-a.sh)});
    if(sd.length)out.push({lv:2,area:"Thị phần tìm kiếm",where:sd.length+" cụm từ lớn bị giảm thị phần từ 2 điểm % trở lên: "+sd.slice(0,4).map(function(r){return "“"+r.term+"” ("+r.acct+") "+pc(r.prev_sh)+"→"+pc(r.sh)}).join(" · "),
      act:"Đối thủ đang hiển thị nhiều hơn ở các cụm từ này. Xem lại bid và từ khóa của chiến dịch tương ứng ở tab Quảng cáo, ưu tiên cụm có lượt tìm lớn nhất."});
    /* 3) cơ hội: thị trường lớn nhưng mình ít hiện ở trang 1 */
    var op=M.st.filter(function(r){return r.impr>=20000&&r.p1!=null&&r.p1<5}).sort(function(a,b){return b.impr-a.impr});
    if(op.length)out.push({lv:1,area:"Cơ hội thị trường",where:op.length+" cụm từ có lượt tìm lớn nhưng thị phần trang 1 còn dưới 5%: "+op.slice(0,4).map(function(r){return "“"+r.term+"” ("+r.acct+") "+fN(r.impr)+" lượt, trang 1 "+pc(r.p1)}).join(" · "),
      act:"Đây là nơi còn nhiều dư địa tăng trưởng. Chọn 1–2 cụm hợp với sản phẩm đang có tồn, kiểm listing đã đủ từ khóa trong tiêu đề, rồi mới tăng ngân sách."});
    /* 4) chất lượng so với chuẩn ngành hàng của Wayfair */
    var Q=D.quality;
    if(Q&&Q.by_grp){var qb=Q.by_grp.filter(function(g){return g.adj>=100&&((g.inc_rate-g.inc_bench>=1)||(g.ret_rate-g.ret_bench>=1))}).sort(function(a,b){return (b.inc_rate-b.inc_bench)-(a.inc_rate-a.inc_bench)});
      if(qb.length)out.push({lv:2,area:"Chất lượng so với chuẩn ngành",where:qb.length+" nhóm cao hơn chuẩn ngành hàng của Wayfair từ 1 điểm % trở lên: "+qb.slice(0,3).map(function(g){return sg(g.grp)+" (sự cố "+pc(g.inc_rate)+" so với "+pc(g.inc_bench)+", hoàn đổi ý "+pc(g.ret_rate)+" so với "+pc(g.ret_bench)+")"}).join(" · "),
        act:"Rà nguyên nhân sự cố và hoàn hàng ở các nhóm này (đóng gói, kích thước ghi trên listing, phụ kiện); nhóm vượt chuẩn lâu có thể bị Wayfair hạ hiển thị."})}
    return out;
  }


  /* ===== Amazon: Brand Analytics (Search Query Performance) + Business Report (Buy Box) ===== */
  var CCN={US:"Mỹ (US)",CA:"Canada (CAN)"};
  function ppt(v,d){return v==null?"—":fN(v,d==null?3:d)+"%"}
  function dlt(cur,prev,d){if(cur==null||prev==null)return "";var x=cur-prev;if(Math.abs(x)<Math.pow(10,-(d==null?3:d))/2)return ' <small style="color:var(--muted)">±0</small>';return ' <small style="color:'+(x>0?"var(--ok-ink,var(--accent))":"var(--bad-ink)")+'">'+(x>0?"▲ ":"▼ ")+fN(Math.abs(x),d==null?3:d)+'</small>'}
  function qprev(q,w){var h=q.hist||{};return h[String(w)]||null}
  function amzAlerts(){
    var A=D.amzmkt,out=[];if(!A)return out;
    Object.keys(A.sqp||{}).forEach(function(cc){
      var S=A.sqp[cc],W=S.weeks,cur=W[W.length-1],prv=W.length>1?W[W.length-2]:null,pw=prv?prv.w:null,nm=CCN[cc]||cc;
      if(prv&&prv.clk_share>0&&cur.clk_share/prv.clk_share<=0.8)out.push({lv:2,area:"Amazon "+cc+" · thị phần click",where:"Thị phần click của thương hiệu trên các cụm từ theo dõi giảm từ "+ppt(prv.clk_share)+" xuống "+ppt(cur.clk_share)+" (tuần W"+prv.w+" → W"+cur.w+"), trong khi thị phần hiển thị "+ppt(prv.imp_share)+" → "+ppt(cur.imp_share)+".",
        act:"Hiển thị còn nhưng người mua nhấp ít hơn: xem lại ảnh chính, tiêu đề, giá và đánh giá của các listing có hiển thị nhiều nhất; đối chiếu bảng cụm từ bên dưới để biết cụm nào giảm."});
      var lag=S.q.filter(function(r){return r.imp_b>=500&&r.p_mkt&&r.p_brand&&r.p_brand/r.p_mkt>=1.5&&r.imp_sh>0&&r.clk_sh<r.imp_sh*0.6}).sort(function(a,b){return b.imp_b-a.imp_b});
      if(lag.length)out.push({lv:1,area:"Amazon "+cc+" · giá so với thị trường",where:lag.length+" cụm từ mà giá trung vị của mình cao hơn thị trường từ 50% trở lên và mức click thấp hơn mức hiển thị: "+lag.slice(0,3).map(function(r){return "“"+r.q+"” (giá mình $"+fN(r.p_brand)+" so với thị trường $"+fN(r.p_mkt)+")"}).join(" · "),
        act:"Sản phẩm gỗ acacia nguyên khối đặt giá cao hơn mặt bằng chung là bình thường; việc cần làm là nhấn mạnh chất liệu và độ bền ở ảnh/tiêu đề, và cân nhắc coupon hoặc giá khuyến mãi cho cụm từ có lượt tìm lớn."});
      if(pw){var dn=S.q.filter(function(r){var p=qprev(r,pw);return p&&r.vol>=20000&&p[1]>0&&r.imp_sh<p[1]*0.7&&p[1]-r.imp_sh>=0.02}).sort(function(a,b){return b.vol-a.vol});
        if(dn.length)out.push({lv:2,area:"Amazon "+cc+" · cụm từ mất hiển thị",where:dn.length+" cụm từ lớn bị giảm thị phần hiển thị từ 30% trở lên so với tuần trước: "+dn.slice(0,3).map(function(r){var p=qprev(r,pw);return "“"+r.q+"” "+ppt(p[1])+" → "+ppt(r.imp_sh)}).join(" · "),
          act:"Kiểm quảng cáo Sponsored Products của cụm từ này (ngân sách, bid, tạm dừng) và tồn kho của listing tương ứng."})}
    });
    Object.keys(A.br||{}).forEach(function(cc){
      var lo=A.br[cc].filter(function(r){return r.sess>=150&&r.bb!=null&&r.bb<90}).sort(function(a,b){return b.sess*(100-b.bb)-a.sess*(100-a.bb)});
      if(lo.length)out.push({lv:2,area:"Amazon "+cc+" · Buy Box",where:lo.length+" ASIN có tỷ lệ giữ Buy Box dưới 90% dù có từ 150 phiên truy cập: "+lo.slice(0,3).map(function(r){return r.asin+" ("+sg(r.grp)+") "+pc(r.bb,0)+", "+fN(r.sess)+" phiên"}).join(" · "),
        act:"Phần phiên không có Buy Box thường chuyển cho người bán khác hoặc listing đang hết hàng/giá lệch. Kiểm tồn kho FBA, giá so với các offer khác và trạng thái listing."});
    });
    return out;
  }
  function amzSection(){
    var A=D.amzmkt;if(!A||!A.sqp)return null;
    var h="";
    Object.keys(A.sqp).forEach(function(cc){
      var S=A.sqp[cc],W=S.weeks,cur=W[W.length-1],prv=W.length>1?W[W.length-2]:null,pw=prv?prv.w:null;
      function box(l,v,s){return '<div class="dc" style="flex:1;min-width:190px"><div style="font-size:12px;color:var(--muted)">'+l+'</div><div style="font-size:24px;font-weight:600;margin:4px 0">'+v+'</div><div style="font-size:12px;color:var(--muted)">'+s+'</div></div>'}
      h+='<h3 style="margin:16px 0 8px">Amazon '+esc(CCN[cc]||cc)+' <span class="cap" style="font-weight:400">· thương hiệu '+esc(S.brand)+' · tuần W'+cur.w+' ('+esc(S.range[0])+' → '+esc(S.range[1])+')</span></h3>';
      h+='<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px">'
        +box("Thị phần hiển thị",ppt(cur.imp_share),prv?"tuần trước "+ppt(prv.imp_share):"chưa có tuần trước")
        +box("Thị phần click",ppt(cur.clk_share),prv?"tuần trước "+ppt(prv.clk_share):"chưa có tuần trước")
        +box("Thị phần mua",ppt(cur.buy_share),prv?"tuần trước "+ppt(prv.buy_share):"chưa có tuần trước")
        +box("Tổng lượt tìm theo dõi",fN(cur.vol),fN(cur.n)+" cụm từ hàng đầu của Amazon")+'</div>';
      if(W.length>1){h+='<div class="scroll"><table><thead><tr><th>Tuần</th><th style="text-align:right">Hiển thị</th><th style="text-align:right">Click</th><th style="text-align:right">Mua</th><th style="text-align:right">Lượt tìm</th></tr></thead><tbody>'
        +W.slice().reverse().map(function(w){return '<tr><td>W'+w.w+' <small style="color:var(--muted)">'+esc(w.d0.slice(5))+' → '+esc(w.d1.slice(5))+'</small></td><td style="text-align:right">'+ppt(w.imp_share)+'</td><td style="text-align:right">'+ppt(w.clk_share)+'</td><td style="text-align:right">'+ppt(w.buy_share)+'</td><td style="text-align:right">'+fN(w.vol)+'</td></tr>'}).join("")+'</tbody></table></div>'}
      var qs=S.q.filter(function(r){return r.imp_b>0}).sort(function(a,b){return b.imp_b-a.imp_b}).slice(0,12);
      h+='<div class="scroll" style="margin-top:10px"><table><thead><tr><th>Cụm từ khách tìm</th><th style="text-align:right">Lượt tìm</th><th style="text-align:right">Hiển thị</th><th style="text-align:right">Click</th><th style="text-align:right">Mua</th><th style="text-align:right">Giá mình / thị trường</th></tr></thead><tbody>'
       +qs.map(function(r){var p=pw?qprev(r,pw):null,pr=(r.p_brand&&r.p_mkt)?'$'+fN(r.p_brand)+' / $'+fN(r.p_mkt)+' <small style="color:var(--muted)">('+(r.p_brand>=r.p_mkt?"+":"−")+fN(Math.abs(r.p_brand/r.p_mkt-1)*100)+'%)</small>':"—";
         return '<tr><td>'+esc(r.q)+'</td><td style="text-align:right">'+fN(r.vol)+'</td><td style="text-align:right">'+ppt(r.imp_sh)+dlt(r.imp_sh,p&&p[1])+'</td><td style="text-align:right">'+ppt(r.clk_sh)+dlt(r.clk_sh,p&&p[2])+'</td><td style="text-align:right">'+ppt(r.buy_sh)+'</td><td style="text-align:right">'+pr+'</td></tr>'}).join("")+'</tbody></table></div>';
    });
    h+='<p class="cap" style="margin-top:8px">Nguồn: Amazon Brand Analytics › Search Query Performance (Brand View). Thị phần là phần của thương hiệu trên tổng toàn thị trường Amazon ở cụm từ đó; tổng hợp tính trên các cụm từ có trong báo cáo (top theo lượt tìm). Giá là giá trung vị của các sản phẩm được click: giá thị trường là của toàn bộ người bán, giá mình là của thương hiệu. Mũi tên là mức thay đổi so với tuần trước, tính bằng điểm %.</p>';
    return h;
  }
  function bbSection(){
    var A=D.amzmkt;if(!A||!A.br)return null;var h="";
    Object.keys(A.br).forEach(function(cc){
      var R=A.br[cc].slice().sort(function(a,b){return b.sess*(100-(b.bb==null?100:b.bb))-a.sess*(100-(a.bb==null?100:a.bb))}).slice(0,10);
      h+='<h3 style="margin:14px 0 8px">Amazon '+esc(CCN[cc]||cc)+'</h3><div class="scroll"><table><thead><tr><th>ASIN</th><th>Nhóm</th><th style="text-align:right">Phiên truy cập</th><th style="text-align:right">Giữ Buy Box</th><th style="text-align:right">Đơn vị bán</th><th style="text-align:right">Tỷ lệ chuyển đổi</th></tr></thead><tbody>'
       +R.map(function(r){return '<tr><td class="mono">'+esc(r.asin)+'<span class="sub-asin">'+esc(String(r.title).slice(0,40))+'</span></td><td>'+esc(sg(r.grp))+'</td><td style="text-align:right">'+fN(r.sess)+'</td><td style="text-align:right;color:'+(r.bb!=null&&r.bb<90?"var(--bad-ink)":"inherit")+'">'+pc(r.bb,1)+'</td><td style="text-align:right">'+fN(r.units)+'</td><td style="text-align:right">'+pc(r.cvr,2)+'</td></tr>'}).join("")+'</tbody></table></div>';
    });
    h+='<p class="cap" style="margin-top:8px">Nguồn: Business Report › Detail Page Sales and Traffic By Child Item. Xếp theo số phiên truy cập đang không có Buy Box. File không ghi khoảng ngày, nên số liệu theo khoảng ngày bạn chọn khi tải báo cáo.</p>';
    return h;
  }

  function kpis(M){
    var up=0,dn=0,hasP=M.rank.filter(function(r){return r.prev_last!=null});
    hasP.forEach(function(r){var d=r.last-r.prev_last;if(d<0)up++;else if(d>0)dn++});
    var tot=0,w=0,pw=0,pt=0;M.st.forEach(function(r){if(r.sh!=null&&r.impr>0){tot+=r.impr;w+=r.impr*r.sh}if(r.prev_sh!=null&&r.prev_impr>0){pt+=r.prev_impr;pw+=r.prev_impr*r.prev_sh}});
    var sh=tot?w/tot:null,psh=pt?pw/pt:null;
    var big=M.st.filter(function(r){return r.impr>=20000&&r.p1!=null&&r.p1<5}).length;
    function box(l,v,s){return '<div class="dc" style="flex:1;min-width:190px"><div style="font-size:12px;color:var(--muted)">'+l+'</div><div style="font-size:26px;font-weight:600;margin:4px 0">'+v+'</div><div style="font-size:12px;color:var(--muted)">'+s+'</div></div>'}
    return '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px">'
     +box("Listing có thứ hạng",fN(M.rank.length),M.has_prev?(up+" lên hạng · "+dn+" xuống hạng so với tuần trước"):"chưa có kỳ trước để so")
     +box("Thị phần tìm kiếm bình quân",sh==null?"—":pc(sh),psh==null?"gia quyền theo lượt tìm":("tuần trước "+pc(psh)+" · gia quyền theo lượt tìm"))
     +box("Cụm từ lớn còn ít hiện",fN(big),"lượt tìm từ 20.000, trang 1 dưới 5%")
     +'</div>';
  }

  function qbench(){
    var Q=D.quality;if(!Q||!Q.by_grp||!Q.by_grp.length)return null;
    var tr=Q.by_grp.map(function(g){var hi=g.inc_rate>g.inc_bench+0.0001,hr=g.ret_rate>g.ret_bench+0.0001,cl=function(b){return b?' style="color:var(--bad-ink)"':''};
      return '<tr><td>'+esc(sg(g.grp))+'</td><td style="text-align:right">'+fN(g.n)+'</td><td style="text-align:right"'+cl(hi)+'>'+pc(g.inc_rate,2)+'</td><td style="text-align:right">'+pc(g.inc_bench,2)+'</td><td style="text-align:right"'+cl(hr)+'>'+pc(g.ret_rate,2)+'</td><td style="text-align:right">'+pc(g.ret_bench,2)+'</td></tr>'}).join("");
    return '<div class="scroll"><table><thead><tr><th>Nhóm</th><th style="text-align:right">Listing</th><th style="text-align:right">Sự cố</th><th style="text-align:right">Chuẩn ngành</th><th style="text-align:right">Hoàn đổi ý</th><th style="text-align:right">Chuẩn ngành</th></tr></thead><tbody>'+tr+'</tbody></table></div>'
      +'<p class="cap" style="margin-top:6px">Chuẩn ngành là mức trung bình của ngành hàng do Wayfair công bố trong Summary-data; số tích luỹ đến '+esc(Q.as_of)+'. Màu đỏ là cao hơn chuẩn.</p>';
  }

  var MISSING=[
    ["Giá của đối thủ cùng ngành hàng","Wayfair: Partner Home › Analytics (nếu tài khoản có báo cáo giá cạnh tranh) · Amazon: chưa có báo cáo chính thức, có thể theo dõi thủ công","Biết mình đang đắt hay rẻ hơn thị trường để chỉnh giá và khuyến mãi kịp lúc (Amazon hiện chỉ có giá trung vị thị trường theo từng cụm từ)"],
    ["Thứ hạng bán chạy (Best Sellers Rank) của từng ASIN","Trang sản phẩm Amazon hoặc công cụ theo dõi (Helium 10, Keepa)","Thấy sớm sản phẩm đang mất vị trí trong danh mục"],
    ["Đánh giá sao và nội dung phản hồi","Amazon: Customer Reviews · Wayfair: Review Dashboard","Phát hiện sớm vấn đề chất lượng mà số hoàn trả chưa phản ánh"],
    ["Danh sách đối thủ chính theo từng nhóm sản phẩm","Do bạn chỉ định (tên thương hiệu hoặc ASIN/listing)","Có danh sách này mới theo dõi giá và thứ hạng đối thủ theo tuần được"],
    ["Brand Analytics tuần tiếp theo","Amazon: Brand Analytics › Search Query Performance (Brand View), mỗi tuần một file, thêm vào ô của US/CAN","Để theo dõi xu hướng thị phần nhiều tuần; hiện US có 5 tuần, CAN có 3 tuần"]
  ];

  function section(n,title,hint,body){return '<section class="mk-sec"><div class="shead"><span class="snum">'+n+'</span><h2>'+esc(title)+'</h2><span class="hint">'+esc(hint||"")+'</span></div>'+body+'</section>'}

  function build(pane){
    var M=market(),al=alerts(M).concat(amzAlerts());
    var tr=al.length?al.sort(function(a,b){return b.lv-a.lv}).map(function(a){return '<tr><td><span class="chip '+(a.lv>=2?"w":"g")+'">'+(a.lv>=2?"Cần theo dõi":"Cơ hội")+'</span></td><td><b>'+esc(a.area)+'</b></td><td>'+esc(a.where)+'</td><td>'+esc(a.act)+'</td></tr>'}).join("")
      :'<tr><td colspan="4" style="color:var(--muted)">Tuần này chưa thấy biến động đáng kể về thứ hạng, thị phần hay chất lượng so với chuẩn ngành.</td></tr>';
    var note=M.has_prev?"":'<p class="cap">Kỳ này chưa có dữ liệu tuần trước nên chưa so sánh được biến động; phần cơ hội và chất lượng vẫn được tính.</p>';
    var s1=section("01","Điều cần ứng phó trong tuần",al.length+" mục",kpis(M)+'<div class="scroll"><table class="mk-al"><thead><tr><th>Mức</th><th>Mảng</th><th>Vấn đề nằm ở đâu</th><th>Việc nên làm</th></tr></thead><tbody>'+tr+'</tbody></table></div>'+note);
    var qb=qbench();
    var s4=section("04","Chất lượng so với chuẩn ngành hàng","Wayfair",qb||'<p class="cap">Chưa có Summary-data của kỳ này. Upload ở ô "Summary-data (Incidents/Returns)" để xem so sánh với chuẩn ngành.</p>');
    var ms=MISSING.map(function(r){return '<tr><td><b>'+esc(r[0])+'</b></td><td>'+esc(r[1])+'</td><td>'+esc(r[2])+'</td></tr>'}).join("");
    var s5=section("05","Dữ liệu đối thủ còn thiếu","chưa có trong bộ file hiện tại",'<p class="cap" style="margin-bottom:8px">Báo cáo hiện có cho biết vị thế của mình (thứ hạng, thị phần, Buy Box) và giá trung vị thị trường, nhưng chưa có dữ liệu trực tiếp của từng đối thủ. Các nguồn dưới đây giúp bổ sung phần này.</p><div class="scroll"><table class="mk-al"><thead><tr><th>Dữ liệu</th><th>Lấy ở đâu</th><th>Dùng để làm gì</th></tr></thead><tbody>'+ms+'</tbody></table></div>');
    pane.insertAdjacentHTML("beforeend",s1);
    var ah=amzSection(),bh=bbSection();
    if(ah)pane.insertAdjacentHTML("beforeend",section("02","Amazon — thị phần và giá so với thị trường","Brand Analytics",ah));
    if(bh)pane.insertAdjacentHTML("beforeend",section("03","Amazon — Buy Box theo ASIN","Business Report",bh));
    var mv=window.__mkMoved||[];            /* 02, 03 là hai mục chuyển từ tab Quảng cáo */
    mv.forEach(function(s){pane.appendChild(s)});
    pane.insertAdjacentHTML("beforeend",s4+s5);
    $$(".snum",pane).forEach(function(n,i){n.textContent=String(i+1).padStart(2,"0")});
  }

  function init(){
    var inner=document.getElementById("tabinner"),cpP=document.getElementById("p-cp");
    if(!inner||!cpP||document.getElementById("p-mk")||typeof builders==="undefined")return;
    /* tab cp dựng trước để lấy hai mục thứ hạng và thị phần tìm kiếm */
    var was=cpP.classList.contains("on");if(!was)cpP.classList.add("on");
    try{if(!built.cp){builders.cp();built.cp=1}}catch(e){console.warn("mk cp",e)}
    var mv=[];
    $$("section",cpP).forEach(function(s){var h=$("h2",s),t=h?h.textContent.trim():"";if(/^Thứ hạng ngành hàng trên Wayfair/.test(t)||/^Vị thế trên tìm kiếm/.test(t))mv.push(s)});
    window.__mkMoved=mv;
    var pane=mk('<div class="panel" id="p-mk" role="tabpanel"></div>');cpP.after(pane);
    mv.forEach(function(s){var d=$("details",s);if(d)d.open=true});
    if(!was)cpP.classList.remove("on");
    builders.mk=function(){build(pane)};
    $$(".snum",cpP).forEach(function(n,i){n.textContent=String(i+1).padStart(2,"0")});
    /* nút trên menu: ngay sau "Listing & Giá" */
    var b=document.createElement("button");b.className="tab";b.setAttribute("role","tab");b.setAttribute("aria-selected","false");b.dataset.p="mk";b.textContent="Thị trường & Đối thủ";
    b.addEventListener("click",function(){activate("mk")});
    var after=$$(".tab",inner).filter(function(x){return x.dataset.p==="bb"})[0];
    if(after)after.after(b);else inner.appendChild(b);
    /* "Dữ liệu & Giả định" dựng mọi tab: để mk dựng cả ở đó không cần, nhưng ensure của reorg chạy builders.* nên mk được dựng khi cần */
  }
  setTimeout(init,0);
})();
