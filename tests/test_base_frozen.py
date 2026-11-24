"""Đảm bảo MẪU GỐC không bị ảnh hưởng bởi bất cứ thay đổi nào cho mẫu mới. Chạy:  python3 -I tests/test_base_frozen.py
Kiểm: (1) file mẫu gốc nguyên vẹn; (2) patches/pro.* dùng chung nguyên vẹn; (3) report render ra đúng từng byte so với chuẩn
tạo bằng logic gốc; (4) đường render mới (builder.render + rtemplates) cho cùng kết quả như logic gốc;
(5) mẫu mới dùng bộ patch riêng, không dùng patches/ chung."""
import sys
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from base_frozen_common import *
import builder, rtemplates

g = json.loads(GOLDEN.read_text(encoding="utf-8"))
errs = []
if sha(builder.TEMPLATE.read_bytes()) != g["template_sha256"]:
    errs.append("templates/report-template-base.html đã bị sửa — dùng bản sao lưu data/report_templates/_backup/")
for n, h in g["patches"].items():
    if sha((builder.PATCHES / n).read_bytes()) != h:
        errs.append(f"patches/{n} (dùng chung với MẪU GỐC) đã bị sửa — hãy đặt thay đổi vào bộ patch riêng patches/<tên>/ cho mẫu mới")
seed, ex = inputs()
new = builder.render(seed, ["pro"], ex, rtemplates.path("base"), rtemplates.patch_dir("base"))
leg = legacy_render(seed, ["pro"], ex, builder.TEMPLATE, builder.PATCHES)
if new != leg:
    errs.append("builder.render cho mẫu gốc khác logic render gốc (đường render đã bị đổi)")
if sha(new.encode("utf-8")) != g["render_sha256"]:
    errs.append("report của mẫu gốc đã thay đổi so với chuẩn (template / patches / insights.py / builder.py)")
if rtemplates.patch_dir("base") is not None:
    errs.append("mẫu gốc phải luôn dùng patches/ chung")
for it in rtemplates.list_all()["items"]:
    if not it["builtin"] and it.get("patches"):
        pd = rtemplates.patch_dir(it["id"])
        if pd is None or pd.resolve() == builder.PATCHES.resolve():
            errs.append(f"mẫu {it['id']} khai báo bộ patch riêng nhưng không tìm thấy thư mục patches/{it['patches']}")
if errs:
    print("FAIL — mẫu gốc có thể bị ảnh hưởng:"); [print(" -", e) for e in errs]; sys.exit(1)
print("OK — mẫu gốc nguyên vẹn, render trùng từng byte với chuẩn", g["render_sha256"][:12])
