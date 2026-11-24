"""Kiểm tra độ mạnh mật khẩu (chỉ thư viện chuẩn). Dùng ở auth.set_password và API /api/auth/strength.
Chính sách: ≥10 ký tự (≤128); không chứa tên đăng nhập; không nằm trong danh sách mật khẩu phổ biến;
không lặp/tuần tự; đủ 3/4 loại ký tự (thường, HOA, số, ký hiệu) — hoặc dài ≥16 ký tự (cụm từ) thì không cần."""
import math, re

MIN_LEN, MAX_LEN, PASSPHRASE_LEN = 10, 128, 16
COMMON = set("""password passw0rd p@ssword p@ssw0rd password1 password12 password123 password1234 123456 1234567 12345678 123456789 1234567890
12345 111111 000000 123123 654321 666666 121212 112233 abc123 abcd1234 qwerty qwerty1 qwerty12 qwerty123 qwertyuiop qwertyui asdfgh asdfghjkl
zxcvbnm 1q2w3e4r 1q2w3e 1qaz2wsx qazwsx zaq12wsx iloveyou letmein welcome welcome1 welcome123 admin admin123 administrator root toor
login master monkey dragon sunshine princess football baseball superman batman shadow michael jessica ashley charlie trustno1 changeme
default guest test test123 testing secret passpass hello hello123 freedom whatever starwars access mustang abc12345 internet google
amazon wayfair shopify walmart acacia arozu megsu sale sales report saleReport salereport thungo thu_ngo thungo123 hmd avori
matkhau matkhau123 123456a 123456aa a123456 a123456789 vietnam vietnam123 admin@123 admin@1234 pass1234 summer2024 winter2024
spring2025 autumn2025 summer2025 winter2025 summer2026 winter2026 spring2026 autumn2026 company company1 company123 letmein123""".split())
LEET = {"@": "a", "4": "a", "$": "s", "5": "s", "0": "o", "1": "l", "!": "i", "3": "e", "7": "t", "|": "l"}
BAD_WORDS = ("password", "passw0rd", "qwerty", "admin", "salereport", "thungo", "wayfair", "amazon", "acacia", "arozu", "megsu", "matkhau", "iloveyou", "letmein")
ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890", "abcdefghijklmnopqrstuvwxyz"]


def _norm(p):
    return "".join(LEET.get(c, c) for c in p.lower())


def _strip_tail(p):
    return re.sub(r"[\d\W_]+$", "", p)


def _sequential(p):
    s = p.lower()
    for row in ROWS:
        for seq in (row, row[::-1]):
            for i in range(len(seq) - 5):
                if seq[i:i + 6] in s:
                    return True
    return False


def _classes(p):
    return sum(bool(re.search(x, p)) for x in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]"))


def _entropy(p):
    pool = (26 if re.search(r"[a-z]", p) else 0) + (26 if re.search(r"[A-Z]", p) else 0) + (10 if re.search(r"\d", p) else 0) + (33 if re.search(r"[^A-Za-z0-9]", p) else 0)
    uniq = len(set(p))
    return len(p) * math.log2(pool or 1) * min(1.0, uniq / max(8, len(p) * 0.6))


def check(pw, username=""):
    """Trả về {ok, score(0-4), label, problems[]}. `problems` rỗng thì ok=True."""
    pw = pw or ""
    probs = []
    if len(pw) < MIN_LEN:
        probs.append(f"Cần ít nhất {MIN_LEN} ký tự (hiện {len(pw)})")
    if len(pw) > MAX_LEN:
        probs.append(f"Tối đa {MAX_LEN} ký tự")
    u = (username or "").strip().lower()
    for part in {u, u.split("@")[0]}:
        if len(part) >= 3 and part in pw.lower():
            probs.append("Không được chứa tên đăng nhập"); break
    n = _norm(pw)
    if pw.lower() in COMMON or n in COMMON or _strip_tail(pw.lower()) in COMMON or _strip_tail(n) in COMMON:
        probs.append("Mật khẩu quá phổ biến, dễ bị đoán")
    flat = re.sub(r"[^a-z0-9]", "", n)
    if not any("phổ biến" in x for x in probs) and any(w in flat or w in re.sub(r"[^a-z0-9]", "", pw.lower()) for w in BAD_WORDS):
        probs.append("Chứa từ dễ đoán (password, admin, tên sàn/sản phẩm…)")
    if pw and len(set(pw)) <= max(2, len(pw) // 5):
        probs.append("Có quá nhiều ký tự lặp lại")
    elif _sequential(pw) and len(pw) < PASSPHRASE_LEN:
        probs.append("Có chuỗi tuần tự dễ đoán (123456, qwerty, abcdef…)")
    if len(pw) >= MIN_LEN and len(pw) < PASSPHRASE_LEN and _classes(pw) < 3:
        probs.append("Cần kết hợp ít nhất 3 trong 4 loại: chữ thường, CHỮ HOA, số, ký hiệu — hoặc dùng cụm từ dài từ 16 ký tự")
    e = _entropy(pw)
    score = 0 if probs and len(pw) < MIN_LEN else 1 if probs else (2 if e < 55 else 3 if e < 75 else 4)
    return {"ok": not probs, "score": score, "label": ["Rất yếu", "Yếu", "Đạt", "Tốt", "Rất mạnh"][score],
            "problems": probs, "bits": round(e)}


def require(pw, username=""):
    r = check(pw, username)
    if not r["ok"]:
        raise ValueError("Mật khẩu chưa đạt: " + "; ".join(r["problems"]))
