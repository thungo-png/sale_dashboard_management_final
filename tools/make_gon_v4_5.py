"""Gọn v4 – chỉnh nhỏ (lần 5): đổi "Tóm tắt điều hành" thành "TỔNG QUAN", đặt ngang hàng với ô chọn khoảng ngày ở góc phải.
   Dùng: python3 make_gon_v4_5.py vào.html ra.html (đã áp make_gon_v4_4). Không đụng dòng const D, không xoá id."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
dl=[l for l in s.split("\n") if l.startswith("const D = ")]
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep1('<div class="meta" id="mmeta"></div>','')
rep1('<div class="shead"><span class="snum">01</span><h2>Tóm tắt điều hành</h2><span class="hint" id="ovhint"></span></div>',
     '<div class="shead ovtop"><span class="snum">01</span><h2>Tổng quan</h2><span class="hint" id="ovhint"></span><div class="meta" id="mmeta"></div></div>')
rep1('.xc{}\n','.xc{}\n.mast{display:none}.ovtop{align-items:center;flex-wrap:wrap;gap:8px 14px}.ovtop .snum{display:none}.ovtop h2{font-family:inherit;font-size:20px;font-weight:700;letter-spacing:.03em;text-transform:uppercase}.ovtop .meta{margin:0 0 0 auto!important}\n')
assert [l for l in s.split("\n") if l.startswith("const D = ")]==dl
open(sys.argv[2],"w",encoding="utf-8").write(s)
