"""Quản lý nhiều MẪU REPORT (report template) để mẫu cũ không bao giờ bị mất.
 - Mẫu gốc 'base' = templates/report-template-base.html (có sẵn, không bao giờ bị sửa / xoá / lưu trữ).
 - Mẫu mới tải lên được lưu thành file riêng data/report_templates/<id>.html, KHÔNG ghi đè (mỗi lần tải lên là một mẫu mới).
 - Không có thao tác xoá: chỉ 'Lưu trữ' (ẩn khỏi danh sách chọn, vẫn giữ file và vẫn dùng được cho các kỳ đã gắn).
 - CÁCH LY VỚI MẪU GỐC: mẫu mới KHÔNG dùng chung mã có thể sửa. Mọi thứ riêng của mẫu mới nằm trong chính file mẫu, và nếu cần
   chỉnh gói giao diện Pro thì dùng bộ patch riêng patches/<tên>/ (trường "patches" trong sổ). Mẫu gốc luôn dùng patches/ như cũ,
   được canh bằng tests/test_base_frozen.py (băm kết quả render) và kiểm tra toàn vẹn file gốc (sha + bản sao lưu).
 - Mỗi kỳ ghi mẫu đang dùng trong meta.json ("template"); kỳ cũ chưa có trường này = mẫu gốc 'base'.
Sổ đăng ký: data/report_templates.json."""
import hashlib, json, os, re, threading
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
BUILTIN = BASE_DIR / "templates" / "report-template-base.html"
DIR = BASE_DIR / "data" / "report_templates"
REG = BASE_DIR / "data" / "report_templates.json"
LOCK = threading.RLock()
D_PREFIX = "const D = "
MAX_BYTES = 30 * 1024 * 1024


def _save(d):
    REG.parent.mkdir(parents=True, exist_ok=True)
    tmp = REG.with_suffix(".tmp"); tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8"); os.replace(tmp, REG)


def _sha(b):
    return hashlib.sha256(b).hexdigest()[:12]


