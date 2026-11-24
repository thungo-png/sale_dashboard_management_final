"""Ghi chú & sự kiện theo kỳ (data/notes.json): 'tuần này chạy Deal', 'đổi giá', 'hết hàng 3 ngày'…
Dùng để giải thích biến động; hiện trong app và đánh dấu trên biểu đồ xu hướng của report."""
import json, os, re, threading, uuid
from datetime import datetime
from pathlib import Path

FILE = Path(__file__).parent / "data" / "notes.json"
LOCK = threading.Lock()
TYPES = {"deal": "Khuyến mãi / Deal", "price": "Đổi giá", "stock": "Tồn kho / hết hàng", "ads": "Quảng cáo", "listing": "Listing / nội dung", "other": "Khác"}


def _load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def _save(n):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp"); tmp.write_text(json.dumps(n, ensure_ascii=False, indent=1), encoding="utf-8"); os.replace(tmp, FILE)


def list_notes(period=None):
    n = sorted(_load(), key=lambda x: (x.get("date", ""), x.get("created", "")), reverse=True)
    return [x for x in n if not period or x.get("period") == period]


def add(period, date, typ, text, user):
    text = (text or "").strip()
    if not text:
        raise ValueError("Cần nhập nội dung")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date or ""):
        date = datetime.now().date().isoformat()
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Ngày không hợp lệ")
    if typ not in TYPES:
        typ = "other"
    with LOCK:
        n = _load()
        x = {"id": uuid.uuid4().hex[:10], "period": period, "date": date, "type": typ, "text": text[:500], "user": user, "created": datetime.now().isoformat(timespec="seconds")}
        n.append(x); _save(n); return x


def remove(nid):
    with LOCK:
        n = _load(); m = [x for x in n if x["id"] != nid]
        if len(m) == len(n):
            raise ValueError("Không có ghi chú này")
        _save(m)
