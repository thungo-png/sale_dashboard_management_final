(function(){
  /* Gọn v4.20: Tổng quan chỉ giữ bản tóm tắt các điểm cần chú ý (ưu tiên cao); hướng xử lý, chi tiết từng mục và việc cần chốt họp nằm ở menu Việc cần làm */
  var css=document.createElement("style");
  css.textContent='#pro-ins.ov-compact #pi-chips,#pro-ins.ov-compact #pi-more,#pro-ins.ov-compact .isu:not(.s3),#pro-ins.ov-compact .isu .fx,#pro-ins.ov-compact .isu details{display:none!important}'
   +'#pro-ins .ov-more{margin-top:10px;font-size:13px;color:var(--ink-2)}#pro-ins .ov-more button{margin-left:6px}';
  document.head.appendChild(css);
  function apply(){
    var s=document.getElementById("pro-ins");if(!s||s.dataset.c20)return;var list=s.querySelector("#pi-list");if(!list||!list.children.length)return;s.dataset.c20="1";s.classList.add("ov-compact");
    var hint=s.querySelector(".hint");if(hint)hint.textContent="Các việc ưu tiên cao · hướng xử lý và việc cần chốt họp ở menu Việc cần làm";
    var n=s.querySelectorAll(".isu").length,hi=s.querySelectorAll(".isu.s3").length;
    var d=document.createElement("div");d.className="ov-more";d.innerHTML='Đang hiển thị '+hi+' nhóm ưu tiên cao. Toàn bộ danh sách, hướng xử lý, người phụ trách, hạn và các việc cần chốt họp: <button type="button" class="pbtn" id="ov-to-td">Mở Việc cần làm</button>';
    s.appendChild(d);
    d.querySelector("#ov-to-td").addEventListener("click",function(){var t=document.querySelector('.tab[data-p="td"]');if(t)t.click()})}
  var tm=null;function sch(){clearTimeout(tm);tm=setTimeout(apply,100)}
  if(window.MutationObserver)new MutationObserver(sch).observe(document.body||document.documentElement,{childList:true,subtree:true});
  [0,400,1500,3500].forEach(function(t){setTimeout(apply,t)});
})();
