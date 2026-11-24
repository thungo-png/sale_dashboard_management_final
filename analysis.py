"""Phân tích D của một kỳ -> danh sách vấn đề (issue). Mỗi issue có: nêu vấn đề nằm ở đâu + hướng xử lý.
Chỉ đọc D, không ghi gì. `key` ổn định giữa các kỳ để task tái dùng được (xem tasks.py)."""

import invnorm

TH = {  # ngưỡng — chỉnh ở đây
    "margin_low": 5.0,        # % margin dưới mức này thì nêu ra
    "min_rev_grp": 500,       # chỉ xét nhóm/kênh có doanh thu >= (USD)
    "min_rev_cell": 300,
    "drop_pct": -30.0,        # doanh thu tuần giảm quá mức này so với tuần trước
    "tacos_high": 10.0,       # %
    "tacos_min_spend": 30,
    "camp_min_spend": 15,
    "acos_high": 50.0,
    "stock_weeks_low": 4.0,
    "dead_stock_qty": 20,
    "max_items": 6,
}
SEV_NAME = {3: "Ưu tiên cao", 2: "Ưu tiên vừa", 1: "Theo dõi"}
MP_CTY = lambda mp, cty: f"{mp} {cty}"


def _n(x):
    return x if isinstance(x, (int, float)) else 0


def _usd(x):
    return f"${_n(x):,.0f}"


def _issue(key, sev, area, title, where, detail, fix, **metric):
    return {"key": key, "sev": sev, "area": area, "title": title, "where": where,
            "detail": [d for d in detail if d], "fix": [f for f in fix if f], "metric": metric}


_NORM = {}


def _g(g):
    return _NORM.get(g, g)


def _stock_by(D):
    """{(grp, cty): qty tồn} từ invdet.sku_tot."""
    out = {}
    for s in (D.get("invdet") or {}).get("sku_tot") or []:
        for c, q in (s.get("by_cty") or {}).items():
            out[(_g(s["grp"]), c)] = out.get((_g(s["grp"]), c), 0) + _n(q)
    return out


# ---------- lợi nhuận ----------
def _drivers(rows):
    r = sum(_n(x.get("r")) for x in rows) or 1
    comp = {
        "giá vốn": sum(_n(x.get("cogs")) for x in rows), "quảng cáo (SEM)": sum(_n(x.get("sem")) for x in rows),
        "vận chuyển/fulfill": sum(_n(x.get("fulfill")) for x in rows),
        "phí sàn (ref/return/WH/OP)": sum(_n(x.get(k)) for x in rows for k in ("ref_fee", "return_fee", "wh_fee", "op_fee")),
    }
    return r, sorted(((k, v / r * 100) for k, v in comp.items()), key=lambda t: -t[1])


FIX_DRV = {
    "giá vốn": "Rà lại giá bán/giá vốn: cân nhắc tăng giá nhẹ hoặc đàm phán lại giá nhập cho SKU có biên thấp.",
    "quảng cáo (SEM)": "Tối ưu quảng cáo: hạ bid ở campaign hiệu quả thấp, tạm dừng keyword không ra đơn (xem các vấn đề ở mục Quảng cáo).",
    "vận chuyển/fulfill": "Xem lại chi phí vận chuyển/fulfill: gộp lô, đổi carrier hoặc kho gần hơn cho SKU nặng.",
    "phí sàn (ref/return/WH/OP)": "Kiểm tra tỷ lệ hoàn trả và phí kho/phí khác của kênh; xử lý nguyên nhân hoàn hàng ở SKU có tỷ lệ cao.",
}


def _fx_drv(k):
    if invnorm.modern() and k == "giá vốn":
        return "Rà lại giá bán (giá sỉ với Wayfair) và giá vốn: đàm phán lại giá nhập hoặc điều chỉnh giá cho SKU có biên thấp."
    return FIX_DRV.get(k)


