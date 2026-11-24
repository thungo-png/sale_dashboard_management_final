"""
ETL Profit PL5 (đợt 4b) — dựng lại từ file 'P&L Thư Ngô.xlsx' + doanh thu tuần + chi phí quảng cáo thật.

Công thức (đối chiếu với D.pl5 của W39; xem D.pl5.why):
  COGS      = COGS US (sheet 'COGS Auto') × SL cho US; COGS CA (CAD) × tỷ giá × SL cho CAN
  Ref. Fee  = Amazon: bậc 15% phần giá ≤ 200 + 10% phần vượt, tính trên GIÁ BÌNH QUÂN/ĐƠN VỊ theo tiền tệ gốc;
              Wayfair/Shopify: % cố định theo rate card (dòng 0 của sheet kênh)
  Return / WH / OP Fee = % × doanh thu thật (theo rate card kênh)
  Fulfill   = Amazon: Ship2AMZ + FBA F.ment (sheet US-FBA / CA-FBA, CAD × tỷ giá); Wayfair: Ship2CG; Shopify: Shipping cost — theo SKU × SL
  SEM       = chi phí quảng cáo thật của nhóm × sàn × quốc gia; Amazon chia đều cho các dòng SKU có bán trong ô, Wayfair chia đều cho số SKU của nhóm trong sheet kênh
  Profit    = Doanh thu − (COGS + Ref + SEM + Return + WH + OP + Fulfill)
Kênh có công thức: Amazon US/CAN, Wayfair US/CAN, Shopify US. Ô khác (Shopify CAN/AUS, Amazon AUS, Walmart) KHÔNG suy đoán — liệt kê ở no_formula_mpcty.
"""
import numpy as np
import pandas as pd

COVER = {("Amazon", "US"), ("Amazon", "CAN"), ("Wayfair", "US"), ("Wayfair", "CAN"), ("Shopify", "US")}
CTYCUR = {"US": "USD", "CAN": "CAD", "AUS": "AUD"}


def _num(x):
    v = pd.to_numeric(x, errors="coerce")
    return 0.0 if pd.isna(v) else float(v)


def _sheet(x, name, key_col=0, hdr=1):
    d = pd.read_excel(x, name, header=None)
    rates = d.iloc[0]
    h = d.iloc[hdr].astype(str).str.strip().tolist()
    seen, h2 = {}, []
    for c in h:                      # tên cột trùng (vd 'List price') -> giữ cột đầu, đổi tên cột sau
        seen[c] = seen.get(c, 0) + 1
        h2.append(c if seen[c] == 1 else f"{c}.{seen[c]}")
    h = h2
    t = d.iloc[hdr + 1:].copy(); t.columns = h
    t = t[t[h[key_col]].notna()]
    t[h[key_col]] = t[h[key_col]].astype(str).str.strip()
    return t.drop_duplicates(h[key_col], keep="first").set_index(h[key_col]), dict(zip(h, rates))


class RateCardLayoutError(ValueError):
    pass


NEED_SHEETS_V2 = ["US-FBA", "CA-FBA", "US-WF Megsu", "CA-WF 1"]
NEED_SHEETS = ["COGS Auto", "US-FBA", "CA-FBA", "US-WF- megsu", "US-WF- Arozu", "CA - WF", "US-Shopify"]


def load_ratecard(path, log=print):
    x = pd.ExcelFile(path)
    if all(n in x.sheet_names for n in NEED_SHEETS_V2):
        return load_ratecard_v2(x)
    miss = [n for n in NEED_SHEETS if n not in x.sheet_names]
    if miss:
        raise RateCardLayoutError(
            f"File P&L không đúng bố cục ETL PL5 hỗ trợ (bố cục W38–W39 hoặc bố cục 10/2026). Thiếu sheet: {', '.join(miss)}. Sheet có trong file: {', '.join(x.sheet_names)}")
    cogs = pd.read_excel(x, "COGS Auto", header=1)
    cogs["Product SKU"] = cogs["Product SKU"].astype(str).str.strip()
    cogs = cogs.drop_duplicates("Product SKU", keep="first").set_index("Product SKU")
    out = {"cogs": cogs}
    for key, sh in [("us_fba", "US-FBA"), ("ca_fba", "CA-FBA"), ("us_wf_ms", "US-WF- megsu"), ("us_wf_az", "US-WF- Arozu"),
                    ("ca_wf", "CA - WF"), ("us_spf", "US-Shopify")]:
        t, r = _sheet(x, sh)
        out[key] = t; out[key + "_rates"] = r
    return out


