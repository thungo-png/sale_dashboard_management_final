"""Tách D theo quốc gia để tính lại các khối 'góc nhìn quản trị' (Điều cần chú ý, Phân loại SKU, Rủi ro tồn kho, Cầu lợi nhuận...)
riêng cho từng quốc gia. Chỉ đọc D, trả bản sao đã lọc; dùng lại đúng insights/analysis nên logic giống bản toàn cầu."""
import copy

NUM = ("r", "cogs", "ref_fee", "sem", "return_fee", "wh_fee", "op_fee", "fulfill", "tong_cp", "profit", "q")


def _n(x):
    return x if isinstance(x, (int, float)) else 0


def _last4(row, wk):
    return sum(_n(((row or {}).get(w) or {}).get("q")) for w in wk) / 4.0


def for_country(D, c):
    X = {k: v for k, v in D.items()}                      # nông; chỉ thay các khối có chiều quốc gia
    f = lambda rows: [x for x in rows or [] if x.get("cty") == c]
    X["cell"], X["cell_prev"] = f(D.get("cell")), f(D.get("cell_prev"))
    X["sku"] = f(D.get("sku"))
    X["tacos"], X["campthu"] = f(D.get("tacos")), f(D.get("campthu"))
    X["askuw_mp"] = f(D.get("askuw_mp"))
    X["grpcmp"] = dict(D.get("grpcmp") or {}); X["grpcmp"]["rows"] = f((D.get("grpcmp") or {}).get("rows"))
    # nhóm sản phẩm
    g = {}
    for s in X["sku"]:
        a = g.setdefault(s["grp"], {"grp": s["grp"], "q": 0, "r": 0.0, "qfc": 0.0, "rfc": 0.0})
        for k in ("q", "r", "qfc", "rfc"):
            a[k] += _n(s.get(k))
    X["bygrp"] = list(g.values())
    # PL5
    pl = copy.deepcopy(D.get("pl5") or {})
    rows = f(pl.get("rows"))
    pl["rows"] = rows
    t = {k: round(sum(_n(x.get(k)) for x in rows), 2) for k in NUM if k != "q"}
    t["margin"] = round(t["profit"] / t["r"] * 100, 2) if t["r"] else 0.0
    t["sem_unalloc"] = 0
    pl["total"] = t
    pl["by_mpcty"] = {k: v for k, v in (pl.get("by_mpcty") or {}).items() if k.endswith("|" + c)}
    pl["by_grp"] = {}
    for x in rows:
        a = pl["by_grp"].setdefault(x["grp"], {"r": 0.0, "profit": 0.0, "q": 0})
        a["r"] += _n(x.get("r")); a["profit"] += _n(x.get("profit")); a["q"] += _n(x.get("q"))
    for a in pl["by_grp"].values():
        a["margin"] = round(a["profit"] / a["r"] * 100, 2) if a["r"] else 0.0
    pl["prev_total"] = None
    X["pl5"] = pl
    # chuỗi tuần theo SKU của quốc gia: l1 dựng từ l2 'sku · cty'
    ts = copy.copy(D.get("ts_sku") or {})
    W = dict((ts.get("W") or {}))
    l2 = {k: v for k, v in (W.get("l2") or {}).items() if k.endswith(" · " + c)}
    W["l1"] = {k.rsplit(" · ", 1)[0]: v for k, v in l2.items()}
    W["l2"] = l2
    ts["W"] = {**W}; X["ts_sku"] = ts
    to = copy.copy(D.get("ts_ov") or {})
    Wo = dict(to.get("W") or {})
    Wo["mp"] = {k.split(" · ")[0]: v for k, v in (Wo.get("mpcty") or {}).items() if k.endswith(" · " + c)}
    to["W"] = Wo; X["ts_ov"] = to
    # tồn kho
    inv = copy.deepcopy(D.get("invdet") or {})
    wk = [str(w) for w in ((D.get("ts_labels") or {}).get("W") or [])][-4:]
    sk = []
    for s in inv.get("sku_tot") or []:
        q = _n((s.get("by_cty") or {}).get(c))
        a = _last4(W["l1"].get(s["sku"]), wk) if len(wk) == 4 else _n(s.get("sold_month"))
        s["by_cty"] = {c: q}; s["qty"] = q
        s["sold_month"] = round(a, 2); s["weeks"] = round(q / a, 1) if a > 0 and q > 0 else None
        if q > 0 or a > 0:
            sk.append(s)
    inv["sku_tot"] = sk
    inv["rows"] = f(inv.get("rows"))
    st = {}
    for r in inv["rows"]:
        st[r["stlab"]] = st.get(r["stlab"], 0) + _n(r.get("qty"))
    inv["st_totals"] = [{"stlab": k, "qty": v} for k, v in st.items()]
    inv["cty_totals"] = [x for x in inv.get("cty_totals") or [] if x.get("cty") == c]
    inv["qty_total"] = sum(_n(r.get("qty")) for r in inv["rows"])
    inv["nsku"] = len({r["sku"] for r in inv["rows"] if _n(r.get("qty")) > 0})
    mx = {}
    for r in inv["rows"]:
        k = (r["grp"], r["stlab"]); mx[k] = mx.get(k, 0) + _n(r.get("qty"))
    inv["matrix"] = [{"grp": k[0], "stlab": k[1], "qty": v} for k, v in mx.items()]
    inv["basis"] = "avg4"
    X["invdet"] = inv
    ia = dict(D.get("invacct") or {})
    ia["rows"] = f(ia.get("rows")); ia["det"] = f(ia.get("det"))
    ia["qty_total"] = sum(_n(r.get("qty")) for r in ia["rows"])
    X["invacct"] = ia
    lt = copy.deepcopy(D.get("lt") or {})
    for k in ("amz", "wf"):
        L = lt.get(k)
        if not L:
            continue
        L["summary"] = f(L.get("summary")); L["sku"] = f(L.get("sku"))
        L["tot"] = sum(_n(x.get("tot")) for x in L["sku"])
        L["n_sku"] = len({x["sku"] for x in L["sku"]})
        L["over270"] = sum(sum(x.get("buckets", [])[3:]) for x in L["sku"])
    X["lt"] = lt
    return X


def build_all(D, build_fn, class_fn):
    """build_fn(D) -> extras gốc của insights.build; class_fn(D) -> sku_class. Trả {cty: {...}} chỉ các khoá phụ thuộc dữ liệu."""
    out = {}
    keys = ("kpi", "summary", "issues", "bridge", "ads", "pareto", "inv", "price", "trend", "questions", "brief")
    for c in (D.get("meta") or {}).get("ctys") or []:
        try:
            Xc = for_country(D, c)
            e = build_fn(Xc)
            o = {k: e.get(k) for k in keys}
            o["sku_class"] = class_fn(Xc)
            out[c] = o
        except Exception as ex:
            out[c] = {"error": f"{type(ex).__name__}: {ex}"[:200]}
    return out
