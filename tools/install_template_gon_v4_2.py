"""Đăng ký mẫu report 'Gọn v4.2' (= Gọn v4.1 + cảnh báo SKU bán thấp hơn COGS) vào sổ mẫu của app.
Chạy MỘT LẦN trong thư mục report_manager (máy local và server):   python tools/install_template_gon_v4_2.py
Không ghi đè mẫu nào. Sau đó ở màn hình Build của kỳ chọn "Mẫu report của kỳ này" = Gọn v4.2 rồi build lại."""
import subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import rtemplates  # noqa: E402

NAME = "Gọn v4.2"
if any(i["name"].strip().lower() == NAME.lower() for i in rtemplates._reg()["items"]):
    print(f"Đã có mẫu “{NAME}” — không cần cài lại."); sys.exit(0)
src = rtemplates.path("gon-v4-f20a98")
if not src.exists() or src.name == "report-template-base.html":
    sys.exit("Không thấy mẫu Gọn v4 (gon-v4-f20a98) — kiểm tra data/report_templates/")
tmp = Path(tempfile.mkdtemp())
subprocess.run([sys.executable, str(ROOT / "tools" / "make_gon_v4_21.py"), str(src), str(tmp / "v41.html")], check=True)
subprocess.run([sys.executable, str(ROOT / "tools" / "make_gon_v4_22.py"), str(tmp / "v41.html"), str(tmp / "v42.html")], check=True)
it = rtemplates.add(NAME, "Gọn v4.1 + cảnh báo SKU có giá bán bình quân thấp hơn COGS (thẻ ở Tổng quan và nhãn ở bảng Profit PL5 theo SKU). Cần ETL có etl/pl5.py mới (D.pl5.below_cogs).",
                    (tmp / "v42.html").read_bytes(), "claude", parent="gon-v4-f20a98", patches="gon-v4")
print("Đã thêm mẫu:", it["id"], f'({it["kb"]} KB)')
