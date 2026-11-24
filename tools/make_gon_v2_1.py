#!/usr/bin/env python3
"""Gọn v2.1 = Gọn v2 bỏ tab Task Tracker (trùng với module "Hôm nay" của app).
Lý do: việc cần làm đã có ở "Hôm nay" (lưu trên máy chủ, có người phụ trách/hạn/nhật ký); tab trong report lưu bằng claude.use("db")
nên khi chạy trong app local luôn ở chế độ chỉ xem. Không đụng dòng `const D`, không xoá id nào khác.
Dùng: python3 make_gon_v2_1.py <gon_v2.html> <ra.html>"""
import re, sys
SRC, DST = sys.argv[1], sys.argv[2]
t = open(SRC, encoding="utf-8").read()
def once(pat, flags=0):
    m = list(re.finditer(pat, t, flags)); assert len(m) == 1, (pat, len(m)); return m[0]
d_before = [l for l in t.split("\n") if l.startswith("const D = ")]
m = once(r'[ \t]*<button class="tab"[^>\n]*data-p="tt">Task Tracker</button>\n'); t = t[:m.start()] + t[m.end():]
m = once(r'<div class="panel" id="p-tt".*?\n</div>\n(?=\s*<footer)', re.S); t = t[:m.start()] + t[m.end():]
m = once(r'// ---------- Tab Task Tracker ----------\n.*?(?=\n\n// =+ MODULE CHUOI)', re.S); t = t[:m.start()] + t[m.end():]
m = once(r',\n  tt:function\(\)\{ttInit\(\);\}\};'); t = t[:m.start()] + "};" + t[m.end():]
assert [l for l in t.split("\n") if l.startswith("const D = ")] == d_before
for bad in ("p-tt", "ttInit", "ttRender", "ttCollect", "data-p=\"tt\""):
    assert bad not in t, bad
open(DST, "w", encoding="utf-8").write(t); print("OK", DST, len(t) // 1024, "KB")