def _split(parts, n):
    return sum(parts) / n


def _rate(rates, col):
    return _num(rates.get(col))


def build_pl5(D, rc, camp_spend, rates, prev_pl5, why, log=print):
    if rc.get("layout") == "v2":
        return build_pl5_v2(D, rc, camp_spend, rates, prev_pl5, why, log)
    """camp_spend: {(grp, mp, cty): [các khoản chi USD]} — từ etl.ads.sem_by_group."""
    fxc = {"US": 1.0, "CAN": rates["CAD"], "AUS": rates["AUD"]}
    cogs = rc["cogs"]
    base = [r for r in D["sku"] if r["q"] > 0]
    scope_rows = [r for r in base if (r["mp"], r["cty"]) in COVER]
    # số dòng SKU có bán trong từng ô nhóm × sàn × quốc gia (để chia đều SEM)
    n_cell = {}
    for r in scope_rows:
        n_cell[(r["grp"], r["mp"], r["cty"])] = n_cell.get((r["grp"], r["mp"], r["cty"]), 0) + 1
    # Wayfair: chi phí chia đều cho SỐ SKU của nhóm có trong sheet kênh (US-WF- megsu / CA - WF), không phụ thuộc SKU có bán hay không
    g_of = {r["sku"]: r["grp"] for r in D["sku_meta"]}
    n_wf = {}
    for cty_, key in (("US", "us_wf_ms"), ("CAN", "ca_wf")):
        for sk in rc[key].index:
            if sk in g_of:
                n_wf[(g_of[sk], cty_)] = n_wf.get((g_of[sk], cty_), 0) + 1
    rows, raws, missing, nof = [], [], [], []
    rf_a = {"US": _rate(rc["us_fba_rates"], "Ref. Fee"), "CAN": _rate(rc["ca_fba_rates"], "Ref. Fee")}
    for r in sorted(base, key=lambda x: (x["sku"], x["mp"], x["cty"])):
        mp, cty, sku, q, rev = r["mp"], r["cty"], r["sku"], r["q"], r["r"]
        if (mp, cty) not in COVER:
            nof.append([mp, cty, rev]); continue
        fx = fxc[cty]
        if sku not in cogs.index:
            missing.append({"sku": sku, "mp": mp, "cty": cty, "r": rev}); continue
        cg = _num(cogs.at[sku, "COGS US"]) if cty == "US" else _num(cogs.at[sku, "COGS CA"]) * fx
        if mp == "Amazon":
            sh, rt = (rc["us_fba"], rc["us_fba_rates"]) if cty == "US" else (rc["ca_fba"], rc["ca_fba_rates"])
            if sku not in sh.index:
                missing.append({"sku": sku, "mp": mp, "cty": cty, "r": rev}); continue
            p = rev / q / fx
            ref = (0.15 * min(p, 200) + 0.10 * max(p - 200, 0)) * q * fx
            ful = (_num(sh.at[sku, "Ship2AMZ"]) + _num(sh.at[sku, "FBA F.ment"])) * q * fx
            ret, wh, op = _rate(rt, "Return") * rev, _rate(rt, next(c for c in rt if str(c).lower() == "wh fee")) * rev, _rate(rt, next(c for c in rt if str(c).lower() == "op fee")) * rev
        elif mp == "Wayfair":
            if cty == "US":
                sh, rt = rc["us_wf_ms"], rc["us_wf_ms_rates"]; col = "Ship2CG"
            else:
                sh, rt = rc["ca_wf"], rc["ca_wf_rates"]; col = "Ship2CG"
            ref = _rate(rt, "Ref. Fee") * rev
            ful = (_num(sh.at[sku, col]) if sku in sh.index else 0.0) * q * fx
            opc = "OP Fee" if "OP Fee" in rt else "Other fee"
            ret, wh, op = _rate(rt, "Return") * rev, _rate(rt, "WH Fee") * rev, _rate(rt, opc) * rev
        else:  # Shopify US
            sh, rt = rc["us_spf"], rc["us_spf_rates"]
            if sku not in sh.index:
                missing.append({"sku": sku, "mp": mp, "cty": cty, "r": rev}); continue
            ref = _rate(rt, "Ref. Fee") * rev
            ful = _num(sh.at[sku, "Shipping cost"]) * q
            ret, wh, op = _rate(rt, "Return") * rev, _rate(rt, "Other fee") * rev, 0.0
        if mp == "Amazon":
            sem = _split(camp_spend.get((r["grp"], mp, cty), []), n_cell[(r["grp"], mp, cty)])
        elif mp == "Wayfair":
            sem = _split(camp_spend.get((r["grp"], mp, cty), []), max(n_wf.get((r["grp"], cty), 0), 1))
        else:
            sem = 0.0
        cg *= q
        tong = cg + ref + sem + ret + wh + op + ful
        raws.append({"r": rev, "cogs": cg, "ref_fee": ref, "sem": sem, "return_fee": ret, "wh_fee": wh, "op_fee": op,
                     "fulfill": ful, "profit": rev - tong})
        rows.append({"sku": sku, "grp": r["grp"], "mp": mp, "cty": cty, "q": q, "r": round(rev, 2), "cogs": round(cg, 2),
                     "ref_fee": round(ref, 2), "sem": round(sem, 2), "return_fee": round(ret, 2), "wh_fee": round(wh, 2),
                     "op_fee": round(op, 2), "fulfill": round(ful, 2), "tong_cp": round(tong, 2), "profit": round(rev - tong, 2),
                     "cur_loc": CTYCUR[cty]})
    return _finish(rows, base, missing, nof, prev_pl5, why)


