"""Nâng cấp NGAY TRÊN mẫu "Gọn v4.2" (không tạo mẫu mới): thêm tách theo quốc gia —
thanh chọn quốc gia, thẻ tóm tắt theo quốc gia ở Tổng quan, bảng Profit PL5 quốc gia × sàn, Top SKU theo quốc gia.
Chạy MỘT LẦN trong thư mục report_manager (máy local và server):   python tools/update_template_gon_v4_2.py
- Sao lưu file mẫu cũ vào data/report_templates/_backup/ trước khi sửa.
- Chỉ sửa file HTML của mẫu Gọn v4.2 và dòng (sha, kb, ghi chú) của đúng mẫu đó trong sổ mẫu; không đụng mẫu khác, users.json.
- Chạy lại lần nữa sẽ tự báo "đã nâng cấp rồi". Các kỳ đang dùng Gọn v4.2 chỉ cần Build lại để thấy bản mới."""
import os, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import rtemplates  # noqa: E402

it = next((i for i in rtemplates._reg()["items"] if i["name"].strip().lower() == "gọn v4.2"), None)
if not it:
    sys.exit("Chưa có mẫu “Gọn v4.2” — chạy trước:  python tools/install_template_gon_v4_2.py")
f = rtemplates.DIR / it["file"]
raw = f.read_bytes()
if b'id="plmc-sec"' in raw:
    print("Mẫu Gọn v4.2 đã có phần tách theo quốc gia — không cần làm lại."); sys.exit(0)

tmp = Path(tempfile.mkdtemp())
(tmp / "in.html").write_bytes(raw)
subprocess.run([sys.executable, str(ROOT / "tools" / "make_gon_v4_23.py"), str(tmp / "in.html"), str(tmp / "out.html")], check=True)
new = (tmp / "out.html").read_bytes()

bk = rtemplates.DIR / "_backup"; bk.mkdir(parents=True, exist_ok=True)
shutil.copy2(f, bk / f"{f.stem}.truoc-tach-quoc-gia.{datetime.now():%Y%m%d-%H%M%S}.html")
t2 = f.with_suffix(".tmp"); t2.write_bytes(new); os.replace(t2, f)
with rtemplates.LOCK:
    d = rtemplates._reg()
    for x in d["items"]:
        if x["id"] == it["id"]:
            x["sha"] = rtemplates._sha(new); x["kb"] = len(new) // 1024
            x["note"] = (x.get("note") or "").rstrip() + " | Đã thêm tách theo quốc gia (thanh chọn US/CAN/AUS, thẻ tóm tắt theo quốc gia, Profit PL5 quốc gia × sàn, Top SKU theo quốc gia). Cần etl/pl5.py mới."
    rtemplates._save(d)
print(f"Đã nâng cấp mẫu “{it['name']}” ({len(raw)//1024} → {len(new)//1024} KB). Bản cũ lưu ở data/report_templates/_backup/. Giờ Build lại kỳ cần xem.")
