"""Gọn v4 – lần 14: huy hiệu (icon + nhãn) cho hạng mục chưa hoàn thiện: Đang phát triển / Đang thử nghiệm / Sắp có (chưa phát triển).
   Danh sách gán trạng thái nằm ở mảng STT trong script; sửa mảng này để đổi trạng thái hoặc thêm hạng mục.
   Dùng: python3 make_gon_v4_14.py vào.html ra.html (đã áp make_gon_v4_13)."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
css='''.stx{display:inline-flex;align-items:center;gap:5px;margin-left:10px;padding:2px 9px 2px 7px;border-radius:99px;font:600 11px/1.5 "Public Sans",system-ui,sans-serif;letter-spacing:.01em;text-transform:none;white-space:nowrap;vertical-align:middle;border:1px solid transparent;cursor:help}
.stx svg{width:13px;height:13px;flex:none;stroke:currentColor;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.stx-dev{color:#8a5a00;background:rgba(214,150,20,.14);border-color:rgba(214,150,20,.35)}
.stx-test{color:#6b3fb5;background:rgba(124,77,214,.12);border-color:rgba(124,77,214,.32)}
.stx-new{color:#4a5a78;background:rgba(100,116,150,.10);border:1px dashed rgba(100,116,150,.55)}
:root[data-theme="dark"] .stx-dev{color:#f1c36a}:root[data-theme="dark"] .stx-test{color:#c3a4f5}:root[data-theme="dark"] .stx-new{color:#a9b7d3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .stx-dev{color:#f1c36a}:root:not([data-theme="light"]) .stx-test{color:#c3a4f5}:root:not([data-theme="light"]) .stx-new{color:#a9b7d3}}
@media print{.stx{border:1px solid #999;background:none;color:#333}}
'''
js=r'''
(function(){
  var IC={
    dev:'<svg viewBox="0 0 24 24"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/></svg>',
    test:'<svg viewBox="0 0 24 24"><path d="M9 3h6M10 3v6.5L4.5 19a1.6 1.6 0 0 0 1.4 2.4h12.2a1.6 1.6 0 0 0 1.4-2.4L14 9.5V3"/><path d="M7.5 15h9"/></svg>',
    nw:'<svg viewBox="0 0 24 24"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 16v4M17 18h4"/></svg>'};
  var T={
    dev:{k:"dev",i:IC.dev,l:"Đang phát triển",t:"Đang phát triển: đã có một phần số liệu, còn thiếu dữ liệu nguồn để hoàn thiện"},
    test:{k:"test",i:IC.test,l:"Thử nghiệm",t:"Đang thử nghiệm: số liệu hoặc cách tính còn mang tính giả lập/tham khảo, chưa dùng để ra quyết định"},
    nw:{k:"new",i:IC.nw,l:"Sắp có",t:"Hạng mục mới, chưa phát triển: đang chờ dữ liệu nguồn"}};
  /* [vùng chứa, regex tiêu đề h2/h3, trạng thái] */
  var STT=[
    ["#p-dt section",/^P&L PL5/,"dev"],
    ["#p-dt section",/^Sản phẩm bán không đạt/,"test"],
    ["#p-mg section",/^Mô phỏng giá & quảng cáo/,"test"],
    ["#p-bb section",/^Phân rã theo size và màu/,"dev"],
    ["#p-bb section",/^Đang chờ dữ liệu nguồn/,"nw"],
    ["#dash .dc",/^Chất lượng sản phẩm/,"dev"]
  ];
  function apply(){
    STT.forEach(function(r){
      document.querySelectorAll(r[0]).forEach(function(box){
        var h=box.querySelector("h2,h3"); if(!h||h.querySelector(".stx"))return;
        var txt=h.textContent.replace(/\s+/g," ").trim(); if(!r[1].test(txt))return;
        var d=T[r[2]],b=document.createElement("span");b.className="stx stx-"+d.k;b.title=d.t;b.innerHTML=d.i+d.l;
        var pk=h.querySelector(".pk"); if(pk)h.insertBefore(b,pk); else h.appendChild(b)})})}
  var tm=null;function sch(){clearTimeout(tm);tm=setTimeout(apply,80)}
  if(window.MutationObserver)new MutationObserver(sch).observe(document.body||document.documentElement,{childList:true,subtree:true});
  [0,300,1200,3000].forEach(function(t){setTimeout(apply,t)});
})();
'''
k=s.index('.xc{'); e=s.index('}\n',k)+2; s=s[:e]+css+s[e:]
k=s.rfind("</script>"); assert k>0; s=s[:k]+js+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
