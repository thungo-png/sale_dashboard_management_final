"""
ETL quảng cáo (đợt 3): Wayfair CR/PR/PSR/ST + Amazon Ads CSV -> campthu, scope, adsum, tacos, adlist_cover, ads.rank, ads.st.

Quy tắc (xem 01-sale-report-modules.md mục F, đối chiếu với D của W39):
 - Chỉ chiến dịch của Thu Ngo: tên khớp ^\\s*thu\\s*ng[oô]\\b (loại 'Thu Nguyen').
 - Chỉ lấy các ngày trong tuần báo cáo [d0, d1].
 - Quốc gia theo TÀI KHOẢN: Arozu/Megsu = US, DHI = CAN, Senno = AUS. Quy đổi USD bằng cùng tỷ giá constant-currency của báo cáo.
 - Nhóm sản phẩm gán theo từ khoá trong tên chiến dịch.
"""
import re
import numpy as np
import pandas as pd

RX_THU = re.compile(r"^\s*thu\s*ng[oô]\b", re.I)
WF_ACCT = {"ARZ": ("US", "USD"), "MS": ("US", "USD"), "DHI": ("CAN", "CAD")}
AMZ_ACCT = {"AROZU INC": ("Arozu", "US", "USD"), "MEGSU INC": ("Megsu", "US", "USD"),
            "DH International Trading Inc.": ("DHI", "CAN", "CAD"), "SENNO": ("Senno", "AUS", "AUD")}
GROUP_KEYS = [("emery", "Acacia - Emery - Wooden Bed Frame with Headboard"), ("aurora", "Aurora - Wooden Bed Frame With Headboard"),
              ("astoria", "Acacia - Astoria - Wooden Bed Frame with Headboard"), (r"tree\s*house", "Arozu - Tree House - Kid Bunk Bed"),
              ("lagom", "Acacia Lagom Office Desk"), ("verve", "Acacia Verve Dining Table"),
              ("alma", "Acacia - Alma Dinning Table"), ("wilma", "Acacia - Wilma Dinning Table")]


def group_of(name, groups):
    n = str(name)
    for k, g in GROUP_KEYS:
        if re.search(k, n, re.I) and g in groups:
            return g
    return None


def _usd(cur, rates):
    return {"USD": 1.0, "CAD": rates["CAD"], "AUD": rates["AUD"]}[cur]


def _r2(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 2)


def _safe(a, b, k=1.0, nd=2):
    return round(a / b * k, nd) if b else None


# ---------------------------------------------------------------- đọc file
def _read_any(path, **kw):
    """Đọc csv hoặc xlsx theo nội dung/đuôi file (đuôi do app giữ nguyên khi upload)."""
    p = str(path).lower()
    if p.endswith(".xlsx") or p.endswith(".xlsm") or p.endswith(".xls"):
        return pd.read_excel(path, **kw)
    return pd.read_csv(path, encoding="utf-8-sig", **kw)


def read_wf(path, d0, d1):
    c = _read_any(path)
    c["Date"] = pd.to_datetime(c["Date"])
    return c[(c.Date >= d0) & (c.Date <= d1)].copy()


def read_pr_names(path):
    """{listing: product_name} từ báo cáo PR — dùng để gắn listing Wayfair vào nhóm sản phẩm."""
    c = _read_any(path, usecols=["listing", "product_name"]).drop_duplicates("listing")
    return {str(a): b for a, b in zip(c["listing"], c["product_name"])}


def read_amazon(path, d0, d1):
    a = pd.read_csv(path)
    a["Date"] = pd.to_datetime(a["Date"], format="%b %d, %Y")
    a = a[(a.Date >= d0) & (a.Date <= d1)].copy()
    a["cid"] = a["Campaign ID"].astype(str).str.replace(r'[="]', "", regex=True)
    for c in ["Total cost", "Sales", "Purchases", "Clicks", "Impressions"]:
        a[c] = pd.to_numeric(a[c], errors="coerce").fillna(0)
    return a


def _spendcol(c):
    return next(x for x in c.columns if x.startswith("spend_"))


