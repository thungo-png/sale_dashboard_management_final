(function(){
  /* Gọn v4.18: thẻ "Sessions & chuyển đổi" ở tab Listing & Rating dùng số thật từ Business Report (D.amzmkt.br) thay cho khung chờ dữ liệu */
  var esc=function(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
  var fN=function(n,d){return Number(n).toLocaleString("vi-VN",{maximumFractionDigits:d||0,minimumFractionDigits:d||0})};
  var pc=function(v,d){return v==null?"—":fN(v,d==null?1:d)+"%"};
  var CCN={US:"Mỹ",CA:"Canada",CAN:"Canada"};
  function med(a){a=a.slice().sort(function(x,y){return x-y});return a.length?a[Math.floor(a.length/2)]:null}
  function card(){
    var A=D.amzmkt;if(!A||!A.br)return null;var ks=Object.keys(A.br).filter(function(k){return (A.br[k]||[]).length});if(!ks.length)return null;
    var h='<h3>Sessions &amp; chuyển đổi</h3><details class="capfold"><summary>Chú thích</summary><p class="cap" style="margin:2px 0 9px">Lưu lượng và tỷ lệ chuyển đổi theo listing (Amazon, nguồn Business Report). File không ghi khoảng ngày, nên số là của khoảng ngày bạn chọn khi tải báo cáo.</p></details>';
    ks.forEach(function(cc){
      var R=A.br[cc], S=0,U=0,P=0;R.forEach(function(r){S+=r.sess||0;U+=r.units||0;P+=r.pv||0});
      var m=med(R.filter(function(r){return r.sess>=100&&r.cvr!=null}).map(function(r){return r.cvr}));
      var top=R.slice().sort(function(a,b){return b.sess-a.sess}).slice(0,12);
      h+='<h4 style="margin:12px 0 6px">Amazon '+esc(CCN[cc]||cc)+' <span class="cap" style="font-weight:400">· '+R.length+' ASIN · '+fN(S)+' phiên · '+fN(U)+' đơn vị · chuyển đổi chung '+pc(S?U/S*100:null,2)+(m!=null?' · trung vị '+pc(m,2):'')+'</span></h4>'
       +'<div class="scroll"><table><thead><tr><th style="text-align:left">ASIN</th><th style="text-align:left">Nhóm</th><th style="text-align:right">Phiên</th><th style="text-align:right">Lượt xem trang</th><th style="text-align:right">Đơn vị</th><th style="text-align:right">Chuyển đổi</th><th style="text-align:left">Nhận định</th></tr></thead><tbody>'
       +top.map(function(r){
          var t="";if(m!=null&&r.sess>=150&&r.cvr!=null&&r.cvr<m*0.5)t="Nhiều người xem nhưng ít mua: xem lại giá, ảnh, review";
          else if(r.sess<60&&r.cvr!=null&&m!=null&&r.cvr>=m)t="Ít người xem nhưng mua tốt: có thể tăng quảng cáo";
          return '<tr><td class="mono">'+esc(r.asin)+'</td><td style="text-align:left">'+esc(String(r.grp||"—").replace(/Dinning/g,"Dining").replace(/^Acacia - /,"").replace(/ - Wooden Bed Frame.*/i,""))+'</td><td style="text-align:right">'+fN(r.sess)+'</td><td style="text-align:right">'+fN(r.pv)+'</td><td style="text-align:right">'+fN(r.units)+'</td><td style="text-align:right">'+pc(r.cvr,2)+'</td><td style="white-space:normal;text-align:left">'+esc(t)+'</td></tr>'}).join("")+'</tbody></table></div>';
    });
    return h;
  }
  function patch(){
    var box=document.getElementById("lrcards");if(!box||box.dataset.sess)return;var cs=box.querySelectorAll(":scope>.card");if(cs.length<3)return;
    var h=card();if(!h)return;box.dataset.sess="1";cs[2].innerHTML=h;cs[2].style.gridColumn="1/-1";
  }
  new MutationObserver(patch).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener("DOMContentLoaded",patch);setTimeout(patch,0);
})();
