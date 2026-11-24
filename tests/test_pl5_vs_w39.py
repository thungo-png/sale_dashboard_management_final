"""Test PL5: python3 -I tests/test_pl5_vs_w39.py "<thư mục Data_W39>" """
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import builder
from etl import pl5
from test_sales_vs_w39 import diff
root = Path(sys.argv[1]); seed = builder.seed_data()
rc = pl5.load_ratecard(next(root.glob("1_Report_W39/P&L*.xlsx")))
import pandas as pd
from etl import ads
d0, d1 = pd.Timestamp(seed["meta"]["d0"]), pd.Timestamp(seed["meta"]["d1"])
nm = {"ARZ": "Arozu", "MS": "Megsu", "DHI": "DHI"}
pr = {nm[a]: ads.read_wf(next((root / "2_SEM_W39").glob(f"{a} PR*.xlsx")), d0, d1) for a in nm}
spend = ads.sem_by_group(pr, seed["campthu"], seed["fx"]["rates"], seed["meta"]["groups"])
out = pl5.build_pl5(seed, rc, spend, seed["fx"]["rates"], seed["pl5"], seed["pl5"]["why"])
bad = 0
for k in ["rows", "total", "by_mpcty", "by_grp", "coverage_pct", "missing_sku_fee", "no_formula_mpcty"]:
    d = diff(out[k], seed["pl5"][k], "pl5/" + k); bad += bool(d)
    print(("OK   " if not d else "DIFF ") + k); [print("      ", x) for x in d[:8]]
print("TỔNG:", "TẤT CẢ KHỚP" if not bad else f"{bad} khối lệch")
if "-v" in sys.argv:
    for a, b in zip(out["rows"], seed["pl5"]["rows"]):
        if abs(a["sem"] - b["sem"]) > 0.001: print(a["sku"], a["mp"], a["cty"], a["sem"], b["sem"])
if "-vv" in sys.argv:
    for a, b in zip(out["rows"], seed["pl5"]["rows"]):
        dd = {k: (a[k], b[k]) for k in ("cogs", "ref_fee", "sem", "return_fee", "wh_fee", "op_fee", "fulfill", "tong_cp", "profit") if abs(a[k] - b[k]) > 0.001}
        if dd: print(a["sku"], a["mp"], a["cty"], dd)
