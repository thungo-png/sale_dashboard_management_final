"""Tối ưu quảng cáo Wayfair (Nhóm 3): từ khoá & search term, đề xuất bid theo ngưỡng hoà vốn, ranking & share of voice.

Dữ liệu lấy từ file report quảng cáo Wayfair đã upload ở các kỳ (CR / KTR / KOR / PR / PSR / ST), chỉ campaign Thu Ngo
(regex ^\\s*thu\\s*ng[oô]\\b). Mỗi kỳ chỉ lấy các ngày trong tuần báo cáo [d0, d1]; số liệu của nhiều kỳ được CỘNG DỒN
(tối đa `window_days` ngày gần nhất) vì mỗi bộ file hằng tuần chỉ phủ ~1 tuần, không phải 90 ngày.

Quy tắc bulk-edit bám skill `wayfair-bulk-ads-optimization` (xem README mục "Nhóm 3"):
 - KHÔNG chỉnh campaign / keyword / listing đang INACTIVE (đọc trạng thái trong CHÍNH template mới nhất khi xuất file).
 - Remove from Current Campaign = 'REMOVE'. Add Negative Keywords: kiểm trùng negative hiện có, xung đột 2 chiều với
   target keyword, trùng không phân biệt hoa/thường, trần 100 negative / campaign.
 - Giảm bid theo tỉ lệ target/ACOS, sàn không giảm quá 80%.
Phần TĂNG bid (keyword / listing ra đơn tốt) là bổ sung của app, có trần mỗi lần `up_cap` (mặc định +25%).
"""
import io, json, os, re, threading, warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from etl.ads import RX_THU, group_of, ST_BRAND

warnings.filterwarnings("ignore")

BASE = Path(__file__).parent
DATA = BASE / "data"
PERIODS = DATA / "periods"
CFG_FILE = DATA / "adsopt.json"
TPL_DIR = DATA / "adsopt_templates"
CACHE_NAME = "adsopt_cache.pkl"
CACHE_VER = 3
LOCK = threading.Lock()
BUILD_LOCK = threading.RLock()

# slot key -> (tên tài khoản, tiền tệ gốc, quốc gia)
ACCTS = {"arozu": ("Arozu", "USD", "US"), "megsu": ("Megsu", "USD", "US"), "dhi": ("DHI", "CAD", "CAN")}
NAME2KEY = {v[0]: k for k, v in ACCTS.items()}
REPORTS = ["CR", "KTR", "KOR", "PR", "PSR", "ST"]
WF_NEG_CAP = 100
SHEETS = {"camp": "Edit Sponsored Product Campaign", "kw": "Edit Target Keyword Bids", "lst": "Edit Listing Bids",
          "neg": "Add Negative Keywords", "negcur": "Edit Negative Keywords"}

DEFAULTS = {
    "window_days": 90,          # cộng dồn tối đa bấy nhiêu ngày gần nhất
    "mode": "breakeven",        # breakeven | margin | fixed
    "fixed_acos": 6.0,          # % — ngưỡng khi P&L chưa cho ngưỡng hoà vốn dương
    "safety": 0.9,              # ngưỡng = biên trước QC × safety (mode breakeven)
    "target_margin": 10.0,      # % biên giữ lại (mode margin)
    "min_target": 3.0, "max_target": 35.0,
    "pause_spend": 150.0, "pause_acos": 33.0,
    "neg_min_spend": 2.0,
    "kw_remove_spend": 8.0, "kw_half_spend": 2.0, "kw_cut_min_spend": 3.0, "lst_cut_min_spend": 5.0,
    "bid_floor_ratio": 0.2,
    "up_min_orders": 2, "up_min_spend": 3.0, "up_ratio": 0.7, "up_cap": 0.25,
    "newterm_min_orders": 2,
    "rank_min_drop": 10, "rank_min_pct": 15.0, "rank_high_drop": 30,
    "sov_min_drop": 2.0, "sov_min_impr": 1000,
    "overrides": {},            # "Nhóm|US" -> ACOS % do người dùng chốt
}
NUM_KEYS = [k for k, v in DEFAULTS.items() if isinstance(v, (int, float))]


# ============================================================ cấu hình
def load_cfg():
    try:
        c = json.loads(CFG_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        c = {}
    out = {**DEFAULTS, **{k: v for k, v in c.items() if k in DEFAULTS}}
    out["overrides"] = dict(c.get("overrides") or {})
    return out


def save_cfg(upd):
    with LOCK:
        c = load_cfg()
        for k, v in (upd or {}).items():
            if k == "overrides":
                ov = {}
                for kk, vv in (v or {}).items():
                    if vv in ("", None):
                        continue
                    x = float(vv)
                    if not (0 < x <= 100):
                        raise ValueError(f"Ngưỡng ACOS của {kk} phải trong (0, 100]%")
                    ov[str(kk)] = round(x, 2)
                c["overrides"] = ov
            elif k == "mode":
                if v not in ("breakeven", "margin", "fixed"):
                    raise ValueError("Chế độ ngưỡng không hợp lệ")
                c["mode"] = v
            elif k in NUM_KEYS:
                x = float(v)
                if x < 0:
                    raise ValueError(f"{k} không được âm")
                c[k] = x
        if not (0 < c["safety"] <= 1.5):
            raise ValueError("Hệ số an toàn phải trong (0, 1.5]")
        if c["fixed_acos"] <= 0:
            raise ValueError("Ngưỡng ACOS cố định phải > 0")
        if not (0 < c["bid_floor_ratio"] <= 1):
            raise ValueError("Sàn giảm bid phải trong (0, 1]")
        DATA.mkdir(exist_ok=True)
        tmp = CFG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, CFG_FILE)
        return c


# ============================================================ đọc & chuẩn hoá file
def _col(df, prefix):
    for c in df.columns:
        if str(c).startswith(prefix):
            return c
    return None


def _num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def _std(df, d0, d1):
    """Chuẩn hoá cột số + lọc ngày [d0,d1]. Nhận cả cột Date (ngày) lẫn date_start_est/date_end_est (xô nhiều ngày)."""
    df = df.copy()
    if "Date" in df.columns:
        df["_ds"] = pd.to_datetime(df["Date"]); df["_de"] = df["_ds"]
    elif "date_start_est" in df.columns:
        df["_ds"] = pd.to_datetime(df["date_start_est"])
        df["_de"] = pd.to_datetime(df["date_end_est"]) if "date_end_est" in df.columns else df["_ds"]
    else:
        raise ValueError("Report không có cột ngày (Date / date_start_est)")
    df = df[(df["_ds"] >= d0) & (df["_de"] <= d1)]
    c = _col(df, "spend_"); df["_spend"] = _num(df[c]) if c else 0.0
    c = _col(df, "attributed_retail_sales"); df["_sales"] = _num(df[c]) if c else 0.0
    c = _col(df, "attributed_orders"); df["_orders"] = _num(df[c]) if c else 0.0
    df["_clicks"] = _num(df["clicks"]) if "clicks" in df.columns else 0.0
    df["_impr"] = _num(df["impressions"]) if "impressions" in df.columns else 0.0
    return df.sort_values("_ds", kind="stable")


