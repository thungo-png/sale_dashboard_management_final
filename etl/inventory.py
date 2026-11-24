"""
ETL tồn kho (đợt 2): invdet, invacct (+ gộp SKU kit). Đối chiếu với D của W39.

Nguồn: sheet 'Inventory Unpivot' trong 'Data Inv & Report Sales - Thư Ngô.xlsx'.
Quy tắc đã chốt:
 - Phạm vi: PIC = Thu Ngô HOẶC Product Group nằm trong 8 nhóm chuẩn (meta.groups). KHÔNG chuẩn hoá tên nhóm
   ("Alma, Wilma" giữ nguyên để dup_sku_grp còn phát hiện được SKU nằm 2 nhóm).
 - Bỏ Country = Unknown; CA -> CAN.
 - SKU kit (vd GDWQ-1/-2/-3): gộp về mã cha, số lượng = MIN các box lẻ tại từng vị trí kho.
 - Storage Type: Local -> 'Kho chung / chưa gán sàn', FBA -> 'Amazon (FBA)', CG -> 'Wayfair (CastleGate)'.
"""
import re
import numpy as np
import pandas as pd

STLAB = {"Local": "Kho chung / chưa gán sàn", "FBA": "Amazon (FBA)", "CG": "Wayfair (CastleGate)"}
CTYS = ["US", "CAN", "AUS"]


def load_scope(master_path, groups, pic, log=print):
    inv = pd.read_excel(master_path, sheet_name="Inventory Unpivot")
    inv["Country"] = inv["Country"].replace({"CA": "CAN"})
    inv["Quantity"] = pd.to_numeric(inv["Quantity"], errors="coerce").fillna(0).astype(int)
    inv["Product SKU"] = inv["Product SKU"].astype(str).str.strip()
    mine = inv[(inv.PIC == pic) | (inv["Product Group"].isin(set(groups)))].copy()
    mine = mine[mine.Country != "Unknown"]

    box_pat = re.compile(r"^(.+)-([1-9])$")
    skus = set(mine["Product SKU"])
    fam = {}
    for s in skus:
        m = box_pat.match(s)
        if m and m.group(1) in skus:
            fam.setdefault(m.group(1), []).append(s)
    rows = []
    for base, kids in fam.items():
        name = mine[mine["Product SKU"] == base]["Product Name"].iloc[0]
        for loc, g in mine[mine["Product SKU"].isin(kids)].groupby("Inventory Location", dropna=False):
            s = g.iloc[0]
            rows.append({**s.to_dict(), "Product SKU": base, "Product Name": name, "Quantity": int(g["Quantity"].min())})
    drop = {x for v in fam.values() for x in v}
    mine = pd.concat([mine[~mine["Product SKU"].isin(drop)], pd.DataFrame(rows)], ignore_index=True)
    mine["Quantity"] = mine["Quantity"].astype(int)
    log(f"[inv] phạm vi: {mine['Product SKU'].nunique()} SKU, gộp kit: {sorted(fam)}")
    return mine


