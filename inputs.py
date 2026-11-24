"""Dữ liệu đầu vào bổ sung (data/inputs.json): giá vốn, lead time, MOQ, tồn an toàn từng SKU → điểm đặt hàng;
mục tiêu; sổ ghi chú "dữ liệu còn thiếu". Giá trị chưa có được GIẢ LẬP (cố định theo SKU, gắn nhãn 'sim')
để dùng thử tính năng; khi người dùng nhập thật thì nhãn đổi thành 'user' và không bị ghi đè."""
import hashlib, json, math, os, threading, uuid
import invnorm
from datetime import datetime, timedelta
from pathlib import Path

FILE = Path(__file__).parent / "data" / "inputs.json"
LOCK = threading.Lock()
FIELDS = ("cost", "lead", "moq", "safety")
TARGETS = {
    "margin": ("Biên lợi nhuận PL5 mục tiêu (%)", 10.0),
    "tacos": ("TACoS mục tiêu (%)", 12.0),
    "weeks_cover": ("Số tuần tồn mong muốn", 8.0),
    "rev_week": ("Doanh thu tuần mục tiêu (USD)", None),   # mặc định = tuần gần nhất × 1.05
}
REGISTER0 = [
    ("Giá vốn (COGS)", "Giá vốn thật từng SKU", "Tính biên theo SKU, định giá, điểm hoà vốn quảng cáo", "gia_lap", "Có sẵn trong P&L cho SKU đã có công thức; SKU còn lại đang giả lập = 35–45% giá bán."),
    ("Nhập hàng", "Lead time từng SKU / nhà cung cấp (ngày)", "Tính điểm đặt hàng và ngày phải đặt", "gia_lap", "Đang giả lập 30–60 ngày."),
    ("Nhập hàng", "MOQ & bội số đặt hàng", "Số lượng đề xuất đặt", "gia_lap", "Đang giả lập 20–60 cái."),
    ("Nhập hàng", "Tồn an toàn (ngày bán)", "Đệm khi lead time dao động", "gia_lap", "Đang đặt mặc định 14 ngày."),
    ("Nhập hàng", "Hàng đang về / PO đã đặt (số lượng, ngày dự kiến)", "Trừ vào nhu cầu để khỏi đặt trùng", "thieu", ""),
    ("Mục tiêu", "Mục tiêu doanh thu, biên, TACoS theo tuần/tháng", "So sánh thực tế với kế hoạch", "gia_lap", "Đang giả lập: doanh thu = tuần gần nhất × 1.05, biên 10%, TACoS 12%."),
    ("Giá", "Giá sàn và giá niêm yết từng SKU", "Mô phỏng 'nếu giảm giá X%' không lỗ", "thieu", ""),
    ("Giá", "Phí vận chuyển / nhập khẩu về kho (landed cost)", "Giá vốn đầy đủ thay vì chỉ giá xuất xưởng", "thieu", ""),
    ("Quảng cáo", "Ngân sách quảng cáo theo tháng / kênh", "Cảnh báo vượt ngân sách", "thieu", ""),
    ("Kế hoạch", "Lịch sự kiện (Prime Day, BFCM, Wayfair Way Day…)", "Dự báo nhu cầu và đặt hàng trước mùa cao điểm", "thieu", ""),
    ("Tồn kho", "Tồn kho theo kho / nhà cung cấp ngoài Amazon, Wayfair", "Tổng tồn thật để tính điểm đặt hàng", "thieu", ""),
]
STATUS = {"thieu": "Chưa có", "gia_lap": "Đang giả lập", "da_co": "Đã có dữ liệu thật"}


def _load():
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        d = {}
    d.setdefault("skus", {}); d.setdefault("targets", {}); d.setdefault("register", None)
    if d["register"] is None:
        d["register"] = [{"id": uuid.uuid4().hex[:8], "area": a, "item": i, "why": w, "status": s, "owner": "", "note": n, "updated": ""}
                         for a, i, w, s, n in REGISTER0]
        _save(d)
    return d


def _save(d):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp"); tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8"); os.replace(tmp, FILE)


