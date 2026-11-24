"""
Kho lưu file P&L (giá vốn COGS + công thức tính phí từng kênh) dùng cho Profit PL5.

 - data/pl_ratecard/current.xlsx  : file P&L đang áp dụng. Kỳ nào KHÔNG upload file P&L thì ETL tự dùng file này.
 - data/pl_ratecard/history/      : các bản cũ (tên có mã sha) — không bao giờ bị xoá tự động.
 - data/pl_ratecard/index.json    : danh sách bản đã lưu (ngày lưu, kỳ nào upload, tên file gốc).
Khi một kỳ upload file P&L mới (nội dung khác bản đang lưu) thì bản đó trở thành current.xlsx và bản cũ được chuyển vào history/.
"""
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

STORE = Path(__file__).resolve().parent.parent / "data" / "pl_ratecard"


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _index():
    try:
        return json.loads((STORE / "index.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {"current": None, "items": []}


def _save_index(ix):
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / "index.json").write_text(json.dumps(ix, ensure_ascii=False, indent=1), encoding="utf-8")


def resolve(uploaded, log=print, period=None, store=None):
    """uploaded: Path file P&L người dùng upload ở kỳ này (hoặc None). Trả Path file P&L sẽ dùng (hoặc None nếu chưa có file nào)."""
    global STORE
    if store is not None:
        STORE = Path(store)
    cur = STORE / "current.xlsx"
    ix = _index()
    if uploaded and Path(uploaded).exists():
        new_sha = _sha(uploaded)
        if cur.exists() and ix.get("current") == new_sha:
            log(f"[pl5] file P&L kỳ này trùng bản đã lưu ({new_sha[:8]}).")
            return cur
        STORE.mkdir(parents=True, exist_ok=True)
        if cur.exists() and ix.get("current"):
            (STORE / "history").mkdir(exist_ok=True)
            shutil.copy2(cur, STORE / "history" / f"PL_{ix['current'][:8]}.xlsx")
        shutil.copy2(uploaded, cur)
        ix["current"] = new_sha
        ix["items"].append({"sha": new_sha, "saved": datetime.now().isoformat(timespec="seconds"), "period": period,
                            "name": Path(uploaded).name})
        _save_index(ix)
        log(f"[pl5] đã LƯU file P&L mới làm file áp dụng cho các kỳ sau ({new_sha[:8]}, data/pl_ratecard/current.xlsx).")
        return cur
    if cur.exists():
        when = next((i["saved"] for i in reversed(ix.get("items", [])) if i["sha"] == ix.get("current")), "")
        log(f"[pl5] kỳ này không upload file P&L — dùng file P&L đã lưu {(ix.get('current') or '')[:8]} {when}.")
        return cur
    return None