def _thu(df):
    return df[df["campaign_name"].astype(str).str.contains(RX_THU)]


M = ["_spend", "_sales", "_orders", "_clicks", "_impr"]
RENAME = {"_spend": "spend", "_sales": "sales", "_orders": "orders", "_clicks": "clicks", "_impr": "impr"}


def _sum(df, keys, last=None):
    """Cộng các chỉ số theo keys; `last` = {tên_mới: cột} lấy giá trị cuối cùng theo ngày."""
    g = df.groupby(keys, sort=False)
    out = g[M].sum().rename(columns=RENAME)
    for new, c in (last or {}).items():
        out[new] = g[c].last()
    return out.reset_index()


def _read_xlsx(path, **kw):
    """Đọc báo cáo Wayfair dạng .xlsx hoặc .csv (theo đuôi file)."""
    if str(path).lower().endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(path, **kw)
    return pd.read_csv(path, encoding="utf-8-sig", **kw)


def _norm_kw(s):
    return str(s).strip().lower()


def _parse_account(files, name, d0, d1, groups, log):
    """files: {CR:path,...} của 1 tài khoản -> dict các DataFrame đã gộp (chỉ Thu Ngo, trong [d0,d1])."""
    out = {}
    brand = ST_BRAND[name]
    if files.get("CR"):
        cr = _thu(_std(_read_xlsx(files["CR"]), d0, d1))
        cap = _col(cr, "campaign_daily_cap_")
        t = _sum(cr, "campaign_id", {"name": "campaign_name", "status": "campaign_status", "active": "campaign_is_active",
                                     "strategy": "bidding_strategy", "troas": "target_roas_percentage",
                                     **({"cap": cap} if cap else {})})
        out["camp"] = t
    if files.get("KTR"):
        raw = _read_xlsx(files["KTR"])
        full = _thu(raw)
        out["kwall"] = (full[["campaign_id", "keyword_value"]].assign(kw=lambda x: x["keyword_value"].map(_norm_kw))
                        [["campaign_id", "kw"]].drop_duplicates().reset_index(drop=True))
        ktr = _thu(_std(raw, d0, d1))
        ktr["kw"] = ktr["keyword_value"].map(_norm_kw)
        out["kw"] = _sum(ktr, ["campaign_id", "kw"], {"keyword": "keyword_value", "match": "keyword_match_type", "bid": "keyword_default_bid"})
    if files.get("KOR"):
        kor = _thu(_std(_read_xlsx(files["KOR"]), d0, d1))
        kor["term"] = kor["customer_search_term"].astype(str).str.strip()
        kor["term_lo"] = kor["term"].str.lower()
        out["st"] = _sum(kor, ["campaign_id", "term_lo"], {"campaign_name": "campaign_name", "term": "term"})
    if files.get("PR"):
        pr = _thu(_std(_read_xlsx(files["PR"]), d0, d1))
        pr["lst"] = pr["listing"].astype(str).str.strip().str.upper()
        out["lst"] = _sum(pr, ["campaign_id", "lst"], {"listing": "listing", "campaign_name": "campaign_name", "bid": "product_default_bid", "status": "product_status"})
        lg = {}
        for l, g in pr.groupby("lst", sort=True):
            lg[l] = group_of(g.sort_values("_ds")["campaign_name"].iloc[-1], groups)
        out["lgrp"] = lg
    if files.get("PSR"):
        psr = _read_xlsx(files["PSR"])
        psr["Date"] = pd.to_datetime(psr["Date"])
        psr = psr[(psr["Date"] >= d0) & (psr["Date"] <= d1)]
        keep = set(out.get("lgrp", {}))
        psr["lst"] = psr["Listing"].astype(str).str.strip().str.upper()
        if keep:
            psr = psr[psr["lst"].isin(keep)]
        out["rank"] = pd.DataFrame({"date": psr["Date"].dt.strftime("%Y-%m-%d"), "lst": psr["lst"], "listing": psr["Listing"],
                                    "status": psr["Campaign Listing Status"].astype(str), "cls": psr["Class Name"].astype(str),
                                    "rank": pd.to_numeric(psr["Class Rank"], errors="coerce")}).dropna(subset=["rank"]).reset_index(drop=True)
    if files.get("ST"):
        s = _read_xlsx(files["ST"], header=0).iloc[:, :8].copy()
        s.columns = ["bc", "term", "cls", "impr", "sh_search", "shs", "sh_p1", "sh_top8"]
        for c in ["impr", "sh_search", "shs", "sh_p1", "sh_top8"]:
            s[c] = pd.to_numeric(s[c], errors="coerce")
        out["sov"] = s[s["bc"] == brand].dropna(subset=["impr"]).reset_index(drop=True)
    return out


# ============================================================ cache theo kỳ
def _sig(paths):
    out = {}
    for p in paths:
        try:
            st = Path(p).stat(); out[Path(p).name] = [st.st_mtime_ns, st.st_size]
        except FileNotFoundError:
            pass
    return out


def _period_files(pid, meta):
    up = PERIODS / pid / "uploads"
    res = {k: {} for k in ACCTS}
    for slot, fname in (meta.get("files") or {}).items():
        m = re.fullmatch(r"wf_(arozu|megsu|dhi)_(CR|KTR|KOR|PR|PSR|ST)", slot)
        if m and (up / fname).exists():
            res[m.group(1)][m.group(2)] = str(up / fname)
    return res


def period_cache(pid, log=print):
    """Trả cache của kỳ (tạo / làm mới nếu file đổi). None nếu kỳ chưa build."""
    with BUILD_LOCK:
        return _period_cache(pid, log)


