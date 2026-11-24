"""Chuẩn hoá D trước khi dùng: tốc độ bán tồn kho theo BÌNH QUÂN 4 TUẦN (không dựa 1 tuần).
Trong data.json cũ, invdet.sku_tot[].sold_month thực chất là SL bán của đúng tuần báo cáo và weeks = tồn ÷ SL đó,
nên SKU có một tuần bán bất thường (hoặc không bán) làm số tuần tồn nhảy mạnh. Hàm này (idempotent):
  - sold_cur  = SL bán tuần báo cáo (giữ lại số cũ)         - weeks_cur = số tuần tồn theo tuần báo cáo (giữ lại số cũ)
  - sold_month = BQ 4 tuần gần nhất (đơn vị/tuần)           - weeks = tồn ÷ BQ 4 tuần (None nếu 4 tuần không có đơn hoặc tồn ≤ 0)
  - invdet.avg4_cty = {"SKU|CTY": BQ 4 tuần theo quốc gia} (để bảng theo quốc gia dùng cùng cơ sở)
"""
import threading
_tl = threading.local()


def modern():
    """True khi đang dựng báo cáo/phân tích theo cách mới (mẫu khác mẫu gốc). Mặc định False để MẪU GỐC giữ nguyên từng byte."""
    return bool(getattr(_tl, "on", False))


class use:
    def __init__(self, on=True):
        self.on = on

    def __enter__(self):
        self.prev = modern(); _tl.on = bool(self.on)

    def __exit__(self, *a):
        _tl.on = self.prev


# SKU ngưng kinh doanh (chủ shop xác nhận 13/10/2026): không đưa vào cảnh báo sắp hết hàng/điểm đặt hàng; tồn còn lại xử lý thanh lý.
DISCONTINUED = {"QCER", "XQG1", "UQ1R", "YHS8", "UKHE", "T1XS", "X5DV", "U6G4", "ADN1", "CQPN", "NKEP", "LDRW", "PXLS", "FXT2", "TTRF", "BF0E", "RLRA", "S0YE", "EHMJ", "V0B3"}


def is_disc(sku):
    return modern() and str(sku).split("-")[0] in DISCONTINUED or modern() and sku in DISCONTINUED


def _n(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _fx(D):
    """Câu mô tả tỷ giá do kỳ trước mang sang còn nhắc 'Tuần W39 giữ nguyên' -> viết trung tính theo mọi kỳ sau."""
    import re
    fx = (D or {}).get("fx") or {}
    src = fx.get("source")
    if isinstance(src, str) and ((D.get("meta") or {}).get("week_no") or 0) > 39:
        src = re.sub(r"Tuần W\d+ GIỮ NGUYÊN tỷ giá này \(không đổi sang bình quân W\d+\)", "Các tuần sau GIỮ NGUYÊN tỷ giá này (không đổi theo bình quân từng tuần)", src)
        src = re.sub(r";\s*bình quân W39[^.]*\.", ".", src)
        fx["source"] = src


def _regroup(D):
    """SKU nằm ở nhóm không có trong danh sách nhóm (vd 'Alma, Wilma') -> dùng nhóm chuẩn trong sku_meta (R1SU, R1AE thuộc Wilma)."""
    inv = D.get("invdet") or {}
    ok = set((D.get("meta") or {}).get("groups") or [])
    gm = {m["sku"]: m.get("grp") for m in D.get("sku_meta") or [] if m.get("grp") in ok}
    fixed = set()
    for lst in (inv.get("sku_tot") or [], inv.get("rows") or []):
        for r in lst:
            g = gm.get(r.get("sku"))
            if g and r.get("grp") not in ok:
                r["grp"] = g; fixed.add(r["sku"])
    for r in (D.get("invacct") or {}).get("det") or []:
        g = gm.get(r.get("sku"))
        if g and r.get("grp") not in ok:
            r["grp"] = g
    if fixed and inv.get("matrix"):      # gộp dòng ma trận nhóm × nguồn kho của nhóm không chuẩn vào nhóm chuẩn
        tgt = next(iter({gm[k] for k in fixed}))
        agg = {}
        for r in inv["matrix"]:
            g = tgt if r.get("grp") not in ok else r["grp"]
            k = (g, r.get("stlab")); o = agg.get(k)
            if o: o["qty"] += r.get("qty") or 0
            else: agg[k] = dict(r, grp=g)
        inv["matrix"] = list(agg.values())
    if inv.get("dup_sku_grp") is not None:
        inv["dup_sku_grp"] = [x for x in inv["dup_sku_grp"] if x.get("sku") not in fixed]
    for s in inv.get("sku_tot") or []:
        if is_disc(s.get("sku")):
            s["disc"] = True
    inv["discontinued"] = sorted(s["sku"] for s in inv.get("sku_tot") or [] if s.get("disc"))


def apply(D):
    if not modern():
        return D
    _fx(D)
    inv = (D or {}).get("invdet")
    _regroup(D)
    if not inv or inv.get("basis") == "avg4":
        return D
    ts = (D.get("ts_sku") or {}).get("W") or {}
    wk = [str(w) for w in ((D.get("ts_labels") or {}).get("W") or (D.get("meta") or {}).get("weeks") or [])][-4:]
    if not ts.get("l1") or len(wk) < 4:
        return D            # thiếu chuỗi tuần: giữ nguyên số cũ
    l1, l2 = ts["l1"], ts.get("l2") or {}
    avg = lambda row: sum(_n(((row or {}).get(w) or {}).get("q")) for w in wk) / 4.0
    for s in inv.get("sku_tot") or []:
        s["sold_cur"], s["weeks_cur"] = s.get("sold_month"), s.get("weeks")
        a = avg(l1.get(s["sku"]))
        s["sold_month"] = round(a, 2)
        q = _n(s.get("qty"))
        s["weeks"] = round(q / a, 1) if a > 0 and q > 0 else None
    a4 = {}
    for k, row in l2.items():
        if " · " in k:
            sku, cty = k.split(" · ", 1)
            a4[sku + "|" + cty] = round(avg(row), 3)
    inv["avg4_cty"] = a4
    inv["basis"] = "avg4"
    inv["basis_weeks"] = wk
    return D
