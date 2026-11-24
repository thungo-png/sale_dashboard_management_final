"""Tính các khối 'góc nhìn quản trị' cho report từ D (chỉ đọc). Kết quả nhúng vào report dưới dạng window.__PRO,
phần giao diện nằm ở patches/pro.js. Tất cả số liệu lấy lại từ D nên khớp với report."""
from datetime import date
import invnorm
import analysis

TARGET_MARGIN = 10.0     # % margin mục tiêu dùng để tính dư địa quảng cáo
MIN_R = 200              # chỉ xét nhóm×kênh có doanh thu >= (USD)


def _n(x):
    return x if isinstance(x, (int, float)) else 0


def _pct(a, b):
    return round(a / b * 100, 1) if b else 0.0


def _kpi(D):
    cells = D.get("cell") or []
    r, q = sum(_n(c.get("r")) for c in cells), sum(_n(c.get("q")) for c in cells)
    rfc = sum(_n(c.get("rfc")) for c in cells)
    prev = sum(_n(c.get("r")) for c in D.get("cell_prev") or [])
    return {"r": round(r, 2), "q": q, "rfc": round(rfc, 2), "ach": _pct(r, rfc), "r_prev": round(prev, 2),
            "wow": round((r / prev - 1) * 100, 1) if prev else None}


def _bridge(D):
    pl = D.get("pl5") or {}
    t = pl.get("total") or {}
    if not pl.get("available") or not t.get("r"):
        return None
    r = t["r"]
    fees = sum(_n(t.get(k)) for k in ("ref_fee", "return_fee", "wh_fee", "op_fee"))
    items = [("Giá vốn", t.get("cogs", 0)), ("Phí sàn & dịch vụ", fees), ("Vận chuyển / fulfill", t.get("fulfill", 0)), ("Quảng cáo (SEM)", t.get("sem", 0))]
    by = []
    for mc, v in sorted((pl.get("by_mpcty") or {}).items(), key=lambda kv: -kv[1].get("r", 0)):
        sub = [x for x in pl.get("rows") or [] if f"{x.get('mp')}|{x.get('cty')}" == mc]
        sem = sum(_n(x.get("sem")) for x in sub)
        pre = v["profit"] + sem
        by.append({"mc": mc.replace("|", " "), "r": v["r"], "q": v.get("q", 0), "margin": v["margin"],
                   "pre_ads": _pct(pre, v["r"]), "ads": _pct(sem, v["r"])})
    return {"r": r, "items": [{"k": k, "v": round(v, 2), "pct": _pct(v, r)} for k, v in items],
            "profit": t.get("profit", 0), "margin": t.get("margin", 0), "coverage": pl.get("coverage_pct"), "by_mc": by}


def _ads_headroom(D):
    pl = D.get("pl5") or {}
    agg = {}
    for x in pl.get("rows") or []:
        k = (x["grp"], x["mp"], x["cty"])
        a = agg.setdefault(k, [0.0, 0.0, 0.0])
        a[0] += _n(x.get("r")); a[1] += _n(x.get("sem")); a[2] += _n(x.get("profit"))
    out = []
    for (g, mp, cty), (r, sem, pr) in agg.items():
        if r < MIN_R:
            continue
        be, tc = _pct(pr + sem, r), _pct(sem, r)
        head = round(be - tc, 1)
        st = "pre" if be <= 0 else "over" if head < 0 else "tight" if head < 3 else "room"
        out.append({"grp": g, "mp": mp, "cty": cty, "r": round(r), "tacos": tc, "breakeven": be, "headroom": head,
                    "to_target": round(be - TARGET_MARGIN - tc, 1), "st": st})
    out.sort(key=lambda x: x["headroom"])
    return out


def _pareto(D):
    by = {}
    for s in D.get("sku") or []:
        by[s["sku"]] = by.get(s["sku"], 0) + _n(s.get("r"))
    tot = sum(by.values()) or 1
    name = {m["sku"]: m.get("name", "") for m in D.get("sku_meta") or []}
    grp = {s["sku"]: s["grp"] for s in D.get("sku") or []}
    rank = sorted(by.items(), key=lambda kv: -kv[1])
    cum, c, n80 = [], 0, None
    for i, (_, v) in enumerate(rank, 1):
        c += v; cum.append(round(c / tot * 100, 1))
        if n80 is None and c / tot >= 0.8:
            n80 = i

    def hhi(key):
        d = {}
        for s in D.get("sku") or []:
            d[s[key]] = d.get(s[key], 0) + _n(s.get("r"))
        return round(sum((v / tot) ** 2 for v in d.values()) * 10000), d
    h_mp, d_mp = hhi("mp"); h_g, d_g = hhi("grp")
    topmp = max(d_mp.items(), key=lambda kv: kv[1]) if d_mp else ("", 0)
    topg = max(d_g.items(), key=lambda kv: kv[1]) if d_g else ("", 0)
    return {"n": len(rank), "n80": n80, "total": round(tot), "top5": _pct(sum(v for _, v in rank[:5]), tot),
            "top10": _pct(sum(v for _, v in rank[:10]), tot), "curve": cum[:60],
            "top": [{"sku": k, "name": name.get(k, ""), "grp": grp.get(k, ""), "r": round(v), "share": _pct(v, tot)} for k, v in rank[:8]],
            "hhi_mp": h_mp, "hhi_grp": h_g, "top_mp": [topmp[0], _pct(topmp[1], tot)], "top_grp": [topg[0], _pct(topg[1], tot)]}


