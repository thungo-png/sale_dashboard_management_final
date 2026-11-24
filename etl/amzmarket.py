"""Thị trường Amazon — từ Brand Analytics (Search Query Performance, Brand View) và Business Report (Buy Box theo ASIN).
Kết quả -> D["amzmkt"]. Không có file thì không có khối này (tab Thị trường tự ẩn phần Amazon)."""
import io, re, zipfile
import pandas as pd

MAX_Q_VOL, MAX_Q_BRAND = 150, 100       # số cụm từ giữ chi tiết cho tuần hiện tại (top theo lượt tìm + top theo lượt hiển thị của brand)


def _norm(c):
    return re.sub(r"\s+", " ", str(c).lower().replace("same-day", "same day")).strip()


def _read_sqp_one(raw):
    txt = raw.decode("utf-8-sig", "ignore")
    head = txt.split("\n", 1)[0]
    m = re.search(r"Week\s+(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*-\s*(\d{4}-\d{2}-\d{2})", head)
    b = re.search(r'Brand=\["([^"]*)"\]', head)
    df = pd.read_csv(io.StringIO(txt), skiprows=1)
    df.columns = [_norm(c) for c in df.columns]
    return (int(m.group(1)) if m else None, m.group(2) if m else None, m.group(3) if m else None, b.group(1) if b else ""), df


def _files(path):
    p = str(path).lower()
    if p.endswith(".zip"):
        z = zipfile.ZipFile(path)
        return [z.read(i) for i in z.infolist() if i.filename.lower().endswith(".csv") and "__macosx" not in i.filename.lower()]
    return [open(path, "rb").read()]


def _num(v):
    x = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(x) else round(float(x), 4)


def build_sqp(path, log=print):
    weeks = []
    for raw in _files(path):
        (wk, d0, d1, brand), df = _read_sqp_one(raw)
        if wk is None:
            continue
        weeks.append((wk, d0, d1, brand, df))
    if not weeks:
        return None
    weeks.sort(key=lambda t: t[0])
    wsum, hist = [], {}
    for wk, d0, d1, brand, df in weeks:
        ti, bi = df["impressions: total count"].sum(), df["impressions: brand count"].sum()
        tc, bc = df["clicks: total count"].sum(), df["clicks: brand count"].sum()
        tp, bp = df["purchases: total count"].sum(), df["purchases: brand count"].sum()
        wsum.append({"w": wk, "d0": d0, "d1": d1, "n": int(len(df)), "vol": int(df["search query volume"].sum()),
                     "imp_share": round(bi / ti * 100, 4) if ti else None, "clk_share": round(bc / tc * 100, 4) if tc else None,
                     "buy_share": round(bp / tp * 100, 4) if tp else None, "brand_imp": int(bi), "brand_clk": int(bc), "brand_buy": int(bp)})
        for _, r in df.iterrows():
            hist.setdefault(str(r["search query"]), {})[wk] = [int(r["search query volume"]), _num(r["impressions: brand share %"]), _num(r["clicks: brand share %"]), _num(r["purchases: brand share %"])]
    wk, d0, d1, brand, cur = weeks[-1]
    pick = set(cur.nlargest(MAX_Q_VOL, "search query volume")["search query"]) | set(cur.nlargest(MAX_Q_BRAND, "impressions: brand count")["search query"])
    rows = []
    for _, r in cur[cur["search query"].isin(pick)].iterrows():
        q = str(r["search query"])
        rows.append({"q": q, "vol": int(r["search query volume"]), "score": _num(r["search query score"]),
                     "imp": int(r["impressions: total count"]), "imp_b": int(r["impressions: brand count"]), "imp_sh": _num(r["impressions: brand share %"]),
                     "clk": int(r["clicks: total count"]), "clk_b": int(r["clicks: brand count"]), "clk_sh": _num(r["clicks: brand share %"]), "ctr": _num(r["clicks: click rate %"]),
                     "p_mkt": _num(r["clicks: price (median)"]), "p_brand": _num(r["clicks: brand price (median)"]),
                     "buy": int(r["purchases: total count"]), "buy_b": int(r["purchases: brand count"]), "buy_sh": _num(r["purchases: brand share %"]),
                     "bp_mkt": _num(r["purchases: price (median)"]), "bp_brand": _num(r["purchases: brand price (median)"]),
                     "hist": {str(k): v for k, v in sorted(hist.get(q, {}).items())}})
    rows.sort(key=lambda x: -x["vol"])
    log(f"[amzmkt] SQP {brand}: {len(weeks)} tuần (W{weeks[0][0]}→W{wk}), {len(rows)} cụm từ chi tiết")
    return {"brand": brand, "cur": wk, "range": [d0, d1], "weeks": wsum, "q": rows}


def _money(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except ValueError:
        return 0.0


def _pct(x):
    try:
        return float(str(x).replace("%", "").replace(",", "").strip())
    except ValueError:
        return None


def build_br(path, asin_map, log=print):
    """asin_map: {ASIN: (sku, group)} từ sheet Listing. Trả list dòng theo ASIN con."""
    b = pd.read_csv(path, encoding="utf-8-sig")
    out = []
    for _, r in b.iterrows():
        a = str(r["(Child) ASIN"]).strip()
        sku, grp = asin_map.get(a, (None, None))
        out.append({"asin": a, "sku": sku, "grp": grp, "title": str(r["Title"])[:90],
                    "sess": int(_money(r["Sessions - Total"])), "pv": int(_money(r["Page Views - Total"])),
                    "bb": _pct(r["Featured Offer (Buy Box) Percentage"]), "units": int(_money(r["Units Ordered"])),
                    "cvr": _pct(r["Unit Session Percentage"]), "sales": round(_money(r["Ordered Product Sales"]), 2),
                    "refund": _pct(r["Refund Rate"])})
    log(f"[amzmkt] Business Report: {len(out)} ASIN, {sum(1 for x in out if x['grp'])} gắn được nhóm")
    return out


def asin_map(master, sku_meta):
    L = pd.read_excel(master, sheet_name="Listing")
    g_of = {r["sku"]: r["grp"] for r in (sku_meta or [])}
    m = {}
    for sku, asin, grp in zip(L["SKU"], L["ASIN"], L["Group"]):
        if pd.notna(asin):
            m[str(asin).strip()] = (str(sku), g_of.get(str(sku)) or grp)
    return m


def build(inp, master, sku_meta, log=print):
    out = {}
    for cc in ("US", "CA"):
        if f"sqp_{cc}" in inp:
            s = build_sqp(inp[f"sqp_{cc}"], log)
            if s:
                out.setdefault("sqp", {})[cc] = s
        k = "amazon_br_" + ("US" if cc == "US" else "CAN")
        if k in inp and master:
            out.setdefault("br", {})[cc] = build_br(inp[k], asin_map(master, sku_meta), log)
    return out or None