def _period_cache(pid, log=print):
    d = PERIODS / pid
    try:
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    if meta.get("status") != "built" or not (d / "data.json").exists():
        return None
    files = _period_files(pid, meta)
    allp = [p for a in files.values() for p in a.values()] + [str(d / "data.json")]
    sig = _sig(allp)
    cf = d / CACHE_NAME
    if cf.exists():
        try:
            c = pd.read_pickle(cf)
            if c.get("ver") == CACHE_VER and c.get("sig") == sig:
                return c
            # raw đã được dọn định kỳ: file không còn nên chữ ký file đổi; cache vẫn đúng nếu data.json không đổi
            if meta.get("uploads_cleaned") and c.get("ver") == CACHE_VER and (c.get("sig") or {}).get("data.json") == sig.get("data.json"):
                return c
        except Exception:
            pass
    D = json.loads((d / "data.json").read_text(encoding="utf-8"))
    m = D["meta"]
    d0, d1 = pd.Timestamp(m["d0"]), pd.Timestamp(m["d1"])
    wk = (m.get("weeks") or [None])[-1]
    c = {"ver": CACHE_VER, "sig": sig, "pid": pid, "d0": m["d0"], "d1": m["d1"], "week": wk,
         "label": f"W{wk} ({(m.get('weeklab') or {}).get(str(wk), '')})" if wk else pid,
         "ndays": int((d1 - d0).days) + 1, "has_files": False, "accts": {},
         "D_rank": (D.get("ads") or {}).get("rank") or {}, "D_st": (D.get("ads") or {}).get("st") or {}}
    groups = m["groups"]
    for k, (name, cur, cty) in ACCTS.items():
        f = files[k]
        if any(f.get(r) for r in ("CR", "KTR", "KOR", "PR")):
            c["has_files"] = True
            try:
                c["accts"][name] = _parse_account(f, name, d0, d1, groups, log)
            except Exception as e:
                log(f"[adsopt] {pid}/{name}: bỏ qua file lỗi — {type(e).__name__}: {e}")
        elif f:
            try:
                c["accts"][name] = _parse_account(f, name, d0, d1, groups, log)
            except Exception as e:
                log(f"[adsopt] {pid}/{name}: bỏ qua — {e}")
    try:
        pd.to_pickle(c, cf)
    except OSError:
        pass
    return c


def refresh_cache(pid, log=print):
    c = period_cache(pid, log)
    return bool(c)


def history(window_days=None):
    """Các kỳ đã build, cũ → mới, chỉ giữ kỳ nằm trong `window_days` ngày gần nhất (tính theo d1 mới nhất)."""
    cs = []
    if PERIODS.exists():
        for p in sorted(PERIODS.iterdir()):
            if (p / "meta.json").exists():
                c = period_cache(p.name)
                if c:
                    cs.append(c)
    # cùng tuần (d0,d1) -> ưu tiên bản có file thô
    best = {}
    for c in cs:
        k = (c["d0"], c["d1"])
        if k not in best or (c["has_files"] and not best[k]["has_files"]):
            best[k] = c
    cs = sorted(best.values(), key=lambda c: c["d0"])
    if cs and window_days:
        end = pd.Timestamp(cs[-1]["d1"])
        cs = [c for c in cs if pd.Timestamp(c["d1"]) > end - pd.Timedelta(days=int(window_days))]
    return cs


# ============================================================ ngưỡng ACOS theo nhóm × thị trường
def pre_ads_table(D):
    """{(nhóm, cty): biên trước quảng cáo % của Wayfair} = (lợi nhuận PL5 + SEM) / doanh thu — cùng cách tính với tab Quản trị."""
    agg = {}
    for x in ((D or {}).get("pl5") or {}).get("rows") or []:
        if x.get("mp") != "Wayfair":
            continue
        a = agg.setdefault((x["grp"], x["cty"]), [0.0, 0.0, 0.0])
        a[0] += float(x.get("r") or 0); a[1] += float(x.get("sem") or 0); a[2] += float(x.get("profit") or 0)
    return {k: round((v[2] + v[1]) / v[0] * 100, 2) for k, v in agg.items() if v[0] > 0}


def target_for_grp(grp, cty, cfg, be_tbl):
    """-> (ACOS mục tiêu %, nguồn: override | pl | fixed, biên trước QC %)."""
    key = f"{grp}|{cty}"
    be = be_tbl.get((grp, cty))
    if key in cfg["overrides"]:
        return cfg["overrides"][key], "override", be
    if cfg["mode"] != "fixed" and be is not None:
        t = be * cfg["safety"] if cfg["mode"] == "breakeven" else be - cfg["target_margin"]
        if t >= cfg["min_target"]:
            return round(min(t, cfg["max_target"]), 2), "pl", be
    return cfg["fixed_acos"], "fixed", be


def target_for(name, cty, cfg, be_tbl, groups):
    """Theo tên campaign: -> (ACOS mục tiêu %, nguồn, nhóm, biên trước QC %)."""
    grp = group_of(name, groups) if groups else None
    t, src, be = target_for_grp(grp, cty, cfg, be_tbl)
    return t, src, grp, be


# ============================================================ gộp lịch sử
def _merge(caches, acct, part, keys, latest_cols=()):
    frames = [c["accts"][acct][part].assign(_p=i) for i, c in enumerate(caches) if acct in c["accts"] and part in c["accts"][acct] and len(c["accts"][acct][part])]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    sums = [m for m in ("spend", "sales", "orders", "clicks", "impr") if m in df.columns]
    g = df.sort_values("_p", kind="stable").groupby(keys, sort=False)
    out = g[sums].sum()
    for c in df.columns:
        if c not in sums and c not in keys and c != "_p":
            out[c] = g[c].last()
    return out.reset_index()


def _days(caches):
    return int(sum(c["ndays"] for c in caches if c["has_files"]))


def _acos(spend, sales):
    return round(spend / sales * 100, 2) if sales and sales > 0 else None


# ============================================================ tính hành động bid / negative
def _active(status, flag):
    return str(status).upper() == "ACTIVE" and (flag in (True, "TRUE", "True", 1, 1.0) or pd.isna(flag))


def _conflict(term_lo, kws):
    for kw in kws:
        if term_lo == kw or term_lo in kw or kw in term_lo:
            return kw
    return None