def _finish(rows, base, missing, nof, prev_pl5, why):
    tot = {k: round(sum(x[k] for x in rows), 2) for k in ("r", "cogs", "ref_fee", "sem", "return_fee", "wh_fee", "op_fee", "fulfill", "profit")}
    tot["margin"] = round(tot["profit"] / tot["r"] * 100, 2) if tot["r"] else None
    def grp_by(keyf):
        out = {}
        for x in rows:
            a = out.setdefault(keyf(x), {"r": 0.0, "profit": 0.0, "q": 0})
            a["r"] += x["r"]; a["profit"] += x["profit"]; a["q"] += x["q"]
        return {k: {"r": round(a["r"], 2), "profit": round(a["profit"], 2), "q": a["q"],
                    "margin": round(a["profit"] / a["r"] * 100, 2) if a["r"] else None} for k, a in sorted(out.items())}
    all_r = sum(r["r"] for r in base)
    # Cảnh báo: SKU × sàn × quốc gia có giá bán bình quân/cái thấp hơn COGS/cái (bán là lỗ trước cả phí sàn và quảng cáo)
    below = sorted(({"sku": x["sku"], "grp": x["grp"], "mp": x["mp"], "cty": x["cty"], "q": x["q"],
                     "price": round(x["r"] / x["q"], 2), "cogs_u": round(x["cogs"] / x["q"], 2), "gap": round(x["cogs"] - x["r"], 2)}
                    for x in rows if x["q"] > 0 and x["cogs"] > x["r"] + 0.005), key=lambda z: -z["gap"])
    return {"available": True, "below_cogs": below, "coverage_pct": round(tot["r"] / all_r * 100, 1) if all_r else None, "total": tot,
            "by_mpcty": grp_by(lambda x: f'{x["mp"]}|{x["cty"]}'), "by_grp": grp_by(lambda x: x["grp"]), "rows": rows,
            "missing_sku_fee": missing, "no_formula_mpcty": nof, "why": why,
            "prev_total": prev_pl5["total"] if prev_pl5 else None}


