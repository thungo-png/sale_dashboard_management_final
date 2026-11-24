"""python3 -I tests/test_lt_vs_w39.py "<thư mục Data_W39>" — đối chiếu D['lt'] với D của W39 (kỳ trước giả lập từ prev_tot)."""
import sys, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import builder
from etl import longterm as T
from test_sales_vs_w39 import diff

root = Path(sys.argv[1])
seed = builder.seed_data()
# kỳ trước giả lập: tot = prev_tot của đáp án
prev = {}
for k in ("amz", "wf"):
    prev[k] = {"summary": [{"acct": r["acct"], "tot": r["prev_tot"]} for r in seed["lt"][k]["summary"]],
               "sku": [{"sku": r["sku"], "acct": r["acct"], "tot": r["prev_tot"]} for r in seed["lt"][k]["sku"]]}
cg = {"ARZ": next(root.glob("2_SEM_W39/ARZ*CastleGate*.csv")), "DHI": next(root.glob("2_SEM_W39/DHI*CastleGate*.csv")),
      "MS": next(root.glob("2_SEM_W39/MS*CastleGate*.csv"))}
fba = {"US": next(root.glob("3_File_bo_sung/*FBA US*.csv")), "CAN": next(root.glob("3_File_bo_sung/*FBA CAN*.csv"))}
master = next(root.glob("1_Report_W39/Data Inv*.xlsx"))
got = T.build_lt(master, seed["meta"]["groups"], cg, fba, prev)
bad = 0
for k in ("amz", "wf"):
    for f in seed["lt"][k]:
        d = diff(got[k][f], seed["lt"][k][f], f"lt/{k}/{f}")
        print(("OK   " if not d else "DIFF ") + f"lt/{k}/{f}" + ("" if not d else f" ({len(d)}+)"))
        for x in d[:4]: print("      ", x)
        bad += bool(d)
print("TỔNG:", "TẤT CẢ KHỚP" if not bad else f"{bad} khối lệch")