def compute(D, cfg=None, caches=None):
    """Toàn bộ phân tích tối ưu quảng cáo cho 3 tài khoản. Trả về dict gọn để vẽ giao diện + làm đầu vào xuất bulk."""
    cfg = cfg or load_cfg()
    caches = caches if caches is not None else history(cfg["window_days"])
    groups = (D or {}).get("meta", {}).get("groups") or []
    be_tbl = pre_ads_table(D)
    fc = [c for c in caches if c["has_files"]]
    res = {"window": {"days": _days(caches), "from": fc[0]["d0"] if fc else None, "to": fc[-1]["d1"] if fc else None,
                      "periods": [c["label"] for c in fc], "max_days": int(cfg["window_days"])},
           "accounts": {}, "has_data": bool(fc)}
    for k, (name, cur, cty) in ACCTS.items():
        camp = _merge(fc, name, "camp", ["campaign_id"])
        if camp.empty:
            res["accounts"][name] = {"cur": cur, "cty": cty, "empty": True}
            continue
        kw = _merge(fc, name, "kw", ["campaign_id", "kw"])
        st = _merge(fc, name, "st", ["campaign_id", "term_lo"])
        lst = _merge(fc, name, "lst", ["campaign_id", "lst"])
        kwall = {}
        for c in caches:
            a = c["accts"].get(name) or {}
            if "kwall" in a:
                for cid, w in zip(a["kwall"]["campaign_id"], a["kwall"]["kw"]):
                    kwall.setdefault(int(cid), set()).add(w)
        camp = camp.set_index("campaign_id")
        info = {}
        for cid, r in camp.iterrows():
            t, src, grp, be = target_for(r["name"], cty, cfg, be_tbl, groups)
            info[int(cid)] = {"campaign_id": int(cid), "name": r["name"], "grp": grp, "strategy": str(r["strategy"]),
                              "active": _active(r["status"], r["active"]), "status": str(r["status"]),
                              "troas": None if pd.isna(r.get("troas")) else float(r["troas"]),
                              "spend": round(float(r["spend"]), 2), "sales": round(float(r["sales"]), 2), "orders": int(r["orders"]),
                              "clicks": int(r["clicks"]), "acos": _acos(r["spend"], r["sales"]), "target": t, "src": src, "pre_ads": be,
                              "manual": "manual" in str(r["strategy"]).lower(), "kw_up": 0, "kw_down": 0, "kw_rm": 0, "lst_down": 0,
                              "lst_up": 0, "lst_rm": 0, "action": None, "reason": "", "new_troas": None, "ratio": None}
        # ---- campaign-level
        for cid, c in info.items():
            if not c["active"]:
                continue
            sp, ac, tg = c["spend"], c["acos"], c["target"]
            if sp >= cfg["pause_spend"] and (ac is None or ac >= cfg["pause_acos"]):
                c["action"] = "pause"
                c["reason"] = f"Tạm dừng: chi {sp:,.0f} {cur} trong {res['window']['days']} ngày, " + ("chưa có doanh thu" if ac is None else f"ACOS {ac:.1f}% còn cao hơn ngưỡng an toàn {cfg['pause_acos']:.0f}%")
            elif "troas" in c["strategy"].lower():
                need = round(100 / tg * 100)
                if c["troas"] is not None and c["troas"] < need:
                    c["action"] = "troas"; c["new_troas"] = need
                    c["reason"] = f"Nâng Target ROAS {c['troas']:.0f}% → {need}% (tương ứng ACOS {tg:.1f}%)"
                elif c["troas"] is not None and ac is not None and c["orders"] >= 5 and ac <= 0.5 * tg and c["troas"] > need * 1.2:
                    new = max(need, round(c["troas"] * 0.85))
                    c["action"] = "troas"; c["new_troas"] = new
                    c["reason"] = f"Còn dư địa: ACOS {ac:.1f}% thấp hơn nhiều so với ngưỡng {tg:.1f}% → nới Target ROAS {c['troas']:.0f}% → {new}% để lấy thêm đơn"
            if c["manual"] and ac is not None and c["orders"] > 0:
                c["ratio"] = round(min(max(tg / ac, cfg["bid_floor_ratio"]), 1 + cfg["up_cap"]), 2)
                if c["ratio"] < 1 and c["spend"] >= cfg["kw_cut_min_spend"] and not c["action"]:
                    c["action"] = "down"
                    c["reason"] = f"ACOS {ac:.1f}% so với ngưỡng {tg:.1f}% → giảm bid khoảng {round((1 - c['ratio']) * 100)}%"
                elif c["ratio"] > 1 and ac <= cfg["up_ratio"] * tg and c["orders"] >= cfg["up_min_orders"] and not c["action"]:
                    c["action"] = "up"
                    c["reason"] = f"ACOS {ac:.1f}% thấp hơn ngưỡng {tg:.1f}% → có thể tăng bid khoảng {round((c['ratio'] - 1) * 100)}%"
            if c["action"] not in ("down", "up"):
                c["ratio"] = None
            if c["manual"] and c["orders"] == 0 and sp >= cfg["kw_half_spend"] and not c["action"]:
                c["action"] = "watch"
                c["reason"] = f"Chi {sp:,.2f} {cur} chưa ra đơn → xem từng từ khoá / listing bên dưới"
        # ---- keyword
        kw_actions = []
        for r in kw.itertuples(index=False):
            c = info.get(int(r.campaign_id))
            if not c or not c["active"]:
                continue
            ac = _acos(r.spend, r.sales); tg = c["target"]; bid = None if pd.isna(r.bid) else float(r.bid)
            a = None
            if r.spend >= cfg["kw_remove_spend"] and r.orders == 0:
                a = ("remove", None, f"Chi {r.spend:.2f} {cur}, 0 đơn")
            elif c["manual"] and cfg["kw_half_spend"] <= r.spend < cfg["kw_remove_spend"] and r.orders == 0 and bid:
                a = ("half", 0.5, f"Chi {r.spend:.2f} {cur}, 0 đơn → giảm 50% bid")
            elif c["manual"] and r.orders > 0 and r.spend >= cfg["kw_cut_min_spend"] and ac is not None and ac >= tg and bid:
                ratio = max(tg / ac, cfg["bid_floor_ratio"])
                a = ("cut", round(ratio, 3), f"ACOS {ac:.1f}% so với ngưỡng {tg:.1f}% → giảm bid")
            elif c["manual"] and r.orders >= cfg["up_min_orders"] and r.spend >= cfg["up_min_spend"] and ac is not None and ac <= cfg["up_ratio"] * tg and bid:
                ratio = min(1 + cfg["up_cap"], 1 + 0.5 * (tg / ac - 1))
                a = ("raise", round(ratio, 3), f"ACOS {ac:.1f}% thấp hơn ngưỡng {tg:.1f}% với {int(r.orders)} đơn → tăng bid")
            if a:
                kind, ratio, why = a
                nb = None
                if ratio is not None and bid:
                    nb = round(bid * ratio, 2)
                    if kind in ("half", "cut") and nb >= bid:
                        continue
                    if kind == "raise" and nb <= bid:
                        continue
                kw_actions.append({"campaign_id": int(r.campaign_id), "campaign": c["name"], "keyword": r.keyword, "kw": r.kw, "match": r.match,
                                   "kind": kind, "bid": bid, "new_bid": nb, "ratio": ratio, "spend": round(float(r.spend), 2),
                                   "orders": int(r.orders), "acos": ac, "target": tg, "why": why})
                c["kw_rm" if kind == "remove" else "kw_up" if kind == "raise" else "kw_down"] += 1
        # ---- listing
        lst_actions = []
        for r in lst.itertuples(index=False):
            c = info.get(int(r.campaign_id))
            if not c or not c["active"] or str(r.status).upper() != "ACTIVE":
                continue
            ac = _acos(r.spend, r.sales); tg = c["target"]; bid = None if pd.isna(r.bid) else float(r.bid)
            a = None
            if r.spend >= cfg["kw_remove_spend"] and r.orders == 0:
                a = ("remove", None, f"Chi {r.spend:.2f} {cur}, 0 đơn")
            elif c["manual"] and cfg["kw_half_spend"] <= r.spend < cfg["kw_remove_spend"] and r.orders == 0 and bid and bid > 0:
                a = ("half", 0.5, f"Chi {r.spend:.2f} {cur}, 0 đơn → giảm 50% bid")
            elif c["manual"] and r.orders > 0 and r.spend >= cfg["lst_cut_min_spend"] and ac is not None and ac >= tg and bid and bid > 0:
                a = ("cut", round(max(tg / ac, cfg["bid_floor_ratio"]), 3), f"ACOS {ac:.1f}% so với ngưỡng {tg:.1f}% → giảm bid")
            elif c["manual"] and r.orders >= cfg["up_min_orders"] and r.spend >= cfg["up_min_spend"] and ac is not None and ac <= cfg["up_ratio"] * tg and bid and bid > 0:
                a = ("raise", round(min(1 + cfg["up_cap"], 1 + 0.5 * (tg / ac - 1)), 3), f"ACOS {ac:.1f}% thấp hơn ngưỡng {tg:.1f}% với {int(r.orders)} đơn → tăng bid")
            if a:
                kind, ratio, why = a
                nb = None
                if ratio is not None and bid:
                    nb = round(bid * ratio, 2)
                    if kind in ("half", "cut") and nb >= bid:
                        continue
                    if kind == "raise" and nb <= bid:
                        continue
                lst_actions.append({"campaign_id": int(r.campaign_id), "campaign": c["name"], "listing": r.listing, "lst": r.lst,
                                    "kind": kind, "bid": bid, "new_bid": nb, "ratio": ratio, "spend": round(float(r.spend), 2),
                                    "orders": int(r.orders), "acos": ac, "target": tg, "why": why})
                c["lst_rm" if kind == "remove" else "lst_up" if kind == "raise" else "lst_down"] += 1
        # ---- negative (search term chi tiền, 0 đơn)
        neg, newterms = [], []
        for r in st.itertuples(index=False):
            c = info.get(int(r.campaign_id))
            if not c:
                continue
            if r.spend >= cfg["neg_min_spend"] and r.orders == 0:
                kws = kwall.get(int(r.campaign_id), set())
                cf = _conflict(r.term_lo, kws)
                neg.append({"campaign_id": int(r.campaign_id), "campaign": r.campaign_name if isinstance(r.campaign_name, str) else c["name"],
                            "term": r.term, "term_lo": r.term_lo, "spend": round(float(r.spend), 2), "clicks": int(r.clicks),
                            "active": c["active"], "conflict": cf,
                            "status": "inactive" if not c["active"] else "conflict" if cf else "ok"})
            elif r.orders >= cfg["newterm_min_orders"] and c["active"]:
                ac = _acos(r.spend, r.sales)
                if ac is not None and ac <= c["target"] and _conflict(r.term_lo, kwall.get(int(r.campaign_id), set())) is None:
                    newterms.append({"campaign_id": int(r.campaign_id), "campaign": c["name"], "term": r.term, "spend": round(float(r.spend), 2),
                                     "orders": int(r.orders), "sales": round(float(r.sales), 2), "acos": ac, "target": c["target"]})
        neg.sort(key=lambda x: -x["spend"]); newterms.sort(key=lambda x: -x["orders"])
        seen, dd = set(), []
        for n in neg:                                # trùng hoa/thường trong cùng campaign
            k = (n["campaign_id"], n["term_lo"])
            if k not in seen:
                seen.add(k); dd.append(n)
        neg = dd
        winners = sorted([a for a in kw_actions if a["kind"] == "raise"], key=lambda x: (x["acos"] or 0))
        res["accounts"][name] = {
            "cur": cur, "cty": cty, "empty": False, "campaigns": sorted(info.values(), key=lambda x: -x["spend"]),
            "kw_actions": kw_actions, "lst_actions": lst_actions, "neg": neg, "winners": winners, "newterms": newterms,
            "totals": {"spend": round(float(camp["spend"].sum()), 2), "sales": round(float(camp["sales"].sum()), 2),
                       "orders": int(camp["orders"].sum()), "ncamp": len(info), "nactive": sum(1 for c in info.values() if c["active"]),
                       "neg_spend": round(sum(n["spend"] for n in neg if n["status"] == "ok"), 2), "neg_ok": sum(1 for n in neg if n["status"] == "ok")}}
        res["accounts"][name]["totals"]["acos"] = _acos(res["accounts"][name]["totals"]["spend"], res["accounts"][name]["totals"]["sales"])
    return res


