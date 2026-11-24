"""Dùng chung cho freeze_base.py và test_base_frozen.py: dựng report của MẪU GỐC từ chính dữ liệu mẫu nằm trong template,
với các đầu vào cố định (không phụ thuộc task, ghi chú, giá vốn, ngày hôm nay) để kết quả luôn xác định."""
import hashlib, json, os, sys
from pathlib import Path

if os.environ.get("PYTHONHASHSEED") != "0":      # insights.py duyệt set nên thứ tự phụ thuộc hash ngẫu nhiên của Python -> cố định để băm ổn định
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
GOLDEN = Path(__file__).resolve().parent / "golden_base.json"
D_PREFIX = "const D = "


def sha(b):
    return hashlib.sha256(b).hexdigest()


def legacy_render(d, patches, extras, template_path, patch_dir):
    """Bản sao NGUYÊN VĂN logic render gốc (trước khi có nhiều mẫu) — chuẩn để đối chiếu."""
    lines = Path(template_path).read_text(encoding="utf-8").split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith(D_PREFIX))
    lines[i] = D_PREFIX + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";"
    html = "\n".join(lines)
    if "name=\"viewport\"" not in html:
        html = '<meta name="viewport" content="width=device-width,initial-scale=1">\n' + html
    for name in (patches or []):
        css_f, js_f = Path(patch_dir) / f"{name}.css.html", Path(patch_dir) / f"{name}.js"
        if "/* ---- Bo loc gon (fbar)" in html and name == "fbar":
            continue
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


def inputs():
    import builder, insights
    seed = builder.seed_data(builder.TEMPLATE)
    ex = insights.build(seed, {"open": 0, "late": 0}, None)
    ex["generated"] = "FROZEN"                       # insights ghi ngày hôm nay; cố định để so sánh
    ex["sku_class"] = insights.sku_class(seed)
    ex["notes"] = []; ex["periods"] = None; ex["reorder"] = {}
    return seed, ex
