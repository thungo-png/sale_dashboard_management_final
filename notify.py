"""Gửi tóm tắt report + link qua Google Chat (webhook) và email (Gmail SMTP). Chỉ gửi khi bấm nút, không tự gửi.
Cấu hình lưu ở data/notify.json (chứa mật khẩu ứng dụng → không đưa vào config.json, API không bao giờ trả lại bí mật)."""
import json, os, smtplib, ssl, urllib.request, urllib.error, html
from email.message import EmailMessage
from pathlib import Path

CF = Path(__file__).parent / "data" / "notify.json"
DEFAULT = {"gchat_webhook": "", "smtp_user": "", "smtp_pass": "", "from_name": "Sale Report",
           "recipients": ["thungo@behmd.com", "dungnguyen@behmd.com"], "public_url": "",
           "use_gchat": True, "use_email": True}
SECRETS = ("gchat_webhook", "smtp_pass")


def load():
    c = dict(DEFAULT)
    try:
        c.update(json.loads(CF.read_text(encoding="utf-8")))
    except Exception:
        pass
    return c


def save(new):
    c = load()
    for k in DEFAULT:
        if k not in new:
            continue
        v = new[k]
        if k in SECRETS and (v is None or v == ""):
            continue                      # để trống = giữ giá trị cũ
        if k == "recipients":
            v = [x.strip() for x in (v if isinstance(v, list) else str(v).replace(";", ",").replace("\n", ",").split(",")) if x.strip()]
        if k in ("use_gchat", "use_email"):
            v = bool(v)
        c[k] = v.strip() if isinstance(v, str) else v
    CF.parent.mkdir(exist_ok=True)
    CF.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        os.chmod(CF, 0o600)
    except Exception:
        pass
    return public(c)


def public(c=None):
    c = c or load()
    o = {k: v for k, v in c.items() if k not in SECRETS}
    o["gchat_set"] = bool(c.get("gchat_webhook"))
    o["smtp_pass_set"] = bool(c.get("smtp_pass"))
    return o


def detect_url():
    """Link cloudflared quick tunnel đang chạy trên máy (đọc từ cổng metrics)."""
    for port in (20241, 20242, 20243, 20244, 20245):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/quicktunnel", timeout=1.5) as r:
                h = json.loads(r.read()).get("hostname")
                if h:
                    return "https://" + h
        except Exception:
            continue
    return ""


def base_url(c, override=""):
    for u in (override, detect_url(), c.get("public_url")):
        if u and u.strip():
            return u.strip().rstrip("/")
    return ""


def _usd(x):
    return ("-" if x < 0 else "") + "$" + f"{abs(x):,.0f}".replace(",", ".")


def _dm(d):
    return d[8:10] + "/" + d[5:7] if len(d) >= 10 else d


def build_summary(D, pid, issues):
    """Trả {'title','lines','focus','actions'} — văn phong: vấn đề ở đâu, hướng xử lý; diễn đạt nhẹ nhàng."""
    m = D["meta"]
    cells = D.get("cell") or []
    r = sum(x["r"] for x in cells); q = sum(x["q"] for x in cells)
    rp = sum(x["r"] for x in (D.get("cell_prev") or []))
    rfc = sum(x["rfc"] for x in cells)
    ach = r / rfc * 100 if rfc else None
    wow = (r / rp - 1) * 100 if rp else None
    ads = sum(a["spend"] for a in (D.get("adsum") or []))
    pl = D.get("pl5") or {}
    tot = pl.get("total") or {}
    k = [f"Doanh thu {_usd(r)} · {q:,.0f} đơn vị" + (f" ({wow:+.1f}% so với tuần trước)" if wow is not None else "")]
    if ach is not None:
        k.append(f"Đạt {ach:.1f}% forecast")
    arev = sum(a["rev"] for a in (D.get("adsum") or []))
    if ads and arev:
        k.append(f"Quảng cáo {_usd(ads)} (TACoS {ads / arev * 100:.1f}%)")
    if pl.get("available") and tot.get("r"):
        k.append(f"Lợi nhuận PL5 {_usd(tot['profit'])} (margin {tot['margin']:.1f}%)")
    focus = []
    if pl.get("available"):
        bad = sorted([(kk, v) for kk, v in (pl.get("by_mpcty") or {}).items() if v.get("profit", 0) < 0 and v.get("r", 0) > 0],
                     key=lambda kv: kv[1]["profit"])[:3]
        good = sorted([(kk, v) for kk, v in (pl.get("by_mpcty") or {}).items() if v.get("profit", 0) > 0], key=lambda kv: -kv[1]["profit"])[:2]
        if good:
            focus.append("Đang làm tốt: " + "; ".join(f"{kk.replace('|', ' ')} {_usd(v['profit'])}" for kk, v in good))
        if bad:
            focus.append("Cần cải thiện biên lợi nhuận: " + "; ".join(f"{kk.replace('|', ' ')} {_usd(v['profit'])} ({v['margin']:.1f}%)" for kk, v in bad))
    acts, seen = [], set()
    for i in sorted(issues, key=lambda i: -i.get("sev", 0)):
        a = i.get("area")
        if a in seen or not i.get("fix"):
            continue
        seen.add(a)
        acts.append(f"[{a}] {i.get('where') or i['title']} → {i['fix'][0]}")
        if len(acts) >= 4:
            break
    return {"title": f"Sale Report tuần {m.get('week_no', '')} ({_dm(m.get('d0', ''))}–{_dm(m.get('d1', ''))})",
            "kpi": k, "focus": focus, "actions": acts, "period": pid}