# ============================================================ template bulk
def tpl_path(key):
    return TPL_DIR / f"{key}.xlsx"


def tpl_meta_path(key):
    return TPL_DIR / f"{key}.json"


def _header_row(ws, must, limit=12):
    for r in range(1, limit + 1):
        for c in range(1, ws.max_column + 1):
            if ws.cell(row=r, column=c).value == must:
                return r
    return None


def _cidx(ws, hr, name, regex=False):
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=hr, column=c).value
        if v is None:
            continue
        if (regex and re.search(name, str(v))) or (not regex and v == name):
            return c
    return None


NEED = {
    "camp": ["Campaign ID", "Current Campaign Name", "Current Campaign Active", "Bidding Strategy", "Current Target ROAS Percentage",
             "New Current Target ROAS Percentage", "New Active Status"],
    "kw": ["Campaign ID", "Target Keyword", r"re:Current Default Bid", "New Default Bid", "Remove from Current Campaign", "Campaign Name", "Campaign Active Status"],
    "lst": ["Campaign ID", "Listing", r"re:Current Default Bid", "New Default Bid", "Remove from Current Campaign", "Campaign Name",
            "Campaign Active Status", "Current Listing Active Status"],
    "neg": ["Negative Keyword", "Negative Keyword Match Type", "Destination Campaign ID", "Destination Campaign Name"],
    "negcur": ["Campaign ID", "Negative Keyword"],
}


def check_template(path):
    """Kiểm tra template có đủ sheet / cột như skill yêu cầu. -> {ok, sheets:{key:{found, missing:[...]}}}"""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=False, data_only=False)
    out, ok = {}, True
    for key, sheet in SHEETS.items():
        if sheet not in wb.sheetnames:
            out[key] = {"sheet": sheet, "found": False, "missing": NEED[key]}; ok = False; continue
        ws = wb[sheet]
        first = NEED[key][0]
        hr = _header_row(ws, first)
        miss = []
        if hr is None:
            miss = [first]
        else:
            for n in NEED[key]:
                if not _cidx(ws, hr, n[3:] if n.startswith("re:") else n, n.startswith("re:")):
                    miss.append(n.replace("re:", ""))
        out[key] = {"sheet": sheet, "found": True, "header_row": hr, "missing": miss}
        ok = ok and not miss
    return {"ok": ok, "sheets": out}


