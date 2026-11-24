"""
ETL của Sale Report Manager (cập nhật tăng dần từ D của kỳ trước).

Đã làm, đối chiếu 100% với D của W39:
  [x] Đợt 1 — bán hàng + chuỗi thời gian (etl/sales.py)
  [x] Đợt 2 — tồn kho: invdet, invacct (etl/inventory.py); Long-term Storage: lt (etl/longterm.py)
Chưa làm (GIỮ NGUYÊN từ kỳ trước, báo rõ trong log):
  [x] Đợt 3 — quảng cáo: adsum, campthu, scope, tacos, dgmk_room, adlist_cover, ads (etl/ads.py)
  [x] Đợt 4 — sku_meta, top_sku2, grpcmp, askuw_mp, sizecolor (etl/extra.py); pl5 (etl/pl5.py)
"""
from etl.sales import build_sales
from etl import inventory as inv
from etl import longterm as ltm
from etl import ads as adsm
from etl import extra as ex
from etl import pl5 as plm
from etl import ratecard_store as rcs

PENDING = []


ADS_BLOCKS = ["adsum", "campthu", "scope", "tacos", "dgmk_room", "adlist_cover", "ads"]


def build(ctx):
    cfg, inp, log = ctx["cfg"], ctx["inputs"], ctx["log"]
    prev = ctx["prev"]
    if prev is None:
        raise ValueError("Chưa có kỳ nền. Hãy dùng kỳ 'Mẫu' (lấy từ template) hoặc upload data.json của kỳ trước.")
    if "data_current" not in inp:
        raise ValueError("Thiếu file bán hàng (ô data_current).")

    fx = cfg.get("fx_to_usd") or {}
    rates = {"CAD": fx["CAD"], "AUD": fx["AUD"]} if fx.get("CAD") and fx.get("AUD") else None
    log(f"[fx] dùng tỷ giá trong Cấu hình: {rates}" if rates else "[fx] dùng tỷ giá constant-currency của kỳ trước (D.fx.rates)")

    # Đợt 1 — bán hàng
    D, S, (d0, d1, wk) = build_sales(prev, inp["data_current"], rates=rates, group_norm=cfg.get("group_norm"), log=log)
    done = ["bán hàng + chuỗi thời gian"]

    # Đợt 2a — tồn kho
    groups = D["meta"]["groups"]
    if "master" in inp:
        mine = inv.load_scope(inp["master"], groups, cfg["pic"], log=log)
        sold = {}
        for r in D["sku"]:
            sold[r["sku"]] = sold.get(r["sku"], 0) + r["q"]
        D["invdet"] = inv.build_invdet(mine, groups, sold, log=log)
        D["invacct"] = inv.build_invacct(mine, len(D["invdet"]["sku_tot"]), prev["invacct"].get("note_longterm", ""), log=log)
        done.append("tồn kho (invdet, invacct)")
        # Đợt 2b — Long-term Storage (cần thêm file tuổi tồn kho)
        cg = {a: inp[f"cg_{a}"] for a in ("ARZ", "DHI", "MS") if f"cg_{a}" in inp}
        fba = {c: inp[f"fba_{c}"] for c in ("US", "CAN") if f"fba_{c}" in inp}
        if len(cg) == 3 and len(fba) == 2:
            D["lt"] = ltm.build_lt(inp["master"], groups, cg, fba, prev.get("lt"), log=log)
            done.append("Long-term Storage (lt)")
        else:
            log(f"[lt] Thiếu file tuổi tồn kho (có CastleGate {sorted(cg)}, FBA {sorted(fba)}) — GIỮ NGUYÊN lt của kỳ trước.")
    else:
        log("[inv] Thiếu file tồn kho (ô master) — GIỮ NGUYÊN invdet, invacct, lt của kỳ trước.")

    # Đợt 3 — quảng cáo (cần CR, PR, PSR, ST của 3 tài khoản Wayfair + Amazon Ads)
    ads_keys = ADS_BLOCKS
    wfmap = {"arozu": "ARZ", "megsu": "MS", "dhi": "DHI"}
    files = {"amazon": inp.get("amazon_ads")}
    for rep, k in [("CR", "wf_CR"), ("PR", "wf_PR"), ("PSR", "wf_PSR"), ("ST", "wf_ST")]:
        files[k] = {a: inp[f"wf_{n}_{rep}"] for n, a in wfmap.items() if f"wf_{n}_{rep}" in inp}
    miss = [k for k in ("wf_CR", "wf_PR", "wf_PSR", "wf_ST") if len(files[k]) < 3] + (["amazon_ads"] if not files["amazon"] else [])
    if miss:
        log(f"[ads] Thiếu file quảng cáo ({', '.join(miss)}) — GIỮ NGUYÊN {', '.join(ads_keys)} của kỳ trước.")
        PEND = PENDING + ads_keys
    else:
        rt = D["fx"]["rates"]
        A = adsm.build_ads(files, S, D, rt, d0, d1, log=log)
        for k in ads_keys:
            D[k] = A[k]
        done.append("quảng cáo (campthu, scope, adsum, tacos, dgmk_room, adlist_cover, ads)")
        try:   # chi phí/doanh thu QC theo ngày — cho ô chọn khoảng ngày (7-14-30 ngày) của mẫu Gọn v4
            from etl.ads_daily import build_ads_daily
            D["ads_daily"] = build_ads_daily(files, rt, log=log); done.append("quảng cáo theo ngày (ads_daily)")
        except Exception as e:
            log(f"[ads_daily] bỏ qua: {type(e).__name__}: {e}")
        PEND = PENDING

    # Đợt 3d — Thị trường Amazon (Brand Analytics + Business Report; tuỳ chọn)
    if any(x in inp for x in ("sqp_US", "sqp_CA", "amazon_br_US", "amazon_br_CAN")):
        from etl import amzmarket as _am
        AM = _am.build(inp, inp.get("master"), D.get("sku_meta"), log=log)
        if AM:
            D["amzmkt"] = AM; done.append("thị trường Amazon (amzmkt)")
    else:
        D.pop("amzmkt", None)

    # Đợt 3c — Thị trường & Đối thủ (so với kỳ trước; chỉ khi có dữ liệu quảng cáo của kỳ này)
    if not miss:
        from etl import market as _m
        M = _m.build_market(D.get("ads"), prev, log=log)
        if M:
            D["market"] = M; done.append("thị trường (market)")
    else:
        D.pop("market", None)

    # Đợt 4a — khối bổ trợ tính từ số bán hàng (+ tên SKU từ sheet Listing nếu có file master)
    D["sku_meta"] = ex.build_sku_meta(prev["sku_meta"], D, inp.get("master"), log=log)
    names = {r["sku"]: r["name"] for r in D["sku_meta"]}

    # Đợt 3b — Chất lượng sản phẩm thật (Summary-data của từng tài khoản; tuỳ chọn)
    qsum = {a: inp[f"wf_{n}_SUM"] for n, a in wfmap.items() if f"wf_{n}_SUM" in inp}
    if qsum:
        from etl import quality as _q
        Q = _q.build_quality(qsum, inp.get("master"), D.get("sku_meta"), D["meta"]["groups"], D["fx"]["rates"], log=log)
        if Q:
            D["quality"] = Q; done.append("chất lượng sản phẩm (quality)")
    else:
        D.pop("quality", None)
    D["top_sku2"] = ex.build_top_sku2(D, names, log=log); D["top_sku2"]["note"] = prev["top_sku2"]["note"]
    D["grpcmp"] = ex.build_grpcmp(D, prev["grpcmp"], log=log)
    D["askuw_mp"] = ex.build_askuw_mp(D, names, D["fx"]["rates"], log=log)
    D["sizecolor"] = ex.build_sizecolor(D, prev["sizecolor"], log=log)
    done.append("sku_meta, top_sku2, grpcmp, askuw_mp, sizecolor")

    # Đợt 4b — Profit PL5 (cần file P&L + chi phí quảng cáo thật của đợt 3)
    # File P&L: kỳ nào upload thì được LƯU làm file áp dụng cho các kỳ sau (data/pl_ratecard/current.xlsx); kỳ không upload thì dùng file đã lưu.
    pl_file = rcs.resolve(inp.get("pl5"), log=log, period=(ctx.get("period") or {}).get("id"))
    D.pop("pl5ts", None)                                  # chuỗi PL5 theo thời gian tính lại mỗi kỳ (xem etl/pl5ts.py)
    rc = None
    if pl_file and not miss:
        try:
            rc = plm.load_ratecard(pl_file, log=log)
        except plm.RateCardLayoutError as e:
            rc = None
            PEND = PEND + ["pl5"]
            log(f"[pl5] CẢNH BÁO: {e} — GIỮ NGUYÊN pl5 của kỳ trước (không tính PL5 kỳ này).")
        if rc is not None:
            sem_in = A["_sem"]
            if rc.get("layout") == "v2":    # bố cục P&L 10/2026: SEM = chi phí quảng cáo thật theo báo cáo chiến dịch (campthu), không dùng báo cáo PR theo listing (thấp hơn)
                sem_in = {}
                for _r in D.get("campthu", []):
                    sem_in.setdefault((_r["grp"], _r["mp"], _r["cty"]), []).append(_r["spend"])
            D["pl5"] = plm.build_pl5(D, rc, sem_in, D["fx"]["rates"], prev["pl5"], "", log=log)
            if rc.get("layout") == "v2":
                D["pl5"]["_v2"] = True
            D["pl5"]["why"] = plm.why_text(D["pl5"], wk)
            D["pl5"].pop("_v2", None)
            done.append(f"Profit PL5 (độ phủ {D['pl5']['coverage_pct']}% doanh thu)")
            # Chuỗi PL5 theo ngày/tuần (cho bộ lọc thời gian): cần chi phí QC thật từng tuần, lưu ở data/pl_sem_history.json
            if rc.get("layout") == "v2":
                try:
                    from etl import pl5ts as _pts
                    hist = _pts.load_hist()
                    cells, full, notes = _pts.sem_from_files(files["wf_CR"], files["amazon"], D["meta"]["groups"], D["fx"]["rates"], log=log)
                    for _n in notes:
                        log(f"[pl5ts] {_n}")
                    _pts.merge_hist(hist, cells, full)
                    cur_cells = {}
                    for _r in D.get("campthu", []):   # tuần báo cáo: đúng số campthu đang dùng cho D.pl5
                        _k = _pts._key(_r["grp"], _r["mp"], _r["cty"]); cur_cells[_k] = round(cur_cells.get(_k, 0.0) + _r["spend"], 2)
                    hist["weeks"][str(wk)] = cur_cells
                    _pts.save_hist(hist)
                    D["pl5ts"] = _pts.build_pl5ts(D, rc, D["fx"]["rates"], None, wk, hist, log=log)
                    if D["pl5ts"]:
                        done.append("Profit PL5 theo thời gian (pl5ts)")
                    else:
                        D.pop("pl5ts", None)
                except Exception as e:
                    D.pop("pl5ts", None)
                    log(f"[pl5ts] bỏ qua: {type(e).__name__}: {e}")
    else:
        PEND = PEND + ["pl5"]
        log("[pl5] Thiếu file P&L (chưa upload và chưa có file lưu) hoặc file quảng cáo — GIỮ NGUYÊN pl5 của kỳ trước.")

    log("[etl] ĐÃ CẬP NHẬT: " + "; ".join(done))
    log("[etl] GIỮ NGUYÊN số của kỳ trước (chưa có ETL): " + ", ".join(PEND))
    return D