# ---------------------------------------------------------------- campthu
def campthu(wf, amz, rates, groups, log=print):
    rows = []
    for acct, c in wf.items():
        cty, cur = WF_ACCT[acct]
        fx = _usd(cur, rates)
        sc = _spendcol(c)
        sales_c = "attributed_retail_sales_window_view_through_USD_Day_14" if "attributed_retail_sales_window_view_through_USD_Day_14" in c.columns else next(
            x for x in c.columns if x.startswith("attributed_retail_sales"))
        ord_c = next(x for x in c.columns if x.startswith("attributed_orders"))
        t = c[c.campaign_name.astype(str).str.contains(RX_THU)]
        for cid, g in t.groupby("campaign_id", sort=False):
            g = g.sort_values("Date")
            sp_loc = float(g[sc].sum()); sp = sp_loc * fx
            sales = float(g[sales_c].sum()) * (1 if cur == "USD" else fx)
            orders = int(g[ord_c].sum()); clicks = int(g.clicks.sum()); imp = int(g.impressions.sum())
            rows.append({"camp": g.campaign_name.iloc[-1].strip(), "grp": group_of(g.campaign_name.iloc[-1], groups), "mp": "Wayfair",
                         "cty": cty, "cur": "USD", "cur_loc": cur, "status": str(g.campaign_status.iloc[-1]),
                         "bid": "" if pd.isna(g.bidding_strategy.iloc[-1]) else str(g.bidding_strategy.iloc[-1]),
                         "spend": round(sp, 2), "spend_loc": round(sp_loc, 2), "orders": orders,
                         "acos": _safe(sp, sales, 100), "cpo": _safe(sp, orders), "cpc": _safe(sp, clicks),
                         "ctr": round(clicks / imp * 100, 3) if imp else None, "roas": round(sales / sp, 3) if sp else 0.0,
                         "sales": round(sales, 2), "clicks": clicks, "impressions": imp, "_acct": acct, "_sp": sp})
    for name, (acct, cty, cur) in AMZ_ACCT.items():
        g0 = amz[amz["Advertiser account name"] == name]
        fx = _usd(cur, rates)
        t = g0[g0["Campaign name"].astype(str).str.contains(RX_THU)]
        for cid, g in t.groupby("cid", sort=False):
            sp_loc = float(g["Total cost"].sum()); sp = sp_loc * fx
            sales = float(g["Sales"].sum()) * fx; orders = int(g["Purchases"].sum())
            clicks = int(g["Clicks"].sum()); imp = int(g["Impressions"].sum()); nm = g["Campaign name"].iloc[-1].strip()
            rows.append({"camp": nm, "grp": group_of(nm, groups), "mp": "Amazon", "cty": cty, "cur": "USD", "cur_loc": cur,
                         "status": "ACTIVE", "bid": "", "spend": round(sp, 2), "spend_loc": round(sp_loc, 2), "orders": orders,
                         "acos": _safe(sp, sales, 100), "cpo": _safe(sp, orders), "cpc": _safe(sp, clicks),
                         "ctr": round(clicks / imp * 100, 3) if imp else None, "roas": round(sales / sp, 3) if sp else 0.0,
                         "sales": round(sales, 2), "clicks": clicks, "impressions": imp, "_acct": acct, "_sp": sp})
    un = [r["camp"] for r in rows if r["grp"] is None]
    if un:
        log(f"[ads] CẢNH BÁO: {len(un)} chiến dịch không gán được nhóm: {un[:3]}")
    return rows


# ---------------------------------------------------------------- scope
def scope(wf, amz, rates, camp_rows, log=print):
    rows = []
    for acct, c in wf.items():
        cty, cur = WF_ACCT[acct]; fx = _usd(cur, rates); sc = _spendcol(c)
        t = c[c.campaign_name.astype(str).str.contains(RX_THU)]
        sp_loc = float(c[sc].sum())
        rows.append({"acct": acct, "mp": "Wayfair", "n_all": int(c.campaign_name.nunique()), "sp_all": round(sp_loc * fx, 2),
                     "sp_all_loc": round(sp_loc, 2), "n_thu": int(t.campaign_id.nunique()),
                     "sp_thu": round(float(t[sc].sum()) * fx, 2), "cur_loc": cur})
    for name, (acct, cty, cur) in AMZ_ACCT.items():
        g = amz[amz["Advertiser account name"] == name]; fx = _usd(cur, rates)
        t = g[g["Campaign name"].astype(str).str.contains(RX_THU)]
        sp_loc = float(g["Total cost"].sum())
        rows.append({"acct": acct, "mp": "Amazon", "n_all": int(g["Campaign name"].nunique()), "sp_all": round(sp_loc * fx, 2),
                     "sp_all_loc": round(sp_loc, 2), "n_thu": int(t.cid.nunique()),
                     "sp_thu": round(float(t["Total cost"].sum()) * fx, 2), "cur_loc": cur})
    return rows


