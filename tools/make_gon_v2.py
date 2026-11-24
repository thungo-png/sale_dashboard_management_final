#!/usr/bin/env python3
"""Tạo mẫu report "Gọn v2" (kế thừa Gọn v1) từ mẫu gốc (report-template-base.html) — KHÔNG sửa dữ liệu `const D`, KHÔNG xoá phần tử nào
(mọi id mà JS của mẫu dùng vẫn còn) nên ETL và các key dữ liệu giữ nguyên. Chỉ thay đổi bố cục:
  1. Tổng quan: KPI -> việc cần làm -> diễn biến -> FC; bảng chi tiết thu gọn; Quảng cáo/Tồn kho toàn danh mục chỉ giữ KPI.
  2. Gom giải pháp lên đầu từng tab, lối tắt từ Tổng quan.
  3. Gộp tab: Listing & Giá (= Giá & Buy Box + Listing & Rating), Quảng cáo (= Chiến dịch + TACoS + Thứ hạng + Thị phần tìm kiếm + Độ phủ listing).
  4. Mục ít dùng / chưa có dữ liệu / giả lập: thu gọn mặc định.
  5. Bảng dài chỉ hiện 10 dòng đầu + nút "Xem tất cả".
  6. (v2) Bảng rộng: cột chính + nút "Hiện thêm cột"; bảng dài sắp theo mức đáng chú ý trước; dải "so với tuần trước"; "Bản tóm tắt";
     tuỳ chỉnh biểu đồ gập lại; nhớ khối đã mở. Gói Pro dùng bộ patch riêng patches/gon-v2/.
Dùng:  python3 make_gon_v2.py <mẫu gốc> <file ra>"""
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
    return f"<section{sec.attrs if 'class=' in sec.attrs else ''}>{sec.inner}</section>"