def why_text(pl, wk):
    cov = pl["coverage_pct"]; t = pl["total"]
    if pl.get("_v2"):
        return (f'Profit PL5 tuần W{wk} = Doanh thu − (COGS + Ref fee + SEM + Warehouse fee + Fulfillment), theo file P&L bố cục 10/2026 (không còn so sánh trực tiếp với W38–W39); bỏ OP fee, Other fee, Promotion, GST. '
                'COGS = giá vốn đơn vị trong đúng sheet của từng kênh × sàn × quốc gia (chuẩn 01/10/2026) × số lượng; CAN (CAD) và AUS (AUD) quy đổi sang USD theo tỷ giá cố định của báo cáo. Ref fee: Amazon/Walmart 15% đến $200 + 10% phần vượt, Wayfair 4%. KHÔNG tính phí Return. Warehouse fee = 6% doanh thu, áp cho mọi kênh. '
                'Fulfillment chỉ tính cho hàng Amazon FBA (cột FBA F.ment sheet US-FBA / CA-FBA); Wayfair, Walmart, Shopify và Amazon Úc không tính. '
                'SEM Amazon/Wayfair = chi phí quảng cáo thật theo báo cáo chiến dịch, chia đủ 100% cho các SKU có bán trong từng nhóm × sàn × quốc gia (phần không gán được vào dòng nào trừ thẳng vào tổng). '
                'Shopify (chưa có báo cáo quảng cáo): Doanh thu − (COGS FBM + phí Shopify 4% doanh thu + SEM 15% doanh thu), SEM Shopify là số ước tính. Walmart chưa có số quảng cáo nên SEM = 0. '
                f'Độ phủ {cov}% doanh thu tuần ({t["r"]:,.2f} USD); ô chưa có sheet kênh không suy đoán, xem danh sách bên dưới.')
    return (f'Profit PL5 tuần W{wk} tính theo cùng công thức đã dùng từ W38: COGS lấy từ sheet "COGS Auto" (COGS US/CA cơ bản, không theo account); '
            'Ref. Fee/Return/Warehouse Fee/OP Fee tính theo % trên doanh thu thật của tuần theo rate card từng kênh (Amazon Ref. Fee theo bậc 15% dưới $200 + 10% phần vượt; '
            'Wayfair Ref. Fee 4% cố định); phí fulfillment lấy đúng cột Ship2AMZ+FBA F.ment (Amazon) hoặc Ship2CG (Wayfair) theo SKU; '
            'SEM lấy chi phí quảng cáo thật — Wayfair phân bổ đều theo mã hàng trong cùng 1 nhóm (báo cáo PR), Amazon TẠM phân bổ đều chi phí theo nhóm×quốc gia cho các SKU có bán '
            '(chưa có báo cáo Advertised Product theo ASIN). '
            f'Độ phủ {cov}% doanh thu tuần ({t["r"]:,.2f} USD trên các ô có công thức); phần còn lại chưa tính vì thiếu công thức/dữ liệu phí (xem danh sách bên dưới), không suy đoán số cho phần thiếu.')


# ======================================================================================
# Bố cục P&L từ 10/2026 (file "P&L_Thu_Ngo_COGS_2026-10"): COGS và rate card nằm TRONG từng sheet kênh.
# Công thức theo đúng cột "Total Cost" của từng sheet:
#   Amazon FBA : COGS + Ref (15% đến 200, 10% phần vượt) + FBA F.ment + SEM + Return
#   Wayfair    : COGS + Ref + SEM + Return (+ Other fee nếu sheet có: Megsu US 6%)
#   Walmart US : COGS + Ref (bậc) + Shipping + SEM + Return + Other fee
#   Amazon AU  : COGS + Ref + SEM + Return + Promotion + Retail Shipping (sheet AU-FBM)
#   Shopify AU : COGS + Ref + SEM + Return + GST + Retail Shipping (sheet AU-Shopify)
# Không còn WH Fee / OP Fee / Ship2AMZ như bố cục cũ => wh_fee = 0; "Other fee"/Promotion/GST ghi vào op_fee.
# ======================================================================================
V2_CHANNELS = {  # (mp, cty): (sheet, kiểu ref, cột fulfill/ship per unit, cột % khác — BỎ, không còn tính OP/Other fee)
    ("Amazon", "US"): ("US-FBA", "tier", "FBA F.ment", []),
    ("Amazon", "CAN"): ("CA-FBA", "tier", "FBA F.ment", []),
    ("Wayfair", "US"): ("US-WF Megsu", "pct", None, []),
    ("Wayfair", "CAN"): ("CA-WF 1", "pct", None, []),
    ("Walmart", "US"): ("US-WM", "tier", None, []),          # Fulfillment chỉ tính cho hàng Amazon FBA
    ("Amazon", "AUS"): ("AU-FBM", "pct", None, []),
    # Shopify: Doanh thu − (COGS FBM + SEM 15% + Shipping Cost + Return 5%); COGS và ship lấy từ sheet FBM của quốc gia (Úc: sheet AU-Shopify)
    ("Shopify", "US"): ("US-FBM", "spf", None, []),
    ("Shopify", "CAN"): ("CA-FBM", "spf", None, []),
    ("Shopify", "AUS"): ("AU-Shopify", "spf", None, []),
}
SPF_SEM = 0.15
WH_FEE = 0.06    # Warehouse fee 6% doanh thu, áp cho mọi kênh (ghi vào cột wh_fee)
SPF_FEE = 0.04   # phí Shopify (cổng thanh toán/phí sàn) 4% doanh thu, ghi vào cột ref_fee
# Sheet phụ cùng kênh (tra COGS khi SKU không có ở sheet chính): Wayfair US có 2 tài khoản (Megsu / Arozu), Wayfair CAN có 2 khối.
V2_ALT = {("Wayfair", "US"): ["US-WF Arozu"], ("Wayfair", "CAN"): ["CA-WF 2"]}


