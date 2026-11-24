"""Khai báo các "ô file" (slot) cần upload cho mỗi kỳ báo cáo — theo SKILL.md Bước 1."""

WF_ACCOUNTS = {"arozu": "Arozu (US/USD)", "megsu": "Megsu (US/USD)", "dhi": "DHI (CAN/CAD)", "senno": "Senno (AUS) – nếu có"}
WF_REPORTS = ["CR", "PR", "KTR", "PSR", "ST", "KOR"]


def all_slots():
    s = [
        {"key": "data_current", "group": "A. Bán hàng & tồn kho", "label": "data W39.xlsx — bán hàng daily (phủ ít nhất tuần báo cáo; kiểm Date.min/max trước khi dùng)", "required": True, "accept": ".xlsx"},
        {"key": "data_ytd", "group": "A. Bán hàng & tồn kho", "label": "report_sale_year_to_date.xlsx — chỉ cần khi file bán hàng không phủ lịch sử (hiện chưa dùng)", "required": False, "accept": ".xlsx"},
        {"key": "master", "group": "A. Bán hàng & tồn kho", "label": "Data Inv & Report Sales - Thư Ngô.xlsx — sheet Inventory Unpivot / Listing", "required": True, "accept": ".xlsx"},
        {"key": "amazon_ads", "group": "A. Bán hàng & tồn kho", "label": "Monthly_Report_…_Amazon.csv — Amazon Advertising Report", "required": True, "accept": ".csv"},
        {"key": "pl5", "group": "A. Bán hàng & tồn kho", "label": "P&L Thư Ngô.xlsx — rate card / COGS (tuỳ chọn, cho Profit PL5)", "required": False, "accept": ".xlsx"},
    ]
    for k, lab in [("cg_ARZ", "CastleGate Inventory Age — ARZ (Arozu)"), ("cg_MS", "CastleGate Inventory Age — MS (Megsu)"),
                   ("cg_DHI", "CastleGate Inventory Age — DHI"), ("fba_US", "FBA US Inventory Age (csv)"), ("fba_CAN", "FBA CAN Inventory Age — DHI (csv)")]:
        s.append({"key": k, "group": "A2. Tuổi tồn kho (Long-term Storage)", "label": lab, "required": False, "accept": ".csv"})
    for acc, accname in WF_ACCOUNTS.items():
        for rep in WF_REPORTS:
            s.append({"key": f"wf_{acc}_{rep}", "group": f"B. Wayfair — {accname}", "label": rep,
                      "required": acc != "senno", "accept": ".csv,.xlsx"})
    for acc, accname in WF_ACCOUNTS.items():
        if acc != "senno":
            s.append({"key": f"wf_{acc}_SUM", "group": "B2. Wayfair — Chất lượng sản phẩm (Summary-data)", "label": f"Summary-data (Incidents/Returns) — {accname}",
                      "required": False, "accept": ".csv,.xlsx"})
    for k, lab in [("sqp_US", "Brand Analytics — Search Query Performance (Brand View) US, nhiều tuần (.csv hoặc .zip)"),
                   ("sqp_CA", "Brand Analytics — Search Query Performance (Brand View) CAN, nhiều tuần (.csv hoặc .zip)"),
                   ("amazon_br_US", "Business Report US — Detail Page Sales and Traffic By Child Item (.csv)"),
                   ("amazon_br_CAN", "Business Report CAN — Detail Page Sales and Traffic By Child Item (.csv)")]:
        s.append({"key": k, "group": "B3. Amazon — Thị trường & Đối thủ", "label": lab, "required": False, "accept": ".csv,.zip"})
    s.append({"key": "data_json", "group": "C. Bỏ qua ETL (nâng cao)", "label": "data.json dựng sẵn (đúng schema const D) — nếu có file này sẽ bỏ qua ETL", "required": False, "accept": ".json"})
    return s


SLOT_KEYS = {s["key"] for s in all_slots()}
