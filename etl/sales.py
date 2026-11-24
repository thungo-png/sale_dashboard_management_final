"""
ETL bán hàng (đợt 1): cập nhật D của kỳ trước bằng số liệu tuần mới.

Nguyên tắc (đã đối chiếu với D của W39):
 - Chỉ lấy các ngày trong [d0, d1] của tuần báo cáo từ file bán hàng. Các ngày trước d0 GIỮ NGUYÊN số đã công bố ở kỳ trước
   (file mới có thể đã hiệu chỉnh số cũ — không ghi đè để WoW nhất quán với báo cáo kỳ trước).
 - Tuần bắt đầu Chủ Nhật, kết thúc Thứ Bảy; đánh số theo ANCHOR (xem 04-bao-cao-tuan-notes.md).
 - Quy đổi USD bằng MỘT tỷ giá cố định (constant currency) lấy từ D["fx"]["rates"] của kỳ trước, trừ khi cấu hình ghi đè.
 - Các chuỗi Tháng / Quý / YTD = số kỳ trước + tổng các ngày mới (kỳ trước kết thúc đúng ngày d0-1).
"""
import copy
import numpy as np
import pandas as pd

ANCHOR = pd.Timestamp("2025-12-28")  # Chủ Nhật mở đầu tuần 1/2026
WINDOW_WEEKS = 12
CTYCUR = {"US": "USD", "CAN": "CAD", "AUS": "AUD"}


