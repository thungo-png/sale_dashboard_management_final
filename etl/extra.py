"""
ETL khối bổ trợ (đợt 4a): sku_meta, top_sku2, grpcmp, askuw_mp, sizecolor — tính từ D đã dựng ở đợt 1 + master Listing.
Các khối này chỉ phụ thuộc số bán hàng (D.sku, D.ts_sku) nên không cần thêm file ngoài sheet Listing.
"""
import re
import numpy as np
import pandas as pd


def _pct(cur, base):
    return round((cur - base) / base * 100, 2) if base and base > 0 else None


# ---------------------------------------------------------------- sku_meta
def build_sku_meta(prev_meta, D, listing_path=None, log=print):
    """Giữ danh sách kỳ trước, thêm SKU mới xuất hiện trong tuần (tên lấy từ sheet Listing, không có thì dùng mã SKU)."""
    names = {}
    if listing_path is not None:
        L = pd.read_excel(listing_path, sheet_name="Listing")
        names = dict(zip(L["SKU"].astype(str).str.strip(), L["Product Name"]))
    out = {r["sku"]: dict(r) for r in prev_meta}
    new = 0
    for r in D["sku"]:
        if r["sku"] not in out:
            out[r["sku"]] = {"sku": r["sku"], "grp": r["grp"], "name": names.get(r["sku"], r["sku"])}; new += 1
    if new:
        log(f"[extra] sku_meta: thêm {new} SKU mới")
    return sorted(out.values(), key=lambda x: x["sku"])


# ---------------------------------------------------------------- top_sku2
def build_top_sku2(D, names, log=print):
    agg = {}
    for r in D["sku"]:
        a = agg.setdefault(r["sku"], {"sku": r["sku"], "grp": r["grp"], "q": 0, "r": 0.0, "rfc": 0.0})
        a["q"] += r["q"]; a["r"] += r["r"]; a["rfc"] += r["rfc"]
    rows = []
    for a in agg.values():
        if a["q"] <= 0:
            continue
        r, rfc, q = round(a["r"], 2), round(a["rfc"], 2), a["q"]
        rows.append({"sku": a["sku"], "name": names.get(a["sku"], a["sku"]), "grp": a["grp"], "q": q, "r": r, "rfc": rfc,
                     "asp": round(r / q, 2) if q > 0 else None, "ach": round(r / rfc * 100, 2) if rfc > 0 else None,
                     "gap": round(rfc - r, 2)})
    best = sorted([x for x in rows if x["r"] > 0], key=lambda x: (-x["r"], x["sku"]))[:10]
    fc = [x for x in rows if x["rfc"] > 0]
    worst = sorted(fc, key=lambda x: (x["ach"], x["sku"]))[:10]
    return {"best": best, "worst": worst, "n_scope": len(rows), "n_fc": len(fc), "note": None}


# ---------------------------------------------------------------- grpcmp
def build_grpcmp(D, prev, log=print):
    lab = D["ts_labels"]["W"]; n = len(lab)
    g_of = {r["sku"]: r["grp"] for r in D["sku_meta"]}
    l3 = D["ts_sku"]["W"]["l3"]
    idx = {w: i for i, w in enumerate(lab)}
    def agg(back):
        if n - 1 - back < 0:
            return None
        w = str(lab[n - 1 - back]); out = {}
        for k, v in l3.items():
            if w in v:
                sku, mp, cty = k.split(" · ")
                a = out.setdefault((g_of.get(sku), mp, cty), [0.0, 0]); a[0] += v[w]["r"]; a[1] += v[w]["q"]
        return out
    per = {"w": agg(1), "m": agg(4), "q": agg(13), "y": None}
    cur = {(g["grp"], g["mp"], g["cty"]): g for g in D["bygrp_cell"]}
    keys = set(cur)
    rows = []
    for k in sorted(keys):
        c = cur.get(k, {"r": 0.0, "q": 0, "rfc": 0.0})
        row = {"grp": k[0], "mp": k[1], "cty": k[2], "r": c["r"], "q": c["q"],
               "ach": round(c["r"] / c["rfc"] * 100, 2) if c["rfc"] else 0.0}
        row["r_w"] = round(per["w"].get(k, [0.0, 0])[0], 2) if per["w"] is not None else None
        for s in "wmqy":
            p = per[s]; b = p.get(k, [0.0, 0]) if p is not None else None
            row["d_" + s] = _pct(c["r"], b[0]) if b else None
            row["dq_" + s] = _pct(c["q"], b[1]) if b else None
        rows.append(row)
    avail = {s: per[s] is not None for s in "wmqy"}
    return {"rows": rows, "avail": avail, "note": prev.get("note", ""), "data_from": prev.get("data_from")}


