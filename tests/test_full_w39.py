"""
Test tích hợp: chạy etl/custom_build.build từ kỳ trước giả lập (W38) với bộ file Data_W39, so với D của W39.
python3 -I tests/test_full_w39.py "<thư mục Data_W39>"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import builder
from etl import sales
from etl.custom_build import build, PENDING
from test_sales_vs_w39 import diff, unapply

root = Path(sys.argv[1])
seed = builder.seed_data()
inputs = {
    "data_current": root / "1_Report_W39/data W39.xlsx",
    "master": next(root.glob("1_Report_W39/Data Inv*.xlsx")),
    "cg_ARZ": next(root.glob("2_SEM_W39/ARZ*CastleGate*.csv")), "cg_DHI": next(root.glob("2_SEM_W39/DHI*CastleGate*.csv")),
    "cg_MS": next(root.glob("2_SEM_W39/MS*CastleGate*.csv")),
    "fba_US": next(root.glob("3_File_bo_sung/*FBA US*.csv")), "fba_CAN": next(root.glob("3_File_bo_sung/*FBA CAN*.csv")),
    "pl5": next(root.glob("1_Report_W39/P&L*.xlsx")),
    "amazon_ads": next(root.glob("3_File_bo_sung/*Amazon*Copy*.csv")),
}
for n, a in (("arozu", "ARZ"), ("megsu", "MS"), ("dhi", "DHI")):
    for rep, f in (("CR", "CR"), ("PR", "PR"), ("PSR", "PSR"), ("ST", "STRR")):
        inputs[f"wf_{n}_{rep}"] = next((root / "2_SEM_W39").glob(f"{a} {f}*.xlsx"))
S = sales.load_sales(inputs["data_current"], seed["fx"]["rates"])
prev = unapply(seed, S, pd.Timestamp(seed["meta"]["d0"]), pd.Timestamp(seed["meta"]["d1"]), seed["meta"]["week_no"])
for k in ("amz", "wf"):  # lt kỳ trước giả lập
    prev["lt"][k]["summary"] = [dict(r, tot=r["prev_tot"]) for r in seed["lt"][k]["summary"]]
    prev["lt"][k]["sku"] = [dict(r, tot=r["prev_tot"]) for r in seed["lt"][k]["sku"]]
D = build({"cfg": {"pic": "Ngô Thị Anh Thư", "group_norm": {}}, "inputs": inputs, "prev": prev, "log": print})

bad = 0
for k in ["cell", "cell_prev", "bygrp", "bygrp_prev", "bygrp_cell", "sku", "weekly_grp", "weekfc", "monthly", "quarterly", "ytd",
          "ts_ov", "ts_grp", "ts_grpcell", "ts_sku", "ts_labels", "invdet", "invacct", "campthu", "scope", "adsum", "tacos", "dgmk_room", "adlist_cover", "sku_meta", "top_sku2", "grpcmp", "askuw_mp"]:
    d = diff(D[k], seed[k], k); bad += bool(d)
    print(("OK   " if not d else "DIFF ") + k); [print("      ", x) for x in d[:3]]
for k in ("amz", "wf"):
    for f in seed["lt"][k]:
        if f == "note": continue
        d = diff(D["lt"][k][f], seed["lt"][k][f], f"lt/{k}/{f}"); bad += bool(d)
        if d: print("DIFF", f"lt/{k}/{f}", d[:2])
print("lt: OK" if not bad else "")
miss, extra = builder.schema_check(D, seed)
for k in ("rows", "total", "by_mpcty", "by_grp", "coverage_pct", "missing_sku_fee", "no_formula_mpcty"):
    d = diff(D["pl5"][k], seed["pl5"][k], "pl5/" + k); bad += bool(d)
    print(("OK   " if not d else "DIFF ") + "pl5/" + k); [print("      ", x) for x in d[:4]]
d = diff(D["sizecolor"], seed["sizecolor"], "sizecolor"); bad += bool(d); print("OK   sizecolor" if not d else "DIFF sizecolor", d[:3])
d = diff(D["ads"], seed["ads"], "ads"); bad += bool(d); print("OK   ads" if not d else "DIFF ads")
print("schema thiếu/thừa key:", miss, extra)
print("GIỮ NGUYÊN so với kỳ trước (không tính lại):", all(D[k] == prev[k] for k in PENDING))
print("TỔNG:", "TẤT CẢ KHỚP" if not bad else f"{bad} khối lệch")
