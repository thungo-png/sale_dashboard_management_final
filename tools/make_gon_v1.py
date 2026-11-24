#!/usr/bin/env python3
"""Tạo mẫu report "Gọn v1" từ mẫu gốc (report-template-base.html) — KHÔNG sửa dữ liệu `const D`, KHÔNG xoá phần tử nào
(mọi id mà JS của mẫu dùng vẫn còn) nên ETL và các key dữ liệu giữ nguyên. Chỉ thay đổi bố cục:
  1. Tổng quan: KPI -> việc cần làm -> diễn biến -> FC; bảng chi tiết thu gọn; Quảng cáo/Tồn kho toàn danh mục chỉ giữ KPI.
  2. Gom giải pháp lên đầu từng tab, lối tắt từ Tổng quan.
  3. Gộp tab: Listing & Giá (= Giá & Buy Box + Listing & Rating), Quảng cáo (= Chiến dịch + TACoS + Thứ hạng + Thị phần tìm kiếm + Độ phủ listing).
  4. Mục ít dùng / chưa có dữ liệu / giả lập: thu gọn mặc định.
  5. Bảng dài chỉ hiện 10 dòng đầu + nút "Xem tất cả".
Dùng:  python3 make_gon_v1.py <mẫu gốc> <file ra>"""
import re, sys

SRC, DST = sys.argv[1], sys.argv[2]
text = open(SRC, encoding="utf-8").read()
lines = text.split("\n")


def once(s, old, new, label=""):
    n = s.count(old)
    assert n == 1, f"[{label or old[:50]}] cần đúng 1 vị trí, tìm thấy {n}"
    return s.replace(old, new, 1)


# ---------- 1. tách head / panels / tail ----------
p0 = next(i for i, l in enumerate(lines) if l.startswith('<div class="panel on" id="p-ov"'))
f0 = next(i for i, l in enumerate(lines) if l.startswith('<footer id="foot">'))
head, body, tail = "\n".join(lines[:p0]), "\n".join(lines[p0:f0]), "\n".join(lines[f0:])
# body = các panel liên tiếp; đóng bằng '</div>' của .wrap? (</div> cuối nằm trong tail: '<footer' ... ) -> kiểm
parts = re.split(r'(?m)^(?=<div class="panel)', body)
parts = [p for p in parts if p.strip()]
PANELS = {}
for p in parts:
    pid = re.match(r'<div class="panel[^"]*" id="p-(\w+)"', p).group(1)
    PANELS[pid] = p
assert list(PANELS) == ["ov", "gr", "dt", "cp", "inv", "bb", "lr", "mc", "tt"], list(PANELS)

SEC_RE = re.compile(r"<section([^>]*)>(.*?)</section>", re.S)


class Sec:
    def __init__(self, attrs, inner):
        self.attrs, self.inner = attrs, inner
        self.lvl = None
        m = re.search(r'\s*<span class="lvl (ceo|ops)">(.*?)</span>', inner, re.S)
        if m:
            self.lvl = (m.group(1), m.group(2)); self.inner = inner.replace(m.group(0), "", 1)
        m = re.search(r'<h2>(.*?)</h2>', self.inner, re.S)
        self.title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""

    def shead(self):
        m = re.search(r'<div class="shead">.*?</div>', self.inner, re.S)
        return m.group(0) if m else ""

    def rest(self):
        return self.inner.replace(self.shead(), "", 1) if self.shead() else self.inner


def parse(pid):
    p = PANELS[pid]
    secs = [Sec(a, i) for a, i in SEC_RE.findall(p)]
    assert p.count("<section") == len(secs), pid
    leftover = SEC_RE.sub("", p)
    leftover = re.sub(r'<div class="panel[^>]*>', "", leftover, count=1)
    leftover = re.sub(r"</div>\s*$", "", leftover.strip())
    assert not leftover.strip(), f"{pid}: còn nội dung ngoài section: {leftover.strip()[:120]}"
    return secs


S = {pid: parse(pid) for pid in PANELS}


def find(pid, prefix):
    r = [s for s in S[pid] if s.title.startswith(prefix)]
    assert len(r) == 1, f"{pid}/{prefix}: {len(r)} kết quả"
    return r[0]