def build_invdet(mine, groups, sold_week, log=print):
    m = mine.copy()
    m["stlab"] = m["Storage Type"].map(STLAB)
    # tồn thật = các dòng khác 0 (kể cả âm)
    nz = m[m.Quantity != 0].sort_values(["Product SKU", "Inventory Location", "Product Group"], kind="stable")
    rows = [{"sku": r["Product SKU"], "grp": r["Product Group"], "name": r["Product Name"], "loc": r["Inventory Location"],
             "cty": r["Country"], "stlab": r["stlab"], "qty": int(r["Quantity"])} for _, r in nz.iterrows()]

    sku_tot = []
    for sku, g in m.groupby("Product SKU", sort=True):
        by = g.groupby("Country")["Quantity"].sum()
        qty = int(g["Quantity"].sum())
        sw = int(sold_week.get(sku, 0))
        sku_tot.append({"sku": sku, "grp": sorted(g["Product Group"].unique())[0], "by_cty": {c: int(by.get(c, 0)) for c in CTYS},
                        "qty": qty, "sold_month": sw, "weeks": round(qty / sw, 1) if sw > 0 and qty > 0 else None})

    matrix = [{"grp": gname, "stlab": st, "qty": int(m[(m["Product Group"] == gname) & (m.stlab == st)].Quantity.sum())}
              for gname in sorted(m["Product Group"].unique()) for st in sorted(STLAB.values())]
    st_tot = m.groupby("stlab")["Quantity"].sum().sort_index()
    cty_tot = m.groupby("Country")["Quantity"].sum().sort_index()

    dup = []
    for sku, g in nz.groupby("Product SKU"):
        gg = g.groupby("Product Group")["Quantity"].sum().sort_index()
        if len(gg) > 1:
            dup.append({"sku": sku, "qty_by_group": [{"grp": k, "qty": int(v)} for k, v in gg.items()]})
    neg = [{"sku": r["sku"], "loc": r["loc"], "qty": r["qty"]} for r in rows if r["qty"] < 0]
    present = set(m["Product Group"])
    zero_grp = sorted(g for g in groups if g not in present or m[m["Product Group"] == g].Quantity.sum() == 0)

    out = {"nsku": int(m[m.Quantity > 0]["Product SKU"].nunique()), "qty_total": int(m.Quantity.sum()),
           "n_loc_nonzero": int((m.Quantity > 0).sum()),
           "st_totals": [{"stlab": k, "qty": int(v)} for k, v in st_tot.items()],
           "cty_totals": [{"cty": k, "qty": int(v)} for k, v in cty_tot.items()],
           "matrix": matrix, "rows": rows, "sku_tot": sku_tot, "zero_grp": zero_grp, "dup_sku_grp": dup, "neg_rows": neg}
    log(f"[inv] invdet: nsku={out['nsku']} qty_total={out['qty_total']} dòng≠0={len(rows)} âm={len(neg)}")
    return out


_ACC = re.compile(r"^(CG|FBA) (.+?)-(Available|In Stock)$")


def build_invacct(mine, n_sku_scope, note, log=print):
    m = mine.copy()
    recs = []
    for loc in m["Inventory Location"].dropna().unique():
        a = _ACC.match(loc)
        if a:
            recs.append((loc, a.group(1), a.group(2)))
        elif loc.startswith("MCF-WF-CG"):
            recs.append((loc, "CG", "MCF (chưa gán tài khoản)"))
        elif loc.startswith("MCF-FBA"):
            recs.append((loc, "FBA", "MCF (chưa gán tài khoản)"))
    kmap = {loc: (k, a) for loc, k, a in recs}
    m = m[m["Inventory Location"].isin(kmap)].copy()
    m["kenh"] = m["Inventory Location"].map(lambda x: kmap[x][0])
    m["acct"] = m["Inventory Location"].map(lambda x: kmap[x][1])
    rows = []
    for (kenh, acct, cty), g in m.groupby(["kenh", "acct", "Country"]):
        rows.append({"kenh": kenh, "acct": acct, "cty": cty, "nsku": int(n_sku_scope), "qty": int(g.Quantity.sum())})
    rows.sort(key=lambda r: (r["kenh"], r["acct"], r["cty"]))
    nz = m[m.Quantity != 0].sort_values(["Product SKU", "kenh", "acct", "Country", "Product Group"], kind="stable")
    det = [{"sku": r["Product SKU"], "name": r["Product Name"], "grp": r["Product Group"], "kenh": r["kenh"],
            "acct": r["acct"], "cty": r["Country"], "qty": int(r["Quantity"])} for _, r in nz.iterrows()]
    out = {"rows": rows, "det": det, "qty_total": int(sum(r["qty"] for r in rows)), "note_longterm": note}
    log(f"[inv] invacct: {len(rows)} tổ hợp, {len(det)} dòng chi tiết, qty_total={out['qty_total']}")
    return out
