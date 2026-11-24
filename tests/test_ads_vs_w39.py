"""
Test đợt 3 (quảng cáo): chạy etl.ads.build_ads trên file thô Data_W39, so với D của W39.
python3 -I tests/test_ads_vs_w39.py "<thư mục Data_W39>"
"""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import builder
from etl import sales, ads
from test_sales_vs_w39 import diff

root = Path(sys.argv[1]); sem = root / "2_SEM_W39"
seed = builder.seed_data()
rates = seed["fx"]["rates"]
d0, d1 = pd.Timestamp(seed["meta"]["d0"]), pd.Timestamp(seed["meta"]["d1"])
S = sales.load_sales(root / "1_Report_W39/data W39.xlsx", rates)
files = {"amazon": next(root.glob("3_File_bo_sung/*Amazon*Copy*.csv"))}
for rep, key in [("CR", "wf_CR"), ("PR", "wf_PR"), ("PSR", "wf_PSR"), ("STRR", "wf_ST")]:
    files[key] = {a: next(sem.glob(f"{a} {rep}*.xlsx")) for a in ("ARZ", "MS", "DHI")}
out = ads.build_ads(files, S, seed, rates, d0, d1)
bad = 0
for k in ["campthu", "scope", "adsum", "tacos", "dgmk_room", "adlist_cover"]:
    d = diff(out[k], seed[k], k); bad += bool(d)
    print(("OK   " if not d else "DIFF ") + k); [print("      ", x) for x in d[:4]]
for k in ("rank", "st"):
    d = diff(out["ads"][k], seed["ads"][k], f"ads/{k}"); bad += bool(d)
    print(("OK   " if not d else "DIFF ") + f"ads.{k}"); [print("      ", x) for x in d[:4]]
print("TỔNG:", "TẤT CẢ KHỚP" if not bad else f"{bad} khối lệch")
