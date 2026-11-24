"""
ETL Long-term Storage (đợt 2): D["lt"] từ báo cáo Inventory Age của FBA (US/CAN) và CastleGate (ARZ/MS/DHI).

Quy tắc (đối chiếu với D của W39):
 - 5 mốc tuổi: 0–90 · 91–180 · 181–270 · 271–365 · 366+.
 - CastleGate: cột 10 ngày gộp 9/9/9/10/1 cột vào 5 mốc (361-365 thuộc mốc 271–365; '366+ days' là mốc cuối).
 - FBA: 4 cột inv-age chuẩn; mốc cuối = 366-455 + 456-plus (US) hoặc 365-plus (CAN).
 - Bảng 'summary' = toàn bộ báo cáo của tài khoản (không lọc SKU). Bảng 'sku' chỉ gồm SKU có Group (sheet Listing) thuộc 8 nhóm chuẩn.
 - Ánh xạ mã: FBA dùng cột 'FBA SKU'; CastleGate ARZ dùng 'SKU - WF ARZ', MS dùng 'SKU - WF MSU', DHI dùng HỢP của mọi cột mã (SKU, FBM SKU, FBA SKU, SKU - WF MSU, SKU - WF ARZ).
 - Kit Tree House (B4F1/GDWQ, chỉ ở ARZ: B4F11/12/13, GDWQ1/2/3): gộp thành 1 bộ = MIN từng mốc tuổi.
 - Sắp xếp: lượng ≥271 ngày giảm dần, rồi tổng giảm dần, rồi sku tăng dần, rồi tài khoản giảm dần.
 - prev_tot / delta lấy từ D['lt'] của kỳ trước (không có -> 0).
"""
import io
import numpy as np
import pandas as pd

LABELS = ["0–90", "91–180", "181–270", "271–365", "366+"]
CG_ACCT = {"ARZ": ("US", "SKU - WF ARZ"), "DHI": ("CAN", "*"), "MS": ("US", "SKU - WF MSU")}
FBA_ACCT = {"US": "US (FBA chung)", "CAN": "CAN (FBA chung)"}


def read_castlegate(path):
    txt = open(path, encoding="utf-8-sig").read().splitlines()
    i = next(k for k, l in enumerate(txt) if l.startswith("Part Number"))
    df = pd.read_csv(io.StringIO("\n".join(txt[i:])))
    df = df[df["Part Number"].notna()].copy()
    df["Part Number"] = df["Part Number"].astype(str).str.strip()
    bins = [c for c in df.columns if "days" in c and "exposure" not in c.lower()]
    assert len(bins) == 38, f"CastleGate: cần 38 cột tuổi, thấy {len(bins)}"
    for c in bins:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    parts = [bins[0:9], bins[9:18], bins[18:27], bins[27:37], bins[37:38]]
    for k, cols in enumerate(parts):
        df[f"b{k}"] = df[cols].sum(axis=1)
    return df[["Part Number"] + [f"b{k}" for k in range(5)]]


