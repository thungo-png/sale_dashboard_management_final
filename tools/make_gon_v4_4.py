"""Gọn v4 – chỉnh nhỏ (lần 4): bỏ dòng tổng bên cạnh ô chọn ngày; đưa ô chọn khoảng ngày sang góc phải (kiểu "7 ngày qua" + biểu tượng lịch).
   Dùng: python3 make_gon_v4_4.py vào.html ra.html (đã áp make_gon_v4_3). Không đụng dòng const D, không xoá id."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
dl=[l for l in s.split("\n") if l.startswith("const D = ")]
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep1('<option value="7">7 ngày (kỳ báo cáo W${D.meta.week_no})</option><option value="14">14 ngày</option><option value="30">30 ngày</option><option value="90">90 ngày</option>',
     '<option value="7">7 ngày qua</option><option value="14">14 ngày qua</option><option value="30">30 ngày qua</option><option value="90">90 ngày qua</option>')
cal="url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2362736b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='16' rx='3'/%3E%3Cpath d='M16 3v4M8 3v4M3 10h18'/%3E%3C/svg%3E\")"
rep1('.xc{}\n','.xc{}\n.meta{justify-content:flex-end;background:none!important;border:0!important;box-shadow:none!important;padding:0!important;margin:0 0 6px!important}.rngsum{display:none!important}.meta select{appearance:none;-webkit-appearance:none;padding:7px 36px 7px 14px!important;background:var(--card) '+cal+' no-repeat right 12px center!important;border-radius:10px;font-weight:500;min-width:140px}\n')
assert [l for l in s.split("\n") if l.startswith("const D = ")]==dl
open(sys.argv[2],"w",encoding="utf-8").write(s)
