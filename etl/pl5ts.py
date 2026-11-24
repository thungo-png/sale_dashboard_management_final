"""
Chuỗi Profit PL5 theo thời gian (D.pl5ts) — để mọi biểu đồ/thẻ PL5 đổi theo khoảng ngày người dùng chọn.

Cách tính (cùng công thức với D.pl5 của kỳ báo cáo — file P&L đã lưu ở data/pl_ratecard/current.xlsx):
  1. Với MỖI TUẦN đủ chi phí quảng cáo thật: dựng lại các dòng SKU × sàn × thị trường của tuần từ D.ts_sku.W.l3
     rồi chạy đúng hàm build_pl5_v2 (COGS, Ref fee, Fulfillment, Return theo file P&L; SEM = chi phí quảng cáo thật của tuần).
     Tuần báo cáo hiện tại dùng thẳng D.pl5.rows nên tổng khớp tuyệt đối với D.pl5.
  2. Mức NGÀY: profit tuần của từng dòng chia về ngày theo tỷ trọng doanh thu ngày của chính dòng đó (D.ts_sku.D.l3).
     => tổng các ngày của một tuần = profit tuần.
  3. Tuần KHÔNG đủ chi phí quảng cáo thật (thiếu file của 1 trong các tài khoản) thì BỎ, không dùng tỷ lệ % ước tính.
Chi phí quảng cáo thật theo tuần × (nhóm, sàn, quốc gia) được lưu ở data/pl_sem_history.json để các kỳ sau còn dùng được
dù file quảng cáo của tuần cũ không còn trong lần upload mới.

Khối ghi vào D: pl5ts = {labels:{D:[ngày],W:[số tuần]}, D:{họ:{tên:{kỳ:[profit,doanh thu]}}}, W:{...}, weeks:{tuần:{p,r}}, note, sem_cov}
  họ: all, mp, cty, mpcty, grp, grp_mp, grp_cty, l1, l2, l3  (tên ghép bằng " · " giống ts_*)
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from etl import ads as adsm
from etl import pl5 as plm
from etl.sales import wkno, wk_start

SEP = " · "
HIST = Path(__file__).resolve().parent.parent / "data" / "pl_sem_history.json"
WF_ACCTS = ("ARZ", "MS", "DHI")
AMZ_NEED = ("Amazon",)


def _noop(*a, **k):
    pass


# ------------------------------------------------------------------ lịch sử SEM theo tuần
def load_hist(path=None):
    p = Path(path) if path else HIST
    try:
        h = json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        h = {}
    h.setdefault("weeks", {})
    return h


def save_hist(h, path=None):
    p = Path(path) if path else HIST
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(h, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, p)


def _key(grp, mp, cty):
    return f"{grp or ''}|{mp}|{cty}"


def _unkey(k):
    g, mp, cty = k.split("|")
    return (g or None, mp, cty)


# ------------------------------------------------------------------ chi phí QC thật theo ngày -> tuần
def sem_from_files(wf_files, amazon_file, groups, rates, log=_noop):
    """wf_files: {ARZ|MS|DHI: path CR}, amazon_file: path. Trả ({tuần: {key: usd}}, {tuần: bool đủ dữ liệu}, ghi chú)."""
    cells, cov, notes = {}, {}, []
    for acct in WF_ACCTS:
        p = wf_files.get(acct)
        if not p:
            notes.append(f"thiếu CR {acct}")
            continue
        try:
            c = adsm._read_any(p)
        except Exception as e:
            notes.append(f"không đọc được CR {acct}: {e}")
            continue
        if "Date" not in c.columns:
            notes.append(f"CR {acct} không có cột Date (xuất theo tuần?) — cần xuất theo NGÀY")
            continue
        cty, cur = adsm.WF_ACCT[acct]
        fx = adsm._usd(cur, rates)
        c["Date"] = pd.to_datetime(c["Date"])
        cov[acct] = (c.Date.min(), c.Date.max())
        sc = adsm._spendcol(c)
        t = c[c.campaign_name.astype(str).str.contains(adsm.RX_THU)].copy()
        t["wk"] = ((t.Date - wk_start(1)).dt.days // 7 + 1).astype(int)
        t["grp"] = [adsm.group_of(n, groups) for n in t.campaign_name]
        for (wk, g), s in t.groupby(["wk", "grp"], dropna=False)[sc].sum().items():
            g = None if pd.isna(g) else g
            k = _key(g, "Wayfair", cty)
            cells.setdefault(int(wk), {})[k] = cells.get(int(wk), {}).get(k, 0.0) + float(s) * fx
    if amazon_file:
        try:
            a = pd.read_csv(amazon_file)
            a["Date"] = pd.to_datetime(a["Date"], format="%b %d, %Y")
            cov["AMZ"] = (a.Date.min(), a.Date.max())
            a["Total cost"] = pd.to_numeric(a["Total cost"], errors="coerce").fillna(0)
            t = a[a["Campaign name"].astype(str).str.contains(adsm.RX_THU)].copy()
            t["wk"] = ((t.Date - wk_start(1)).dt.days // 7 + 1).astype(int)
            t["grp"] = [adsm.group_of(n, groups) for n in t["Campaign name"]]
            for name, (acct, cty, cur) in adsm.AMZ_ACCT.items():
                fx = adsm._usd(cur, rates)
                u = t[t["Advertiser account name"] == name]
                for (wk, g), s in u.groupby(["wk", "grp"], dropna=False)["Total cost"].sum().items():
                    g = None if pd.isna(g) else g
                    k = _key(g, "Amazon", cty)
                    cells.setdefault(int(wk), {})[k] = cells.get(int(wk), {}).get(k, 0.0) + float(s) * fx
        except Exception as e:
            notes.append(f"không đọc được file Amazon Ads: {e}")
    else:
        notes.append("thiếu file Amazon Ads")
    need = [cov.get(a) for a in WF_ACCTS] + [cov.get("AMZ")]
    full = {}
    if all(need):
        lo = max(x[0] for x in need); hi = min(x[1] for x in need)
        for wk in range(1, 60):
            s = wk_start(wk); e = s + pd.Timedelta(days=6)
            if s >= lo and e <= hi:
                full[wk] = True
    return cells, full, notes


def merge_hist(hist, cells, full, log=_noop):
    """Ghi các tuần đủ dữ liệu vào lịch sử (ghi đè số cũ của cùng tuần bằng file mới nhất)."""
    n = 0
    for wk in sorted(full):
        c = {k: round(v, 2) for k, v in cells.get(wk, {}).items()}
        old = hist["weeks"].get(str(wk))
        if old != c:
            hist["weeks"][str(wk)] = c
            n += 1
    return n


# ------------------------------------------------------------------ dựng chuỗi PL5
def _fam_names(mp, cty, grp, sku):
    return {
        "all": "Tổng", "mp": mp, "cty": cty, "mpcty": mp + SEP + cty, "grp": grp,
        "grp_mp": grp + SEP + mp, "grp_cty": grp + SEP + cty,
        "l1": sku, "l2": sku + SEP + cty, "l3": sku + SEP + mp + SEP + cty,
    }


def build_pl5ts(D, rc, rates, camp_spend_cur, wk_cur, hist=None, log=_noop):
    """D: dict dữ liệu (đã có ts_sku, sku_meta, pl5 của tuần hiện tại). camp_spend_cur: {(grp,mp,cty):[chi]} của tuần hiện tại."""
    hist = hist if hist is not None else load_hist()
    tsl = D["ts_labels"]
    days_all = list(tsl["D"]); weeks_all = [int(w) for w in tsl["W"]]
    l3W = D["ts_sku"]["W"]["l3"]; l3D = D["ts_sku"]["D"]["l3"]
    g_of = {r["sku"]: r["grp"] for r in D.get("sku_meta", [])}
    for r in D.get("sku", []):
        g_of.setdefault(r["sku"], r["grp"])
    # tuần nào tính được: có SEM thật (lịch sử) hoặc là tuần báo cáo hiện tại
    wk_days = {}
    for w in weeks_all:
        s = wk_start(w)
        wk_days[w] = [d for d in days_all if s <= pd.Timestamp(d) <= s + pd.Timedelta(days=6)]
    use = []
    for w in weeks_all:
        if len(wk_days[w]) < 7:
            continue                                  # chỉ lấy tuần đủ 7 ngày trong chuỗi ngày
        if w == wk_cur or str(w) in hist["weeks"]:
            use.append(w)
    skipped = [w for w in weeks_all if w not in use and len(wk_days[w]) == 7]
    log(f"[pl5ts] tuần có PL5 theo chi phí QC thật: {', '.join('W%d' % w for w in use) or 'không có'}"
        + (f" | chưa đủ chi phí QC thật: {', '.join('W%d' % w for w in skipped)}" if skipped else ""))
    if not use:
        return None

    base_D = {"sku_meta": D.get("sku_meta", [])}
    DAY, WEEK = {}, {}      # DAY[fam][name][day] = [p, r]
    wsum = {}

    def add(store, fam, name, per, p, r):
        x = store.setdefault(fam, {}).setdefault(name, {}).setdefault(per, [0.0, 0.0])
        x[0] += p; x[1] += r

    for w in use:
        if w == wk_cur and D.get("pl5") and D["pl5"].get("rows"):
            rows = D["pl5"]["rows"]
            unal = float((D["pl5"].get("total") or {}).get("sem_unalloc") or 0.0)
        else:
            ws = str(w)
            rowsin = []
            for name, ser in l3W.items():
                x = ser.get(ws) or ser.get(w)
                if x and x.get("q", 0) > 0:
                    sku, mp, cty = name.split(SEP)
                    rowsin.append({"sku": sku, "grp": g_of.get(sku), "mp": mp, "cty": cty, "q": x["q"], "r": x["r"]})
            cs = {}
            for k, v in hist["weeks"][ws].items():
                cs.setdefault(_unkey(k), []).append(v)
            res = plm.build_pl5_v2(dict(base_D, sku=rowsin), rc, cs, rates, None, "", log=_noop)
            rows = res["rows"]
            unal = float((res["total"] or {}).get("sem_unalloc") or 0.0)
        days = wk_days[w]
        rsum = sum(x["r"] for x in rows) or 1.0
        for rw in rows:
            sku, mp, cty, grp = rw["sku"], rw["mp"], rw["cty"], rw["grp"]
            # chi phí QC thật không gán được vào dòng nào (unalloc) trừ theo tỷ trọng doanh thu để tổng khớp D.pl5.total.profit
            rw = dict(rw, profit=rw["profit"] - unal * rw["r"] / rsum)
            nm = _fam_names(mp, cty, grp, sku)
            for fam, name in nm.items():
                add(WEEK, fam, name, str(w), rw["profit"], rw["r"])
            ser = l3D.get(SEP.join((sku, mp, cty))) or {}
            rv = np.array([float((ser.get(d) or {}).get("r", 0.0)) for d in days])
            if rv.sum() > 1e-9:
                sh = rv / rv.sum()
            else:
                qv = np.array([float((ser.get(d) or {}).get("q", 0.0)) for d in days])
                sh = qv / qv.sum() if qv.sum() > 0 else np.full(len(days), 1 / len(days))
            rtot = rw["r"]
            for i, d in enumerate(days):
                if sh[i] == 0:
                    continue
                p_d = rw["profit"] * sh[i]
                r_d = rtot * sh[i]
                for fam, name in nm.items():
                    add(DAY, fam, name, d, p_d, r_d)
        wsum[str(w)] = [round(sum(r["profit"] for r in rows) - unal, 2), round(sum(r["r"] for r in rows), 2)]

    def pack(store):
        return {fam: {name: {per: [round(float(v[0]), 2), round(float(v[1]), 2)] for per, v in sorted(pp.items()) if abs(v[0]) > 1e-9 or abs(v[1]) > 1e-9}
                      for name, pp in sorted(d.items())} for fam, d in store.items()}

    day_labels = [d for w in use for d in wk_days[w]]
    out = {"labels": {"D": day_labels, "W": use}, "D": pack(DAY), "W": pack(WEEK),
           "weeks": {k: {"p": v[0], "r": v[1]} for k, v in wsum.items()},
           "note": ("Profit PL5 theo công thức trong file P&L đã lưu; SEM = chi phí quảng cáo thật của từng tuần. "
                    "Mức ngày = profit tuần chia theo tỷ trọng doanh thu ngày của từng dòng SKU × sàn × thị trường. "
                    "Tuần chưa đủ file quảng cáo thật thì không có số.")}
    log(f"[pl5ts] {len(use)} tuần, {len(day_labels)} ngày; tổng {sum(v[0] for v in wsum.values()):,.0f} USD profit trên {sum(v[1] for v in wsum.values()):,.0f} USD doanh thu")
    return out
