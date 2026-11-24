"""Kho task dùng chung (data/tasks.json). Task tự sinh từ analysis.py, hoặc tạo tay.
Một task ứng với một `key` vấn đề; sang kỳ sau vấn đề còn thì task cũ được cập nhật thay vì tạo trùng."""
import json, os, threading, uuid
from datetime import datetime, timedelta
from pathlib import Path

FILE = Path(__file__).parent / "data" / "tasks.json"
LOCK = threading.Lock()
STATUS = ("todo", "doing", "done", "dismissed")
DUE_DAYS = {3: 2, 2: 5, 1: 7}


def _load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def _save(t):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, FILE)


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _log(t, user, text):
    t.setdefault("log", []).append({"t": _now(), "u": user, "x": text})
    t["updated"] = _now()


def list_tasks(period=None, status=None):
    out = _load()
    if period:
        out = [t for t in out if period in t.get("periods", [])]
    if status:
        out = [t for t in out if t["status"] == status]
    return out


def sync(period, issues, owner, user="auto", latest=True):
    """Tạo/cập nhật task từ danh sách issue của `period`. Trả về {new, updated, recurred, stale}."""
    with LOCK:
        ts = _load()
        by_key = {}
        for t in ts:
            if t.get("key") and t["status"] in ("todo", "doing"):
                by_key[t["key"]] = t
        done_keys = {}
        for t in ts:
            if t.get("key") and t["status"] in ("done", "dismissed"):
                done_keys.setdefault(t["key"], set()).update(t.get("periods", []))
        res = {"new": 0, "updated": 0, "recurred": 0, "stale": 0}
        seen = set()
        for i in issues:
            seen.add(i["key"])
            t = by_key.get(i["key"])
            if t:                                                    # task đang mở -> làm mới số liệu, giữ phần người dùng đã nhập
                t.update(title=i["title"], where=i["where"], detail=i["detail"], fix=i["fix"], metric=i["metric"], sev=i["sev"], detected=True)
                if period not in t["periods"]:
                    t["periods"].append(period); t["last_period"] = period
                    _log(t, user, f"Vấn đề vẫn còn ở kỳ {period}")
                res["updated"] += 1
                continue
            if period in done_keys.get(i["key"], ()):                  # đã đóng/bỏ qua ngay trong kỳ này -> không mở lại
                continue
            due = (datetime.now() + timedelta(days=DUE_DAYS.get(i["sev"], 7))).date().isoformat()
            t = {"id": uuid.uuid4().hex[:10], "key": i["key"], "auto": True, "title": i["title"], "area": i["area"], "sev": i["sev"],
                 "where": i["where"], "detail": i["detail"], "fix": i["fix"], "metric": i["metric"], "status": "todo",
                 "owner": owner, "due": due, "note": "", "periods": [period], "first_period": period, "last_period": period,
                 "detected": True, "created": _now(), "updated": _now(), "log": []}
            if i["key"] in done_keys:  # đã từng đóng ở kỳ trước nhưng vấn đề xuất hiện lại
                t["recurred"] = True; res["recurred"] += 1
                _log(t, user, "Tái phát: task trước cùng vấn đề đã đóng")
            else:
                _log(t, user, f"Tự tạo từ phân tích kỳ {period}")
            ts.append(t); res["new"] += 1
        if latest:                                                    # task mở không còn được phát hiện -> gợi ý đóng
            for t in ts:
                if t.get("auto") and t["status"] in ("todo", "doing") and t["key"] not in seen:
                    if t.get("detected", True):
                        _log(t, user, f"Kỳ {period} không còn phát hiện vấn đề này — có thể đóng task")
                    t["detected"] = False; res["stale"] += 1
        _save(ts)
        return res


def update(tid, patch, user):
    with LOCK:
        ts = _load()
        t = next((x for x in ts if x["id"] == tid), None)
        if not t:
            raise ValueError("Không có task này")
        for k in ("status", "owner", "due", "note", "title"):
            if k in patch and patch[k] != t.get(k):
                v = str(patch[k])[:500]
                if k == "status" and v not in STATUS:
                    raise ValueError("Trạng thái không hợp lệ")
                _log(t, user, f"{k}: {t.get(k) or '—'} → {v or '—'}" if k != "note" else "Cập nhật ghi chú")
                t[k] = v
        _save(ts)
        return t


def add(title, owner, due, area, user, period=None):
    title = (title or "").strip()
    if not title:
        raise ValueError("Cần nhập tiêu đề task")
    with LOCK:
        ts = _load()
        t = {"id": uuid.uuid4().hex[:10], "key": None, "auto": False, "title": title[:300], "area": area or "Khác", "sev": 1, "where": "",
             "detail": [], "fix": [], "metric": {}, "status": "todo", "owner": owner, "due": due or "", "note": "",
             "periods": [period] if period else [], "first_period": period, "last_period": period, "detected": True,
             "created": _now(), "updated": _now(), "log": []}
        _log(t, user, "Tạo thủ công")
        ts.append(t); _save(ts)
        return t


def remove(tid):
    with LOCK:
        ts = _load()
        n = [t for t in ts if t["id"] != tid]
        if len(n) == len(ts):
            raise ValueError("Không có task này")
        _save(n)
