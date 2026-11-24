"""GHI LẠI chuẩn của mẫu gốc (tests/golden_base.json). Chỉ chạy khi CHỦ ĐỘNG muốn đổi cách mẫu gốc hiển thị
(ví dụ sửa patches/pro.js dùng chung). Mặc định chuẩn được tạo bằng logic render gốc, nên không bao giờ vô tình ghi nhận một thay đổi."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from base_frozen_common import *
import builder

seed, ex = inputs()
html = legacy_render(seed, ["pro"], ex, builder.TEMPLATE, builder.PATCHES)
g = {"render_sha256": sha(html.encode("utf-8")), "template_sha256": sha(builder.TEMPLATE.read_bytes()),
     "patches": {n: sha((builder.PATCHES / n).read_bytes()) for n in ("pro.js", "pro.css.html")},
     "note": "Chuẩn render của MẪU GỐC. Lệch = có thay đổi chung (template gốc, patches/pro.*, insights.py hoặc builder.py) làm đổi mẫu gốc."}
GOLDEN.write_text(json.dumps(g, indent=1), encoding="utf-8")
print("đã ghi", GOLDEN, g["render_sha256"][:12])
