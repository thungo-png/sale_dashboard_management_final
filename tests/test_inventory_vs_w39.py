"""python3 -I tests/test_inventory_vs_w39.py "<Data Inv & Report Sales.xlsx>" — đối chiếu invdet/invacct với D của W39."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import builder
from etl import inventory as I
from test_sales_vs_w39 import diff

seed = builder.seed_data()
mine = I.load_scope(sys.argv[1], seed["meta"]["groups"], "Ngô Thị Anh Thư")
sold = {}
for r in seed["sku"]: sold[r["sku"]] = sold.get(r["sku"], 0) + r["q"]
det = I.build_invdet(mine, seed["meta"]["groups"], sold)
n_scope = len(det["sku_tot"])
acct = I.build_invacct(mine, n_scope, seed["invacct"]["note_longterm"])
bad = 0
for name, got, want in [("invdet", det, seed["invdet"]), ("invacct", acct, seed["invacct"])]:
    for k in want:
        d = diff(got[k], want[k], f"{name}/{k}")
        print(("OK   " if not d else "DIFF ") + f"{name}/{k}" + ("" if not d else f" ({len(d)}+)"))
        for x in d[:3]: print("      ", x)
        bad += bool(d)
print("TỔNG:", "TẤT CẢ KHỚP" if not bad else f"{bad} khối lệch")
