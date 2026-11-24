"""Gọn v4.2 = Gọn v4.1 + cảnh báo "giá bán < COGS" (đọc D.pl5.below_cogs do etl/pl5.py tạo).
 - Tổng quan: thêm một thẻ cảnh báo liệt kê các SKU × sàn × quốc gia bán thấp hơn giá vốn (top 6 theo mức chênh).
 - Bảng Profit PL5 theo SKU: dòng SKU bán dưới giá vốn có nhãn "giá < COGS".
Chạy: python tools/make_gon_v4_22.py <gon-v4-1.html> <file ra>. Không có D.pl5.below_cogs (kỳ cũ) thì không hiện gì."""
import sys
s = open(sys.argv[1], encoding="utf-8").read()

def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:70], s.count(a))
    s = s.replace(a, b)

# 1) Bảng PL5 theo SKU: nhãn cạnh mã SKU
rep('''        body+=`<tr><td>${x.sku}<span class="sub-asin">${short(x.grp)} · ${x.mp} · ${x.cty}</span></td>
          <td>${N(f.r)}</td><td>${N(f.cogs)}</td>''',
    '''        const lowp=f.q>0&&f.cogs>f.r+0.005?` <span class="chip w" title="Giá bán bình quân ${N(f.r/f.q)} USD/cái thấp hơn COGS ${N(f.cogs/f.q)} USD/cái — bán là lỗ trước cả phí sàn và quảng cáo">giá &lt; COGS</span>`:"";
        body+=`<tr><td>${x.sku}${lowp}<span class="sub-asin">${short(x.grp)} · ${x.mp} · ${x.cty}</span></td>
          <td>${N(f.r)}</td><td>${N(f.cogs)}</td>''')

# 2) Thẻ cảnh báo ở Tổng quan (ngay trước thẻ "Khoảng cách tới FC")
rep('''  a+=`<div class="alert warn"><div class="stripe"></div><div class="body"><div class="t">Khoảng cách tới FC lặp lại''',
    '''  {const bc=(D.pl5&&D.pl5.below_cogs)||[];
   if(bc.length){
    const tot=bc.reduce((u,z)=>u+z.gap,0), top=bc.slice(0,6);
    a+=`<div class="alert"><div class="stripe"></div><div class="body"><div class="t">${bc.length} SKU bán thấp hơn giá vốn (COGS) tuần này <span class="chip w">rà giá bán / khuyến mãi</span></div><div class="d">Giá bán bình quân/cái thấp hơn COGS/cái, nên mỗi cái bán ra đã lỗ trước cả phí sàn và quảng cáo; tổng chênh ${N(tot)} USD. Nhiều nhất: ${top.map(z=>`<b>${z.sku}</b> ${z.mp} ${z.cty} (giá ${N(z.price)} &lt; COGS ${N(z.cogs_u)}, ${z.q} cái, chênh ${N(z.gap)})`).join("; ")}${bc.length>top.length?`; và ${bc.length-top.length} SKU khác`:""}. Hướng xử lý: nâng giá/Base Cost hoặc giảm khuyến mãi lên mức không thấp hơn COGS, đồng thời giảm quảng cáo cho các SKU này. Xem nhãn "giá &lt; COGS" ở bảng Profit PL5 theo SKU.</div></div></div>`;
   }}
  a+=`<div class="alert warn"><div class="stripe"></div><div class="body"><div class="t">Khoảng cách tới FC lặp lại''')
open(sys.argv[2], "w", encoding="utf-8").write(s)
