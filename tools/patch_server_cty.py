"""Thêm vào server.py: tính lại các khối quản trị theo từng quốc gia (extras["by_cty"]). Chạy 1 lần: python tools/patch_server_cty.py
Idempotent; sao lưu server.py.truoc-tach-quoc-gia trước khi sửa. Cần file ctyview.py cùng thư mục gốc."""
import os, shutil, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(root, "server.py")
s = open(p, encoding="utf-8").read()
if "ctyview" in s:
    print("server.py đã có ctyview — bỏ qua"); sys.exit(0)
a = "import insights\n"
b = '            extras["sku_class"] = insights.sku_class(d)\n'
assert a in s and b in s, "không tìm thấy vị trí cần sửa trong server.py"
shutil.copy2(p, p + ".truoc-tach-quoc-gia")
s = s.replace(a, a + "import ctyview\n", 1)
s = s.replace(b, b + '''            try:     # tách theo quốc gia: tính lại Điều cần chú ý / Phân loại SKU / Rủi ro tồn kho... cho từng quốc gia
                extras["by_cty"] = ctyview.build_all(d, lambda X: insights.build(X, None, cfg.get("group_norm")), insights.sku_class)
            except Exception as e:
                extras["by_cty"] = {}; extras["by_cty_err"] = f"{type(e).__name__}: {e}"[:200]
''', 1)
open(p, "w", encoding="utf-8").write(s)
print("Đã cập nhật server.py (bản cũ: server.py.truoc-tach-quoc-gia)")
