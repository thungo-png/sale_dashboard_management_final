"""Gọn v4 – lần 13: tinh gọn báo cáo, ẩn các mục trùng ý nghĩa / placeholder / dữ liệu giả lập (chỉ ẩn, không xoá dữ liệu hay id).
   Việc "chưa phát sinh đơn" (Walmart...) trong mục "Việc cần làm theo số liệu" được chuyển sang cuối "Điều cần chú ý tuần này".
   Đánh lại số thứ tự mục trong từng tab. Dùng: python3 make_gon_v4_13.py vào.html ra.html (đã áp make_gon_v4_12)."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
js=r'''
(function(){
  /* Gọn v4.13: [tab, regex tiêu đề] – các mục bị ẩn vì trùng ý nghĩa với mục khác */
  var HIDE=[
    ["p-ov",/^Việc cần làm theo số liệu/],      /* trùng "Điều cần chú ý tuần này" */
    ["p-ov",/^Quảng cáo toàn danh mục/],         /* trùng thẻ Hiệu quả quảng cáo + KPI chi phí QC */
    ["p-ov",/^Tồn kho toàn danh mục/],           /* trùng thẻ Tồn kho & cảnh báo */
    ["p-gr",/^Đọc số & giải pháp theo nhóm/],    /* trùng vòng tròn doanh thu theo nhóm + bảng bên dưới + Điều cần chú ý */
    ["p-dt",/^Việc nên làm với SKU/],            /* trùng "Phân loại SKU" (Quản trị chuyên sâu) + Điều cần chú ý */
    ["p-inv",/^Giả định & ghi chú dữ liệu/],     /* ghi chú */
    ["p-mg",/^Xu hướng 12 tuần/],                /* trùng thẻ Xu hướng 12 tuần ở Tổng quan */
    ["p-mg",/^Rủi ro tồn kho/],                  /* trùng tab Tồn kho + thẻ Tồn kho & cảnh báo */
    ["p-mg",/^Giá bán thực hiện/]                /* trùng tab Listing & Giá + cảnh báo giá trong Điều cần chú ý */
  ];
  function title(sec){var h=sec.querySelector("h2");return h?h.textContent.replace(/\s+/g," ").trim():""}
  function moveZero(){
    var f=document.getElementById("alerts-fold"),ins=document.getElementById("pro-ins");
    if(!f||!ins||f.dataset.mv)return; var al=f.querySelectorAll(".alert"); if(!al.length)return;
    var box=document.getElementById("pi-extra");
    if(!box){box=document.createElement("div");box.id="pi-extra";var l=document.getElementById("pi-list");if(!l)return;l.after(box)}
    var z=[];al.forEach(function(a){var t=a.querySelector(".t");if(t&&/chưa phát sinh đơn/.test(t.textContent))z.push(t.firstChild.textContent.replace(/\s*chưa phát sinh đơn,?\s*FC\s*/," (FC ").trim()+")")});
    if(z.length)box.innerHTML='<div class="isu s2"><span class="sev s2">Ưu tiên vừa</span> <span class="chip">Doanh số</span> <span class="chip">'+z.length+' kênh</span><h4>'+z.length+' kênh có kế hoạch (FC) nhưng chưa phát sinh đơn trong kỳ</h4><div class="w">Vấn đề nằm ở: '+z.join(" · ")+'</div><ul class="fx"><li>Kiểm theo thứ tự: listing đã live chưa → có tồn kho tại thị trường đó chưa → đã bật quảng cáo chưa; ba nguyên nhân cần ba cách xử lý khác nhau.</li></ul></div>';
    f.dataset.mv="1"}
  function apply(){
    moveZero();
    HIDE.forEach(function(h){var pn=document.getElementById(h[0]);if(!pn)return;
      pn.querySelectorAll("section").forEach(function(sec){if(h[1].test(title(sec)))sec.style.display="none"})});
    /* tab Quản trị chuyên sâu: dải KPI đầu trang trùng KPI ở Tổng quan */
    var mg=document.getElementById("p-mg"); if(mg){var f=mg.querySelector("section");if(f&&!f.querySelector("h2")&&/DOANH THU TUẦN|Doanh thu tuần/i.test(f.textContent)&&f.textContent.length<600)f.style.display="none"}
    /* đánh lại số thứ tự mục */
    document.querySelectorAll("[id^=p-]").forEach(function(pn){if(pn.id.length>5)return;var n=0;
      pn.querySelectorAll("section").forEach(function(sec){if(sec.style.display==="none")return;var sn=sec.querySelector(".snum");
        if(sn&&getComputedStyle(sn).display!=="none"&&/^\d+$/.test(sn.textContent.trim())&&sn.textContent.trim()!=="00"){n++;var t=(n<10?"0":"")+n;if(sn.textContent!==t)sn.textContent=t}})})}
  var tm=null;function sch(){clearTimeout(tm);tm=setTimeout(apply,60)}
  if(window.MutationObserver)new MutationObserver(sch).observe(document.body||document.documentElement,{childList:true,subtree:true});
  [0,300,1200,3000].forEach(function(t){setTimeout(apply,t)});
})();
'''
k=s.rfind("</script>"); assert k>0; s=s[:k]+js+s[k:]   # chèn vào script cuối (builder chèn pro.js trước </script> cuối)
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