def _profit(D):
    out = []
    pl = D.get("pl5") or {}
    if not pl.get("available") or not pl.get("rows"):
        return out
    rows = pl["rows"]
    for grp, v in sorted((pl.get("by_grp") or {}).items(), key=lambda t: t[1].get("margin", 0)):
        if _n(v.get("r")) < TH["min_rev_grp"] or _n(v.get("margin")) >= TH["margin_low"]:
            continue
        sub = [x for x in rows if x.get("grp") == grp]
        r, dr = _drivers(sub)
        top = [d for d in dr if d[1] > 0][:2]
        grev = next((_n(b.get("r")) for b in D.get("bygrp") or [] if b.get("grp") == grp), 0)
        cov = (_n(v.get("r")) / grev * 100) if grev else 100
        out.append(_issue(f"margin_grp|{grp}", 3 if v["margin"] < -10 else 2, "Lợi nhuận",
                          f"Margin nhóm “{grp}” cần cải thiện ({v['margin']:.1f}%)", f"Nhóm sản phẩm: {grp}",
                          [f"Doanh thu {_usd(v['r'])}, margin {v['margin']:.1f}% (P&L tuần)."
                           + (f" Mới tính được trên {cov:.0f}% doanh thu của nhóm (phần còn lại chưa có phí trong file P&L) nên cần đọc thận trọng." if invnorm.modern() and cov < 90 else ""),
                           "Khoản chiếm tỷ trọng lớn nhất: " + ", ".join(f"{k} {p:.0f}% doanh thu" for k, p in top)],
                          [_fx_drv(k) for k, _ in top], r=v["r"], margin=v["margin"]))
    for mc, v in sorted((pl.get("by_mpcty") or {}).items(), key=lambda t: t[1].get("margin", 0)):
        if _n(v.get("r")) < TH["min_rev_grp"] or _n(v.get("margin")) >= TH["margin_low"]:
            continue
        mp, cty = mc.split("|")
        sub = [x for x in rows if x.get("mp") == mp and x.get("cty") == cty]
        r, dr = _drivers(sub)
        top = [d for d in dr if d[1] > 0][:2]
        # SKU kéo margin của kênh xuống nhiều nhất
        worst = sorted(sub, key=lambda x: _n(x.get("profit")))[:3]
        out.append(_issue(f"margin_mc|{mc}", 3 if v["margin"] < -10 else 2, "Lợi nhuận",
                          f"Kênh {MP_CTY(mp, cty)}: margin {v['margin']:.1f}% — cần rà cơ cấu chi phí", f"Kênh: {MP_CTY(mp, cty)}",
                          [f"Doanh thu {_usd(v['r'])}, {v.get('q', 0)} đơn vị.",
                           "Khoản chiếm tỷ trọng lớn: " + ", ".join(f"{k} {p:.0f}%" for k, p in top),
                           "SKU cần xem đầu tiên: " + ", ".join(f"{x['sku']} ({_usd(x['r'])})" for x in worst)],
                          [_fx_drv(k) for k, _ in top], r=v["r"], margin=v["margin"]))
    miss = pl.get("missing_sku_fee") or []
    if miss:
        skus = sorted({m["sku"] for m in miss})
        out.append(_issue("pl5_missing", 2, "Dữ liệu",
                          f"{len(skus)} SKU có doanh thu nhưng chưa có công thức phí trong file P&L",
                          "File P&L (rate card)", ["SKU: " + ", ".join(skus[:12]) + (" …" if len(skus) > 12 else ""),
                                                   f"Độ phủ P&L hiện {pl.get('coverage_pct', 0):.1f}%."],
                          ["Bổ sung dòng SKU còn thiếu vào sheet kênh tương ứng của file P&L rồi build lại để margin đầy đủ."], n=len(skus)))
    nf = pl.get("no_formula_mpcty") or []
    if nf:
        out.append(_issue("pl5_noformula", 1, "Dữ liệu", "Một số kênh chưa có sheet tính phí trong P&L",
                          "File P&L", ["Kênh: " + ", ".join(map(str, nf))],
                          ["Thêm sheet tính phí cho các kênh này ở kỳ P&L tiếp theo để báo cáo lợi nhuận bao phủ đủ."]))
    return out


