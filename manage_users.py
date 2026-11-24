"""Quản lý tài khoản đăng nhập (đồng bộ với phân quyền theo module trong data/permissions.json).
   python3 manage_users.py add <tên> [admin|report|viewer|ops|ads]   # tạo tài khoản hoặc đổi mật khẩu; mặc định: admin
   python3 manage_users.py role <tên> admin|report|viewer|ops|ads    # đổi vai trò
   python3 manage_users.py list
   python3 manage_users.py remove <tên>
 admin = toàn quyền · report = chỉ xem report · viewer/ops/ads = bộ quyền theo module có sẵn (xem perms.PRESETS)
"""
import getpass, sys
import auth, perms

ROLES = ("admin", "report") + tuple(perms.PRESETS)

def apply_role(name, role):
    name = name.strip().lower()
    if role not in ROLES:
        raise ValueError("Vai trò phải là: " + ", ".join(ROLES))
    if role in perms.PRESETS:
        perms.set_user(name, "custom", perms.PRESETS[role][1], "")
    else:
        perms.set_user(name, role, {}, "")

def main(a):
    if len(a) == 3 and a[0] == "role":
        apply_role(a[1], a[2]); print("Đã đặt vai trò", a[1].lower(), "=", a[2])
    elif len(a) >= 1 and a[0] in ("add", "passwd") and len(a) in (2, 3):
        role = a[2] if len(a) == 3 else None
        if role and role not in ROLES:
            sys.exit("Vai trò phải là: " + ", ".join(ROLES))
        existed = a[1].strip().lower() in auth.list_users()
        p1 = getpass.getpass("Mật khẩu (≥10 ký tự, đủ 3/4 loại ký tự hoặc cụm từ ≥16 ký tự): "); p2 = getpass.getpass("Nhập lại: ")
        if p1 != p2:
            sys.exit("Hai lần nhập không khớp")
        auth.set_password(a[1], p1)
        if role or not existed:                      # tài khoản mới: mặc định admin; tài khoản cũ đổi mật khẩu: giữ nguyên vai trò
            apply_role(a[1], role or "admin")
        print("Đã lưu tài khoản", a[1].lower())
    elif a[:1] == ["list"]:
        us = auth.list_users()
        print(*([f"{u}  [{perms.get(u)['role']}]" for u in us] or ["(chưa có tài khoản)"]), sep="\n")
    elif len(a) == 2 and a[0] == "remove":
        auth.remove_user(a[1]); perms.remove(a[1].strip().lower()); print("Đã xoá", a[1].lower())
    else:
        print(__doc__)

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except ValueError as e:
        sys.exit(str(e))
