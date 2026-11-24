"""Đăng nhập cho Sale Report Manager — chỉ dùng thư viện chuẩn.
 - Tài khoản lưu ở data/users.json (mật khẩu băm PBKDF2-SHA256, 240k vòng, salt riêng).
 - Phiên đăng nhập = cookie ký HMAC (khoá ở data/secret.key), HttpOnly + SameSite=Lax, hết hạn sau SESSION_HOURS.
 - Chống dò mật khẩu: sai 5 lần liên tiếp từ cùng 1 IP thì khoá 5 phút.
"""
import pwcheck
import base64, hashlib, hmac, json, os, secrets, time
from pathlib import Path

DATA = Path(__file__).parent / "data"
USERS = DATA / "users.json"
SECRET = DATA / "secret.key"
ITER = 240_000
SESSION_HOURS = 12
COOKIE = "srm_session"
MAX_FAIL, LOCK_SEC = 5, 300
_fails = {}   # ip -> (số lần, thời điểm hết khoá)


def _load():
    try:
        return json.loads(USERS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _save(u):
    DATA.mkdir(parents=True, exist_ok=True)
    USERS.write_text(json.dumps(u, indent=1), encoding="utf-8")
    try:
        os.chmod(USERS, 0o600)
    except OSError:
        pass


def _hash(pw, salt, it=ITER):
    return base64.b64encode(hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, it)).decode()


def has_users():
    return bool(_load())


def list_users():
    return sorted(_load())


ROLES = {"admin": "Quản trị (đầy đủ quyền)", "viewer": "Chỉ xem report"}


def get_role(name):
    """Tài khoản cũ chưa có trường role = admin (giữ nguyên quyền như trước)."""
    return (_load().get((name or "").strip().lower()) or {}).get("role", "admin")


def list_users_full():
    return [{"name": k, "role": v.get("role", "admin")} for k, v in sorted(_load().items())]


def _n_admin(u, skip=None):
    return sum(1 for k, v in u.items() if k != skip and v.get("role", "admin") == "admin")


def set_role(name, role):
    name = name.strip().lower(); u = _load()
    if name not in u:
        raise ValueError("Không có tài khoản này")
    if role not in ROLES:
        raise ValueError("Quyền không hợp lệ")
    if role != "admin" and u[name].get("role", "admin") == "admin" and _n_admin(u, name) == 0:
        raise ValueError("Phải còn ít nhất một tài khoản quản trị")
    u[name]["role"] = role; _save(u)


def set_password(name, pw, role=None):
    name = name.strip().lower()
    if not name or len(name) > 40 or not all(c.isalnum() or c in "._-@" for c in name):
        raise ValueError("Tên đăng nhập chỉ gồm chữ, số, . _ - @")
    pwcheck.require(pw, name)
    salt = secrets.token_bytes(16)
    u = _load()
    if role is not None and role not in ROLES:
        raise ValueError("Quyền không hợp lệ")
    keep = (u.get(name) or {}).get("role")          # đổi mật khẩu không đổi quyền; tài khoản mới mặc định admin
    u[name] = {"salt": base64.b64encode(salt).decode(), "iter": ITER, "hash": _hash(pw, salt), "role": role or keep or "admin"}
    _save(u)


def remove_user(name):
    u = _load()
    if name.strip().lower() not in u:
        raise ValueError("Không có tài khoản này")
    k = name.strip().lower()
    if u[k].get("role", "admin") == "admin" and _n_admin(u, k) == 0:
        raise ValueError("Phải còn ít nhất một tài khoản quản trị")
    del u[k]; _save(u)


def check(name, pw):
    u = _load().get((name or "").strip().lower())
    salt = base64.b64decode(u["salt"]) if u else b"x" * 16          # vẫn băm khi sai tên để thời gian phản hồi như nhau
    h = _hash(pw or "", salt, u["iter"] if u else ITER)
    return bool(u) and hmac.compare_digest(h, u["hash"])


def _key():
    if not SECRET.exists():
        DATA.mkdir(parents=True, exist_ok=True)
        SECRET.write_bytes(secrets.token_bytes(32))
        try:
            os.chmod(SECRET, 0o600)
        except OSError:
            pass
    return SECRET.read_bytes()


def make_token(name):
    body = base64.urlsafe_b64encode(json.dumps({"u": name.strip().lower(), "e": int(time.time()) + SESSION_HOURS * 3600}).encode()).decode()
    sig = hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_token(tok):
    """Trả tên người dùng nếu cookie hợp lệ, chưa hết hạn và tài khoản còn tồn tại."""
    try:
        body, sig = (tok or "").rsplit(".", 1)
        if not hmac.compare_digest(sig, hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()):
            return None
        d = json.loads(base64.urlsafe_b64decode(body))
        return d["u"] if d["e"] > time.time() and d["u"] in _load() else None
    except Exception:
        return None


def locked(ip):
    n, until = _fails.get(ip, (0, 0))
    return n >= MAX_FAIL and until > time.time()


def note_fail(ip):
    n, until = _fails.get(ip, (0, 0))
    n = 1 if until and until < time.time() and n < MAX_FAIL else n + 1
    _fails[ip] = (n, time.time() + LOCK_SEC)


def note_ok(ip):
    _fails.pop(ip, None)
