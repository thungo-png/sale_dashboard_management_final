"""Cảnh báo chủ động + 'Việc hôm nay' + bản tin định kỳ (email / webhook).
CLI (chạy bằng cron/launchd trên máy chạy app):
   python3 alerts.py weekly [--send]    # bản tin điều hành đầy đủ (sáng thứ Hai)
   python3 alerts.py events [--send]    # chỉ cảnh báo MỚI chưa gửi (chạy mỗi vài giờ)
Cấu hình gửi trong data/config.json:
   "notify": {"email": {"host":"smtp.gmail.com","port":587,"user":"a@x.com","pass_env":"SRM_SMTP_PASS","from":"a@x.com","to":["b@x.com"]},
              "webhook": {"url":"https://...","field":"text"}}
Mật khẩu SMTP lấy từ biến môi trường (pass_env), không lưu trong file."""
import json, os, smtplib, sys, urllib.request
import invnorm
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import insights, tasks

STATE = Path(__file__).parent / "data" / "alert_state.json"
LEVELS = {"urgent": "Khẩn", "warn": "Cần xử lý", "info": "Theo dõi"}


def _a(key, level, area, title, detail="", fix="", **link):
    return {"key": key, "level": level, "area": area, "title": title, "detail": detail, "fix": fix, "link": link}


def _n0(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def compute(D, norm=None, today=None):
    """Danh sách cảnh báo của một kỳ (đã sắp xếp: khẩn trước)."""
    X = insights.build(D, None, norm)
    out = []
    for s in X["inv"]["low"]:
        if s["weeks"] < 2:
            out.append(_a(f"stock2|{s['sku']}", "urgent", "Tồn kho", f"SKU {s['sku']} chỉ còn đủ ~{s['weeks']:.1f} tuần bán", f"Tồn {s['qty']}, bán {s['sold']}/tuần.",
                          "Chốt lịch nhập bổ sung; nếu hàng về chậm, giảm quảng cáo để tránh hết hàng giữa chừng.", sku=s["sku"]))
        elif s["weeks"] < 4:
            out.append(_a(f"stock4|{s['sku']}", "warn", "Tồn kho", f"SKU {s['sku']} còn đủ ~{s['weeks']:.1f} tuần bán", f"Tồn {s['qty']}.", "Lên kế hoạch nhập hàng.", sku=s["sku"]))
    try:
        import inputs
        for r in inputs.build(D)["rows"]:
            if r["status"] == "now":
                sim = " (lead time/MOQ đang giả lập — cập nhật ở 📥 Dữ liệu đầu vào)" if "sim" in r["src"].values() else ""
                out.append(_a(f"reorder|{r['sku']}", "urgent" if (r["cover_days"] or 0) < _n0(r["lead"]) else "warn", "Tồn kho",
                              f"SKU {r['sku']} đã tới điểm đặt hàng",
                              f"Tồn {int(r['stock'])} ≤ điểm đặt {r['rop']} (bán {r['vel']}/ngày, lead time {int(r['lead'])} ngày){sim}.",
                              f"Chốt PO khoảng {r['order_qty']} cái, kiểm tra hàng đang về.", sku=r["sku"]))
    except Exception:
        pass
    for i in X["issues"]:
        if i["key"].startswith("drop|"):
            zero = any("$0 so với" in d for d in i["detail"])
            out.append(_a(i["key"], "urgent" if zero else "warn", "Doanh số", i["title"], "; ".join(i["detail"][:2]), i["fix"][0] if i["fix"] else "", grp=i["key"].split("|")[1]))
    for a in X["ads"]:
        if a["st"] == "over" and a["r"] >= 1000:
            out.append(_a(f"ads|{a['grp']}|{a['mp']}|{a['cty']}", "warn", "Quảng cáo", f"Chi quảng cáo vượt ngưỡng hoà vốn: {a['grp']} · {a['mp']} {a['cty']}",
                          f"TACoS {a['tacos']}% so với hoà vốn {a['breakeven']}%.", "Hạ bid/ngân sách campaign hiệu quả thấp, đo lại sau 3–5 ngày.", grp=a["grp"]))
    for p in X["price"]:
        if p["chg"] <= -15 and p["q"] >= 3:
            out.append(_a(f"price|{p['sku']}|{p['mp']}|{p['cty']}", "warn", "Giá", f"Giá bán {p['sku']} ({p['mp']} {p['cty']}) thấp hơn nền 4 tuần {abs(p['chg']):.0f}%",
                          f"{p['asp']:.2f} so với {p['avg4']:.2f} {p['cur']}.", "Xác nhận đây là khuyến mãi chủ động hay bị đối thủ kéo giá.", sku=p["sku"]))
    pl = D.get("pl5") or {}
    if pl.get("available") and (pl.get("coverage_pct") or 100) < 95:
        out.append(_a("health|pl5", "warn", "Dữ liệu", f"Độ phủ P&L chỉ {pl['coverage_pct']:.1f}%", "Margin có thể chưa phản ánh đủ.", "Bổ sung SKU còn thiếu vào file P&L."))
    if X["inv"]["lt_over270"] > 0:
        out.append(_a("lt270", "info", "Tồn kho", f"{X['inv']['lt_over270']} sản phẩm FBA tồn trên 270 ngày", "", "Xử lý trước kỳ tính phí lưu kho dài hạn."))
    rank = {"urgent": 0, "warn": 1, "info": 2}
    out.sort(key=lambda a: (rank[a["level"]], a["area"], a["key"]))
    return out, X


def task_alerts(today=None):
    today = today or datetime.now().date().isoformat()
    soon = (datetime.now().date() + timedelta(days=2)).isoformat()
    op = [t for t in tasks.list_tasks() if t["status"] in ("todo", "doing")]
    late = sorted([t for t in op if t.get("due") and t["due"] < today], key=lambda t: t["due"])
    due = sorted([t for t in op if t.get("due") and today <= t["due"] <= soon], key=lambda t: t["due"])
    return late, due, op


def cockpit(D, period, norm=None):
    invnorm.apply(D)
    alerts, X = compute(D, norm)
    late, due, op = task_alerts()
    sc = insights.sku_class(D)
    k = X["kpi"]
    b = X["bridge"]
    return {"period": period, "week": (D.get("meta") or {}).get("week_no"), "range": X["summary"]["range"],
            "kpi": {"r": k["r"], "wow": k["wow"], "ach": k["ach"], "margin": b["margin"] if b else None},
            "alerts": alerts, "tasks": {"late": late[:8], "due": due[:8], "open": len(op)},
            "sku_counts": sc["counts"], "sku_names": {kk: v["name"] for kk, v in sc["classes"].items()},
            "ads_focus": [a for a in X["ads"] if a["st"] in ("pre", "over") and a["r"] >= 500][:5],
            "room": [a for a in X["ads"] if a["st"] == "room" and a["to_target"] > 3][:3], "questions": X["questions"]}


def digest_text(c, mode="weekly", new_keys=None):
    L = [f"Sale Report tuần {c['week']} ({c['range']})"]
    k = c["kpi"]
    L.append(f"Doanh thu ${k['r']:,.0f}" + (f" ({k['wow']:+.1f}% so tuần trước)" if k["wow"] is not None else "") + f", đạt {k['ach']:.1f}% FC" + (f", margin PL5 {k['margin']:.1f}%" if k["margin"] is not None else ""))
    al = [a for a in c["alerts"] if (new_keys is None or a["key"] in new_keys)]
    if mode == "events" and not al and not c["tasks"]["late"]:
        return ""
    for lv in ("urgent", "warn", "info"):
        sel = [a for a in al if a["level"] == lv][: (12 if mode == "weekly" else 8)]
        if sel and (lv != "info" or mode == "weekly"):
            L += ["", f"{LEVELS[lv]}:"] + [f"- {a['title']}" + (f" → {a['fix']}" if a["fix"] else "") for a in sel]
    if c["tasks"]["late"]:
        L += ["", f"Task quá hạn ({len(c['tasks']['late'])}):"] + [f"- {t['title']} (hạn {t['due']}, {t.get('owner') or 'chưa giao'})" for t in c["tasks"]["late"][:6]]
    if mode == "weekly" and c["questions"]:
        L += ["", "Câu hỏi cho buổi họp:"] + [f"- {q}" for q in c["questions"][:4]]
    return "\n".join(L)


def send(text, subject, cfg):
    n = (cfg or {}).get("notify") or {}
    res = {"email": None, "webhook": None}
    e = n.get("email")
    if e and e.get("to"):
        try:
            m = EmailMessage(); m["Subject"] = subject; m["From"] = e.get("from") or e.get("user"); m["To"] = ", ".join(e["to"]); m.set_content(text)
            with smtplib.SMTP(e["host"], int(e.get("port", 587)), timeout=20) as s:
                if e.get("tls", True):
                    s.starttls()
                if e.get("user"):
                    s.login(e["user"], os.environ.get(e.get("pass_env", "SRM_SMTP_PASS"), ""))
                s.send_message(m)
            res["email"] = "ok"
        except Exception as x:
            res["email"] = f"lỗi: {x}"
    w = n.get("webhook")
    if w and w.get("url"):
        try:
            body = json.dumps({w.get("field", "text"): text}).encode()
            urllib.request.urlopen(urllib.request.Request(w["url"], body, {"Content-Type": "application/json"}), timeout=15).read()
            res["webhook"] = "ok"
        except Exception as x:
            res["webhook"] = f"lỗi: {x}"
    return res


def _state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"sent": []}