# ---------- 2. helper dựng khối ----------
def _fid(fid):
    return ' id="%s"' % fid if fid else ""


def fold(sec, open_=False, fid=None):
    """Section -> <details class=fold>; shead nằm trong summary (giữ nguyên id của hint)."""
    return ('<section><details class="fold"' + (" open" if open_ else "") + _fid(fid) + '>'
            '<summary>' + sec.shead() + '</summary>'
            '<div class="foldbody">' + sec.rest() + '</div></details></section>')


def plain(sec):
    return f"<section>{sec.inner}</section>"


def bundle(title, hint, secs, open_=False, fid=None):
    inner = ""
    for s in secs:
        x = re.sub(r'<span class="snum">[^<]*</span>', "", s.inner)
        inner += '<div class="bsec">' + x + '</div>'
    return ('<section><details class="fold"' + (" open" if open_ else "") + _fid(fid) + '>'
            '<summary><div class="shead"><span class="snum">+</span><h2>' + title + '</h2><span class="hint">' + hint + '</span></div></summary>'
            '<div class="foldbody">' + inner + '</div></details></section>')


def table_fold(sec, label, marker='<div class="scroll"', jump=None):
    """Giữ phần đầu (KPI) của section, gấp từ bảng trở xuống vào <details class=fold sub>."""
    r = sec.rest()
    i = r.index(marker)
    j = ""
    if jump:
        key, txt = jump
        j = f'<div class="jumps"><button class="pick" onclick="goTab(\'{key}\')">{txt}</button></div>'
    return (f'<section>{sec.shead()}{r[:i]}{j}<details class="fold sub"><summary>{label}</summary>'
            f'<div class="foldbody">{r[i:]}</div></details></section>')


def panel(pid, items, lvl, first_margin=False):
    m = re.match(r'(<div class="panel[^>]*>)', PANELS[pid]).group(1)
    L = '<div class="plvl"><span class="lvl ' + lvl[0] + '">' + lvl[1] + '</span></div>' if lvl else ""
    out = m + "\n" + L + "\n" + "\n\n".join(items) + "\n</div>\n"
    n = [0]

    def rn(mm):                                   # đánh số lại các mục (bỏ qua 00)
        if mm.group(1) == "00":
            return mm.group(0)
        n[0] += 1
        return '<span class="snum">%02d</span>' % n[0]
    return re.sub(r'<span class="snum">(\d+)</span>', rn, out)


CEO = ("ceo", "Báo cáo cấp CEO")
OPS = ("ops", "Báo cáo vận hành")

# ---------- 3. TỔNG QUAN ----------
ov = S["ov"]
howto = ov[0]
kpi = find("ov", "Tóm tắt điều hành")
alerts = find("ov", "Điểm cần xử lý")
alerts_html = ("<section><details class=\"fold\" open id=\"alerts-fold\"><summary>"
               + alerts.shead().replace("Điểm cần xử lý", "Việc cần làm theo số liệu") + "</summary><div class=\"foldbody\">"
               + alerts.rest()
               + '<div class="jumps"><span>Giải pháp chi tiết:</span> '
                 '<button class="pick" onclick="goTab(\'gr\',\'grsol\')">Nhóm sản phẩm</button> '
                 '<button class="pick" onclick="goTab(\'dt\',\'dtsol1\')">SKU</button> '
                 '<button class="pick" onclick="goTab(\'cp\',\'adsol\')">Quảng cáo</button></div>'
               + "</div></details></section>")
matrix = find("ov", "Ma trận")
trend = find("ov", "Diễn biến theo thời gian")
wfc = find("ov", "Theo dõi FC")
share = find("ov", "Cơ cấu doanh thu")
kpitbl = find("ov", "Bảng KPI")
ads = find("ov", "Quảng cáo toàn danh mục")
inv = find("ov", "Tồn kho toàn danh mục")
ov_items = [
    plain(howto), plain(kpi), '<div id="pro-slot"></div>', alerts_html,
    plain(matrix), plain(trend), plain(wfc),
    bundle("Cơ cấu và bảng KPI theo sàn · thị trường · nhóm", "doanh thu chia theo ba chiều, bảng KPI chi tiết", [share, kpitbl]),
    table_fold(ads, "Xem bảng theo sàn × thị trường", jump=("cp", "Mở tab Quảng cáo →")),
    table_fold(inv, "Xem bảng tồn theo sàn × thị trường", jump=("inv", "Mở tab Tồn kho →")),
]

