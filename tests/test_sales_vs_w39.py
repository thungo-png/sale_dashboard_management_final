"""
Kiểm chứng ETL bán hàng: lấy D của W39 (trong template) làm đáp án, 'gỡ' tuần W39 để ra trạng thái kỳ trước giả lập,
chạy build_sales từ file data W39.xlsx rồi so với đáp án.
Chạy:  python3 -I tests/test_sales_vs_w39.py "<đường dẫn data W39.xlsx>"
"""
import copy, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
import builder
from etl import sales

TOL = 0.02


def close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= TOL
    return a == b


def diff(a, b, path="", out=None, limit=8):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a: out.append(f"{path}/{k}: thiếu ở kết quả")
            elif k not in b: out.append(f"{path}/{k}: thừa ở kết quả")
            else: diff(a[k], b[k], f"{path}/{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): out.append(f"{path}: độ dài {len(a)} ≠ {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)): diff(x, y, f"{path}[{i}]", out, limit)
    elif not close(a, b):
        out.append(f"{path}: {a!r} ≠ {b!r}")
    return out


def unapply(seed, S, d0, d1, wk):
    P = copy.deepcopy(seed)
    P["cell"], P["bygrp"] = seed["cell_prev"], seed["bygrp_prev"]
    P["meta"]["week_no"] = wk - 1
    P["weekly_grp"] = [r for r in P["weekly_grp"] if r["W"] < wk]
    P["weekfc"]["all"] = [w for w in P["weekfc"]["all"] if w["wk"] < wk]
    cur = S[(S.date >= d0) & (S.date <= d1)].copy()
    cur["M"], cur["Q"] = cur.date.map(sales.mlabel), cur.date.map(sales.qlabel)

    def sub(block, keys, fk):
        idx = {tuple(r[k] for k in keys): r for r in block}
        for x in sales._agg(cur, fk).itertuples():
            r = idx[tuple(getattr(x, k) for k in keys)]
            r["q"] -= int(x.q)
            for f in ("r", "qfc", "rfc"): r[f] = round(r[f] - float(getattr(x, f)), 2)
    sub(P["monthly"], ["M", "mp"], ["M", "mp"]); sub(P["quarterly"], ["Q", "mp"], ["Q", "mp"]); sub(P["ytd"], ["cty", "mp"], ["cty", "mp"])
    # ts_*: xoá ngày >= d0, tuần wk; trừ M/Q
    cur["day"] = cur.date.dt.strftime("%Y-%m-%d")
    cut = d0.strftime("%Y-%m-%d")
    for path, names in sales._families(cur):
        t = cur.assign(_n=names.values)
        top, fam = path
        for g, col in (("M", "M"), ("Q", "Q")):
            node = P[top][g] if fam is None else P[top][g][fam]
            for x in t.groupby(["_n", col]).agg(q=("q", "sum"), r=("r", "sum"), rfc=("rfc", "sum")).reset_index().itertuples():
                if not sales._nz(x.q, x.r, x.rfc): continue
                c = node[x._1][getattr(x, col)]
                c["q"] -= int(x.q); c["r"] = round(c["r"] - x.r, 2); c["rfc"] = round(c["rfc"] - x.rfc, 2)
                if not sales._nz(c["q"], c["r"], c["rfc"]): del node[x._1][getattr(x, col)]
        for g in ("D", "W"):
            node = P[top][g] if fam is None else P[top][g][fam]
            for n in list(node):
                node[n] = {k: v for k, v in node[n].items() if (k < cut if g == "D" else int(k) < wk)}
                if not node[n]: del node[n]
    return P


def main(path):
    seed = builder.seed_data()
    rates = seed["fx"]["rates"]
    S = sales.load_sales(path, rates)
    d0, d1, wk = pd.Timestamp(seed["meta"]["d0"]), pd.Timestamp(seed["meta"]["d1"]), seed["meta"]["week_no"]
    prev = unapply(seed, S, d0, d1, wk)
    D, _, _ = sales.build_sales(prev, path, log=print)

    keys = ["cell", "cell_prev", "bygrp", "bygrp_prev", "bygrp_cell", "sku", "weekly_grp", "weekfc",
            "monthly", "quarterly", "ytd", "ts_ov", "ts_grp", "ts_grpcell", "ts_sku", "ts_labels"]
    bad = 0
    for k in keys:
        d = diff(D[k], seed[k], k)
        print(("OK   " if not d else "DIFF ") + k + ("" if not d else f"  ({len(d)}+)"))
        for x in d[:4]: print("      ", x)
        bad += bool(d)
    m = {k: (D["meta"][k], seed["meta"][k]) for k in ["weeks", "weeklab", "d0", "d1", "ndays", "ytd1", "week_no", "curm", "months", "quarters"] if D["meta"][k] != seed["meta"][k]}
    print("meta khác:", m or "không")
    print("TỔNG:", "TẤT CẢ KHỚP" if not bad and not m else f"{bad} khối lệch")


if __name__ == "__main__":
    main(sys.argv[1])
