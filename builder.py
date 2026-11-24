"""Chèn JSON vào template, áp patch tuỳ chọn, kiểm tra schema."""
import json, re
from pathlib import Path

BASE = Path(__file__).parent
TEMPLATE = BASE / "templates" / "report-template-base.html"
PATCHES = BASE / "patches"
D_PREFIX = "const D = "


def read_template_lines(path=None):
    return Path(path or TEMPLATE).read_text(encoding="utf-8").split("\n")


def find_d_line(lines):
    return next(i for i, l in enumerate(lines) if l.startswith(D_PREFIX))


def seed_data(path=None):
    """Lấy dict D mẫu đang nằm trong template (path = mẫu được chọn cho kỳ; mặc định mẫu gốc)."""
    lines = read_template_lines(path)
    raw = lines[find_d_line(lines)][len(D_PREFIX):].rstrip().rstrip(";")
    return json.loads(raw)


def schema_check(d, seed):
    """So top-level key với template. Trả (missing, extra)."""
    return sorted(set(seed) - set(d)), sorted(set(d) - set(seed))


def render(d, patches=None, extras=None, path=None, patch_dir=None):
    """Trả HTML hoàn chỉnh: template + D mới + patch (nếu bật)."""
    lines = read_template_lines(path)
    i = find_d_line(lines)
    lines[i] = D_PREFIX + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";"
    html = "\n".join(lines)
    if "name=\"viewport\"" not in html:      # template là mảnh HTML không có <head>: thêm viewport để điện thoại dùng đúng @media của report
        html = '<meta name="viewport" content="width=device-width,initial-scale=1">\n' + html

    pdir = Path(patch_dir) if patch_dir else PATCHES          # mẫu mới có thể dùng bộ patch riêng; mẫu gốc luôn dùng patches/ như cũ
    for name in (patches or []):
        css_f, js_f = pdir / f"{name}.css.html", pdir / f"{name}.js"
        if "/* ---- Bo loc gon (fbar)" in html and name == "fbar":
            continue  # template đã có sẵn patch này
        if name == "pro" and extras is not None:
            blob = json.dumps(extras, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
            html = html.replace('<div class="wrap"><div class="mast">', "<script>window.__PRO=" + blob + ";</script>\n" + '<div class="wrap"><div class="mast">', 1)
        if css_f.exists():
            anchor = '<div class="wrap"><div class="mast">'
            html = html.replace(anchor, css_f.read_text(encoding="utf-8") + "\n" + anchor, 1)
        if js_f.exists():
            k = html.rfind("</script>")
            html = html[:k] + "\n" + js_f.read_text(encoding="utf-8") + "\n" + html[k:]
    return html