def _inv(D):
    sk = (D.get("invdet") or {}).get("sku_tot") or []
    low = sorted([s for s in sk if not s.get("disc") and s.get("weeks") is not None and s["weeks"] < 6 and _n(s.get("sold_month")) > 0], key=lambda s: s["weeks"])
    dead = [s for s in sk if _n(s.get("qty")) >= 20 and _n(s.get("sold_month")) == 0]
    bins = [0, 0, 0, 0, 0]       # <4, 4-8, 8-16, 16+, không có đơn
    for s in sk:
        if _n(s.get("qty")) <= 0:
            continue
        w = s.get("weeks")
        bins[4 if w is None else 0 if w < 4 else 1 if w < 8 else 2 if w < 16 else 3] += 1
    lt = (D.get("lt") or {}).get("amz") or {}
    return {"low": [{"sku": s["sku"], "grp": s["grp"], "qty": s["qty"], "weeks": s["weeks"], "sold": s["sold_month"]} for s in low[:10]],
            "n_low": len(low), "dead_n": len(dead), "dead_units": sum(s["qty"] for s in dead), "bins": bins,
            "labels": ["< 4 tuần", "4–8 tuần", "8–16 tuần", "≥ 16 tuần", "Chưa có đơn"],
            "lt_over270": _n(lt.get("over270")), "units": sum(_n(s.get("qty")) for s in sk)}


def _price(D):
    wk = str((D.get("meta") or {}).get("week_no"))
    out = []
    for a in D.get("askuw_mp") or []:
        c = (a.get("cells") or {}).get(wk)
        if not c or not a.get("avg4") or not c.get("asp"):
            continue
        chg = (c["asp"] / a["avg4"] - 1) * 100
        if abs(chg) >= 5:
            out.append({"sku": a["sku"], "name": a.get("name", ""), "mp": a["mp"], "cty": a["cty"], "cur": a.get("cur", ""),
                        "asp": c["asp"], "avg4": a["avg4"], "chg": round(chg, 1), "q": c.get("q", 0)})
    out.sort(key=lambda x: x["chg"])
    return out[:12]


def _trend(D):
    ov = ((D.get("ts_ov") or {}).get("W") or {}).get("mp") or {}
    weeks = (D.get("ts_labels") or {}).get("W") or []
    r = [round(sum(_n((ov.get(mp) or {}).get(str(w), {}).get("r")) for mp in ov), 2) for w in weeks]
    fc = [round(sum(_n((ov.get(mp) or {}).get(str(w), {}).get("rfc")) for mp in ov), 2) for w in weeks]
    ma = [round(sum(r[max(0, i - 3):i + 1]) / len(r[max(0, i - 3):i + 1]), 2) for i in range(len(r))]
    lab = (D.get("meta") or {}).get("weeklab") or {}
    return {"weeks": weeks, "lab": [lab.get(str(w), "") for w in weeks], "r": r, "fc": fc, "ma4": ma}


def _health(D, tasks_sum, extra):
    pl = D.get("pl5") or {}
    cov = pl.get("coverage_pct")
    h = [{"k": "Độ phủ P&L (PL5)", "v": f"{cov:.1f}%" if cov is not None else "n/a", "ok": bool(cov and cov >= 95), "hint": "≥ 95% là đủ tin cậy để đọc margin"}]
    h.append({"k": "Tỷ giá quy đổi", "v": "Cố định theo tuần chốt", "ok": True, "hint": (D.get("fx") or {}).get("source", "")[:140]})
    nsku = (D.get("meta") or {}).get("nsku")
    h.append({"k": "SKU phát sinh doanh thu", "v": str(nsku), "ok": True, "hint": ""})
    for e in extra or []:
        h.append(e)
    if tasks_sum:
        h.append({"k": "Task đang mở", "v": f"{tasks_sum['open']} (quá hạn {tasks_sum['late']})", "ok": tasks_sum["late"] == 0, "hint": "Theo dõi trong app, mục Phân tích & Task"})
    return h


