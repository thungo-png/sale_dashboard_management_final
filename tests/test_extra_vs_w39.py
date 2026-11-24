"""Test đợt 4a: top_sku2, grpcmp, sku_meta trên số W39 đã dựng. python3 -I tests/test_extra_vs_w39.py"""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import builder
from etl import extra
from test_sales_vs_w39 import diff
seed = builder.seed_data(); bad = 0
names = {r["sku"]: r["name"] for r in seed["sku_meta"]}
res = {"top_sku2": extra.build_top_sku2(seed, names), "grpcmp": extra.build_grpcmp(seed, seed["grpcmp"])}
res["askuw_mp"] = extra.build_askuw_mp(seed, names, seed["fx"]["rates"])
res["sizecolor"] = extra.build_sizecolor(seed, dict(seed["sizecolor"], **{k: [x for x in seed["sizecolor"][k] if x["W"] != 39] for k in ("size_wk", "color_wk")}))
res["top_sku2"]["note"] = seed["top_sku2"]["note"]
for k, v in res.items():
    d = diff(v, seed[k], k); bad += bool(d)
    print(("OK   " if not d else "DIFF ") + k); [print("      ", x) for x in d[:6]]
print("TỔNG:", "TẤT CẢ KHỚP" if not bad else f"{bad} khối lệch")