# ---------- quảng cáo ----------
def _ads(D):
    out = []
    for x in D.get("tacos") or []:
        if _n(x.get("spend")) >= TH["tacos_min_spend"] and _n(x.get("tacos")) >= TH["tacos_high"]:
            out.append(_issue(f"tacos|{x['grp']}|{x['mp']}|{x['cty']}", 2, "Quảng cáo",
                              f"TACoS {x['tacos']:.1f}% ở {x['grp']} · {MP_CTY(x['mp'], x['cty'])}",
                              f"{x['grp']} · {MP_CTY(x['mp'], x['cty'])}",
                              [f"Chi quảng cáo {_usd(x['spend'])} trên doanh thu {_usd(x['rev'])}; {x.get('ncamp', 0)} campaign."],
                              ["Hạ bid hoặc giảm ngân sách campaign có ROAS thấp; dồn ngân sách sang campaign/keyword đang ra đơn."],
                              spend=x["spend"], tacos=x["tacos"]))
    # campaign không ra đơn / ACoS cao, gộp theo nhóm × kênh
    agg = {}
    for c in D.get("campthu") or []:
        sp = _n(c.get("spend"))
        if sp < TH["camp_min_spend"]:
            continue
        zero = _n(c.get("orders")) == 0
        high = c.get("acos") is not None and c["acos"] >= TH["acos_high"]
        if zero or high:
            agg.setdefault((c["grp"], c["mp"], c["cty"]), []).append((sp, zero, c))
    for (g, mp, cty), lst in agg.items():
        lst.sort(key=lambda t: -t[0])
        tot = sum(t[0] for t in lst)
        if tot < 2 * TH["camp_min_spend"]:
            continue
        nz = sum(1 for t in lst if t[1])
        out.append(_issue(f"camp|{g}|{mp}|{cty}", 2 if tot >= 50 else 1, "Quảng cáo",
                          f"{len(lst)} campaign chưa hiệu quả ở {g} · {MP_CTY(mp, cty)}", f"{g} · {MP_CTY(mp, cty)}",
                          [f"Tổng chi {_usd(tot)}; {nz} campaign chưa có đơn, {len(lst) - nz} campaign ACoS ≥ {TH['acos_high']:.0f}%.",
                           "Campaign chi nhiều nhất: " + "; ".join(f"{t[2]['camp']} ({_usd(t[0])})" for t in lst[:TH["max_items"] // 2])],
                          ["Tạm dừng hoặc hạ bid các campaign chưa có đơn sau khi đã có đủ click; thêm negative keyword cho search term không liên quan."],
                          spend=tot, n=len(lst)))
    return out


# ---------- doanh số ----------
def _sales(D):
    out = []
    stock = _stock_by(D)
    ads_ok = {(x["grp"], x["mp"], x["cty"]) for x in D.get("tacos") or []}
    ads_mps = {x["mp"] for x in D.get("tacos") or []}          # sàn có báo cáo quảng cáo (Shopify/Walmart chưa có → không kết luận "chưa chạy QC")
    for x in (D.get("grpcmp") or {}).get("rows") or []:
        dw = x.get("d_w")
        if dw is None or _n(x.get("r_w")) < TH["min_rev_cell"] or dw > TH["drop_pct"]:
            continue
        g, mp, cty = x["grp"], x["mp"], x["cty"]
        st = stock.get((g, cty))
        why, fix = [], []
        if st is not None and st <= 0:
            why.append(f"Tồn kho {cty} của nhóm này đang bằng 0.")
            fix.append(f"Lên kế hoạch bổ sung hàng cho {cty} (hoặc điều chuyển từ kho khác) để mở lại bán.")
        if invnorm.modern() and mp not in ads_mps:
            why.append(f"Chưa có báo cáo quảng cáo của {mp} nên chưa đánh giá được vai trò của quảng cáo.")
        elif (g, mp, cty) not in ads_ok:
            why.append("Kỳ này chưa có quảng cáo Thu Ngo chạy cho nhóm này ở kênh đó.")
            fix.append("Bật lại/tạo campaign cho nhóm này nếu tồn kho cho phép.")
        fix.append("Kiểm tra trạng thái listing (active, giá, buy box/ranking) và so với tuần trước.")
        out.append(_issue(f"drop|{g}|{mp}|{cty}", 3 if x["r"] == 0 else 2, "Doanh số",
                          f"Doanh thu tuần của {g} · {MP_CTY(mp, cty)} chưa giữ được mức tuần trước",
                          f"{g} · {MP_CTY(mp, cty)}",
                          [f"Tuần này {_usd(x['r'])} so với {_usd(x['r_w'])} tuần trước ({dw:+.0f}%)."] + why, fix, r=x["r"], r_prev=x["r_w"], d_w=dw))
    return out


# ---------- tồn kho ----------
def _stock(D):
    out = []
    skus = (D.get("invdet") or {}).get("sku_tot") or []
    low = sorted([s for s in skus if not s.get("disc") and s.get("weeks") is not None and s["weeks"] < TH["stock_weeks_low"] and _n(s.get("sold_month")) > 0],
                 key=lambda s: s["weeks"])
    byg = {}
    for s in low:
        byg.setdefault(_g(s["grp"]), []).append(s)
    for g, lst in byg.items():
        out.append(_issue(f"lowstock|{g}", 3 if lst[0]["weeks"] < 2 else 2, "Tồn kho",
                          f"{len(lst)} SKU của {g} sắp hết hàng", f"Nhóm: {g}",
                          ["; ".join(f"{s['sku']}: còn {s['qty']} (đủ ~{s['weeks']} tuần)" for s in lst[:TH["max_items"]])],
                          ["Chốt số lượng và lịch nhập bổ sung cho các SKU này; nếu hàng về chậm, giảm quảng cáo để tránh hết hàng giữa chừng."], n=len(lst)))
    dead = [s for s in skus if _n(s.get("qty")) >= TH["dead_stock_qty"] and _n(s.get("sold_month")) == 0]
    byg = {}
    for s in dead:
        byg.setdefault(_g(s["grp"]), []).append(s)
    for g, lst in byg.items():
        tq = sum(s["qty"] for s in lst)
        out.append(_issue(f"deadstock|{g}", 1, "Tồn kho",
                          f"{len(lst)} SKU của {g} có tồn nhưng chưa phát sinh bán gần đây", f"Nhóm: {g}",
                          [f"Tổng {tq} sản phẩm; SKU: " + ", ".join(s["sku"] for s in lst[:TH["max_items"]])],
                          ["Rà lại listing (giá, ảnh, từ khoá) hoặc đưa vào chương trình khuyến mãi để tăng vòng quay."], qty=tq))
    lt = (D.get("lt") or {}).get("amz") or {}
    if _n(lt.get("over270")) > 0:
        old = sorted([s for s in lt.get("sku") or [] if sum(s["buckets"][3:]) > 0], key=lambda s: -sum(s["buckets"][3:]))
        out.append(_issue("lt_amz", 2, "Tồn kho", f"Amazon FBA: {lt['over270']} sản phẩm tồn trên 270 ngày",
                          "Amazon FBA (inventory age)",
                          ["SKU: " + ", ".join(f"{s['sku']} ({sum(s['buckets'][3:])})" for s in old[:TH["max_items"]])],
                          ["Lên kế hoạch xử lý trước kỳ tính phí lưu kho dài hạn: giảm giá/Deal, hoặc tạo removal order cho phần tồn lâu."],
                          over270=lt["over270"]))
    return out


MAX_HIGH = 6        # số mục "Ưu tiên cao" tối đa: xếp theo mức ảnh hưởng tiền, phần còn lại xuống "vừa"


def _impact(D, i):
    """Ước tính ảnh hưởng tiền/tuần (USD) để xếp thứ tự xử lý: (số tiền, mô tả). Không có cơ sở thì (None, '')."""
    k, m = i["key"], i.get("metric") or {}
    pl = D.get("pl5") or {}
    if k.startswith("margin_grp|") or k.startswith("margin_mc|"):
        src = pl.get("by_grp" if k.startswith("margin_grp|") else "by_mpcty") or {}
        p = _n((src.get(k.split("|", 1)[1]) or {}).get("profit"))
        return (round(-p), f"lợi nhuận PL5 âm {_usd(-p)}/tuần") if p < 0 else (0, "")
    if k.startswith("drop|"):
        d = _n(m.get("r_prev")) - _n(m.get("r"))
        return (round(d), f"doanh thu giảm {_usd(d)} so với tuần trước") if d > 0 else (0, "")
    if k.startswith("camp|"):
        return round(_n(m.get("spend"))), f"chi quảng cáo chưa hiệu quả {_usd(m.get('spend'))}"
    if k.startswith("tacos|"):
        return round(_n(m.get("spend"))), f"chi quảng cáo {_usd(m.get('spend'))} ở mức TACoS cao"
    if k.startswith("lowstock|"):
        sk = {s["sku"]: s for s in (D.get("invdet") or {}).get("sku_tot") or []}
        asp = {}
        for x in D.get("sku") or []:
            a = asp.setdefault(x["sku"], [0.0, 0.0]); a[0] += _n(x.get("r")); a[1] += _n(x.get("q"))
        tot = 0.0
        for sku, s in sk.items():
            if not s.get("disc") and _g(s["grp"]) == k.split("|", 1)[1] and s.get("weeks") is not None and s["weeks"] < TH["stock_weeks_low"] and _n(s.get("sold_month")) > 0:
                a = asp.get(sku)
                tot += _n(s["sold_month"]) * (a[0] / a[1] if a and a[1] else 0)
        return (round(tot), f"khoảng {_usd(tot)} doanh thu/tuần có thể gián đoạn nếu hết hàng") if tot > 0 else (None, "")
    return None, ""


def analyze(D, norm=None):
    invnorm.apply(D)
    """Trả về (danh sách issue đã sắp xếp, tóm tắt). norm = config.group_norm."""
    _NORM.clear(); _NORM.update(norm or {})
    issues = []
    for fn in (_profit, _sales, _ads, _stock):
        try:
            issues += fn(D)
        except Exception as e:                       # một nhóm luật lỗi không làm hỏng cả phân tích
            issues.append(_issue(f"rule_error|{fn.__name__}", 1, "Hệ thống", f"Bước phân tích {fn.__name__} gặp lỗi", "analysis.py", [repr(e)], []))
    if invnorm.modern():
        for i in issues:
            try:
                v, note = _impact(D, i)
            except Exception:
                v, note = None, ""
            i["impact"], i["impact_note"] = v, note
        hi = sorted([i for i in issues if i["sev"] == 3], key=lambda i: -(i["impact"] or 0))
        for i in hi[MAX_HIGH:]:
            i["sev"] = 2; i["demoted"] = True
        issues.sort(key=lambda i: (-i["sev"], -(i["impact"] or 0), i["area"], i["key"]))
    else:
        issues.sort(key=lambda i: (-i["sev"], i["area"], i["key"]))
    tot = (D.get("pl5") or {}).get("total") or {}
    m = D.get("meta") or {}
    summary = {"n": len(issues), "by_sev": {s: sum(1 for i in issues if i["sev"] == s) for s in (3, 2, 1)},
               "by_area": {a: sum(1 for i in issues if i["area"] == a) for a in sorted({i["area"] for i in issues})},
               "range": f"{m.get('d0', '')} → {m.get('d1', '')}", "margin": tot.get("margin"), "r": tot.get("r")}
    return issues, summary
