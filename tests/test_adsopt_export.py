"""Test xuất bulk-edit Wayfair bằng TEMPLATE GIẢ LẬP (dựng theo tên sheet / tên cột trong skill wayfair-bulk-ads-optimization).
Không cần dữ liệu thật. Chạy:  python3 -I tests/test_adsopt_export.py
Kiểm: không đụng dòng INACTIVE, 'REMOVE' đúng literal, bid giảm/tăng đúng tỉ lệ, negative bị chặn khi trùng / xung đột / chạm trần 100,
và không ghi vào cột 'Current …'."""
import io, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import openpyxl
import adsopt

HR = 4


def mk_sheet(wb, title, headers, rows):
    ws = wb.create_sheet(title)
    ws.cell(row=1, column=1).value = "ghi chú Wayfair"
    for i, h in enumerate(headers, 1):
        ws.cell(row=HR, column=i).value = h
    for r, row in enumerate(rows, HR + 1):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c).value = v
    return ws


def build_template(path):
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    mk_sheet(wb, "Edit Sponsored Product Campaign",
             ["Campaign ID", "Current Campaign Name", "Current Campaign Active", "Bidding Strategy", "Current Target ROAS Percentage",
              "New Current Target ROAS Percentage", "New Active Status"],
             [[1, "Thu Ngo A", "ACTIVE", "Manual Bidding", None, None, None],
              [2, "Thu Ngo B troas", "ACTIVE", "AI Bidding - TROAS", 800, None, None],
              [3, "Thu Ngo C pause", "ACTIVE", "Manual Bidding", None, None, None],
              [4, "Thu Ngo D inactive", "INACTIVE", "Manual Bidding", None, None, None]])
    mk_sheet(wb, "Edit Target Keyword Bids",
             ["Campaign ID", "Campaign Name", "Target Keyword", "Current Default Bid (USD)", "New Default Bid", "Remove from Current Campaign", "Campaign Active Status"],
             [[1, "Thu Ngo A", "Queen Bed", 0.50, None, None, "ACTIVE"],        # cut 0.5 -> 0.25
              [1, "Thu Ngo A", "king bed", 0.40, None, None, "ACTIVE"],         # raise ×1.25 -> 0.5
              [1, "Thu Ngo A", "bad term", 0.30, None, None, "ACTIVE"],         # remove
              [4, "Thu Ngo D inactive", "queen bed", 0.50, None, None, "INACTIVE"]])
    mk_sheet(wb, "Edit Listing Bids",
             ["Campaign ID", "Campaign Name", "Listing", "Current Default Bid (USD)", "New Default Bid", "Remove from Current Campaign",
              "Campaign Active Status", "Current Listing Active Status"],
             [[1, "Thu Ngo A", "aaai1", 0.40, None, None, "ACTIVE", "ACTIVE"],
              [1, "Thu Ngo A", "aaai2", 0.40, None, None, "ACTIVE", "INACTIVE"]])
    mk_sheet(wb, "Add Negative Keywords",
             ["Negative Keyword", "Negative Keyword Match Type", "Destination Campaign ID", "Destination Campaign Name"], [])
    mk_sheet(wb, "Edit Negative Keywords", ["Campaign ID", "Campaign Name", "Negative Keyword"],
             [[1, "Thu Ngo A", "already there"]] + [[3, "Thu Ngo C pause", f"neg{i}"] for i in range(100)])
    wb.save(path)


