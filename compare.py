"""So sánh hai kỳ: A (kỳ xem) so với B (kỳ gốc). Phân rã thay đổi doanh thu theo SKU×kênh thành
 khối lượng (đổi SL ở giá cũ) + giá (đổi giá ở SL mới) + mới bán + ngừng bán — tổng khớp chính xác ΔDT."""


def _n(x):
    return x if isinstance(x, (int, float)) else 0


def _tot(D):
    cells = D.get("cell") or []
    t = (D.get("pl5") or {}).get("total") or {}
    r, q = sum(_n(c.get("r")) for c in cells), sum(_n(c.get("q")) for c in cells)
    fees = sum(_n(t.get(k)) for k in ("ref_fee", "return_fee", "wh_fee", "op_fee"))
    return {"r": r, "q": q, "asp": r / q if q else 0, "pl_r": t.get("r", 0), "cogs": t.get("cogs", 0), "fees": fees, "fulfill": t.get("fulfill", 0),
            "sem": t.get("sem", 0), "profit": t.get("profit", 0), "margin": t.get("margin"), "pl_ok": bool((D.get("pl5") or {}).get("available")),
            "v2": bool((D.get("pl5") or {}).get("_v2")), "ndays": (D.get("meta") or {}).get("ndays"), "wk": (D.get("meta") or {}).get("week_no"),
            "range": f"{(D.get('meta') or {}).get('d0', '')} → {(D.get('meta') or {}).get('d1', '')}"}


def compare(A, B, norm=None):
    ta, tb = _tot(A), _tot(B)
    key = lambda s: (s["sku"], s["mp"], s["cty"])
    a = {key(s): s for s in A.get("sku") or []}
    b = {key(s): s for s in B.get("sku") or []}
    name = {m["sku"]: m.get("name", "") for m in (A.get("sku_meta") or []) + (B.get("sku_meta") or [])}
    eff = {"volume": 0.0, "price": 0.0, "new": 0.0, "lost": 0.0}
    rows = []
    for k in set(a) | set(b):
        s1, s0 = a.get(k), b.get(k)
        r1, q1 = (_n(s1["r"]), _n(s1["q"])) if s1 else (0.0, 0)
        r0, q0 = (_n(s0["r"]), _n(s0["q"])) if s0 else (0.0, 0)
        if q0 > 0 and q1 > 0:
            p0 = r0 / q0; v = (q1 - q0) * p0; p = r1 - r0 - v
            eff["volume"] += v; eff["price"] += p
        elif q1 > 0 and q0 == 0:
            eff["new"] += r1 - r0
        elif q0 > 0 and q1 == 0:
            eff["lost"] += r1 - r0
        else:
            eff["new"] += r1 - r0                      # chỉ có doanh thu không SL (hiếm) — gộp vào "mới"
        grp = (s1 or s0)["grp"]
        rows.append({"sku": k[0], "name": name.get(k[0], k[0]), "grp": (norm or {}).get(grp, grp), "mp": k[1], "cty": k[2], "r1": r1, "r0": r0, "d": r1 - r0, "q1": q1, "q0": q0})
    by_grp, by_sku = {}, {}
    for x in rows:
        g = by_grp.setdefault(x["grp"], [0.0, 0.0]); g[0] += x["r1"]; g[1] += x["r0"]
        s = by_sku.setdefault(x["sku"], {"sku": x["sku"], "name": x["name"], "grp": x["grp"], "r1": 0.0, "r0": 0.0}); s["r1"] += x["r1"]; s["r0"] += x["r0"]
    grp_rows = sorted(({"grp": g, "r1": v[0], "r0": v[1], "d": v[0] - v[1]} for g, v in by_grp.items()), key=lambda x: x["d"])
    sku_rows = sorted(({**v, "d": v["r1"] - v["r0"]} for v in by_sku.values()), key=lambda x: x["d"])
    dr = ta["r"] - tb["r"]
    dsku = sum(x["d"] for x in rows)                 # tổng thay đổi theo dòng SKU×kênh (= tổng 4 yếu tố)
    other = dr - dsku                                  # phần chênh giữa tổng ô (cell) và tổng dòng SKU
    if abs(other) >= 1:
        eff["other"] = other
    pl = None
    if ta["pl_ok"] and tb["pl_ok"]:
        pl = {"items": [{"k": k, "a": ta[f], "b": tb[f], "d": ta[f] - tb[f]} for k, f in
                        (("Doanh thu (P&L)", "pl_r"), ("Giá vốn", "cogs"), ("Phí sàn & dịch vụ", "fees"), ("Vận chuyển / fulfill", "fulfill"), ("Quảng cáo (SEM)", "sem"), ("Lợi nhuận", "profit"))],
              "margin_a": ta["margin"], "margin_b": tb["margin"]}
    warn = []
    if ta["ndays"] != tb["ndays"]:
        warn.append(f"Hai kỳ dài khác nhau ({ta['ndays']} và {tb['ndays']} ngày) — nên đọc theo trung bình ngày.")
    if pl and ta["v2"] != tb["v2"]:
        warn.append("Công thức P&L của hai kỳ khác nhau (file P&L đổi bố cục) — margin không so sánh trực tiếp được.")
    if not (ta["pl_ok"] and tb["pl_ok"]):
        warn.append("Một trong hai kỳ chưa có dữ liệu P&L nên không so sánh được lợi nhuận.")
    top = max(((k, v) for k, v in eff.items() if k != "other"), key=lambda kv: abs(kv[1]))
    lab = {"other": "chênh lệch nguồn dữ liệu (tổng ô so với dòng SKU)", "volume": "thay đổi số lượng bán", "price": "thay đổi giá bán thực hiện", "new": "SKU/kênh mới phát sinh", "lost": "SKU/kênh không còn bán"}
    summary = (f"Doanh thu {'tăng' if dr >= 0 else 'giảm'} ${abs(dr):,.0f} ({(dr / tb['r'] * 100 if tb['r'] else 0):+.1f}%). "
               f"Yếu tố ảnh hưởng lớn nhất là {lab[top[0]]} ({'+' if top[1] >= 0 else '−'}${abs(top[1]):,.0f}).")
    return {"a": ta, "b": tb, "dr": dr, "dsku": dsku, "effects": [{"k": k, "v": v} for k, v in eff.items()], "grp": grp_rows, "sku": sku_rows,
            "pl": pl, "warn": warn, "summary": summary}
