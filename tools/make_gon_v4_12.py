"""Gọn v4 – lần 12: bỏ các mục chú thích gập (details.capfold: "Chú thích", "Điều chỉnh số kỳ trước"...) và các dòng ghi chú giải thích trong 2 thẻ mới.
   Chỉ ẩn bằng CSS (không xoá id/nội dung để JS cũ vẫn chạy). Dùng: python3 make_gon_v4_12.py vào.html ra.html (đã áp make_gon_v4_11)."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]); s=s.replace(a,b)
# ghi chú trong thẻ Hiệu quả QC (theo quốc gia) và Chất lượng sản phẩm
i=s.index('<div class="note">Gộp các kênh cùng quốc gia.'); j=s.index('</div>`:',i)+len('</div>')
s=s[:i]+s[j:]
i=s.index('<div class="note" style="margin-top:8px">Chỉ báo gián tiếp'); j=s.index('</div>',i)+len('</div>')
s=s[:i]+s[j:]
rep1('<h3>Chất lượng sản phẩm<span','<h3 title="Chỉ báo gián tiếp từ phí Return/Refund trong PL5; chưa có dữ liệu đánh giá sao hay lý do trả hàng">Chất lượng sản phẩm<span')
rep1('.xc{}\n','.xc{}\ndetails.capfold,.capfold{display:none!important}\n') if s.count('.xc{}\n')==1 else None
if 'details.capfold,.capfold{display:none' not in s:
    k=s.index('.xc{'); e=s.index('}\n',k)+2; s=s[:e]+'details.capfold,.capfold{display:none!important}\n'+s[e:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
