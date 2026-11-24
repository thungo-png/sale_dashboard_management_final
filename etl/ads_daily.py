"""Chi phí + doanh thu quảng cáo THEO NGÀY của chiến dịch Thu Ngo (để ô chọn khoảng ngày của mẫu Gọn v4 tính được chi phí/ROAS 7-14-30 ngày).

Khác ads.py: KHÔNG cắt theo tuần báo cáo, đọc nguyên khoảng ngày có trong file. Quy tắc nhận chiến dịch / quốc gia / quy đổi USD giống ads.py
(tổng đúng 7 ngày của kỳ phải trùng adsum.spend; có test tests/test_ads_daily.py).
Kết quả -> D["ads_daily"] = {"cov": {"Wayfair|US": ["2026-09-27","2026-10-05"], ...},          # ngày đầu/cuối CÓ trong file của kênh đó
                            "d":   {"Wayfair|US": {"2026-09-27": [chi_phí_USD, doanh_thu_QC_USD], ...}, ...}}
Kênh không có file thì không có trong cov -> báo cáo hiểu là "chưa đủ dữ liệu". Khối này chỉ mẫu có dùng; mẫu gốc bỏ qua."""
import pandas as pd
from etl.ads import RX_THU, WF_ACCT, AMZ_ACCT, _usd, _spendcol, _read_any


def _add(d, cov, key, day, sp, sa):
    x = d.setdefault(key, {}).setdefault(day, [0.0, 0.0]); x[0] += sp; x[1] += sa


def _cov(cov, key, t):
    a, b = t.min(), t.max()
    o = cov.get(key)
    cov[key] = [min(o[0], a), max(o[1], b)] if o else [a, b]


def build_ads_daily(files, rates, log=print):
    d, cov = {}, {}
    for acct, path in (files.get("wf_CR") or {}).items():
        cty, cur = WF_ACCT[acct]; fx = _usd(cur, rates)
        c = _read_any(path); c["Date"] = pd.to_datetime(c["Date"])
        sc = _spendcol(c)
        sales_c = "attributed_retail_sales_window_view_through_USD_Day_14" if "attributed_retail_sales_window_view_through_USD_Day_14" in c.columns else next(
            x for x in c.columns if x.startswith("attributed_retail_sales"))
        key = "Wayfair|" + cty
        _cov(cov, key, c.Date.dt.strftime("%Y-%m-%d"))
        t = c[c.campaign_name.astype(str).str.contains(RX_THU)]
        for day, g in t.groupby(t.Date.dt.strftime("%Y-%m-%d")):
            _add(d, cov, key, day, float(g[sc].sum()) * fx, float(g[sales_c].sum()) * (1 if cur == "USD" else fx))
    if files.get("amazon"):
        a = pd.read_csv(files["amazon"]); a["Date"] = pd.to_datetime(a["Date"], format="%b %d, %Y")
        for c in ["Total cost", "Sales"]:
            a[c] = pd.to_numeric(a[c], errors="coerce").fillna(0)
        for name, (acct, cty, cur) in AMZ_ACCT.items():
            g0 = a[a["Advertiser account name"] == name]
            if g0.empty:
                continue
            fx = _usd(cur, rates); key = "Amazon|" + cty
            _cov(cov, key, g0.Date.dt.strftime("%Y-%m-%d"))
            t = g0[g0["Campaign name"].astype(str).str.contains(RX_THU)]
            for day, g in t.groupby(t.Date.dt.strftime("%Y-%m-%d")):
                _add(d, cov, key, day, float(g["Total cost"].sum()) * fx, float(g["Sales"].sum()) * fx)
    out = {"cov": {k: v for k, v in sorted(cov.items())},
           "d": {k: {day: [round(x[0], 2), round(x[1], 2)] for day, x in sorted(v.items())} for k, v in sorted(d.items())}}
    log("[ads_daily] " + "; ".join(f"{k}: {v[0]}→{v[1]}" for k, v in out["cov"].items()))
    return out