def _norm(h):
    return " ".join(str(h).replace("\n", " ").split())


def _sheet2(x, name):
    d = pd.read_excel(x, name, header=None)
    h = [_norm(c) for c in d.iloc[1].tolist()]
    seen, h2 = {}, []
    for c in h:
        seen[c] = seen.get(c, 0) + 1
        h2.append(c if seen[c] == 1 else f"{c}.{seen[c]}")
    t = d.iloc[2:].copy(); t.columns = h2
    t = t[t[h2[0]].notna()]
    t[h2[0]] = t[h2[0]].astype(str).str.strip()
    t = t.drop_duplicates(h2[0], keep="first").set_index(h2[0])
    rates = {c: d.iloc[0, i] for i, c in enumerate(h2)}
    return t, rates, d.iloc[0].tolist()


def _col(cols, name):
    """Tên cột bắt đầu bằng `name` (vd 'Ref. Fee' khớp 'Ref. Fee 15% / 10% > $200'); None nếu không có."""
    for c in cols:
        if c == name or c.startswith(name + " ") or c.startswith(name + ".") and False:
            return c
    return next((c for c in cols if c.startswith(name)), None)


def load_ratecard_v2(x):
    out = {"layout": "v2"}
    for key, (sh, *_rest) in V2_CHANNELS.items():
        if sh in x.sheet_names:
            t, r, row0 = _sheet2(x, sh)
            out[key] = {"t": t, "rates": r, "row0": row0}
            out[key]["alt"] = []
            for sh2 in V2_ALT.get(key, []):
                if sh2 in x.sheet_names:
                    out[key]["alt"].append(_sheet2(x, sh2)[0])
    return out


