"""
Điểm cắm ETL của app.

Chạy theo thứ tự ưu tiên:
 1. Nếu kỳ có file `data_json` đã upload  -> dùng thẳng, bỏ qua ETL.
 2. Nếu có `etl/custom_build.py` với hàm `build(ctx) -> dict` -> gọi hàm đó.
    (Đây là chỗ bọc etl_v3.py / patch_v3.py của bạn vào.)
 3. Ngược lại: báo lỗi hướng dẫn.

ctx là dict:
    ctx["period"]   : meta của kỳ (id, label, type ...)
    ctx["inputs"]   : {slot_key: Path} — các file đã upload
    ctx["cfg"]      : cấu hình (data/config.json)
    ctx["prev"]     : dict D của kỳ đã build gần nhất trước đó (hoặc None)
    ctx["seed"]     : dict D mẫu lấy từ template (để tham chiếu schema)
    ctx["log"]      : hàm log(str) — hiện trong màn hình Build
Kết quả: dict D đúng schema (xem reference doc/03 và 07).
"""
import importlib.util, json
from pathlib import Path

HERE = Path(__file__).parent


class EtlNotReady(Exception):
    pass


def build_data(ctx):
    inputs = ctx["inputs"]
    if "data_json" in inputs:
        ctx["log"]("[etl] Dùng data.json đã upload, bỏ qua ETL.")
        return json.loads(Path(inputs["data_json"]).read_text(encoding="utf-8"))

    custom = HERE / "custom_build.py"
    if custom.exists():
        spec = importlib.util.spec_from_file_location("custom_build", custom)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ctx["log"]("[etl] Chạy etl/custom_build.py ...")
        return mod.build(ctx)

    raise EtlNotReady(
        "Chưa có ETL. Hãy (a) upload data.json dựng sẵn ở mục C, hoặc (b) tạo file etl/custom_build.py "
        "với hàm build(ctx) -> dict (xem etl/custom_build.example.py)."
    )