# ---------------------------------------------------------------- adsum / tacos
def adsum(camp, bygrp_cell, log=print):
    """camp: campthu rows. rev = doanh thu thật của CÁC NHÓM CÓ chiến dịch Thu Ngo trong ô sàn×quốc gia (khớp W39)."""
    have = {(r["grp"], r["mp"], r["cty"]) for r in camp if r["grp"]}
    rev = {}
    for g in bygrp_cell:
        if (g["grp"], g["mp"], g["cty"]) in have:
            rev[(g["mp"], g["cty"])] = rev.get((g["mp"], g["cty"]), 0.0) + g["r"]
    out = []
    for mp, cty in [("Wayfair", "US"), ("Wayfair", "CAN"), ("Amazon", "US"), ("Amazon", "CAN"), ("Amazon", "AUS")]:
        rs = [r for r in camp if r["mp"] == mp and r["cty"] == cty]
        sp = sum(r["spend"] for r in rs); whl = sum(r["sales"] for r in rs); rv = rev.get((mp, cty), 0.0)
        out.append({"mp": mp, "cty": cty, "cur": "USD", "ncamp": len(rs), "spend": round(sp, 2), "rev": round(rv, 2),
                    "tacos": _safe(sp, rv, 100), "whl": round(whl, 2), "roas": round(whl / sp, 3) if sp else 0.0})
    return out


def tacos(camp, bygrp_cell, log=print):
    rev = {(g["grp"], g["mp"], g["cty"]): g["r"] for g in bygrp_cell}
    keys = sorted({(r["grp"], r["mp"], r["cty"]) for r in camp if r["grp"]}, key=lambda k: ({"Wayfair": 0, "Amazon": 1}[k[1]], k[0], k[2]))
    out = []
    for grp, mp, cty in keys:
        rs = [r for r in camp if (r["grp"], r["mp"], r["cty"]) == (grp, mp, cty)]
        sp = sum(r["spend"] for r in rs); cl = sum(r["clicks"] for r in rs); sa = sum(r["sales"] for r in rs)
        rv = rev.get((grp, mp, cty), 0.0)
        out.append({"grp": grp, "mp": mp, "cty": cty, "cur": "USD", "ncamp": len(rs), "spend": round(sp, 2), "rev": round(rv, 2),
                    "tacos": _safe(sp, rv, 100), "cpc": _safe(sp, cl), "roas": round(sa / sp, 3) if sp else 0.0})
    return out


def dgmk_room(S, d0, d1):
    cur = S[(S.date >= d0) & (S.date <= d1)]
    g = cur.groupby(["grp", "cty", "mp"])["fee"].sum().round(2)
    return {f"{a}|{b}|{c}": float(v) for (a, b, c), v in g.items() if abs(v) > 1e-9}


# ---------------------------------------------------------------- adlist_cover
def adlist_cover(pr, rates, log=print):
    """pr: {Arozu|Megsu|DHI: DataFrame PR (đã lọc ngày)}"""
    out = {}
    for name, p in pr.items():
        cur = "CAD" if name == "DHI" else "USD"; fx = _usd(cur, rates); sc = _spendcol(p)
        t = p[p.campaign_name.astype(str).str.contains(RX_THU)]
        out[name] = {"n_all": int(p.listing.nunique()), "sp_all": round(float(p[sc].sum()) * fx, 2),
                     "n_thu": int(t.listing.nunique()), "sp_thu": round(float(t[sc].sum()) * fx, 2)}
    return out


# ---------------------------------------------------------------- ads.rank / ads.st
ACCT_PR = {"Arozu": "ARZ", "Megsu": "MS", "DHI": "DHI"}
ST_BRAND = {"Arozu": "Wayfair US", "Megsu": "Wayfair US", "DHI": "Wayfair Canada (English)"}


def ads_rank(pr, psr, groups, log=print):
    """pr/psr: {name: df}. psr đã lọc [d0,d1]. Listing thuộc chiến dịch Thu Ngo (PR) và có trong PSR."""
    out, classes = {}, set()
    for name in pr:
        p = pr[name]; s = psr[name]
        t = p[p.campaign_name.astype(str).str.contains(RX_THU)]
        lg = {}
        for l, g in t.groupby("listing", sort=True):
            lg[l] = group_of(g.sort_values("Date").campaign_name.iloc[-1], groups)
        rows = []
        for l, g in s.groupby("Listing", sort=True):
            if l not in lg:
                continue
            g = g.sort_values("Date")
            rk = g["Class Rank"]
            rows.append({"Listing": l, "name": "", "grp": lg[l], "Class Name": g["Class Name"].iloc[-1],
                         "first": int(rk.iloc[0]), "last": int(rk.iloc[-1]), "best": int(rk.min()),
                         "status": str(g["Campaign Listing Status"].iloc[-1])})
            classes.add(g["Class Name"].iloc[-1])
        out[name] = rows
    return out, classes