def save_template(key, data, filename):
    if key not in ACCTS:
        raise ValueError("Tài khoản không hợp lệ")
    if not data[:2] == b"PK":
        raise ValueError("File không phải .xlsx")
    TPL_DIR.mkdir(parents=True, exist_ok=True)
    p = tpl_path(key)
    p.write_bytes(data)
    try:
        chk = check_template(p)
    except Exception as e:
        p.unlink(missing_ok=True)
        raise ValueError(f"Không đọc được template: {e}")
    meta = {"name": filename, "uploaded": datetime.now().isoformat(timespec="seconds"), "size": len(data), "check": chk}
    tpl_meta_path(key).write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


def templates():
    out = {}
    for k, (name, cur, cty) in ACCTS.items():
        try:
            out[name] = {"key": k, **json.loads(tpl_meta_path(k).read_text(encoding="utf-8"))}
        except (FileNotFoundError, ValueError):
            out[name] = {"key": k, "missing": True}
    return out


def delete_template(key):
    tpl_path(key).unlink(missing_ok=True); tpl_meta_path(key).unlink(missing_ok=True)


def _isnum(v):
    try:
        float(v); return True
    except (TypeError, ValueError):
        return False


PARTS = ("neg", "kwup", "camp", "kwbid", "lstbid")


def export_bulk(key, comp, parts):
    """Ghi hành động vào BẢN SAO template của tài khoản. Trả (bytes xlsx, báo cáo). Chỉ ghi cột 'New …' / 'Remove …'."""
    import openpyxl
    name, cur, cty = ACCTS[key]
    A = (comp.get("accounts") or {}).get(name)
    if not A or A.get("empty"):
        raise ValueError(f"Chưa có dữ liệu quảng cáo của {name}. Upload đủ file CR/KTR/KOR/PR của kỳ rồi Build.")
    if not tpl_path(key).exists():
        raise ValueError(f"Chưa có template bulk của {name}. Tải template MỚI NHẤT từ Wayfair và upload ở tab Cài đặt.")
    parts = [p for p in parts if p in PARTS]
    if not parts:
        raise ValueError("Chọn ít nhất một nhóm thay đổi để xuất")
    wb = openpyxl.load_workbook(tpl_path(key))
    for p, sheet in (("camp", "camp"), ("kwbid", "kw"), ("kwup", "kw"), ("lstbid", "lst"), ("neg", "neg")):
        if p in parts and SHEETS[sheet] not in wb.sheetnames:
            raise ValueError(f"Template thiếu sheet “{SHEETS[sheet]}”")
    rep = {"parts": parts, "counts": {}, "skipped": {}, "samples": {}}

    def skip(k, n=1):
        rep["skipped"][k] = rep["skipped"].get(k, 0) + n

    # ---- trạng thái campaign trong CHÍNH template (nguồn sự thật cho ACTIVE/INACTIVE)
    ws0 = wb[SHEETS["camp"]]
    hr0 = _header_row(ws0, "Campaign ID")
    if hr0 is None:
        raise ValueError("Không tìm thấy dòng tiêu đề (Campaign ID) trong sheet Edit Sponsored Product Campaign")
    c_id, c_act = _cidx(ws0, hr0, "Campaign ID"), _cidx(ws0, hr0, "Current Campaign Active")
    tpl_active = {}
    for r in range(hr0 + 1, ws0.max_row + 1):
        v = ws0.cell(row=r, column=c_id).value
        if v is not None and _isnum(v):
            tpl_active[int(v)] = ws0.cell(row=r, column=c_act).value == "ACTIVE"
    camp_by_id = {c["campaign_id"]: c for c in A["campaigns"]}

    # ---- 1. campaign
    if "camp" in parts:
        hr = hr0
        c_new_active, c_new_troas = _cidx(ws0, hr, "New Active Status"), _cidx(ws0, hr, "New Current Target ROAS Percentage")
        c_troas, c_strat, c_name = _cidx(ws0, hr, "Current Target ROAS Percentage"), _cidx(ws0, hr, "Bidding Strategy"), _cidx(ws0, hr, "Current Campaign Name")
        n = 0
        for r in range(hr + 1, ws0.max_row + 1):
            v = ws0.cell(row=r, column=c_id).value
            if v is None or not _isnum(v):
                continue
            cid = int(v); c = camp_by_id.get(cid)
            if not c or c["action"] not in ("pause", "troas"):
                continue
            if ws0.cell(row=r, column=c_act).value != "ACTIVE":
                skip("camp_inactive"); continue
            if c["action"] == "pause":
                ws0.cell(row=r, column=c_new_active).value = "INACTIVE"
            else:
                cur_t = ws0.cell(row=r, column=c_troas).value
                if "troas" not in str(ws0.cell(row=r, column=c_strat).value or "").lower() or not _isnum(cur_t):
                    skip("camp_not_troas"); continue
                ws0.cell(row=r, column=c_new_troas).value = c["new_troas"]
            n += 1
            rep["samples"].setdefault("camp", []).append(f"{c['name']}: {c['reason']}")
        rep["counts"]["camp"] = n

    # ---- 2. keyword bids (giảm / xoá / tăng)
    want_kind = set()
    if "kwbid" in parts:
        want_kind |= {"remove", "half", "cut"}
    if "kwup" in parts:
        want_kind |= {"raise"}
    if want_kind:
        ws = wb[SHEETS["kw"]]
        hr = _header_row(ws, "Campaign ID")
        c_i, c_kw = _cidx(ws, hr, "Campaign ID"), _cidx(ws, hr, "Target Keyword")
        c_bid, c_nb = _cidx(ws, hr, r"Current Default Bid", True), _cidx(ws, hr, "New Default Bid")
        c_rm, c_ca = _cidx(ws, hr, "Remove from Current Campaign"), _cidx(ws, hr, "Campaign Active Status")
        amap = {(a["campaign_id"], a["kw"]): a for a in A["kw_actions"] if a["kind"] in want_kind}
        n = 0
        for r in range(hr + 1, ws.max_row + 1):
            v = ws.cell(row=r, column=c_i).value
            kwv = ws.cell(row=r, column=c_kw).value
            if v is None or kwv is None or not _isnum(v):
                continue
            a = amap.get((int(v), _norm_kw(kwv)))
            if not a:
                continue
            if ws.cell(row=r, column=c_ca).value != "ACTIVE":
                skip("kw_inactive"); continue
            if a["kind"] == "remove":
                ws.cell(row=r, column=c_rm).value = "REMOVE"
            else:
                cb = ws.cell(row=r, column=c_bid).value
                if not _isnum(cb) or float(cb) <= 0:
                    skip("kw_no_bid"); continue
                nb = round(float(cb) * a["ratio"], 2)
                if (a["kind"] == "raise" and nb <= float(cb)) or (a["kind"] != "raise" and nb >= float(cb)):
                    skip("kw_no_change"); continue
                ws.cell(row=r, column=c_nb).value = nb
            n += 1
            if len(rep["samples"].setdefault("kw", [])) < 6:
                rep["samples"]["kw"].append(f"{a['keyword']}: {a['why']}")
        rep["counts"]["kw"] = n

    # ---- 3. listing bids
    if "lstbid" in parts:
        if SHEETS["lst"] in wb.sheetnames:
            ws = wb[SHEETS["lst"]]
            hr = _header_row(ws, "Campaign ID")
            c_i, c_l = _cidx(ws, hr, "Campaign ID"), _cidx(ws, hr, "Listing")
            c_bid, c_nb = _cidx(ws, hr, r"Current Default Bid", True), _cidx(ws, hr, "New Default Bid")
            c_rm, c_ca, c_la = _cidx(ws, hr, "Remove from Current Campaign"), _cidx(ws, hr, "Campaign Active Status"), _cidx(ws, hr, "Current Listing Active Status")
            amap = {(a["campaign_id"], a["lst"]): a for a in A["lst_actions"]}
            n = 0
            for r in range(hr + 1, ws.max_row + 1):
                v = ws.cell(row=r, column=c_i).value
                lv = ws.cell(row=r, column=c_l).value
                if v is None or lv is None or not _isnum(v):
                    continue
                a = amap.get((int(v), str(lv).strip().upper()))
                if not a:
                    continue
                if ws.cell(row=r, column=c_ca).value != "ACTIVE" or ws.cell(row=r, column=c_la).value != "ACTIVE":
                    skip("lst_inactive"); continue
                if a["kind"] == "remove":
                    ws.cell(row=r, column=c_rm).value = "REMOVE"
                else:
                    cb = ws.cell(row=r, column=c_bid).value
                    if not _isnum(cb) or float(cb) <= 0:
                        skip("lst_no_bid"); continue
                    nb = round(float(cb) * a["ratio"], 2)
                    if (a["kind"] == "raise" and nb <= float(cb)) or (a["kind"] != "raise" and nb >= float(cb)):
                        skip("lst_no_change"); continue
                    ws.cell(row=r, column=c_nb).value = nb
                n += 1
            rep["counts"]["lst"] = n

    # ---- 4. negative keywords (4 lớp kiểm tra theo skill)
    if "neg" in parts:
        wsn, wsc = wb[SHEETS["neg"]], wb[SHEETS["negcur"]]
        hn, hc = _header_row(wsn, "Negative Keyword"), _header_row(wsc, "Campaign ID")
        c_kw, c_mt = _cidx(wsn, hn, "Negative Keyword"), _cidx(wsn, hn, "Negative Keyword Match Type")
        c_di, c_dn = _cidx(wsn, hn, "Destination Campaign ID"), _cidx(wsn, hn, "Destination Campaign Name")
        e_id, e_kw = _cidx(wsc, hc, "Campaign ID"), _cidx(wsc, hc, "Negative Keyword")
        existing, count = set(), {}
        for r in range(hc + 1, wsc.max_row + 1):
            cid, kv = wsc.cell(row=r, column=e_id).value, wsc.cell(row=r, column=e_kw).value
            if cid is not None and kv is not None and _isnum(cid):
                existing.add((int(cid), _norm_kw(kv))); count[int(cid)] = count.get(int(cid), 0) + 1
        ptr = hn + 1
        while wsn.cell(row=ptr, column=c_kw).value not in (None, ""):
            ptr += 1
        # xung đột 2 chiều với target keyword đã được tính ở compute() (n["conflict"]) từ toàn bộ keyword của campaign
        n, batch = 0, set()
        for x in A["neg"]:
            cid, lo = x["campaign_id"], x["term_lo"]
            if not tpl_active.get(cid, False):
                skip("neg_inactive"); continue
            if (cid, lo) in existing:
                skip("neg_exists"); continue
            if (cid, lo) in batch:
                skip("neg_dup"); continue
            if x["conflict"]:
                skip("neg_conflict"); continue
            if count.get(cid, 0) >= WF_NEG_CAP:
                skip("neg_cap"); continue
            wsn.cell(row=ptr, column=c_kw).value = x["term"]
            wsn.cell(row=ptr, column=c_mt).value = "EXACT"
            wsn.cell(row=ptr, column=c_di).value = cid
            wsn.cell(row=ptr, column=c_dn).value = x["campaign"]
            batch.add((cid, lo)); count[cid] = count.get(cid, 0) + 1
            ptr += 1; n += 1
        rep["counts"]["neg"] = n

    bio = io.BytesIO()
    wb.save(bio)
    rep["total"] = sum(rep["counts"].values())
    return bio.getvalue(), rep