def build_pl5_v2(D, rc, camp_spend, rates, prev_pl5, why, log=print):
    fxc = {"US": 1.0, "CAN": rates["CAD"], "AUS": rates["AUD"]}
    base = [r for r in D["sku"] if r["q"] > 0]
    cov = {k for k in V2_CHANNELS if k in rc}
    n_cell = {}
    for r in base:
        if (r["mp"], r["cty"]) in cov:
            n_cell[(r["grp"], r["mp"], r["cty"])] = n_cell.get((r["grp"], r["mp"], r["cty"]), 0) + 1
    g_of = {r["sku"]: r["grp"] for r in D["sku_meta"]}
    n_wf = {}
    for cty_ in ("US", "CAN"):
        ch = rc.get(("Wayfair", cty_))
        if ch is not None:
            for sk in ch["t"].index:
                if sk in g_of:
                    n_wf[(g_of[sk], cty_)] = n_wf.get((g_of[sk], cty_), 0) + 1
    rows, missing, nof = [], [], []
    for r in sorted(base, key=lambda x: (x["sku"], x["mp"], x["cty"])):
        mp, cty, sku, q, rev = r["mp"], r["cty"], r["sku"], r["q"], r["r"]
        key = (mp, cty)
        if key not in cov:
            nof.append([mp, cty, rev]); continue
        ch = rc[key]; t = ch["t"]; cols = list(t.columns)
        fx = fxc[cty]; sheet, kind, ful_col, other_cols = V2_CHANNELS[key]
        rt = ch["rates"]
        cg_src = t if sku in t.index else next((a for a in ch.get("alt", []) if sku in a.index), None)
        if cg_src is None:
            missing.append({"sku": sku, "mp": mp, "cty": cty, "r": rev}); continue
        ccols = list(cg_src.columns)
        cogs_c = _col(ccols, "COGS") if _col(ccols, "COGS (") is None else _col(ccols, "COGS (")
        row = t.loc[sku] if sku in t.index else None
        # COGS đúng sheet kênh × sàn × quốc gia, đơn giá theo tiền địa phương (CAD/AUD) × tỷ giá → USD
        cg = _num(cg_src.loc[sku][cogs_c]) * fx * q
        ful = (_num(row[_col(cols, ful_col)]) * q * fx) if (ful_col and row is not None and _col(cols, ful_col)) else 0.0
        ret = 0.0                                  # BỎ phí Return
        op = 0.0                                   # bỏ OP fee / Other fee / Promotion / GST
        if kind == "spf":                          # Shopify: không có phí sàn; SEM 15% và Return 5% doanh thu
            ref = SPF_FEE * rev
        else:
            ref_c = _col(cols, "Ref. Fee")
            if kind == "tier":
                thr, hi = _num(ch["row0"][2]) or 200.0, _num(ch["row0"][3]) or 0.10
                lo = _num(rt[ref_c]) or 0.15
                p = rev / q / fx
                ref = (lo * min(p, thr) + hi * max(p - thr, 0)) * q * fx
            else:
                ref = _num(rt[ref_c]) * rev
        if mp == "Amazon":
            sem = _split(camp_spend.get((r["grp"], mp, cty), []), n_cell[(r["grp"], mp, cty)])
        elif mp == "Wayfair":
            sem = _split(camp_spend.get((r["grp"], mp, cty), []), max(n_wf.get((r["grp"], cty), 0), 1))
        elif mp == "Shopify":
            sem = SPF_SEM * rev                    # chưa có báo cáo quảng cáo Shopify: ước tính 15% doanh thu
        else:
            sem = 0.0
        wh = WH_FEE * rev
        tong = cg + ref + sem + ret + op + ful + wh
        rows.append({"sku": sku, "grp": r["grp"], "mp": mp, "cty": cty, "q": q, "r": round(rev, 2), "cogs": round(cg, 2),
                     "ref_fee": round(ref, 2), "sem": round(sem, 2), "return_fee": round(ret, 2), "wh_fee": round(wh, 2),
                     "op_fee": round(op, 2), "fulfill": round(ful, 2), "tong_cp": round(tong, 2), "profit": round(rev - tong, 2),
                     "cur_loc": CTYCUR[cty]})
    # SEM = chi phí quảng cáo THẬT, phân bổ đủ 100%: mỗi ô nhóm × sàn × quốc gia chia cho các SKU CÓ BÁN trong ô (không chia cho SKU không bán nên không bị rơi mất);
    # phần của ô không có SKU bán (hoặc nhóm không có dòng nào) chia theo doanh thu cho các SKU cùng sàn × quốc gia; còn không có dòng nào thì ghi riêng ở sem_unalloc.
    import collections as _c
    cell = _c.defaultdict(list)
    for x in rows:
        cell[(x["grp"], x["mp"], x["cty"])].append(x)
    resid = _c.defaultdict(float)
    for k, parts in camp_spend.items():
        S = float(sum(parts))
        if k in cell:
            for x in cell[k]:
                x["sem"] = round(S / len(cell[k]), 2)
        else:
            resid[(k[1], k[2])] += S
    unalloc = 0.0
    for (mp_, cty_), S in resid.items():
        rr = [x for x in rows if x["mp"] == mp_ and x["cty"] == cty_]
        tr = sum(x["r"] for x in rr)
        if rr and tr > 0:
            for x in rr:
                x["sem"] = round(x["sem"] + S * x["r"] / tr, 2)
        else:
            unalloc += S
    for x in rows:
        x["tong_cp"] = round(x["cogs"] + x["ref_fee"] + x["sem"] + x["return_fee"] + x["op_fee"] + x["fulfill"] + x["wh_fee"], 2)
        x["profit"] = round(x["r"] - x["tong_cp"], 2)
    res = _finish(rows, base, missing, nof, prev_pl5, why)
    if unalloc:
        t = res["total"]
        t["sem_unalloc"] = round(unalloc, 2); t["profit"] = round(t["profit"] - unalloc, 2)
        t["margin"] = round(t["profit"] / t["r"] * 100, 2) if t["r"] else None
    res["sem_full"] = True
    return res