def wkno(ts):
    return int((ts - ANCHOR).days // 7) + 1


def wk_start(w):
    return ANCHOR + pd.Timedelta(days=7 * (w - 1))


def wklab(w):
    a = wk_start(w)
    b = a + pd.Timedelta(days=6)
    return a.strftime("%d/%m") + "–" + b.strftime("%d/%m")


def qlabel(ts):
    return f"{ts.year}Q{(ts.month - 1) // 3 + 1}"


def mlabel(ts):
    return ts.strftime("%Y-%m")


# ------------------------------------------------------------------ đọc file
def pick_sales_file(folder, csv_name="data_1.csv", xlsx_name="data_1.xlsx"):
    """Có data_1.csv thì dùng CSV, không thì dùng data_1.xlsx."""
    import os
    c, x = os.path.join(folder, csv_name), os.path.join(folder, xlsx_name)
    return c if os.path.exists(c) else x


def _channel_to_cty_mp(ch):
    ch = str(ch)
    low = ch.lower()
    mp = "Amazon" if low.startswith("amz") else "Wayfair" if low.startswith("wayfair") else "Shopify"
    cty = "AUS" if ("australia" in low or "com.au" in low or "comau" in low) else "US"
    return cty, mp


def _read_sales_raw(path):
    """xlsx: Sheet1 skiprows=2 (định dạng data.xlsx). csv: report_date, channel, product_group, product_sku, total_quantity
    (chỉ có số lượng — không có doanh thu/phí nên r, rfc, fee = 0)."""
    if str(path).lower().endswith(".csv"):
        C = pd.read_csv(path)
        cm = C["channel"].map(_channel_to_cty_mp)
        S = pd.DataFrame({"Date": C["report_date"], "Country": [x[0] for x in cm], "Marketplace": [x[1] for x in cm],
                          "Group Name": C["product_group"], "SKU": C["product_sku"],
                          "Quantity": pd.to_numeric(C["total_quantity"], errors="coerce").fillna(0)})
        for c in ["Revenue", "Quantity FC", "Revenue FC", "DGMK Fee FC"]:
            S[c] = 0.0
        return S
    return pd.read_excel(path, sheet_name="Sheet1", skiprows=2)


def load_sales(path, rates, group_norm=None):
    """Đọc dữ liệu bán hàng (.xlsx Sheet1 skiprows=2, hoặc .csv). rates: {"CAD":x,"AUD":y}. Trả DataFrame đã quy đổi USD."""
    S = _read_sales_raw(path)
    S = S.rename(columns={"Date": "date", "Country": "cty", "Marketplace": "mp", "Group Name": "grp", "SKU": "sku",
                          "Quantity": "q", "Revenue": "r_loc", "Quantity FC": "qfc", "Revenue FC": "rfc_loc",
                          "DGMK Fee FC": "fee_loc"})
    S["date"] = pd.to_datetime(S["date"])
    S["cty"] = S["cty"].replace({"CA": "CAN"})
    if group_norm:
        S["grp"] = S["grp"].replace(group_norm)
    fx = {"US": 1.0, "CAN": rates["CAD"], "AUS": rates["AUD"]}
    S["fx"] = S["cty"].map(fx)
    for c in ["r", "rfc", "fee"]:
        S[c] = S[c + "_loc"] * S["fx"]
    S["sku"] = S["sku"].astype(str).str.strip()
    return S


def coverage(S):
    return S.date.min(), S.date.max(), S.date.nunique(), len(S)


def _agg(df, keys):
    g = df.groupby(keys, sort=True).agg(q=("q", "sum"), r=("r", "sum"), qfc=("qfc", "sum"), rfc=("rfc", "sum"),
                                         fee=("fee", "sum"), r_loc=("r_loc", "sum")).reset_index()
    for c in ["r", "qfc", "rfc", "fee", "r_loc"]:
        g[c] = g[c].round(2)
    g["q"] = g["q"].round().astype(int)
    return g


def _nz(*vals):
    return any(abs(v) > 1e-12 for v in vals)


def _cell3(row):
    return {"q": int(row["q"]), "r": round(float(row["r"]), 2), "rfc": round(float(row["rfc"]), 2)}


# ------------------------------------------------------------------ khối KPI tuần
def week_blocks(S, d0, d1, prev):
    cur = S[(S.date >= d0) & (S.date <= d1)]
    combos = S[["cty", "mp"]].drop_duplicates()

    cell = []
    a = _agg(cur, ["cty", "mp"]).set_index(["cty", "mp"])
    for cty, mp in sorted(map(tuple, combos.values), key=lambda x: (x[0], x[1])):
        if (cty, mp) in a.index:
            x = a.loc[(cty, mp)]
            cell.append({"cty": cty, "mp": mp, "q": int(x.q), "r": float(x.r), "qfc": float(x.qfc), "rfc": float(x.rfc),
                         "feefc": float(x.fee), "r_loc": float(x.r_loc), "cur_loc": CTYCUR[cty], "cur": "USD"})
        else:
            cell.append({"cty": cty, "mp": mp, "q": 0, "r": 0.0, "qfc": 0.0, "rfc": 0.0, "feefc": 0.0, "r_loc": 0.0,
                         "cur_loc": CTYCUR[cty], "cur": "USD"})

    bygrp = [{"grp": x.grp, "q": int(x.q), "r": float(x.r), "qfc": float(x.qfc), "rfc": float(x.rfc)}
             for x in _agg(cur, ["grp"]).itertuples()]
    bygrp_cell = [{"grp": x.grp, "mp": x.mp, "cty": x.cty, "r": float(x.r), "rfc": float(x.rfc), "q": int(x.q)}
                  for x in _agg(cur, ["grp", "mp", "cty"]).itertuples()]
    sku = [{"sku": x.sku, "grp": x.grp, "mp": x.mp, "cty": x.cty, "q": int(x.q), "qfc": float(x.qfc), "r": float(x.r),
            "rfc": float(x.rfc), "feefc": float(x.fee)}
           for x in _agg(cur, ["sku", "grp", "mp", "cty"]).sort_values(["sku", "mp", "cty"]).itertuples()]

    out = {"cell": cell, "bygrp": bygrp, "bygrp_cell": bygrp_cell, "sku": sku}
    # tuần trước = số ĐÃ CÔNG BỐ ở kỳ trước (không tính lại từ file mới)
    if prev:
        out["cell_prev"] = [{k: c[k] for k in ("cty", "mp", "q", "r", "qfc", "rfc")} for c in prev["cell"]]
        out["bygrp_prev"] = copy.deepcopy(prev["bygrp"])
    return out


# ------------------------------------------------------------------ weekly_grp / weekfc / monthly / quarterly / ytd
def update_aggregates(D, S, d0, d1, wk):
    cur = S[(S.date >= d0) & (S.date <= d1)].copy()
    lab = wklab(wk)

    # weekly_grp: cửa sổ 12 tuần
    lo = wk - WINDOW_WEEKS + 1
    rows = [r for r in D.get("weekly_grp", []) if lo <= r["W"] < wk]
    for x in _agg(cur, ["grp"]).itertuples():
        if _nz(x.q, x.r, x.qfc, x.rfc):
            rows.append({"grp": x.grp, "W": wk, "q": int(x.q), "r": float(x.r), "qfc": float(x.qfc), "rfc": float(x.rfc)})
    D["weekly_grp"] = sorted(rows, key=lambda r: (r["grp"], r["W"]))

    # weekfc: toàn năm
    t = _agg(cur.assign(_k=1), ["_k"]).iloc[0]
    row = {"wk": wk, "lab": lab, "nd": int(cur.date.nunique()), "q": int(t.q), "r": float(t.r), "qfc": float(t.qfc),
           "rfc": float(t.rfc), "ach": round(float(t.r) / float(t.rfc) * 100, 2) if t.rfc else 0.0}
    wf = [w for w in D["weekfc"]["all"] if w["wk"] != wk] + [row]
    D["weekfc"]["all"] = sorted(wf, key=lambda w: w["wk"])

    # monthly / quarterly (theo mp), ytd (theo cty×mp): cộng thêm số của các ngày mới
    cur["M"] = cur.date.map(mlabel)
    cur["Q"] = cur.date.map(qlabel)

    def add(block, keyname, keycols, frame_keys):
        idx = {tuple(r[k] for k in keycols): r for r in block}
        for x in _agg(cur, frame_keys).itertuples():
            k = tuple(getattr(x, c) for c in keycols)
            r = idx.get(k)
            if r is None:
                r = {c: getattr(x, c) for c in keycols}
                r.update({"q": 0, "r": 0.0, "qfc": 0.0, "rfc": 0.0})
                block.append(r)
                idx[k] = r
            r["q"] += int(x.q)
            for f in ("r", "qfc", "rfc"):
                r[f] = round(r[f] + float(getattr(x, f)), 2)
        return block

    D["monthly"] = sorted(add(D["monthly"], "M", ["M", "mp"], ["M", "mp"]), key=lambda r: (r["M"], r["mp"]))
    D["quarterly"] = sorted(add(D["quarterly"], "Q", ["Q", "mp"], ["Q", "mp"]), key=lambda r: (r["Q"], r["mp"]))
    cur["_y"] = 1
    D["ytd"] = sorted(add(D["ytd"], None, ["cty", "mp"], ["cty", "mp"]), key=lambda r: (r["cty"], r["mp"]))


# ------------------------------------------------------------------ chuỗi thời gian ts_*
def _families(cur):
    """Trả danh sách (đường dẫn trong ts_*, hàm tên) -> DataFrame tên chuỗi."""
    c = cur
    sep = " · "
    return [
        (("ts_ov", "mp"), c["mp"]),
        (("ts_ov", "cty"), c["cty"]),
        (("ts_ov", "mpcty"), c["mp"] + sep + c["cty"]),
        (("ts_grp", None), c["grp"]),
        (("ts_grpcell", "grp_mp"), c["grp"] + sep + c["mp"]),
        (("ts_grpcell", "grp_cty"), c["grp"] + sep + c["cty"]),
        (("ts_sku", "l1"), c["sku"]),
        (("ts_sku", "l2"), c["sku"] + sep + c["cty"]),
        (("ts_sku", "l3"), c["sku"] + sep + c["mp"] + sep + c["cty"]),
    ]


def _fam_dict(D, path, g):
    top, fam = path
    node = D[top].setdefault(g, {})
    if fam is not None:
        node = node.setdefault(fam, {})
    return node


def _add_cell(ser, per, c):
    x = ser.get(per)
    if x is None:
        ser[per] = {"q": int(c["q"]), "r": round(float(c["r"]), 2), "rfc": round(float(c["rfc"]), 2)}
    else:
        x["q"] += int(c["q"])
        x["r"] = round(x["r"] + float(c["r"]), 2)
        x["rfc"] = round(x["rfc"] + float(c["rfc"]), 2)


def update_ts(D, S, d0, d1, wk):
    cur = S[(S.date >= d0) & (S.date <= d1)].copy()
    cur["day"] = cur.date.dt.strftime("%Y-%m-%d")
    cur["W"] = cur.date.map(wkno)
    cur["M"] = cur.date.map(mlabel)
    cur["Q"] = cur.date.map(qlabel)
    win_start = wk_start(wk - WINDOW_WEEKS + 1)
    days = [(win_start + pd.Timedelta(days=i)).strftime("%Y-%m-%d") for i in range((d1 - win_start).days + 1)]
    weeks = list(range(wk - WINDOW_WEEKS + 1, wk + 1))
    D.setdefault("ts_labels", {})

    for path, names in _families(cur):
        t = cur.assign(_n=names.values)
        for g, per_col in (("D", "day"), ("W", "W"), ("M", "M"), ("Q", "Q")):
            ser_all = _fam_dict(D, path, g)
            agg = t.groupby(["_n", per_col]).agg(q=("q", "sum"), r=("r", "sum"), rfc=("rfc", "sum")).reset_index()
            for x in agg.itertuples():
                if not _nz(x.q, x.r, x.rfc):
                    continue
                per = str(getattr(x, per_col)) if g != "W" else str(int(getattr(x, per_col)))
                ser = ser_all.setdefault(x._1, {})
                if g == "D":
                    ser[per] = {"q": int(x.q), "r": round(float(x.r), 2), "rfc": round(float(x.rfc), 2)}  # ghi đè
                elif g == "W":
                    # tuần = tổng các ngày ĐÃ LÀM TRÒN (khớp cách D mẫu tính)
                    dser = _fam_dict(D, path, "D").get(x._1, {})
                    tot = {"q": 0, "r": 0.0, "rfc": 0.0}
                    for dd, c in dser.items():
                        if wk_start(wk).strftime("%Y-%m-%d") <= dd <= d1.strftime("%Y-%m-%d"):
                            tot["q"] += c["q"]; tot["r"] += c["r"]; tot["rfc"] += c["rfc"]
                    ser[per] = {"q": tot["q"], "r": round(tot["r"], 2), "rfc": round(tot["rfc"], 2)}
                else:
                    _add_cell(ser, per, {"q": x.q, "r": x.r, "rfc": x.rfc})  # cộng dồn
            # cắt cửa sổ cho D và W
            if g == "D":
                keep = set(days)
                for n in list(ser_all):
                    ser_all[n] = {k: v for k, v in ser_all[n].items() if k in keep}
                    if not ser_all[n]:
                        del ser_all[n]
            elif g == "W":
                keep = {str(w) for w in weeks}
                for n in list(ser_all):
                    ser_all[n] = {k: v for k, v in ser_all[n].items() if k in keep}
                    if not ser_all[n]:
                        del ser_all[n]

    tl = D["ts_labels"]
    tl["D"] = days
    tl["W"] = weeks
    for key, vals in (("M", sorted(cur.M.unique())), ("Q", sorted(cur.Q.unique()))):
        tl[key] = sorted(set(tl.get(key, [])) | set(vals))


# ------------------------------------------------------------------ meta
def update_meta(D, d0, d1, wk, S):
    m = D["meta"]
    weeks = list(range(wk - WINDOW_WEEKS + 1, wk + 1))
    m["weeks"] = weeks
    m["weeklab"] = {str(w): wklab(w) for w in weeks}
    m["d0"], m["d1"] = d0.strftime("%Y-%m-%d"), d1.strftime("%Y-%m-%d")
    m["ndays"] = int((d1 - d0).days) + 1
    m["ytd1"] = m["d1"]
    m["week_no"] = wk
    m["curm"] = f"tuần W{wk} ({wklab(wk)})"
    m["months"] = sorted(set(m.get("months", [])) | {mlabel(d1)})
    m["quarters"] = sorted(set(m.get("quarters", [])) | {qlabel(d1)})


# ------------------------------------------------------------------ điểm vào
def build_sales(prev, sales_path, d1=None, rates=None, group_norm=None, log=print):
    """prev: dict D kỳ trước. d1: Thứ Bảy cuối tuần báo cáo (mặc định: Thứ Bảy gần nhất có đủ 7 ngày trong file)."""
    D = copy.deepcopy(prev)
    rates = rates or D["fx"]["rates"]
    S = load_sales(sales_path, rates, group_norm)
    lo, hi, nd, n = coverage(S)
    log(f"[sales] file {lo.date()}→{hi.date()}, {nd} ngày, {n} dòng")

    if d1 is None:
        sat = [d for d in pd.date_range(lo, hi) if d.dayofweek == 5]  # Thứ Bảy
        d1 = sat[-1]
    d1 = pd.Timestamp(d1)
    d0 = d1 - pd.Timedelta(days=6)
    wk = wkno(d0)
    if d0 < lo:
        raise ValueError(f"File bán hàng không phủ đủ tuần {d0.date()}→{d1.date()}")
    pw = prev["meta"].get("week_no")
    if pw is not None and pw >= wk:
        raise ValueError(f"Kỳ trước đã là W{pw} (>= W{wk}). Build lại sẽ cộng dồn tháng/quý/YTD hai lần. "
                         f"Hãy xoá kỳ W{pw} hoặc chọn kỳ nền là tuần ngay trước W{wk}.")
    if pw is not None and pw != wk - 1:
        log(f"[sales] CẢNH BÁO: kỳ trước là W{pw}, kỳ này là W{wk} — thiếu {wk - 1 - pw} tuần ở giữa.")
    log(f"[sales] tuần W{wk}: {d0.date()} → {d1.date()}")

    D.update(week_blocks(S, d0, d1, prev))
    update_aggregates(D, S, d0, d1, wk)
    update_ts(D, S, d0, d1, wk)
    update_meta(D, d0, d1, wk, S)

    t = D["weekfc"]["all"][-1]
    log(f"[sales] W{wk}: q={t['q']} r={t['r']:.2f} USD rfc={t['rfc']:.2f} ach={t['ach']}%")
    return D, S, (d0, d1, wk)