def read_st(path):
    s = _read_any(path, header=0).iloc[:, :8].copy()
    s.columns = ["bc", "term", "cls", "impr", "sh_search", "shs", "sh_p1", "sh_top8"]
    for c in ["impr", "sh_search", "shs", "sh_p1", "sh_top8"]:
        s[c] = pd.to_numeric(s[c], errors="coerce")
    return s[s["impr"].notna()].copy()   # bỏ dòng chú thích (nếu có) thay vì cắt cứng dòng đầu


def ads_st(st, classes, log=print):
    out = {}
    for name, s in st.items():
        t = s[(s.bc == ST_BRAND[name]) & s.cls.isin(classes)].sort_values("impr", ascending=False, kind="stable")
        out[name] = [{"term": r.term, "cls": r.cls, "impr": int(r.impr), "sh_search": float(r.sh_search),
                      "sh_p1": float(r.sh_p1), "sh_top8": float(r.sh_top8)} for r in t.itertuples()]
    return out


# ---------------------------------------------------------------- entry point
def build_ads(files, S, D, rates, d0, d1, log=print):
    """files: {'wf_CR':{ARZ:path,MS:..,DHI:..}, 'wf_PR':..,'wf_PSR':..,'wf_ST':..,'amazon':path}. Trả dict các khối."""
    groups = D["meta"]["groups"]
    wf = {a: read_wf(p, d0, d1) for a, p in files["wf_CR"].items()}
    amz = read_amazon(files["amazon"], d0, d1)
    camp = campthu(wf, amz, rates, groups, log)
    sort_mp = {"Wayfair": 0, "Amazon": 1}; sort_c = {"US": 0, "CAN": 1, "AUS": 2}
    camp.sort(key=lambda r: (sort_mp[r["mp"]], sort_c[r["cty"]], r["_acct"], r["camp"]))
    sc = scope(wf, amz, rates, camp, log)
    nm = {"ARZ": "Arozu", "MS": "Megsu", "DHI": "DHI"}
    pr = {nm[a]: read_wf(p, d0, d1) for a, p in files["wf_PR"].items()}
    psr = {nm[a]: read_wf(p, d0, d1) for a, p in files["wf_PSR"].items()}
    rank, classes = ads_rank(pr, psr, groups, log)
    st = {nm[a]: read_st(p) for a, p in files["wf_ST"].items()}
    out = {"campthu": [{k: v for k, v in r.items() if not k.startswith("_")} for r in camp], "scope": sc, "adsum": adsum(camp, D["bygrp_cell"], log), "tacos": tacos(camp, D["bygrp_cell"], log),
           "dgmk_room": dgmk_room(S, d0, d1), "adlist_cover": adlist_cover(pr, rates, log),
           "ads": {"rank": rank, "st": ads_st(st, classes, log)}}
    out["_sem"] = sem_by_group(pr, camp, rates, groups)   # dùng cho PL5, không ghi vào D
    log(f"[ads] campthu={len(camp)} dòng, rank={ {k: len(v) for k, v in rank.items()} }, st={ {k: len(v) for k, v in out['ads']['st'].items()} }")
    return out


def sem_by_group(pr, camp, rates, groups):
    """Chi phí quảng cáo thật theo (nhóm, sàn, quốc gia) để tính PL5 -> {key: [các khoản chi]}.
    Wayfair: mỗi khoản = spend của 1 listing trong chiến dịch Thu Ngo (báo cáo PR), nhóm theo tên chiến dịch của listing;
    Amazon: mỗi khoản = spend 1 chiến dịch (campthu). PL5 chia từng khoản cho số SKU rồi cộng lại (đúng cách làm tròn của W39)."""
    out = {}
    for name, p in pr.items():
        cty, cur = ("CAN", "CAD") if name == "DHI" else ("US", "USD"); fx = _usd(cur, rates); sc = _spendcol(p)
        t = p[p.campaign_name.astype(str).str.contains(RX_THU)]
        for lst, g in t.groupby("listing"):
            k = (group_of(g.sort_values("Date").campaign_name.iloc[-1], groups), "Wayfair", cty)
            out.setdefault(k, []).append(round(float(g[sc].sum()) * fx, 2) if fx == 1.0 else float(g[sc].sum()) * fx)
    for r in camp:
        if r["mp"] == "Amazon":
            out.setdefault((r["grp"], "Amazon", r["cty"]), []).append(r["spend"] if r["cur_loc"] == "USD" else r.get("_sp", r["spend"]))
    return out