# ============================================================ ranking & share of voice
def _week_points(c, name):
    """Điểm theo tuần của từng listing trong kỳ c: {lst: {first,last,best,avg,n,status,cls,grp,listing}}."""
    a = c["accts"].get(name) or {}
    out = {}
    if "rank" in a and len(a["rank"]):
        lg = a.get("lgrp") or {}
        for l, g in a["rank"].sort_values("date").groupby("lst", sort=True):
            r = g["rank"].astype(int)
            out[l] = {"listing": g["listing"].iloc[-1], "first": int(r.iloc[0]), "last": int(r.iloc[-1]), "best": int(r.min()),
                      "avg": round(float(r.mean()), 1), "n": int(len(r)), "status": g["status"].iloc[-1], "cls": g["cls"].iloc[-1], "grp": lg.get(l)}
    else:
        for x in c["D_rank"].get(name) or []:
            l = str(x["Listing"]).strip().upper()
            out[l] = {"listing": x["Listing"], "first": x["first"], "last": x["last"], "best": x["best"], "avg": None, "n": None,
                      "status": x.get("status"), "cls": x.get("Class Name"), "grp": x.get("grp")}
    return out


def _sov_recs(c, name, classes):
    a = c["accts"].get(name) or {}
    if "sov" in a and len(a["sov"]):
        s = a["sov"]
        s = s[s["cls"].isin(classes)] if classes else s
        return "file", s[["term", "cls", "impr", "shs", "sh_p1", "sh_top8"]].to_dict("records")
    return "báo cáo", [{"term": x["term"], "cls": x["cls"], "impr": x["impr"], "shs": None, "sh_p1": x["sh_p1"], "sh_top8": x["sh_top8"]}
                       for x in c["D_st"].get(name) or []]


def _wavg(recs, f):
    vals = [(r[f], r["impr"]) for r in recs if r.get(f) is not None and not (isinstance(r[f], float) and np.isnan(r[f]))]
    sw = sum(v[1] for v in vals)
    return round(sum(v[0] * v[1] for v in vals) / sw, 2) if sw else None