def comp():
    camps = [{"campaign_id": 1, "name": "Thu Ngo A", "action": None, "new_troas": None},
             {"campaign_id": 2, "name": "Thu Ngo B troas", "action": "troas", "new_troas": 1667, "reason": "x"},
             {"campaign_id": 3, "name": "Thu Ngo C pause", "action": "pause", "new_troas": None, "reason": "y"},
             {"campaign_id": 4, "name": "Thu Ngo D inactive", "action": "pause", "new_troas": None, "reason": "z"}]
    kw = [{"campaign_id": 1, "kw": "queen bed", "keyword": "Queen Bed", "kind": "cut", "ratio": 0.5, "why": "cut"},
          {"campaign_id": 1, "kw": "king bed", "keyword": "king bed", "kind": "raise", "ratio": 1.25, "why": "raise"},
          {"campaign_id": 1, "kw": "bad term", "keyword": "bad term", "kind": "remove", "ratio": None, "why": "rm"},
          {"campaign_id": 4, "kw": "queen bed", "keyword": "queen bed", "kind": "cut", "ratio": 0.5, "why": "cut"}]
    lst = [{"campaign_id": 1, "lst": "AAAI1", "listing": "AAAI1", "kind": "cut", "ratio": 0.8, "why": "c"},
           {"campaign_id": 1, "lst": "AAAI2", "listing": "AAAI2", "kind": "cut", "ratio": 0.8, "why": "c"}]
    mk = lambda cid, t, **k: {"campaign_id": cid, "campaign": f"c{cid}", "term": t, "term_lo": t.lower(), "spend": 3, "clicks": 3, "conflict": None, **k}
    neg = [mk(1, "Fresh One"), mk(1, "fresh one"), mk(1, "Already There"), mk(1, "in conflict", conflict="in conflict bed"),
           mk(3, "extra term"), mk(4, "inactive camp")]
    return {"accounts": {"Arozu": {"empty": False, "campaigns": camps, "kw_actions": kw, "lst_actions": lst, "neg": neg}}}


def main():
    tmp = Path(tempfile.mkdtemp())
    adsopt.TPL_DIR = tmp
    build_template(tmp / "arozu.xlsx")
    chk = adsopt.check_template(tmp / "arozu.xlsx")
    assert chk["ok"], chk
    data, rep = adsopt.export_bulk("arozu", comp(), list(adsopt.PARTS))
    wb = openpyxl.load_workbook(io.BytesIO(data))
    g = lambda sh, r, c: wb[sh].cell(row=r, column=c).value
    # campaign
    assert g("Edit Sponsored Product Campaign", 6, 6) == 1667, "TROAS phải được nâng"
    assert g("Edit Sponsored Product Campaign", 7, 7) == "INACTIVE", "campaign cần pause"
    assert g("Edit Sponsored Product Campaign", 8, 7) is None, "campaign INACTIVE không được đụng"
    # keyword
    assert g("Edit Target Keyword Bids", 5, 5) == 0.25, g("Edit Target Keyword Bids", 5, 5)
    assert g("Edit Target Keyword Bids", 6, 5) == 0.5, g("Edit Target Keyword Bids", 6, 5)
    assert g("Edit Target Keyword Bids", 7, 6) == "REMOVE" and g("Edit Target Keyword Bids", 7, 5) is None
    assert g("Edit Target Keyword Bids", 8, 5) is None and g("Edit Target Keyword Bids", 8, 6) is None, "keyword của campaign INACTIVE phải giữ nguyên"
    # listing
    assert g("Edit Listing Bids", 5, 5) == 0.32 and g("Edit Listing Bids", 6, 5) is None
    # negative: 'Fresh One' thêm 1 lần; 'Already There' trùng; 'in conflict' bị chặn; campaign 3 chạm trần; campaign 4 INACTIVE
    ws = wb["Add Negative Keywords"]
    added = [(ws.cell(row=r, column=1).value, ws.cell(row=r, column=2).value, ws.cell(row=r, column=3).value) for r in range(5, 12) if ws.cell(row=r, column=1).value]
    assert added == [("Fresh One", "EXACT", 1)], added
    # không ghi vào cột 'Current …'
    assert g("Edit Target Keyword Bids", 5, 4) == 0.50 and g("Edit Sponsored Product Campaign", 6, 5) == 800
    sk = rep["skipped"]
    assert sk.get("neg_exists") == 1 and sk.get("neg_dup") == 1 and sk.get("neg_conflict") == 1 and sk.get("neg_cap") == 1 and sk.get("neg_inactive") == 1, sk
    assert sk.get("camp_inactive") == 1 and sk.get("kw_inactive") == 1 and sk.get("lst_inactive") == 1, sk
    # template thiếu cột phải bị báo lỗi rõ
    bad = openpyxl.load_workbook(tmp / "arozu.xlsx"); bad["Edit Target Keyword Bids"].cell(row=HR, column=5).value = "Moi"; bad.save(tmp / "bad.xlsx")
    assert not adsopt.check_template(tmp / "bad.xlsx")["ok"]
    print("OK — export bulk đúng:", rep["counts"], sk)


if __name__ == "__main__":
    main()