def bundle(title, hint, secs, open_=False, fid=None):
    inner = ""
    for s in secs:
        x = re.sub(r'<span class="snum">[^<]*</span>', "", s.inner)
        inner += '<div class="bsec">' + x + '</div>'
    return ('<section class="bh"><details class="fold"' + (" open" if open_ else "") + _fid(fid) + '>'
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
# (v2) #7: chỉ giữ hàng chọn chỉ số; độ chi tiết và chiều phân tách gập vào "Tuỳ chỉnh"
_g = '<div class="pickrow" id="ovgran" style="margin-bottom:7px"></div>'
_m = '<div class="pickrow" id="ovmetric" style="margin-bottom:7px"></div>'
_d = '<div class="pickrow" id="ovdim" style="margin-bottom:11px"></div>'
assert all(trend.inner.count(x) == 1 for x in (_g, _m, _d)), "trend pickrows"
trend.inner = trend.inner.replace(_g, "", 1).replace(_m, "", 1).replace(
    _d, _m + '<details class="capfold"><summary>Tuỳ chỉnh: độ chi tiết · chiều phân tách</summary>' + _g + _d + '</details>', 1)
# (v2) #5: dải so với tuần trước ngay dưới KPI
_k = '<div class="kpis" style="margin-bottom:15px" id="ovkpi"></div>'
assert kpi.inner.count(_k) == 1, "ovkpi"
kpi.inner = kpi.inner.replace(_k, _k + '<div class="wow" id="wowstrip"></div>', 1)
# (v2) #6: đánh dấu phần ẩn trong "Bản tóm tắt"
howto.attrs = ' class="bh"'
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
head = once(head, "Monthly business review · Số liệu thực tế", "Monthly business review · Số liệu thực tế · Mẫu Gọn v2", "eyebrow")
head = once(head, '<div class="meta" id="mmeta"></div>', '<div class="meta" id="mmeta"></div>\n  <div class="mastact"><button id="briefbtn" class="pick" type="button" title="Chỉ hiện Tổng quan để gửi nhanh; dùng được cùng nút In / PDF">Bản tóm tắt</button></div>', "mast button")

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
.xc{}
table.cc:not(.cc-all) .xc{display:none}
.tblctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:9px}.tblctl .limbtn{margin:0}
.tblnote{font-size:11.5px;color:var(--muted)}
.wow{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline;margin:0 0 4px;padding:10px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card);font-size:13px;color:var(--ink-2)}
.wow .wlab{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.mastact{margin-top:10px}
body.brief .tabbar,body.brief .panel:not(#p-ov),body.brief .bh,body.brief .jumps,body.brief details.fold.sub,body.brief .tblctl,body.brief #pro-bar .pbtn-x{display:none!important}
body.brief #p-ov .panel{display:block}
@media(max-width:560px){
  details.fold>summary{flex-wrap:wrap;gap:4px 8px}
  .wow{display:grid;gap:6px}
  .tblctl{gap:6px}.limbtn{padding:6px 11px}
  .cgrid{grid-template-columns:minmax(0,1fr)}
  .cgrid>*,.card,.chartbox{min-width:0;max-width:100%}
  .card{overflow-x:auto}
}
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
/* ===== Mẫu Gọn v2 ===== */
function goTab(key,id){activate(key);setTimeout(()=>{const e=id&&document.getElementById(id);(e||document.getElementById("p-"+key)).scrollIntoView({behavior:"smooth",block:"start"})},80);}

/* --- Bảng: giới hạn dòng, cột chính, sắp theo mức đáng chú ý --- */
const TBL={
 "tbl-grcmp":{n:10,core:["Nhóm","Sàn","Thị trường","Kỳ này","% đạt FC","vs tuần trước"],sort:{cols:["% đạt FC"],dir:1,label:"mức đạt FC thấp nhất trước"}},
 "tbl-tacos":{n:10,core:["Nhóm","Sàn","Thị trường","Spend","Doanh thu kênh","TACoS","Room còn lại"],sort:{cols:["TACoS"],dir:-1,label:"TACoS cao nhất trước"}},
 "tbl-invmx":{n:10},
 "tbl-dt":{n:10},
 "tbl-pl5":{n:10,core:["SKU","Doanh thu","Tổng chi phí","Profit PL5"],sort:{cols:["Profit PL5"],dir:1,label:"lợi nhuận PL5 thấp nhất trước (cần rà trước)"}},
 "tbl-campthu":{n:10,core:["Chiến dịch","Nhóm","Sàn","Spend","Đơn","ACOS","ROAS"],sort:{cols:["Spend"],dir:-1,label:"chi nhiều nhất trước"}},
 "tbl-invdet":{n:10,core:["SKU","Nhóm","Tổng","Hàng sắp"]},
 "tbl-invsku":{n:10,core:["SKU","Nhóm","Tổng tồn","Tuần tồn (tổng)","SL bán","Trạng thái"],sort:{cols:["Tuần tồn (tổng)"],dir:1,label:"sắp hết hàng trước"}},
 "tbl-ltsku":{n:10,core:["SKU","Nhóm","Tài khoản","271","366","Tổng tồn","Chênh lệch"],sort:{cols:["271","366"],dir:-1,sum:true,label:"tồn lâu ngày nhiều nhất trước"}},
 "tbl-iaccdet":{n:10},
 "b-tbl-asp":{n:10,core:["SKU","Nhóm","SL W","BQ","Xu hướng"],weeks:3,sort:{cols:["Xu hướng"],dir:-1,abs:true,label:"giá biến động lớn nhất trước"}},
 "tbl-mcrank":{n:10,sort:{cols:["Đổi"],dir:1,label:"tụt hạng nhiều nhất trước"}},
 "tbl-mcst":{n:10}
};
const LIMIT_IDS={}; Object.keys(TBL).forEach(k=>LIMIT_IDS[k]=TBL[k].n);
function numOf(t){t=(t||"").trim();if(!t||/^(—|-|chưa|n\/a)/i.test(t))return NaN;const neg=/[↓−]/.test(t.charAt(0))||t.charAt(0)==="-"||t.charAt(0)==="−";
  const m=t.replace(/\s/g,"").match(/[\d.]+(?:,\d+)?/);if(!m)return NaN;let v=parseFloat(m[0].replace(/\./g,"").replace(",","."));return neg?-v:v;}
function limitTable(id){
  const spec=TBL[id]; if(!spec) return;
  const t=document.getElementById(id); if(!t||!t.tBodies[0]||t.dataset.lim) return; t.dataset.lim=1;
  const host=t.closest(".scroll")||t, tb=t.tBodies[0];
  const ctl=document.createElement("div"); ctl.className="tblctl"; host.after(ctl);
  const bRows=document.createElement("button"), bCols=document.createElement("button"), note=document.createElement("span");
  bRows.className=bCols.className="limbtn"; bRows.type=bCols.type="button"; note.className="tblnote"; ctl.append(bRows,bCols,note);
  bRows.onclick=()=>{t.classList.toggle("lim-all");paint()}; bCols.onclick=()=>{t.classList.toggle("cc-all");paint()};
  let prev=new Set(), sortedOnce=false;
  const hdrs=()=>{const hr=t.tHead&&t.tHead.rows[t.tHead.rows.length-1];return hr?[...hr.cells].map(c=>c.textContent.trim()):[]};
  function colIdx(h,pfx){return h.findIndex(x=>x.startsWith(pfx))}
  function paint(){
    if(obs)obs.disconnect();
    const rows=[...tb.rows], h=hdrs();
    // 1) sắp mặc định khi bảng được dựng lại (không ghi đè khi người dùng tự bấm sắp xếp ở tiêu đề)
    const rebuilt=rows.length!==prev.size||rows.some(r=>!prev.has(r));
    if(rebuilt&&spec.sort&&rows.length>spec.n){
      const ix=spec.sort.cols.map(c=>colIdx(h,c)).filter(i=>i>=0);
      if(ix.length){
        const key=r=>{let v=ix.map(i=>numOf(r.cells[i]&&r.cells[i].textContent));if(v.some(Number.isNaN))return NaN;let x=spec.sort.sum?v.reduce((a,b)=>a+b,0):v[0];return spec.sort.abs?Math.abs(x):x};
        const dec=rows.map((r,i)=>({r,i,k:key(r)})); dec.sort((a,b)=>{const an=Number.isNaN(a.k),bn=Number.isNaN(b.k);if(an&&bn)return a.i-b.i;if(an)return 1;if(bn)return -1;return (a.k-b.k)*spec.sort.dir||a.i-b.i});
        dec.forEach(x=>tb.appendChild(x.r)); rows.length=0; dec.forEach(x=>rows.push(x.r));
      }
    }
    prev=new Set(rows);
    // 2) cột chính / cột phụ
    let hid=0;
    if(spec.core&&h.length){
      const wk=h.map((x,i)=>/^W\d+/.test(x)?i:-1).filter(i=>i>=0), keepWk=new Set(spec.weeks?wk.slice(-spec.weeks):[]);
      const core=new Set(h.map((x,i)=>(spec.core.some(p=>x.startsWith(p))||keepWk.has(i))?i:-1).filter(i=>i>=0));
      hid=h.length-core.size; const showAll=t.classList.contains("cc-all");
      [...(t.tHead?t.tHead.rows:[]),...tb.rows,...(t.tFoot?t.tFoot.rows:[])].forEach(r=>{      /* theo dõi cả ô gộp (colspan): chỉ ẩn ô nằm hoàn toàn trong cột phụ, ô gộp thì co lại */
        const cells=[...r.cells]; cells.forEach(c=>{if(c.dataset.ocs===undefined)c.dataset.ocs=c.colSpan});
        if(cells.reduce((a,c)=>a+(+c.dataset.ocs),0)!==h.length)return;
        let ci=0; cells.forEach(c=>{const k=+c.dataset.ocs;let vis=0;for(let j=ci;j<ci+k;j++)if(core.has(j))vis++;
          if(showAll||!hid){c.colSpan=k;c.classList.remove("xc")}else if(!vis){c.classList.add("xc")}else{c.classList.remove("xc");c.colSpan=vis}ci+=k});
      });
    }
    t.classList.toggle("cc",hid>0);
    bCols.style.display=hid>0?"":"none"; bCols.textContent=t.classList.contains("cc-all")?"Chỉ hiện cột chính":"Hiện thêm cột (+"+hid+")";
    // 3) giới hạn dòng
    const all=t.classList.contains("lim-all"); rows.forEach((r,i)=>r.classList.toggle("lim-h",i>=spec.n));
    const many=rows.length>spec.n+2; t.classList.toggle("lim",many);
    bRows.style.display=many?"":"none"; bRows.textContent=all?"Chỉ hiện "+spec.n+" dòng đầu":"Xem tất cả ("+rows.length+" dòng)";
    note.textContent=(spec.sort&&many&&!all)?"Đang xếp: "+spec.sort.label:"";
    ctl.style.display=(many||hid>0)?"":"none";
    if(obs)obs.observe(t,{childList:true,subtree:true});
  }
  let obs=new MutationObserver(()=>{requestAnimationFrame(paint)});
  paint();
}

/* --- Dải "so với tuần trước" dưới KPI --- */
function wowStrip(){
  const el=document.getElementById("wowstrip"); if(!el) return;
  const wk=(D.weekfc&&D.weekfc.all)||[]; const cur=wk[wk.length-1], prv=wk[wk.length-2];
  const it=[];
  if(cur&&prv&&prv.r>0){const d=(cur.r/prv.r-1)*100;it.push(`Doanh thu <b>${N(cur.r)}</b> <span class="${cls(d)}">${pct(d)}</span> so với tuần trước`);}
  if(cur&&prv&&cur.ach!=null&&prv.ach!=null){const d=cur.ach-prv.ach;it.push(`Đạt FC <b>${pc0(cur.ach)}</b> (tuần trước ${pc0(prv.ach)}, <span class="${cls(d)}">${d>=0?"+":"−"}${Math.abs(d).toFixed(1).replace(".",",")} điểm</span>)`);}
  const t=D.pl5&&D.pl5.total, p=D.pl5&&D.pl5.prev_total;
  if(t&&p&&t.margin!=null&&p.margin!=null){const d=t.margin-p.margin;it.push(`Biên PL5 <b>${pc0(t.margin)}</b> (tuần trước ${pc0(p.margin)}, <span class="${cls(d)}">${d>=0?"+":"−"}${Math.abs(d).toFixed(1).replace(".",",")} điểm</span>)`);}
  el.innerHTML=it.length?'<span class="wlab">So với tuần trước</span>'+it.map(x=>"<span>"+x+"</span>").join(""):"";
  el.style.display=it.length?"":"none";
}
const _ovb=builders.ov; builders.ov=function(){_ovb();wowStrip();};

/* --- Bản tóm tắt: chỉ Tổng quan, ẩn phần chi tiết --- */
function setBrief(on){document.body.classList.toggle("brief",on);const b=document.getElementById("briefbtn");if(b)b.textContent=on?"Xem đầy đủ":"Bản tóm tắt";
  if(on)activate("ov");try{history.replaceState(null,"",on?"#brief":location.pathname+location.search)}catch(e){}}
document.getElementById("briefbtn").addEventListener("click",()=>setBrief(!document.body.classList.contains("brief")));
if(location.hash==="#brief")setBrief(true);

/* --- Gói Pro (nếu bật): chuyển "Điều cần chú ý" vào #pro-slot, thu gọn cảnh báo trùng ý; nhớ khối đã mở/đóng --- */
const FOLDKEY="gonv2.fold.";
function foldName(d){const h=d.querySelector("h2");return (d.id||(h?h.textContent.trim().slice(0,60):""))}
setTimeout(()=>{const pi=document.getElementById("pro-ins"),sl=document.getElementById("pro-slot");
  if(pi){if(sl)sl.replaceWith(pi);const d=document.getElementById("alerts-fold");if(d)d.open=false}
  document.querySelectorAll("details.fold").forEach(d=>{const k=foldName(d);if(!k)return;try{const v=localStorage.getItem(FOLDKEY+k);if(v==="1")d.open=true;else if(v==="0")d.open=false}catch(e){}});
  setTimeout(()=>document.querySelectorAll("details.fold").forEach(d=>d.addEventListener("toggle",()=>{const k=foldName(d);if(!k)return;try{localStorage.setItem(FOLDKEY+k,d.open?"1":"0")}catch(e){}})),80);
},0);
"""
# gắn bảng khi mở tab (builder chạy trước) — thay bản v1
js = once(js, "  counters(panel);\n  panel.querySelectorAll", "  counters(panel);\n  if(typeof TBL!==\"undefined\")Object.keys(TBL).forEach(id=>{const t=document.getElementById(id);if(t&&panel.contains(t)&&t.tBodies[0])limitTable(id)});\n  panel.querySelectorAll", "activate")
js = once(js, 'activate("ov");\nfunction rebuild()', EXTRA + 'activate("ov");\nfunction rebuild()', "activate ov")

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