# ---------- 4. NHÓM SẢN PHẨM ----------
gr_read = find("cp", "Đọc số")           # chuyển từ tab Chiến dịch: kết luận theo nhóm đặt lên đầu tab Nhóm
gr_over = find("gr", "Tổng quan các nhóm")
gr_trend = find("gr", "Diễn biến theo thời gian")
gr_break = find("gr", "Phân rã từng nhóm")
gr_cmp = find("gr", "So với các kỳ trước")
gr_top = find("gr", "Top sản phẩm")
gr_tacos = find("gr", "Chi phí quảng cáo")
gr_inv = find("gr", "Cơ cấu tồn")
gr_items = [plain(gr_read), plain(gr_over), plain(gr_top), plain(gr_trend), fold(gr_break), fold(gr_cmp), fold(gr_inv)]

# ---------- 5. SKU & P&L ----------
dt_filter = find("dt", "Chọn sàn và quốc gia")
dt_mock = find("dt", "Sản phẩm bán không đạt")
dt_trend = find("dt", "Diễn biến theo thời gian của từng SKU")
dt_break = find("dt", "Phân rã doanh thu")
dt_pl = find("dt", "P&amp;L PL5")
m = re.search(r'\s*<div class="sol"><h3>Giải pháp cho phần phân rã</h3>.*?</div>', dt_break.inner, re.S)
assert m
dt_sol = m.group(0)
dt_break.inner = dt_break.inner.replace(dt_sol, "", 1)
dt_sol_sec = ('<section><div class="shead"><span class="snum">+</span><h2>Việc nên làm với SKU</h2>'
              '<span class="hint">kết luận trước, bảng bên dưới</span></div>' + dt_sol + "</section>")
dt_mock.inner = dt_mock.inner.replace("</h2>", " · số liệu giả lập</h2>", 1) if "MOCK" in dt_mock.inner else dt_mock.inner
dt_items = [plain(dt_filter), dt_sol_sec, plain(dt_break), plain(dt_pl), fold(dt_trend), fold(dt_mock)]

# ---------- 6. QUẢNG CÁO ----------
cp_det = find("cp", "Chi tiết chiến dịch")
cp_todo = find("cp", "Điểm cần xử lý về quảng cáo")
mc_rank = find("mc", "Thứ hạng ngành hàng")
mc_st = find("mc", "Vị thế trên tìm kiếm")
mc_comp = find("mc", "Đối thủ")
lr_list = find("lr", "Listing &amp; Rating")
lr_cov = find("lr", "Độ phủ listing")
cp_items = [plain(cp_todo), plain(gr_tacos), plain(cp_det), plain(lr_cov), fold(mc_rank), fold(mc_st)]

# ---------- 7. TỒN KHO ----------
iv = S["inv"]
iv_kpi, iv_det, iv_sku, iv_lt, iv_acc, iv_note = iv
inv_items = [plain(iv_kpi), plain(iv_sku), plain(iv_lt), fold(iv_det), fold(iv_acc), fold(iv_note)]

# ---------- 8. LISTING & GIÁ ----------
bb_asp = find("bb", "Giá bán bình quân")
bb_size = find("bb", "Phân rã theo size")
bb_box = find("bb", "Buy Box")
bb_items = [plain(bb_asp), fold(bb_size),
            bundle("Đang chờ dữ liệu nguồn", "Buy Box · Listing &amp; Rating · Đối thủ — chưa có số, mở ra để xem cần file gì",
                   [bb_box, lr_list, mc_comp])]

# ---------- 9. TASK ----------
tt_items = [plain(S["tt"][0])]

new_panels = "\n".join([
    panel("ov", ov_items, CEO), panel("gr", gr_items, CEO),
    panel("dt", dt_items, OPS, True), panel("cp", cp_items, OPS, True), panel("inv", inv_items, OPS, True),
    panel("bb", bb_items, OPS, True), panel("tt", tt_items, OPS, True),
])

# ---------- 10. thanh tab ----------
head = once(head, '<button class="tab" role="tab" aria-selected="false" data-p="dt">Hiệu quả theo SKU</button>',
            '<button class="tab" role="tab" aria-selected="false" data-p="dt">SKU &amp; P&amp;L</button>', "tab dt")