def render_text(s, link):
    L = [s["title"], ""] + [f"• {x}" for x in s["kpi"]]
    if s["focus"]:
        L += [""] + s["focus"]
    if s["actions"]:
        L += ["", "Việc ưu tiên:"] + [f"- {a}" for a in s["actions"]]
    if link:
        L += ["", f"Xem report đầy đủ: {link}", "(đăng nhập bằng tài khoản được cấp)"]
    return "\n".join(L)


def render_gchat(s, link):
    L = [f"*{s['title']}*", ""] + [f"• {x}" for x in s["kpi"]]
    if s["focus"]:
        L += [""] + s["focus"]
    if s["actions"]:
        L += ["", "*Việc ưu tiên:*"] + [f"- {a}" for a in s["actions"]]
    if link:
        L += ["", f"👉 Xem report đầy đủ: {link}"]
    return "\n".join(L)


def render_html(s, link):
    e = html.escape
    h = f"<div style='font-family:Arial,sans-serif;font-size:14px;color:#222;max-width:640px'><h2 style='margin:0 0 10px'>{e(s['title'])}</h2><ul style='padding-left:18px;line-height:1.6'>"
    h += "".join(f"<li>{e(x)}</li>" for x in s["kpi"]) + "</ul>"
    h += "".join(f"<p style='margin:6px 0'>{e(x)}</p>" for x in s["focus"])
    if s["actions"]:
        h += "<p style='margin:12px 0 4px'><b>Việc ưu tiên</b></p><ul style='padding-left:18px;line-height:1.6'>" + "".join(f"<li>{e(a)}</li>" for a in s["actions"]) + "</ul>"
    if link:
        h += f"<p style='margin:18px 0'><a href='{e(link)}' style='background:#1a73e8;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none'>Xem report đầy đủ</a></p><p style='color:#777;font-size:12px'>Đăng nhập bằng tài khoản được cấp. Nếu link không mở được, báo lại để được hỗ trợ.</p>"
    return h + "</div>"


def send_email(c, s, link):
    if not (c.get("smtp_user") and c.get("smtp_pass")):
        return "chưa cấu hình Gmail (tài khoản gửi + mật khẩu ứng dụng)"
    to = c.get("recipients") or []
    if not to:
        return "chưa có người nhận"
    m = EmailMessage()
    m["Subject"] = s["title"]
    m["From"] = f"{c.get('from_name') or 'Sale Report'} <{c['smtp_user']}>"
    m["To"] = ", ".join(to)
    m.set_content(render_text(s, link))
    m.add_alternative(render_html(s, link), subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=25) as sm:
            sm.login(c["smtp_user"], c["smtp_pass"].replace(" ", ""))
            sm.send_message(m)
        return "ok"
    except smtplib.SMTPAuthenticationError:
        return "Gmail từ chối đăng nhập — kiểm tra lại mật khẩu ứng dụng (16 ký tự) và bật xác minh 2 bước"
    except Exception as x:
        return f"lỗi: {type(x).__name__}: {x}"


def send_gchat(c, s, link):
    u = c.get("gchat_webhook")
    if not u:
        return "chưa cấu hình webhook Google Chat"
    try:
        req = urllib.request.Request(u, data=json.dumps({"text": render_gchat(s, link)}, ensure_ascii=False).encode(),
                                     headers={"Content-Type": "application/json; charset=UTF-8"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            r.read()
        return "ok"
    except urllib.error.HTTPError as x:
        return f"lỗi HTTP {x.code} — kiểm tra lại webhook"
    except Exception as x:
        return f"lỗi: {type(x).__name__}: {x}"


def send(D, pid, issues, link_override="", preview=False):
    c = load()
    link = base_url(c, link_override)
    link = f"{link}/report/{pid}" if link else ""
    s = build_summary(D, pid, issues)
    out = {"link": link, "text": render_text(s, link), "email": None, "gchat": None}
    if preview:
        return out
    if c.get("use_email"):
        out["email"] = send_email(c, s, link)
    if c.get("use_gchat"):
        out["gchat"] = send_gchat(c, s, link)
    return out
