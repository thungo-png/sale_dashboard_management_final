(function(){
  /* Gọn v4.19: rà soát toàn report — nhãn trạng thái dữ liệu cho từng hạng mục, bỏ mục trùng, sửa chữ chờ-dữ-liệu đã lỗi thời */
  var $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var IC={part:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/></svg>',
          miss:'<svg viewBox="0 0 24 24"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17.2v.1"/></svg>',
          sim:'<svg viewBox="0 0 24 24"><path d="M9 3h6M10 3v6.5L4.5 19a1.6 1.6 0 0 0 1.4 2.4h12.2a1.6 1.6 0 0 0 1.4-2.4L14 9.5V3"/><path d="M7.5 15h9"/></svg>',
          est:'<svg viewBox="0 0 24 24"><path d="M5 17c3-8 5-8 7-4s4 3 7-6"/><path d="M4 20h16"/></svg>'};
  var K={part:"Một phần",miss:"Thiếu dữ liệu",sim:"Giả lập",est:"Ước tính"};
  /* [vùng chứa, tiêu đề, loại, nhãn riêng, giải thích] */
  var R=[
    ["#dash .dc",/^Chất lượng sản phẩm/,"part","Một phần","Số thật của Wayfair nhưng mới gắn được 92/580 listing vào danh mục theo dõi; số tích luỹ nhiều tháng nên không so theo tuần"],
    ["#dash .dc",/^Hiệu quả quảng cáo/,"part","Thiếu Shopify, Walmart","Chưa có báo cáo quảng cáo của Shopify và Walmart; Wayfair chỉ có số của tuần báo cáo"],
    ["section",/^P&L PL5/,"est","Ước tính một phần","Cột quảng cáo (SEM) trong file P&L là số tạm tính, thấp hơn chi phí quảng cáo thật; chưa tính được Shopify US/CAN; giá vốn theo chuẩn mới từ 01/10"],
    ["#p-mg section",/^Rủi ro tồn kho/,"sim","Lead time giả lập","Số tuần còn bán được thật, nhưng ngày hàng về (lead time) và MOQ đang là số giả lập"],
    ["#p-inv section",/^Tổng tồn theo SKU/,"sim","Lead time giả lập","Số tuần còn bán được thật, nhưng ngày hàng về (lead time) và MOQ đang là số giả lập"],
    ["#p-mg section",/^Chi phí giữ hàng/,"est","Ước tính","Chưa có báo cáo phí lưu kho thật; đang tính theo giả định"],
    ["#p-mg section",/^Tồn chưa có giá vốn/,"part","Thiếu giá vốn","757 sản phẩm / 15 SKU chưa có giá vốn nên vốn tồn kho đang thấp hơn thực tế"],
    ["#p-cp section",/^Chi phí quảng cáo, TACoS/,"part","Thiếu Shopify, Walmart","TACoS mới phủ Amazon và Wayfair; Wayfair chỉ có số tuần báo cáo nên chưa so được 14/30 ngày"],
    ["#p-mk section",/^Amazon — Buy Box/,"part","Chỉ có Mỹ","Business Report chưa có file Canada và không ghi khoảng ngày"],
    ["#p-mk section",/^Chất lượng so với chuẩn/,"part","92/580 listing","Chỉ các listing gắn được vào danh mục theo dõi"],
    ["#p-mk section",/^Thứ hạng ngành hàng/,"part","Một phần","Chỉ 17 listing thuộc chiến dịch có báo cáo thứ hạng; Amazon không có nguồn tương đương"],
    ["#p-mk section",/^Dữ liệu đối thủ còn thiếu/,"miss","Thiếu dữ liệu","Chưa có danh sách đối thủ, giá đối thủ, rating và review"],
    ["#p-bb .card",/^Rating & Review/,"miss","Thiếu dữ liệu","Chưa có file rating, review"],
    ["#p-bb .card",/^Trạng thái listing/,"miss","Thiếu dữ liệu","Chưa có file trạng thái listing"],
    ["#p-bb .card",/^Sessions & chuyển đổi/,"part","Chỉ có Mỹ","Business Report Amazon Mỹ (khoảng ngày chưa ghi rõ); chưa có Wayfair, Shopify"]
  ];
  function badge(k,l,t){var b=document.createElement("span");b.className="stx stx-"+(k==="sim"?"test":k==="est"?"dev":k==="miss"?"miss":"part");b.dataset.a19="1";b.title=t;b.innerHTML=IC[k]+l;return b}
  function put(box,h,r){var old=$$(".stx",h);old.forEach(function(x){x.remove()});var pk=$(".pk",h);var b=badge(r[2],r[3]||K[r[2]],r[4]);if(pk)h.insertBefore(b,pk);else h.appendChild(b)}
  function labels(){
    R.forEach(function(r){$$(r[0]).forEach(function(box){var h=$("h2,h3",box);if(!h||$('[data-a19]',h))return;var t=h.textContent.replace(/\s+/g," ").trim();if(r[1].test(t))put(box,h,r)})})}
  /* bỏ phần trùng: thứ hạng và thị phần tìm kiếm Wayfair nằm ở cả Quảng cáo lẫn Thị trường; Buy Box và khung đối thủ ở Listing & Giá trùng với Thị trường */
  function dedupe(){
    var mk=$("#p-mk");if(!mk)return;
    var cp=$("#p-cp");
    if(cp&&!cp.dataset.dd19){var hit=0;$$("section",cp).forEach(function(s){var h=$("h2",s);if(h&&/^(Thứ hạng ngành hàng trên Wayfair|Vị thế trên tìm kiếm)/.test(h.textContent.trim())){s.style.display="none";hit++}});
      if(hit){cp.dataset.dd19="1";var n=document.createElement("p");n.className="cap";n.style.cssText="margin:14px 0";n.innerHTML="Thứ hạng ngành hàng và thị phần tìm kiếm Wayfair đã chuyển sang menu <b>Thị trường &amp; Đối thủ</b> (có so với kỳ trước).";cp.appendChild(n)}}
    var bb=$("#p-bb");
    if(bb&&!bb.dataset.dd19){var fold=null;$$("section",bb).forEach(function(s){var h=$("h2",s);if(h&&/^Đang chờ dữ liệu nguồn|^Listing & Rating, Đối thủ/.test(h.textContent.trim()))fold=s});
      if(fold){bb.dataset.dd19="1";
        $$(".bsec",fold).forEach(function(b){var h=$("h2",b),t=h?h.textContent.trim():"";
          if(/^Buy Box$/.test(t)||/^Đối thủ & thị trường/.test(t))b.style.display="none"});
        var h2=$("h2",fold);if(h2){h2.textContent="Listing & Rating — còn thiếu một phần dữ liệu"}
        var hint=$(".hint",fold);if(hint)hint.innerHTML="Đã có Sessions &amp; chuyển đổi (Mỹ); chưa có Rating, Review, trạng thái listing. Buy Box và đối thủ xem ở menu Thị trường &amp; Đối thủ";
        var al=$(".alert .t",fold);if(al)al.innerHTML='Rating, review và trạng thái listing chưa có dữ liệu nguồn <span class="chip w">cần bổ sung nguồn</span>';
        var ad=$(".alert .d",fold);if(ad)ad.innerHTML="Thẻ Sessions &amp; chuyển đổi đã có số từ Business Report. Hai thẻ còn lại tự lên số khi có file tương ứng.";
        var tag=$(".stx",h2.parentNode);if(tag)tag.remove();var b=badge("part","Một phần","Có Sessions Mỹ; thiếu Rating, Review, trạng thái listing");var pk=$(".pk",h2.parentNode);h2.parentNode.insertBefore(b,$(".hint",fold))}}
    /* Sức khỏe dữ liệu và Giả định ở nhiều tab: giữ bản ở Dữ liệu & Giả định */
    var dd=$("#p-dd");
    if(dd){["#p-mg","#p-inv"].forEach(function(id){var p=$(id);if(!p)return;$$("section",p).forEach(function(s){var h=$("h2",s);if(h&&/^(Sức khỏe dữ liệu|Giả định & ghi chú dữ liệu)/.test(h.textContent.trim()))s.style.display="none"})})}
  }
  /* bảng "Dữ liệu còn thiếu" ở tab Dữ liệu & Giả định: sửa dòng đã lỗi thời, thêm dòng mới */
  function fixMissing(){
    var dd=$("#p-dd");if(!dd||dd.dataset.fm19)return;var rows=$$("tr",dd);var any=rows.some(function(r){return /Buy Box, đối thủ/.test(r.textContent)});if(!any)return;dd.dataset.fm19="1";
    rows.forEach(function(r){var c=r.cells;if(!c||c.length<3)return;var t=c[0].textContent;
      if(/^Đánh giá sao, lý do trả hàng/.test(t)){c[0].textContent="Đánh giá sao và review (Amazon, Wayfair)";c[1].textContent="Amazon Reviews, Wayfair Reviews. Đã có sự cố và hoàn đổi ý của Wayfair (Summary-data)";c[2].textContent="Rating theo listing; chất lượng sản phẩm đủ hơn"}
      if(/^Buy Box, đối thủ/.test(t)){c[0].textContent="Giá đối thủ, danh sách thương hiệu và ASIN đối thủ";c[1].textContent="Giá đối thủ theo ASIN/SKU. Buy Box Mỹ đã có từ Business Report";c[2].textContent="Mục Đối thủ trong Thị trường & Đối thủ"}});
    var last=rows.filter(function(r){return r.cells&&r.cells.length>=3&&r.parentNode.tagName==="TBODY"}).pop();if(!last)return;
    [["Business Report Amazon Canada và khoảng ngày","File Canada, kèm khoảng ngày của cả hai file Business Report","Buy Box Canada; xác định đúng kỳ"],
     ["Lead time và MOQ thật của từng SKU","Bảng nhà cung cấp: lead time sản xuất + vận chuyển, MOQ","Lịch nhập hàng; hiện đang là số giả lập"],
     ["Báo cáo quảng cáo Wayfair các tuần trước","CR của Wayfair cho ít nhất 4 tuần gần nhất","Chi phí quảng cáo 14 và 30 ngày của Wayfair"],
     ["Xác nhận cơ sở giá vốn mới","Giá vốn chuẩn áp dụng từ 01/10/2026: đã gồm cước, thuế nhập khẩu hay chưa","Biên lợi nhuận Wayfair đang âm sâu; cần chắc giá vốn không bị tính trùng"]
    ].forEach(function(x){var n=last.cloneNode(true);for(var i=0;i<3;i++)if(n.cells[i])n.cells[i].textContent=x[i];last.parentNode.appendChild(n)})}
  var tm=null;function run(){clearTimeout(tm);tm=setTimeout(function(){try{labels();dedupe();fixMissing()}catch(e){console.warn("audit19",e)}},120)}
  var css=document.createElement("style");css.textContent='.stx-miss{color:#a3282a;background:rgba(200,50,50,.10);border-color:rgba(200,50,50,.32)}.stx-part{color:#0f6b73;background:rgba(15,130,140,.11);border-color:rgba(15,130,140,.32)}:root[data-theme="dark"] .stx-miss{color:#f19a9b}:root[data-theme="dark"] .stx-part{color:#7fd3d9}@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .stx-miss{color:#f19a9b}:root:not([data-theme="light"]) .stx-part{color:#7fd3d9}}';document.head.appendChild(css);
  if(window.MutationObserver)new MutationObserver(run).observe(document.body||document.documentElement,{childList:true,subtree:true});
  [0,400,1500,3500].forEach(function(t){setTimeout(run,t)});
})();