def read_fba(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["sku"] = df["sku"].astype(str).str.strip()
    num = lambda c: pd.to_numeric(df[c], errors="coerce").fillna(0) if c in df.columns else 0
    df["b0"], df["b1"], df["b2"], df["b3"] = (num("inv-age-0-to-90-days"), num("inv-age-91-to-180-days"),
                                              num("inv-age-181-to-270-days"), num("inv-age-271-to-365-days"))
    df["b4"] = num("inv-age-366-to-455-days") + num("inv-age-456-plus-days") + num("inv-age-365-plus-days")
    return df[["sku"] + [f"b{k}" for k in range(5)]]


def _bk(df):
    return [int(round(df[f"b{k}"].sum())) for k in range(5)]


GROUP_NORM = {"Acacia - Alma, Wilma Dinning Table": "Acacia - Alma Dinning Table"}


def load_listing(master_path, groups):
    L = pd.read_excel(master_path, sheet_name="Listing")
    L["Group"] = L["Group"].replace(GROUP_NORM)
    for c in ["SKU", "Product Name", "Group", "FBA SKU", "FBM SKU", "SKU - WF MSU", "SKU - WF ARZ"]:
        L[c] = L[c].astype("object").where(L[c].notna(), None)
        L[c] = L[c].map(lambda v: str(v).strip() if v is not None and str(v).strip() not in ("", "nan") else None)
    return L[L["Group"].isin(set(groups))].copy()


def _rows_for(df, key, mapcol, L, acct, cty, prev_idx):
    """df: bảng có cột key + b0..b4. Trả list các dòng sku chuẩn."""
    cols = ["SKU", "FBM SKU", "FBA SKU", "SKU - WF MSU", "SKU - WF ARZ"] if mapcol == "*" else [mapcol]
    L = L.reset_index(drop=True)
    m = {}  # mã -> chỉ số dòng Listing (SKU trùng 2 dòng có tên khác nhau: tên lấy theo dòng khớp mã)
    for c in cols:
        for i, v in L[c].items():
            if v and v not in m:
                m[v] = i
    d = df.copy()
    d["_row"] = d[key].map(m)
    d["_sku"] = d["_row"].map(lambda i: L.loc[int(i), "SKU"] if pd.notna(i) else None)
    # kit CastleGate: code của parent (vd B4F11) -> các box = code[:-1] + 1..3
    if mapcol == "SKU - WF ARZ":
        for i, (s, v) in enumerate(zip(L["SKU"], L[mapcol])):
            if v and s in ("B4F1", "GDWQ"):
                codes = [v[:-1] + str(k) for k in (1, 2, 3)]
                boxes = d[d[key].isin(codes)]
                if len(boxes) == len(codes):
                    d = d[~d[key].isin(codes)]
                    mn = boxes[[f"b{k}" for k in range(5)]].min()
                    d = pd.concat([d, pd.DataFrame([{key: codes[0], **mn.to_dict(), "_sku": s, "_row": i}])], ignore_index=True)
    d = d[d["_sku"].notna()].copy()
    d["_tot"] = d[[f"b{k}" for k in range(5)]].sum(axis=1)
    out = []
    for sku, g in d.groupby("_sku"):
        b = [int(round(g[f"b{k}"].sum())) for k in range(5)]
        tot = sum(b)
        pt = prev_idx.get((sku, acct), 0)
        if tot == 0 and pt == 0:
            continue
        r = L[L["SKU"] == sku].iloc[-1]  # SKU trùng 2 dòng trong Listing: lấy dòng sau (tên 'V2')
        out.append({"sku": sku, "name": r["Product Name"], "grp": r["Group"], "acct": acct, "cty": cty,
                    "buckets": b, "tot": tot, "prev_tot": pt, "delta": tot - pt})
    # SKU kỳ trước có tồn nhưng kỳ này không còn trong báo cáo -> dòng 0 (delta âm)
    have = {r["sku"] for r in out}
    for (sku, a), pt in prev_idx.items():
        if a == acct and sku not in have and pt > 0 and (L["SKU"] == sku).any():
            r = L[L["SKU"] == sku].iloc[-1]
            out.append({"sku": sku, "name": r["Product Name"], "grp": r["Group"], "acct": acct, "cty": cty,
                        "buckets": [0, 0, 0, 0, 0], "tot": 0, "prev_tot": pt, "delta": -pt})
    return out


def _pack(summary, rows):
    rows = sorted(rows, key=lambda r: r["acct"], reverse=True)  # hoà tất cả -> tài khoản theo thứ tự ngược (US trước CAN; MS/DHI trước ARZ)
    rows = sorted(rows, key=lambda r: (-sum(r["buckets"][3:]), -r["tot"], r["sku"]))
    return {"labels": LABELS, "n_sku": len({r["sku"] for r in rows if r["tot"] > 0}), "tot": sum(r["tot"] for r in rows),
            "over270": sum(sum(r["buckets"][3:]) for r in rows), "over90_idx": 1, "summary": summary, "sku": rows}


NOTE = ("Nguồn: báo cáo Inventory Age của từng kênh — FBA US/CAN và CastleGate ARZ/MEGSU/DHI. "
        "<b>Bảng theo tài khoản (mục trên)</b> là số của toàn bộ báo cáo, không cần khớp SKU. "
        "<b>Bảng chi tiết theo SKU (mục dưới)</b> đối chiếu mã \"Part Number\"/\"sku\" riêng của CastleGate và FBA với SKU chuẩn qua bảng mapping "
        "trong sheet Listing (FBA SKU, SKU - WF MSU, SKU - WF ARZ); 3 box lẻ của Tree House (B4F1/GDWQ) gộp thành 1 bộ theo MIN từng mốc tuổi. "
        "Loại khỏi bảng: các nhóm ngoài 8 nhóm Thu Ngo và các mã không có trong sheet Listing. "
        "Ngưỡng tô đỏ: từ 271 ngày trở lên cho FBA, từ 91 ngày trở lên cho CastleGate.")


def build_lt(master_path, groups, cg_files, fba_files, prev_lt=None, log=print):
    """cg_files: {"ARZ": path, "DHI": path, "MS": path}; fba_files: {"US": path, "CAN": path} (có thể thiếu một số)."""
    L = load_listing(master_path, groups)
    prev_lt = prev_lt or {}

    def pidx(k):
        return {(r["sku"], r["acct"]): r["tot"] for r in prev_lt.get(k, {}).get("sku", [])}

    def psum(k):
        return {r["acct"]: r["tot"] for r in prev_lt.get(k, {}).get("summary", [])}

    wf_sum, wf_rows = [], []
    for acct in sorted(cg_files):
        cty, col = CG_ACCT[acct]
        df = read_castlegate(cg_files[acct])
        b = _bk(df); t = sum(b); pt = psum("wf").get(acct, 0)
        wf_sum.append({"acct": acct, "cty": cty, "buckets": b, "tot": t, "prev_tot": pt, "delta": t - pt})
        wf_rows += _rows_for(df, "Part Number", col, L, acct, cty, pidx("wf"))
    amz_sum, amz_rows = [], []
    for cty in ("US", "CAN"):
        if cty not in fba_files:
            continue
        df = read_fba(fba_files[cty])
        b = _bk(df); t = sum(b); name = f"Toàn tài khoản FBA ({cty})"; pt = psum("amz").get(name, 0)
        amz_sum.append({"acct": name, "cty": cty, "buckets": b, "tot": t, "prev_tot": pt, "delta": t - pt})
        amz_rows += _rows_for(df, "sku", "FBA SKU", L, FBA_ACCT[cty], cty, pidx("amz"))
    out = {"amz": _pack(amz_sum, amz_rows), "wf": _pack(wf_sum, wf_rows), "note": NOTE}
    log(f"[lt] FBA: {out['amz']['n_sku']} SKU, tot={out['amz']['tot']}, ≥271 ngày={out['amz']['over270']} | "
        f"CastleGate: {out['wf']['n_sku']} SKU, tot={out['wf']['tot']}, ≥271 ngày={out['wf']['over270']}")
    return out