# ---------------------------------------------------------------- askuw_mp
CTYCUR = {"US": "USD", "CAN": "CAD", "AUS": "AUD"}


def build_askuw_mp(D, names, rates, log=print):
    """ASP theo SKU × sàn × quốc gia × tuần, giữ tiền tệ gốc (r_loc = r_usd / tỷ giá constant-currency)."""
    labs = [str(w) for w in D["ts_labels"]["W"]]; cur_w = labs[-1]; prev4 = labs[-5:-1]
    fx = {"US": 1.0, "CAN": rates["CAD"], "AUS": rates["AUD"]}
    g_of = {r["sku"]: r["grp"] for r in D["sku_meta"]}
    rows = []
    for key, v in D["ts_sku"]["W"]["l3"].items():
        sku, mp, cty = key.split(" · ")
        cells = {}
        for w in labs:
            c = v.get(w)
            if c and c["q"] > 0:
                r_loc = round(c["r"] / fx[cty], 2)
                cells[w] = {"q": c["q"], "r": r_loc, "asp": round(r_loc / c["q"], 2), "asp_usd": round(c["r"] / c["q"], 2)}
        if not cells:
            continue
        cc = cells.get(cur_w)
        base = [cells[w]["asp"] for w in prev4 if w in cells]
        avg4 = round(sum(base) / len(base), 2) if base else None
        rows.append({"sku": sku, "name": names.get(sku, sku), "grp": g_of.get(sku), "mp": mp, "cty": cty, "cur": CTYCUR[cty],
                     "cells": cells, "q_cur": cc["q"] if cc else None, "avg4": avg4,
                     "trend": round((cc["asp"] / avg4 - 1) * 100, 2) if cc and avg4 else None,
                     "r_cur": v[cur_w]["r"] if cc else 0.0})
    rows.sort(key=lambda x: (x["sku"], x["mp"], x["cty"]))
    return rows


# ---------------------------------------------------------------- sizecolor
SIZES = ["King", "Queen", "Twin", "Full", "Double"]
COLORS = ["Black", "Caramel", "Chocolate", "Natural", "Walnut", "White", "Grey", "Gray"]


SYN = {"Mocha": "Chocolate", "Americano": "Walnut", "Oak": "Natural", "Ristretto": "Black", "Gray": "Grey"}


def _kw(name, words):
    for w in words:
        if re.search(rf"\b{w}\b", str(name), re.I):
            return w
    return None


def _color(name):
    c = _kw(name, COLORS + list(SYN))
    return SYN.get(c, c)


def build_sizecolor(D, prev_sc, log=print):
    """Tăng dần: các tuần cũ GIỮ NGUYÊN như đã công bố (kỳ trước có thể tách size/màu theo quy tắc cũ); chỉ tính lại tuần mới."""
    meta = {r["sku"]: r for r in D["sku_meta"]}
    parsed = {s: (_kw(r["name"], SIZES), _color(r["name"])) for s, r in meta.items()}
    weeks = [int(w) for w in D["ts_labels"]["W"]]; cur_w = weeks[-1]
    wk = {"size": {}, "color": {}}
    for sku, v in D["ts_sku"]["W"]["l1"].items():
        sz, co = parsed.get(sku, (None, None)); g = meta.get(sku, {}).get("grp")
        c = v.get(str(cur_w))
        if c and c["q"] > 0:
            for kind, k in (("size", sz), ("color", co)):
                if k:
                    wk[kind][(g, k)] = wk[kind].get((g, k), 0) + c["q"]
    cur = {"size": {}, "color": {}}
    for r in D["sku"]:
        sz, co = parsed.get(r["sku"], (None, None))
        for kind, k in (("size", sz), ("color", co)):
            if k:
                a = cur[kind].setdefault((r["grp"], k), [0, 0.0]); a[0] += r["q"]; a[1] += r["r"]
    def rows(kind):
        old = [x for x in prev_sc[kind + "_wk"] if x["W"] in weeks and x["W"] != cur_w]
        new = [{"grp": g, "k": k, "W": cur_w, "q": q} for (g, k), q in wk[kind].items()]
        return sorted(old + new, key=lambda x: (x["grp"], x["k"], x["W"]))
    curl = lambda kind: [{"grp": g, "k": k, "q": q, "r": round(r, 2), "asp": round(r / q, 2)} for (g, k), (q, r) in sorted(cur[kind].items()) if q > 0]
    unp = [{"sku": s, "name": meta[s]["name"], "grp": meta[s]["grp"]} for s in sorted(meta) if parsed[s] == (None, None)]
    return {"weeks": weeks, "size_wk": rows("size"), "color_wk": rows("color"), "size_cur": curl("size"), "color_cur": curl("color"),
            "unparsed": unp, "note": prev_sc["note"]}