def _questions(issues, bridge, ads, par, inv):
    q = []
    if bridge:
        top = max(bridge["items"], key=lambda i: i["pct"])
        q.append(f"Khoản “{top['k']}” chiếm {top['pct']:.0f}% doanh thu — đội đã có phương án giữ ở mức nào trong 4 tuần tới?")
    pre = [a for a in ads if a["st"] == "pre"]
    if pre:
        q.append(f"{len(pre)} cụm nhóm×kênh có biên trước quảng cáo chưa dương (đứng đầu: {pre[0]['grp']} · {pre[0]['mp']} {pre[0]['cty']}) — giá bán/giá vốn/phí vận chuyển nào cần chỉnh trước, và quảng cáo giữ ở mức tối thiểu thế nào?")
    over = [a for a in ads if a["st"] == "over"]
    if over:
        q.append(f"Có {len(over)} cụm nhóm×kênh chi quảng cáo vượt ngưỡng hoà vốn (đứng đầu: {over[0]['grp']} · {over[0]['mp']} {over[0]['cty']}) — ai điều chỉnh bid và khi nào đo lại?")
    room = [a for a in ads if a["st"] == "room" and a["to_target"] > 3]
    if room:
        q.append(f"{room[0]['grp']} · {room[0]['mp']} {room[0]['cty']} còn dư địa quảng cáo — có nên thử tăng ngân sách có kiểm soát không?")
    if inv["n_low"]:
        q.append(f"{inv['n_low']} SKU còn dưới 6 tuần tồn — kế hoạch nhập hàng và ngày hàng về đã chốt chưa?")
    if par["n80"] and par["n"] and par["n80"] / par["n"] < 0.3:
        q.append(f"{par['n80']} SKU tạo 80% doanh thu — có SKU nào cần bảo vệ riêng (tồn kho, giá, quảng cáo)?")
    rec = [i for i in issues if i["key"].startswith("drop|")]
    if rec:
        q.append(f"{len(rec)} cụm doanh thu chưa giữ được mức tuần trước — nguyên nhân chung là tồn kho, quảng cáo hay listing?")
    return q[:6]


def _brief(D, kpi, bridge, issues):
    m = D.get("meta") or {}
    lines = [f"Sale Report tuần {m.get('week_no')} ({m.get('d0')} → {m.get('d1')})",
             f"Doanh thu ${kpi['r']:,.0f} (đạt {kpi['ach']:.1f}% FC), {kpi['q']} sản phẩm" + (f", so tuần trước {kpi['wow']:+.1f}%" if kpi["wow"] is not None else "")]
    if bridge:
        lines.append(f"Margin PL5 {bridge['margin']:.1f}% (độ phủ {bridge['coverage']:.0f}%)")
    lines.append("")
    lines.append("Điểm cần chú ý & hướng xử lý:")
    for i, x in enumerate(issues[:6], 1):
        lines.append(f"{i}. {x['title']}" + (f" → {x['fix'][0]}" if x["fix"] else ""))
    return "\n".join(lines)


def build(D, tasks_sum=None, norm=None, extra_health=None):
    invnorm.apply(D)
    issues, summary = analysis.analyze(D, norm)
    kpi, bridge, ads, par, inv = _kpi(D), _bridge(D), _ads_headroom(D), _pareto(D), _inv(D)
    ks = ("key", "sev", "area", "title", "where", "detail", "fix") + (("impact", "impact_note") if invnorm.modern() else ())
    top = [{k: i.get(k) for k in ks} for i in issues[:60]]
    return {"generated": date.today().isoformat(), "kpi": kpi, "summary": summary, "issues": top, "bridge": bridge, "ads": ads,
            "pareto": par, "inv": inv, "price": _price(D), "trend": _trend(D), "health": _health(D, tasks_sum, extra_health),
            "questions": _questions(issues, bridge, ads, par, inv), "brief": _brief(D, kpi, bridge, issues), "target_margin": TARGET_MARGIN}


