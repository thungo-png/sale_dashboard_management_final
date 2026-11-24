"""Phân quyền theo module (data/permissions.json). Mỗi người dùng có vai trò:
 - admin: toàn quyền, kể cả quản lý tài khoản và phân quyền.
 - report: chỉ xem report của các kỳ, không thấy module nào khác, không tạo / sửa kỳ.
 - custom: mỗi module một mức  none (ẩn) < view (xem) < edit (xem + thay đổi).
Kiểm tra ở server cho mọi API; giao diện chỉ ẩn nút theo quyền.
Tài khoản có sẵn trước khi có tính năng này được chuyển thành admin (để không ai bị khoá ngoài)."""
import json, os, threading
from pathlib import Path

FILE = Path(__file__).parent / "data" / "permissions.json"
LOCK = threading.Lock()
LEVELS = ["none", "view", "edit"]
RANK = {k: i for i, k in enumerate(LEVELS)}
MODULES = [
    ("home", "Hôm nay", "Việc hôm nay, cảnh báo, bản tin"),
    ("periods", "Kỳ báo cáo", "Xem report; upload file, build, xoá kỳ (mức Sửa)"),
    ("analysis", "Phân tích & Task", "Vấn đề phát hiện, task, ghi chú sự kiện"),
    ("compare", "So sánh hai kỳ", "So sánh doanh thu, lợi nhuận giữa các kỳ"),
    ("inputs", "Dữ liệu đầu vào", "Giá vốn, lead time, điểm đặt hàng, mục tiêu"),
    ("adsopt", "Tối ưu quảng cáo", "Từ khoá, đề xuất bid, ranking; Sửa = lưu cài đặt, upload template, xuất bulk"),
    ("config", "Cấu hình", "Cấu hình ETL dùng chung"),
]
KEYS = [m[0] for m in MODULES]
PRESETS = {
    "viewer": ("Chỉ xem", {k: ("view" if k != "config" else "none") for k in KEYS}),
    "ops": ("Vận hành", {**{k: "edit" for k in KEYS}, "config": "none"}),
    "ads": ("Chuyên viên quảng cáo", {**{k: "view" for k in KEYS}, "adsopt": "edit", "config": "none", "inputs": "none", "compare": "none"}),
}


def _load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def _save(d):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp"); tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8"); os.replace(tmp, FILE)


def _db():
    """Lần đầu: mọi tài khoản hiện có thành admin."""
    d = _load()
    if d is None:
        import auth
        d = {"users": {u: {"role": "admin", "mods": {}} for u in auth.list_users()}}
        _save(d)
    return d


def get(user):
    u = _db()["users"].get(user)
    if u is None:                                    # tài khoản tạo ngoài app (manage_users.py): mặc định chỉ xem
        return {"role": "custom", "mods": dict(PRESETS["viewer"][1])}
    if u["role"] == "admin":
        return {"role": "admin", "mods": {k: "edit" for k in KEYS}}
    if u["role"] == "report":                        # chỉ xem report: không thấy module nào khác, không tạo / sửa kỳ
        return {"role": "report", "mods": {k: ("view" if k == "periods" else "none") for k in KEYS}}
    return {"role": "custom", "mods": {k: u["mods"].get(k, "none") for k in KEYS}}


def is_admin(user):
    return get(user)["role"] == "admin"


def allowed(user, module, level):
    if module == "admin":
        return is_admin(user)
    return RANK[get(user)["mods"].get(module, "none")] >= RANK[level]


def all_users():
    import auth
    return {u: get(u) for u in auth.list_users()}


def set_user(name, role, mods, me):
    if role not in ("admin", "custom", "report"):
        raise ValueError("Vai trò không hợp lệ")
    with LOCK:
        d = _db()
        import auth
        if name not in auth.list_users():
            raise ValueError("Không có tài khoản này")
        clean = {}
        for k, v in (mods or {}).items():
            if k not in KEYS or v not in LEVELS:
                raise ValueError(f"Quyền không hợp lệ: {k}={v}")
            clean[k] = v
        if name == me and role != "admin":
            raise ValueError("Không thể tự bỏ quyền quản trị của chính mình")
        admins = [u for u in auth.list_users() if (d["users"].get(u, {}).get("role") == "admin")]
        if role != "admin" and admins == [name]:
            raise ValueError("Phải còn ít nhất một tài khoản quản trị")
        d["users"][name] = {"role": role, "mods": clean if role == "custom" else {}}
        _save(d)


def add_default(name, preset="viewer"):
    with LOCK:
        d = _db()
        d["users"][name] = {"role": "custom", "mods": dict(PRESETS[preset][1])}
        _save(d)


def remove(name):
    with LOCK:
        d = _db(); d["users"].pop(name, None); _save(d)


def required(method, parts):
    """(module, level) cần có cho request; None = chỉ cần đăng nhập."""
    if not parts:
        return None
    if parts[0] == "report":
        return ("periods", "view")
    if parts[0] != "api" or len(parts) < 2:
        return None
    a, p = parts[1], parts[2:]
    rd = method == "GET"
    if a in ("cockpit", "digest"):
        return ("home", "view")
    if a == "compare":
        return ("compare", "view")
    if a in ("notes", "tasks"):
        return ("analysis", "view" if rd else "edit")
    if a == "inputs":
        return ("inputs", "view" if rd else "edit")
    if a == "adsopt":
        return ("adsopt", "edit" if (not rd or (p and p[0] in ("export", "template"))) else "view")
    if a == "cleanup":
        return ("config", "view" if rd else "edit")
    if a == "config":
        return ("config", "view" if rd else "edit")
    if a == "rtemplates":                           # xem danh sách / xem thử: ai xem được report; thêm, nhân bản, đổi tên, lưu trữ, đặt mặc định: quản trị
        return ("periods", "view") if (rd and "download" not in p) else ("admin", "edit")
    if a == "notify":
        return ("periods", "edit") if p in (["send"], ["preview"]) else ("admin", "edit")
    if a == "perms":
        return ("admin", "edit")
    if a == "users":
        return None if (rd and not p) else ("admin", "edit")
    if a == "periods":
        if not p:
            return None if rd else ("periods", "edit")
        if len(p) >= 2 and p[1] == "analysis":
            return ("analysis", "view")
        if len(p) >= 2 and p[1] == "analyze":
            return ("analysis", "edit")
        if len(p) >= 2 and p[1] in ("log", "data"):      # log build và data.json thô: chỉ người có quyền Sửa kỳ
            return ("periods", "edit")
        return ("periods", "view" if rd else "edit")
    return None