def _n(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _h(sku, salt):
    return int(hashlib.md5(f"{salt}:{sku}".encode()).hexdigest()[:8], 16)


def _sim(sku, asp):
    return {"cost": round(asp * (0.35 + (_h(sku, "c") % 11) / 100), 2), "lead": 30 + _h(sku, "l") % 31,
            "moq": 20 + 10 * (_h(sku, "m") % 5), "safety": 14}


def _skus(D):
    """SKU → thông tin từ D: tên, nhóm, giá bán TB, giá vốn P&L (nếu có), tồn, bán/tháng, doanh thu."""
    meta = {m["sku"]: m for m in D.get("sku_meta") or []}
    inv = {s["sku"]: s for s in (D.get("invdet") or {}).get("sku_tot") or []}
    r, q = {}, {}
    for s in D.get("sku") or []:
        r[s["sku"]] = r.get(s["sku"], 0) + _n(s.get("r")); q[s["sku"]] = q.get(s["sku"], 0) + _n(s.get("q"))
    pl = {}
    for x in (D.get("pl5") or {}).get("rows") or []:
        a = pl.setdefault(x["sku"], [0.0, 0.0]); a[0] += _n(x.get("cogs")); a[1] += _n(x.get("q"))
    grp_asp = {}
    for sku, rv in r.items():
        g = (meta.get(sku) or inv.get(sku) or {}).get("grp", "")
        a = grp_asp.setdefault(g, [0.0, 0.0]); a[0] += rv; a[1] += q.get(sku, 0)
    out = {}
    for sku in set(meta) | set(inv) | set(r):
        if (inv.get(sku) or {}).get("disc"):
            continue          # SKU ngưng kinh doanh: không tính điểm đặt hàng
        m = meta.get(sku) or {}; st = inv.get(sku) or {}
        grp = m.get("grp") or st.get("grp", "")
        asp = r[sku] / q[sku] if q.get(sku) else 0
        if asp <= 0:
            g = grp_asp.get(grp)
            asp = g[0] / g[1] if g and g[1] else 150.0
        p = pl.get(sku)
        out[sku] = {"sku": sku, "name": m.get("name") or sku, "grp": grp, "asp": round(asp, 2),
                    "pl_cost": round(p[0] / p[1], 2) if p and p[1] > 0 and p[0] > 0 else None,
                    "stock": _n(st.get("qty")), "sold_period": _n(st.get("sold_month")),   # 'sold_month' trong data.json thực chất là SL bán trong kỳ (cột "SL bán tuần")
                     "rev": round(r.get(sku, 0), 2)}
    return out


def build(D, today=None):
    """Bảng đầu vào + điểm đặt hàng cho từng SKU. today: để test."""
    today = today or datetime.now().date()
    invnorm.apply(D)
    nd = max(1.0, _n((D.get("meta") or {}).get("ndays")) or 7.0)
    with LOCK:
        d = _load(); changed = False
        rows = []
        for sku, b in sorted(_skus(D).items(), key=lambda kv: -kv[1]["rev"]):
            s = d["skus"].setdefault(sku, {"src": {}}); sim = _sim(sku, b["asp"])
            src = s.setdefault("src", {})
            for f in FIELDS:
                if src.get(f) == "user" and s.get(f) is not None:
                    continue
                if f == "cost" and b["pl_cost"] is not None:
                    v, sc = b["pl_cost"], "pl"
                else:
                    v, sc = sim[f], "sim"
                if s.get(f) != v or src.get(f) != sc:
                    s[f] = v; src[f] = sc; changed = True
            vel = b["sold_period"] / nd   # đơn vị/ngày: bán trong kỳ báo cáo ÷ số ngày của kỳ
            lead, saf, moq = _n(s["lead"]), _n(s["safety"]), max(1, int(_n(s["moq"])))
            rop = math.ceil(vel * (lead + saf))
            stock = b["stock"]
            cover = stock / vel if vel > 0 else None
            if vel <= 0:
                stt = "none"
            elif stock <= rop:
                stt = "now"
            elif stock <= rop * 1.3:
                stt = "soon"
            else:
                stt = "ok"
            need = math.ceil(vel * (lead + saf + 30)) - stock
            qty = int(math.ceil(max(need, 0) / moq) * moq) if stt in ("now", "soon") else 0
            if stt in ("now", "soon") and qty < moq:
                qty = moq
            order_by = None
            if vel > 0 and (stock - rop) / vel < 365:
                order_by = (today + timedelta(days=max(0, int((stock - rop) / vel)))).isoformat()
            rows.append({**b, "cost": s["cost"], "lead": s["lead"], "moq": s["moq"], "safety": s["safety"], "src": dict(src),
                         "note": s.get("note", ""), "vel": round(vel, 2), "rop": rop, "cover_days": None if cover is None else round(cover),
                         "status": stt, "order_qty": qty, "order_by": order_by,
                         "stockout": None if vel <= 0 else (today + timedelta(days=int(cover))).isoformat(),
                         "cost_pct": round(s["cost"] / b["asp"] * 100, 1) if b["asp"] else None, "stock_value": round(stock * s["cost"], 2)})
        tg = _targets(d, D); changed = d.pop("_tg_changed", False) or changed
        if changed:
            _save(d)
        cnt = {k: sum(1 for r in rows if r["status"] == k) for k in ("now", "soon", "ok", "none")}
        n_sim = sum(1 for r in rows if "sim" in r["src"].values())
        summ = {"n": len(rows), "counts": cnt, "n_sim": n_sim, "n_pl": sum(1 for r in rows if r["src"].get("cost") == "pl"),
                "stock_value": round(sum(r["stock_value"] for r in rows), 2), "reorder_value": round(sum(r["order_qty"] * r["cost"] for r in rows), 2)}
        return {"rows": rows, "summary": summ, "targets": tg, "register": d["register"], "status": STATUS}


def _targets(d, D):
    t = d["targets"]; out = []
    wk = (D.get("ts_ov") or {})
    last = _n((D.get("cell") and sum(_n(c.get("r")) for c in D["cell"])) or 0)
    for k, (label, dflt) in TARGETS.items():
        cur = t.get(k)
        if cur is None or (cur.get("src") == "sim" and k == "rev_week" and cur["v"] != round(last * 1.05, 0)):
            v = round(last * 1.05, 0) if k == "rev_week" else dflt
            cur = t[k] = {"v": v, "src": "sim"}; d["_tg_changed"] = True
        out.append({"key": k, "label": label, "v": cur["v"], "src": cur["src"]})
    return out


def set_sku(sku, vals):
    with LOCK:
        d = _load(); s = d["skus"].setdefault(sku, {"src": {}}); src = s.setdefault("src", {})
        for f in FIELDS:
            if f in vals and vals[f] not in (None, ""):
                try:
                    v = float(vals[f])
                except (TypeError, ValueError):
                    raise ValueError(f"Giá trị {f} không hợp lệ")
                if v < 0 or (f != "cost" and v == 0 and f != "safety"):
                    raise ValueError(f"Giá trị {f} không hợp lệ")
                s[f] = int(v) if f != "cost" else round(v, 2); src[f] = "user"
        if "note" in vals:
            s["note"] = str(vals["note"] or "")[:300]
        _save(d); return s


def reset_sku(sku):
    with LOCK:
        d = _load(); d["skus"].pop(sku, None); _save(d)


def set_target(key, v):
    if key not in TARGETS:
        raise ValueError("Mục tiêu không tồn tại")
    try:
        v = float(v)
    except (TypeError, ValueError):
        raise ValueError("Giá trị không hợp lệ")
    if v < 0:
        raise ValueError("Giá trị không hợp lệ")
    with LOCK:
        d = _load(); d["targets"][key] = {"v": v, "src": "user"}; _save(d)


def reg_save(rid, vals, new=False):
    with LOCK:
        d = _load(); now = datetime.now().isoformat(timespec="seconds")
        if new:
            if not (vals.get("item") or "").strip():
                raise ValueError("Cần nhập tên mục dữ liệu")
            x = {"id": uuid.uuid4().hex[:8], "area": "", "item": "", "why": "", "status": "thieu", "owner": "", "note": "", "updated": now}
            d["register"].append(x)
        else:
            x = next((r for r in d["register"] if r["id"] == rid), None)
            if not x:
                raise ValueError("Không có mục này")
        for k in ("area", "item", "why", "owner", "note"):
            if k in vals:
                x[k] = str(vals[k] or "")[:300]
        if vals.get("status") in STATUS:
            x["status"] = vals["status"]
        x["updated"] = now; _save(d); return x


def reg_del(rid):
    with LOCK:
        d = _load(); d["register"] = [r for r in d["register"] if r["id"] != rid]; _save(d)


def reorder_map(D):
    """Gọn cho report: SKU → điểm đặt hàng, trạng thái, SL đề xuất (để cột 'Đặt hàng' trong bảng tồn kho dùng chung một nguồn)."""
    out = {}
    for r in build(D)["rows"]:
        out[r["sku"]] = {"rop": r["rop"], "lead": r["lead"], "moq": r["moq"], "st": r["status"], "qty": r["order_qty"], "by": r["order_by"],
                         "sim": "sim" in r["src"].values()}
    return out