# ---------- Phân loại SKU (ma trận doanh thu × margin) ----------
THIN = ("Biên mỏng", "Bán nhiều, margin dương nhưng chưa tới mức tốt", "Tăng nhẹ giá hoặc giảm chi phí vận chuyển/fulfill để lên mức tốt; tăng quảng cáo khi biên trước QC đã đủ.")
FIX_NEG = ("Cần sửa biên", "Bán nhiều nhưng margin đang âm", "Chỉnh giá bán / giá vốn / vận chuyển trước; đừng tăng quảng cáo khi biên trước QC còn thấp.")
MARGIN_GOOD = 5.0
TREND_MIN_BASE = 500.0     # USD: nền 4 tuần trước nhỏ hơn mức này thì không tính % tăng/giảm (tránh +2550% trên nền vài chục đô)
CLASSES = {
    "star": ("Ngôi sao", "Bán tốt, margin tốt", "Bảo vệ: giữ tồn kho, giữ giá, duy trì quảng cáo hiệu quả."),
    "fix": ("Cần sửa biên", "Bán nhiều nhưng margin thấp", "Chỉnh giá bán / giá vốn / vận chuyển trước; đừng tăng quảng cáo khi biên trước QC còn thấp."),
    "potential": ("Tiềm năng", "Margin tốt, doanh thu còn nhỏ", "Thử tăng hiển thị và quảng cáo có kiểm soát, theo dõi TACoS so với ngưỡng hoà vốn."),
    "exit": ("Cân nhắc rút", "Doanh thu nhỏ và margin thấp", "Rà listing; nếu không cải thiện trong 4–6 tuần thì thanh lý hoặc ngừng nhập."),
    "idle": ("Tồn chưa bán", "Có tồn nhưng không có doanh thu tuần này", "Xem giá, ảnh, từ khoá hoặc đưa vào khuyến mãi để tăng vòng quay."),
    "nodata": ("Chưa đủ dữ liệu phí", "Có doanh thu nhưng chưa có công thức phí P&L", "Bổ sung SKU vào file P&L để đọc được margin."),
}


def sku_class(D):
    modern = invnorm.modern()
    invnorm.apply(D)
    pl = D.get("pl5") or {}
    agg = {}
    for x in pl.get("rows") or []:
        a = agg.setdefault(x["sku"], [0.0, 0.0, 0])
        a[0] += _n(x.get("r")); a[1] += _n(x.get("profit")); a[2] += _n(x.get("q"))
    rev, q = {}, {}
    for s in D.get("sku") or []:
        rev[s["sku"]] = rev.get(s["sku"], 0) + _n(s.get("r")); q[s["sku"]] = q.get(s["sku"], 0) + _n(s.get("q"))
    meta = {m["sku"]: m for m in D.get("sku_meta") or []}
    stock = {s["sku"]: s for s in (D.get("invdet") or {}).get("sku_tot") or []}
    sold = sorted(v for v in rev.values() if v > 0)
    med = sold[len(sold) // 2] if sold else 0
    ser = ((D.get("ts_sku") or {}).get("W") or {}).get("l1") or {}
    weeks = [str(w) for w in (D.get("ts_labels") or {}).get("W") or []]
    out = []
    for sku in set(rev) | set(stock):
        r = rev.get(sku, 0.0); st = stock.get(sku) or {}
        pr = agg.get(sku)
        if r <= 0:
            if _n(st.get("qty")) >= 10 and _n(st.get("sold_month")) == 0:
                cls, mg = "idle", None
            else:
                continue
        elif not pr or pr[0] <= 0:
            cls, mg = "nodata", None
        else:
            mg = pr[1] / pr[0] * 100
            hi = r >= med
            cls = ("star" if mg >= MARGIN_GOOD else ("thin" if (modern and mg >= 0) else "fix")) if hi else ("potential" if mg >= MARGIN_GOOD else "exit")
        t = ser.get(sku) or {}
        last4 = sum(_n((t.get(w) or {}).get("r")) for w in weeks[-4:]); prev4 = sum(_n((t.get(w) or {}).get("r")) for w in weeks[-8:-4])
        m = meta.get(sku, {})
        out.append({"sku": sku, "name": m.get("name", sku), "grp": m.get("grp", ""), "r": round(r, 2), "q": q.get(sku, 0),
                    "margin": None if mg is None else round(mg, 1), "profit": round(pr[1], 2) if pr else None, "cls": cls,
                    "trend4": round((last4 / prev4 - 1) * 100) if prev4 > (TREND_MIN_BASE if modern else 0) else None, "stock": st.get("qty"), "weeks": st.get("weeks")})
    out.sort(key=lambda x: -x["r"])
    cls_tbl = {}
    for k, v in CLASSES.items():
        if modern and k == "fix":
            cls_tbl[k] = FIX_NEG; cls_tbl["thin"] = THIN
        else:
            cls_tbl[k] = v
    cnt = {k: sum(1 for x in out if x["cls"] == k) for k in cls_tbl}
    res = {"rows": out, "counts": cnt, "median_r": round(med, 2), "margin_good": MARGIN_GOOD,
           "classes": {k: {"name": v[0], "desc": v[1], "action": v[2]} for k, v in cls_tbl.items()}}
    if modern:
        res["note"] = "Biên SKU của Amazon dùng chi phí quảng cáo chia đều theo nhóm × quốc gia (chưa có báo cáo theo ASIN) nên chỉ mang tính tham khảo; cột 4 tuần để trống khi nền 4 tuần trước dưới " + str(int(TREND_MIN_BASE)) + " USD."
    return res