head = once(head, 'data-p="cp">Chiến dịch &amp; giải pháp</button>', 'data-p="cp">Quảng cáo</button>', "tab cp")
head = once(head, 'data-p="inv">Tồn kho chi tiết</button>', 'data-p="inv">Tồn kho</button>', "tab inv")
head = once(head, 'data-p="bb">Giá &amp; Buy Box</button>', 'data-p="bb">Listing &amp; Giá</button>', "tab bb")
head = once(head, '  <button class="tab" role="tab" aria-selected="false" data-p="lr">Listing &amp; Rating</button>\n', "", "tab lr")
head = once(head, '  <button class="tab" role="tab" aria-selected="false" data-p="mc">Market &amp; Competitor</button>\n', "", "tab mc")
head = once(head, "Monthly business review · Số liệu thực tế", "Monthly business review · Số liệu thực tế · Mẫu Gọn v1", "eyebrow")

# ---------- 11. CSS ----------
CSS = """<style>
/* ===== Mẫu Gọn v1: khối thu gọn, lối tắt, bảng giới hạn dòng ===== */
details.fold{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:0 16px;box-shadow:var(--shadow)}
details.fold>summary{cursor:pointer;list-style:none;display:flex;gap:10px;align-items:baseline;padding:13px 0}
details.fold>summary::-webkit-details-marker{display:none}
details.fold>summary::before{content:"▸";color:var(--accent);font-size:12px;flex:none}
details.fold[open]>summary::before{content:"▾"}
details.fold>summary .shead{border:0;margin:0;padding:0;flex:1}
details.fold>summary:hover h2{color:var(--accent)}
details.fold[open]>summary{border-bottom:1px solid var(--line);margin-bottom:16px}
details.fold .foldbody{padding-bottom:18px}
details.fold.sub{margin-top:12px;box-shadow:none;background:transparent}
details.fold.sub>summary{font-size:13px;color:var(--ink-2);padding:9px 0}
.bsec{margin-top:26px}.bsec:first-child{margin-top:0}
.plvl{margin:26px 0 -18px}
.jumps{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:14px;font-size:12.5px;color:var(--muted)}
.limbtn{margin:9px 0 0;appearance:none;border:1px solid var(--line);background:var(--card);color:var(--ink-2);font:inherit;font-size:12.5px;padding:6px 14px;border-radius:20px;cursor:pointer}
.limbtn:hover{border-color:var(--accent);color:var(--ink)}
table.lim:not(.lim-all) tbody tr.lim-h{display:none}
@media print{details.fold>.foldbody{display:block}}
</style>
"""
head = head.rstrip("\n") + "\n" + CSS

# ---------- 12. JS ----------
js = tail
# builders: dồn nội dung theo tab mới
js = once(js, "grTop();tacos2();invMatrix2();},", "grTop();invMatrix2();grExec();},", "builder gr")
js = once(js, "cp:function(){campaigns();grExec();},", "cp:function(){campaigns();tacos2();lrTab();mcTab();},", "builder cp")
js = once(js, "  lr:function(){lrTab();}, mc:function(){mcTab();}, tt:", "  tt:", "builder lr/mc")
# getTotalLength an toàn khi biểu đồ nằm trong khối đang thu gọn
js = once(js, 'host.querySelectorAll(".ln").forEach((p,i)=>{const L=p.getTotalLength();',
          'host.querySelectorAll(".ln").forEach((p,i)=>{let L=0;try{L=p.getTotalLength()}catch(e){} if(!L)return;', "ln")
js = once(js, 'host.querySelectorAll(".tsl").forEach((p,i)=>{const L=p.getTotalLength();',
          'host.querySelectorAll(".tsl").forEach((p,i)=>{let L=0;try{L=p.getTotalLength()}catch(e){} if(!L)return;', "tsl")
