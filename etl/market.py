"""Thị trường & Đối thủ — so sánh tuần này với tuần trước từ báo cáo PSR (thứ hạng ngành hàng) và ST (thị phần tìm kiếm) của Wayfair.
Kết quả -> D["market"]. Chỉ là phép so sánh với kỳ trước đã build, không thêm nguồn dữ liệu mới."""


def _idx(rows, key):
    return {key(r): r for r in rows or []}


def build_market(ads, prev, log=print):
    if not ads:
        return None
    pads = (prev or {}).get("ads") or {}
    prk, pst = pads.get("rank") or {}, pads.get("st") or {}
    rank, st = [], []
    for acc, rows in (ads.get("rank") or {}).items():
        pi = _idx(prk.get(acc), lambda r: r.get("Listing"))
        for r in rows:
            p = pi.get(r.get("Listing"))
            rank.append({"acct": acc, "listing": r.get("Listing"), "grp": r.get("grp"), "cls": r.get("Class Name"), "status": r.get("status"),
                         "first": r.get("first"), "last": r.get("last"), "best": r.get("best"),
                         "prev_last": p.get("last") if p else None})
    for acc, rows in (ads.get("st") or {}).items():
        pi = _idx(pst.get(acc), lambda r: r.get("term"))
        for r in rows:
            p = pi.get(r.get("term"))
            st.append({"acct": acc, "term": r.get("term"), "cls": r.get("cls"), "impr": r.get("impr"), "sh": r.get("sh_search"),
                       "p1": r.get("sh_p1"), "top8": r.get("sh_top8"),
                       "prev_sh": p.get("sh_search") if p else None, "prev_impr": p.get("impr") if p else None})
    has_prev = bool(prk or pst)
    log(f"[market] {len(rank)} listing có hạng, {len(st)} cụm từ; so với kỳ trước: {'có' if has_prev else 'không có dữ liệu kỳ trước'}")
    return {"has_prev": has_prev, "rank": rank, "st": st}