def rank_view(cfg=None):
    """Xu hướng thứ hạng listing (PSR) theo tuần/ngày + share of voice theo từ khoá (ST). Cảnh báo khi tụt hạng / mất hiện diện.
    Lưu ý: Class Rank của cùng một mã listing giống nhau ở mọi tài khoản (chỉ trạng thái campaign khác nhau) nên gộp theo listing."""
    cfg = cfg or load_cfg()
    cs = history(None)
    if not cs:
        return {"has_data": False}
    cs = cs[-8:]                                  # tối đa 8 tuần gần nhất
    weeks = [{"label": c["label"], "d0": c["d0"], "d1": c["d1"], "src": "file" if c["has_files"] else "báo cáo"} for c in cs]
    merged, accts, alerts = {}, {}, []
    for k, (name, cur, cty) in ACCTS.items():
        pts = [_week_points(c, name) for c in cs]
        daily = {}
        for c in cs:
            a = c["accts"].get(name) or {}
            if "rank" in a and len(a["rank"]):
                for r in a["rank"].itertuples(index=False):
                    daily.setdefault(r.lst, {})[r.date] = int(r.rank)
        for l in sorted({l for p in pts for l in p}):
            series = [p.get(l) for p in pts]
            have = [s for s in series if s]
            last = have[-1]
            m = merged.get(l)
            row = {"lst": l, "listing": last["listing"], "grp": last["grp"], "cls": last["cls"],
                   "series": [None if not s else {"first": s["first"], "last": s["last"], "best": s["best"], "avg": s["avg"]} for s in series],
                   "daily": sorted(daily.get(l, {}).items()), "accts": []}
            if m is None or sum(1 for x in row["series"] if x) + len(row["daily"]) > sum(1 for x in m["series"] if x) + len(m["daily"]):
                row["accts"] = m["accts"] if m else []
                merged[l] = m = row
            m["accts"].append({"acct": name, "status": str(last["status"])})
        # ---- share of voice
        classes = {x["cls"] for l, x in merged.items() if x.get("cls")}
        sov, recs_all = [], []
        for c in cs:
            src, recs = _sov_recs(c, name, classes)
            recs_all.append(recs)
            sov.append({"label": c["label"], "n": len(recs), "impr": int(sum(r["impr"] for r in recs)), "p1": _wavg(recs, "sh_p1"),
                        "top8": _wavg(recs, "sh_top8"), "shs": _wavg(recs, "shs"), "src": src})
        changes = []
        if len(recs_all) >= 2:
            a, b = {r["term"]: r for r in recs_all[-2]}, {r["term"]: r for r in recs_all[-1]}
            for t, rb in b.items():
                ra = a.get(t)
                if not ra or rb["impr"] < cfg["sov_min_impr"] or ra.get("sh_p1") is None or rb.get("sh_p1") is None:
                    continue
                changes.append({"term": t.strip(), "cls": rb["cls"], "impr": int(rb["impr"]), "p1_a": ra["sh_p1"], "p1_b": rb["sh_p1"], "d_p1": round(rb["sh_p1"] - ra["sh_p1"], 2),
                                "top8_a": ra["sh_top8"], "top8_b": rb["sh_top8"], "d_top8": round(rb["sh_top8"] - ra["sh_top8"], 2)})
            changes.sort(key=lambda x: x["d_p1"])
            for ch in changes:
                if ch["d_p1"] <= -cfg["sov_min_drop"]:
                    alerts.append({"acct": name, "listing": "", "cls": ch["cls"], "sev": 2 if ch["d_p1"] <= -2 * cfg["sov_min_drop"] else 1, "kind": "sov",
                                   "why": f"“{ch['term']}”: có mặt ở trang 1 {ch['p1_a']:.2f}% → {ch['p1_b']:.2f}% ({ch['d_p1']:+.2f} điểm)"})
        accts[name] = {"sov": sov, "changes": changes[:15], "gains": [c for c in changes[::-1] if c["d_p1"] > 0][:10], "cur": cur}
    # ---- cảnh báo hạng theo listing (chỉ listing đang ACTIVE ở ít nhất một tài khoản)
    rows = []
    for l, r in merged.items():
        series = r["series"]
        have = [s for s in series if s]
        last = have[-1]
        prev = next((s for s in reversed(series[:-1]) if s), None) if series[-1] else None
        d_in = last["last"] - last["first"]
        d_wow = (last["last"] - prev["last"]) if prev else None
        r["last"], r["best"], r["d_week"], r["d_wow"] = last["last"], last["best"], d_in, d_wow
        r["active_accts"] = [a["acct"] for a in r["accts"] if a["status"].upper() == "ACTIVE"]
        r["alert"] = None
        worst = max([d for d in (d_in, d_wow) if d is not None] or [0])
        base = prev["last"] if (prev and d_wow is not None and d_wow >= d_in) else last["first"]
        pct = worst / base * 100 if base else 0
        if r["active_accts"]:
            if worst >= cfg["rank_min_drop"] and pct >= cfg["rank_min_pct"]:
                r["alert"], r["sev"] = "drop", (3 if worst >= cfg["rank_high_drop"] else 2)
                r["why"] = f"Thứ hạng {base} → {last['last']} (thấp đi {worst} bậc, {pct:.0f}%)"
                alerts.append({"acct": ", ".join(r["active_accts"]), "listing": r["listing"], "grp": r["grp"], "cls": r["cls"], "sev": r["sev"], "kind": "rank", "why": r["why"]})
            else:
                gain = -min([d for d in (d_in, d_wow) if d is not None] or [0])
                if gain >= cfg["rank_min_drop"] and gain / max(last["last"] + gain, 1) * 100 >= cfg["rank_min_pct"]:
                    r["alert"] = "rise"
        rows.append(r)
    rows.sort(key=lambda x: (-(x.get("sev") or 0), 0 if x["active_accts"] else 1, x["listing"]))
    alerts.sort(key=lambda x: -x["sev"])
    return {"has_data": True, "weeks": weeks, "listings": rows, "accounts": accts, "alerts": alerts,
            "cfg": {k: cfg[k] for k in ("rank_min_drop", "rank_min_pct", "rank_high_drop", "sov_min_drop", "sov_min_impr")}}


# ============================================================ tổng quan cho giao diện
def overview(D):
    cfg = load_cfg()
    comp = compute(D, cfg)
    groups = (D or {}).get("meta", {}).get("groups") or []
    be = pre_ads_table(D)
    tt = []
    for g in groups:
        for cty in ("US", "CAN"):
            t, src, b = target_for_grp(g, cty, cfg, be)
            tt.append({"grp": g, "cty": cty, "pre_ads": b, "target": t, "src": src, "key": f"{g}|{cty}", "override": cfg["overrides"].get(f"{g}|{cty}")})
    n_pl = sum(1 for x in tt if x["src"] == "pl")
    rates = ((D or {}).get("fx") or {}).get("rates") or {}
    comp["fx"] = {"USD": 1.0, "CAD": float(rates.get("CAD") or 1.0)}
    n_low = sum(1 for x in tt if x["pre_ads"] is not None and x["pre_ads"] < cfg["min_target"])
    return {"n_low": n_low, "cfg": cfg, "defaults": DEFAULTS, "targets": tt, "n_pl": n_pl, "n_targets": len(tt), "templates": templates(), "comp": comp}