EXTRA = r"""
/* ===== Mẫu Gọn v1: lối tắt, thu gọn cảnh báo khi đã có khối "Điều cần chú ý", giới hạn dòng bảng ===== */
function goTab(key,id){activate(key);setTimeout(()=>{const e=id&&document.getElementById(id);(e||document.getElementById("p-"+key)).scrollIntoView({behavior:"smooth",block:"start"})},80);}
const LIMIT_IDS={"tbl-grcmp":10,"tbl-tacos":10,"tbl-invmx":10,"tbl-dt":10,"tbl-pl5":10,"tbl-campthu":10,"tbl-invdet":10,"tbl-invsku":10,"tbl-ltsku":10,"tbl-iaccdet":10,"b-tbl-asp":10,"tbl-mcrank":10,"tbl-mcst":10};
function limitTable(id,n){
  const t=document.getElementById(id); if(!t||!t.tBodies[0]) return;
  const host=t.closest(".scroll")||t, tb=t.tBodies[0];
  let btn=host.nextElementSibling; if(!btn||!btn.classList||!btn.classList.contains("limbtn")){btn=document.createElement("button");btn.className="limbtn";btn.type="button";
    btn.onclick=()=>{t.classList.toggle("lim-all");paint()};host.after(btn);}
  function paint(){
    const rows=[...tb.rows], all=t.classList.contains("lim-all");
    rows.forEach((r,i)=>r.classList.toggle("lim-h",i>=n));
    t.classList.add("lim");
    if(rows.length<=n+2){t.classList.remove("lim");btn.style.display="none";return}
    btn.style.display="";btn.textContent=all?"Chỉ hiện "+n+" dòng đầu":"Xem tất cả ("+rows.length+" dòng)";
  }
  paint();
  let busy=false;
  new MutationObserver(()=>{if(busy)return;busy=true;requestAnimationFrame(()=>{paint();busy=false})}).observe(tb,{childList:true});
}
Object.keys(LIMIT_IDS).forEach(id=>{const t=document.getElementById(id);if(t&&t.tBodies[0])limitTable(id,LIMIT_IDS[id])});
/* gói Pro (nếu bật) chèn "Điều cần chú ý" sau mục đầu; mẫu này tự chuyển nó vào #pro-slot và thu gọn danh sách cảnh báo trùng ý.
   Làm ở đây (trong mẫu) để không phải sửa patches/pro.js dùng chung với mẫu gốc. */
setTimeout(()=>{const pi=document.getElementById("pro-ins"),sl=document.getElementById("pro-slot");
  if(pi){if(sl)sl.replaceWith(pi);const d=document.getElementById("alerts-fold");if(d)d.open=false}},0);
"""
# limitTable cần chạy sau khi các bảng được dựng (mỗi builder tự dựng khi mở tab) -> gắn vào activate
js = once(js, "  counters(panel);\n  panel.querySelectorAll", "  counters(panel);\n  if(typeof LIMIT_IDS!==\"undefined\")Object.keys(LIMIT_IDS).forEach(id=>{const t=document.getElementById(id);if(t&&panel.contains(t)&&t.tBodies[0]&&!t.dataset.lim){t.dataset.lim=1;limitTable(id,LIMIT_IDS[id])}});\n  panel.querySelectorAll", "activate")
js = once(js, 'activate("ov");\nfunction rebuild()', EXTRA.replace('Object.keys(LIMIT_IDS).forEach(id=>{const t=document.getElementById(id);if(t&&t.tBodies[0])limitTable(id,LIMIT_IDS[id])});\n', '') + 'activate("ov");\nfunction rebuild()', "activate ov")

out = head + "\n" + new_panels + "\n" + js

# ---------- 13. cập nhật các câu nhắc tên tab / số mục cũ ----------
REPL = [("chi tiết ở tab Chiến dịch", "chi tiết ở tab Quảng cáo", 1),
        ("đang chờ file template · chuyển từ tab Listing &amp; Rating", "đang chờ file template", 1),
        ("(tab Hiệu quả theo SKU, mục 04)", "(tab SKU &amp; P&amp;L, mục 02)", 1),
        ("xem mục 04 tab Hiệu quả theo SKU", "xem mục 02 tab SKU &amp; P&amp;L", 2),
        ("ở tab Giá: SKU tụt", "ở tab Listing &amp; Giá: SKU tụt", 1)]
for old, new, n in REPL:
    c = out.count(old)
    assert c == n, f"{old!r}: {c} (cần {n})"
    out = out.replace(old, new)

open(DST, "w", encoding="utf-8").write(out)
print("OK", DST, len(out) // 1024, "KB")
