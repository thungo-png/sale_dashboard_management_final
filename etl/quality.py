"""Chất lượng sản phẩm thật — từ báo cáo Wayfair "Summary-data" (Incidents / Buyer's Remorse Returns) của từng tài khoản.
File là số TÍCH LŨY nhiều tháng (không theo tuần), nên chỉ dùng làm bức tranh chất lượng, không so tuần với tuần."""
import pandas as pd
from etl import ads  # noqa

ACC_LABEL = {"ARZ": "Arozu", "MS": "Megsu", "DHI": "DHI"}


def _pct(v):
    try:
        return float(str(v).replace("%", "").replace(",", "").strip())
    except ValueError:
        return None


def _num(v):
    x = pd.to_numeric(v, errors="coerce")
    return 0.0 if pd.isna(x) else float(x)


ACC_COLS = {"ARZ": ["SKU - WF ARZ"], "MS": ["SKU - WF MSU"], "DHI": ["SKU", "SKU - WF MSU", "SKU - WF ARZ", "FBM SKU"]}


def _idmap(master, sku_meta, groups, log=print):
    """Product ID (mã nhà cung cấp trên Wayfair) -> nhóm sản phẩm, theo sheet Listing của file master:
    mỗi tài khoản dùng cột SKU tương ứng (SKU - WF ARZ / SKU - WF MSU; DHI dùng mã gốc), nhóm lấy từ sku_meta (trùng với phần còn lại của report)."""
    L = pd.read_excel(master, sheet_name="Listing")
    g_of = {r["sku"]: r["grp"] for r in (sku_meta or [])}
    out = {}
    for acc, cols in ACC_COLS.items():
        m = {}
        for c in cols:
            if c not in L.columns:
                continue
            for k, sku, grp in zip(L[c], L["SKU"], L["Group"]):
                if pd.isna(k):
                    continue
                g = g_of.get(str(sku)) or (grp if grp in groups else None)
                if g:
                    m.setdefault(str(k).strip(), g)
        out[acc] = m
    return out


def build_quality(sum_files, master, sku_meta, groups, rates, log=print):
    """sum_files / pr_files: {ARZ|MS|DHI: path}. Trả dict D["quality"] hoặc None nếu không có file."""
    rows, all_n, per_acc = [], 0, {}
    idm = _idmap(master, sku_meta, groups, log) if master else {}
    for acc, path in sum_files.items():
        x = pd.read_csv(path, encoding="utf-8-sig")
        x.columns = [c.strip() for c in x.columns]
        m = idm.get(acc, {})
        all_n += len(x); per_acc[acc] = [len(x), 0]
        for _, r in x.iterrows():
            g = m.get(str(r["Product ID"]).strip())
            if not g:
                continue
            cur = str(r.get("Total Deductions Currency", "USD"))
            fx = 1.0 if cur in ("USD", "nan", "Multiple") else rates.get(cur, 1.0)
            per_acc[acc][1] += 1
            rows.append({
                "acc": ACC_LABEL.get(acc, acc), "wsku": str(r["Wayfair SKU"]), "pid": str(r["Product ID"]), "grp": g, "cls": str(r.get("Class", "")),
                "inc": _num(r["Incidents Number"]), "adj": _num(r["Incidents Adjusted Delivered Quantity"]),
                "inc_b": _pct(r["Product Benchmark Incident Rate"]),
                "ret": _num(r["Buyers's Remorse Returns Number"]), "dlv": _num(r["Delivered Quantity"]),
                "ret_b": _pct(r["Product Benchmark Returns Rate"]),
                "ded": round(_num(r.get("Total Deductions")) * fx, 2),
                "rep": _num(r.get("Replacement Parts Count")),
                "last": str(r.get("Last Delivery Date Reported", ""))[:10],
            })
    if not sum_files:
        return None

    def agg(rs):
        adj, dlv = sum(r["adj"] for r in rs), sum(r["dlv"] for r in rs)
        inc, ret = sum(r["inc"] for r in rs), sum(r["ret"] for r in rs)
        bi = sum((r["inc_b"] or 0) * r["adj"] for r in rs if r["inc_b"] is not None); wi = sum(r["adj"] for r in rs if r["inc_b"] is not None)
        br = sum((r["ret_b"] or 0) * r["dlv"] for r in rs if r["ret_b"] is not None); wr = sum(r["dlv"] for r in rs if r["ret_b"] is not None)
        return {"n": len(rs), "inc": inc, "adj": adj, "inc_rate": round(inc / adj * 100, 2) if adj else None,
                "inc_bench": round(bi / wi, 2) if wi else None,
                "ret": ret, "dlv": dlv, "ret_rate": round(ret / dlv * 100, 2) if dlv else None,
                "ret_bench": round(br / wr, 2) if wr else None,
                "ded": round(sum(r["ded"] for r in rs), 2)}
    gs = {}
    for r in rows:
        gs.setdefault(r["grp"], []).append(r)
    by_grp = sorted(({"grp": g, **agg(v)} for g, v in gs.items()), key=lambda t: -(t["ded"] or 0))
    for r in rows:   # SKU nào cao hơn chuẩn Wayfair và đủ mẫu (>= 30 đơn giao) thì gắn cờ
        r["flag_inc"] = bool(r["inc_b"] is not None and r["adj"] >= 30 and r["inc"] / r["adj"] * 100 > r["inc_b"])
        r["flag_ret"] = bool(r["ret_b"] is not None and r["dlv"] >= 30 and r["ret"] / r["dlv"] * 100 > r["ret_b"])
    last = max((r["last"] for r in rows), default="")
    log(f"[quality] {len(rows)}/{all_n} listing thuộc danh mục ({', '.join(f'{k} {v[1]}/{v[0]}' for k, v in per_acc.items())})")
    return {"as_of": last, "scope_n": len(rows), "all_n": all_n, "per_acc": {ACC_LABEL.get(k, k): v for k, v in per_acc.items()},
            "total": agg(rows) if rows else None, "by_grp": by_grp, "rows": rows}