def _reg():
    try:
        d = json.loads(REG.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        d = None
    if d is None or not any(i["id"] == "base" for i in d.get("items", [])):
        raw = BUILTIN.read_bytes() if BUILTIN.exists() else b""
        base = {"id": "base", "name": "Mẫu gốc", "note": "Mẫu report ban đầu của dự án (templates/report-template-base.html). Không sửa / xoá được.",
                "file": None, "builtin": True, "archived": False, "created": datetime.now().isoformat(timespec="seconds"),
                "by": "hệ thống", "sha": _sha(raw), "kb": len(raw) // 1024, "parent": None}
        d = d or {"default": "base", "items": []}
        d["items"].insert(0, base)
        d.setdefault("default", "base")
        _save(d)
    return d


def inspect(text):
    """Kiểm tra file có đúng dạng template của app: có đúng một dòng 'const D = {...};' mang JSON hợp lệ.
    Trả về dict D mẫu (seed)."""
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(D_PREFIX)]
    if not idx:
        raise ValueError("File không đúng dạng mẫu report: không thấy dòng bắt đầu bằng “const D = ” (dữ liệu mẫu). Hãy lấy từ mẫu gốc rồi chỉnh sửa.")
    if len(idx) > 1:
        raise ValueError("File có nhiều hơn một dòng “const D = ”")
    raw = lines[idx[0]][len(D_PREFIX):].rstrip().rstrip(";")
    try:
        seed = json.loads(raw)
    except ValueError as e:
        raise ValueError(f"Dòng “const D = ” không phải JSON hợp lệ ({e})")
    if not isinstance(seed, dict) or not seed:
        raise ValueError("Dữ liệu mẫu “const D” rỗng hoặc sai kiểu")
    return seed


def _base_keys():
    try:
        return set(inspect(BUILTIN.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _item(i, usage=None):
    out = {k: i.get(k) for k in ("id", "name", "note", "builtin", "archived", "created", "by", "kb", "sha", "parent", "missing", "extra", "patches")}
    out["builtin"] = bool(i.get("builtin")); out["archived"] = bool(i.get("archived"))
    out["used"] = (usage or {}).get(i["id"], 0)
    return out


def default_id():
    d = _reg(); did = d.get("default", "base")
    return did if any(i["id"] == did and not i.get("archived") for i in d["items"]) else "base"


def list_all(usage=None):
    d = _reg()
    ok, msg = verify_base()
    return {"default": default_id(), "base_ok": ok, "base_msg": msg, "items": [_item(i, usage) for i in d["items"]]}


def get(tid):
    for i in _reg()["items"]:
        if i["id"] == tid:
            return i
    return None


def exists(tid):
    return get(tid) is not None


def usable(tid):
    """Id có thể gán cho kỳ mới (có tồn tại và chưa lưu trữ)."""
    i = get(tid)
    return bool(i) and not i.get("archived")


def path(tid=None):
    """Đường dẫn file mẫu. Id lạ / file mất → rơi về mẫu gốc (để report luôn mở được)."""
    i = get(tid or "base")
    if i and i.get("file"):
        p = DIR / i["file"]
        if p.exists():
            return p
    return BUILTIN


PATCH_ROOT = BASE_DIR / "patches"
BACKUP = DIR / "_backup"


def patch_dir(tid=None):
    """Thư mục bộ patch của mẫu; None = bộ chung patches/ (mẫu gốc luôn None)."""
    i = get(tid or "base")
    name = (i or {}).get("patches")
    if not name or (i or {}).get("builtin"):
        return None
    pd = PATCH_ROOT / name
    return pd if pd.is_dir() else None


def verify_base():
    """Kiểm file mẫu gốc còn nguyên (so sha đã ghi khi đăng ký) và giữ một bản sao lưu bất biến.
    Trả (ok, thông báo)."""
    try:
        raw = BUILTIN.read_bytes()
    except OSError as e:
        return False, f"Không đọc được mẫu gốc: {e}"
    cur = _sha(raw)
    d = _reg()
    it = next(i for i in d["items"] if i["id"] == "base")
    try:
        BACKUP.mkdir(parents=True, exist_ok=True)
        bk = BACKUP / f"report-template-base.{it['sha']}.html"
        if not bk.exists() and cur == it["sha"]:
            with open(bk, "xb") as f:
                f.write(raw)
            try:
                os.chmod(bk, 0o444)
            except OSError:
                pass
        try:
            os.chmod(BUILTIN, 0o444)           # chỉ đọc: sửa tay phải chủ động chmod u+w
        except OSError:
            pass
    except OSError:
        bk = None
    if cur == it["sha"]:
        return True, "Mẫu gốc còn nguyên"
    msg = f"Mẫu gốc đã bị thay đổi (sha {cur}, ban đầu {it['sha']})."
    if bk and bk.exists():
        msg += f" Bản sao lưu nguyên vẹn: {bk.relative_to(BASE_DIR)}"
    return False, msg


def name_of(tid):
    i = get(tid or "base")
    return i["name"] if i else "Mẫu gốc"


def _slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower().encode("ascii", "ignore").decode()).strip("-")
    return s[:30] or "mau"


def add(name, note, raw, by, parent=None, patches=None):
    """Thêm mẫu mới từ nội dung file. Không bao giờ ghi đè."""
    name = (name or "").strip()
    if not name:
        raise ValueError("Cần đặt tên cho mẫu")
    if len(raw) > MAX_BYTES:
        raise ValueError("File quá lớn")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("File phải mã hoá UTF-8")
    seed = inspect(text)
    with LOCK:
        d = _reg()
        if any(i["name"].strip().lower() == name.lower() for i in d["items"]):
            raise ValueError("Đã có mẫu trùng tên — hãy đặt tên khác (ví dụ thêm số phiên bản)")
        sha = _sha(raw)
        dup = next((i for i in d["items"] if i["sha"] == sha and not i.get("archived")), None)
        if dup and parent is None:
            raise ValueError(f"File này giống hệt mẫu “{dup['name']}” — không cần thêm lại")
        base = _base_keys()
        keys = set(seed)
        tid = f"{_slug(name)}-{sha[:6]}"
        n = 1
        while any(i["id"] == tid for i in d["items"]) or (DIR / f"{tid}.html").exists():
            n += 1; tid = f"{_slug(name)}-{sha[:6]}-{n}"
        DIR.mkdir(parents=True, exist_ok=True)
        with open(DIR / f"{tid}.html", "xb") as f:               # 'x' = không bao giờ ghi đè
            f.write(raw)
        it = {"id": tid, "name": name, "note": (note or "").strip(), "file": f"{tid}.html", "builtin": False, "archived": False,
              "created": datetime.now().isoformat(timespec="seconds"), "by": by, "sha": sha, "kb": len(raw) // 1024, "parent": parent,
              "missing": sorted(base - keys) if base else [], "extra": sorted(keys - base) if base else [], "patches": patches}
        d["items"].append(it); _save(d)
        return _item(it)


def clone(tid, name, by):
    src = get(tid)
    if not src:
        raise ValueError("Không có mẫu này")
    raw = path(tid).read_bytes()
    return add(name, f"Nhân bản từ “{src['name']}”", raw, by, parent=tid)


def update(tid, by, name=None, note=None, archived=None, make_default=False):
    with LOCK:
        d = _reg()
        it = next((i for i in d["items"] if i["id"] == tid), None)
        if not it:
            raise ValueError("Không có mẫu này")
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Tên không được để trống")
            if it.get("builtin") and name != it["name"]:
                raise ValueError("Không đổi tên mẫu gốc")
            if any(i["id"] != tid and i["name"].strip().lower() == name.lower() for i in d["items"]):
                raise ValueError("Đã có mẫu trùng tên")
            it["name"] = name
        if note is not None and not it.get("builtin"):
            it["note"] = note.strip()
        if archived is not None:
            if archived and (it.get("builtin") or d.get("default") == tid):
                raise ValueError("Không lưu trữ được mẫu gốc hoặc mẫu đang là mặc định")
            it["archived"] = bool(archived)
        if make_default:
            if it.get("archived"):
                raise ValueError("Mẫu đã lưu trữ — hãy khôi phục trước khi đặt mặc định")
            d["default"] = tid
        _save(d)
        return _item(it)
