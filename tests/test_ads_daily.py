"""Chi phí QC theo ngày (etl/ads_daily.py) phải cộng đúng 7 ngày của kỳ = adsum.spend / whl của kỳ đó.
   Chạy: python3 tests/test_ads_daily.py [id_kỳ]  (mặc định kỳ mới nhất có file upload)"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from etl.ads_daily import build_ads_daily

pid = sys.argv[1] if len(sys.argv) > 1 else "2026-W40"
P = ROOT / "data" / "periods" / pid
if not (P / "data.json").exists() or not (P / "uploads").exists():
    print("BỎ QUA: không có data.json / uploads của kỳ", pid); sys.exit(0)
D = json.loads((P / "data.json").read_text(encoding="utf-8")); U = P / "uploads"
pick = lambda pat: next(iter(sorted(U.glob(pat))), None)
f = {"wf_CR": {a: pick(f"wf_{n}_CR__*") for a, n in (("ARZ", "arozu"), ("MS", "megsu"), ("DHI", "dhi"))}, "amazon": pick("amazon_ads__*")}
if not f["amazon"] or not all(f["wf_CR"].values()):
    print("BỎ QUA: thiếu file quảng cáo"); sys.exit(0)
o = build_ads_daily(f, D["fx"]["rates"], log=lambda *_: None)
d0, d1 = D["meta"]["d0"], D["meta"]["d1"]; bad = 0
for x in D["adsum"]:
    k = f'{x["mp"]}|{x["cty"]}'; v = o["d"].get(k, {})
    sp = sum(c[0] for day, c in v.items() if d0 <= day <= d1); sa = sum(c[1] for day, c in v.items() if d0 <= day <= d1)
    ok = abs(sp - x["spend"]) <= 0.1 and abs(sa - x["whl"]) <= 0.1
    bad += not ok
    print(("OK  " if ok else "LỆCH"), k, round(sp, 2), x["spend"], round(sa, 2), x["whl"])
sys.exit(1 if bad else 0)