def run(mode, do_send, load_cfg, latest):
    """latest() -> (period_id, D) của kỳ build mới nhất."""
    pid, D = latest()
    if D is None:
        return "Chưa có kỳ nào được build.", None
    cfg = load_cfg()
    c = cockpit(D, pid, cfg.get("group_norm"))
    st = _state()
    new = None
    if mode == "events":
        urgent_keys = {a["key"] for a in c["alerts"] if a["level"] in ("urgent", "warn")}
        new = urgent_keys - set(st.get("sent", []))
    text = digest_text(c, mode, new)
    res = None
    if text and do_send:
        res = send(text, f"[Sale Report] {'Bản tin tuần' if mode == 'weekly' else 'Cảnh báo mới'} W{c['week']}", cfg)
        if mode == "events" and res and any(v == "ok" for v in res.values()):
            st["sent"] = sorted(set(st.get("sent", [])) | (new or set()))[-500:]
            STATE.parent.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps(st), encoding="utf-8")
    return text or "(không có cảnh báo mới)", res


if __name__ == "__main__":
    import server
    a = sys.argv[1:]
    mode = a[0] if a and a[0] in ("weekly", "events") else "weekly"

    def latest():
        for m in server.list_periods():
            f = server.pdir(m["id"]) / "data.json"
            if m["status"] == "built" and f.exists():
                return m["id"], json.loads(f.read_text(encoding="utf-8"))
        return None, None
    t, r = run(mode, "--send" in a, server.load_config, latest)
    print(t)
    if r is not None:
        print("\nKết quả gửi:", r)
