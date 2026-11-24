"""Nhận 1 file .zip chứa toàn bộ file của kỳ, tự xếp vào đúng ô upload theo tên file (và nội dung khi cần)."""
import io
import re
import zipfile
from pathlib import PurePosixPath

MAX_FILE = 300 * 1024 * 1024
MAX_TOTAL = 1500 * 1024 * 1024
ACC = {"ARZ": "arozu", "AROZU": "arozu", "MS": "megsu", "MEGSU": "megsu", "DHI": "dhi", "SENNO": "senno"}
CG_KEY = {"ARZ": "cg_ARZ", "AROZU": "cg_ARZ", "MS": "cg_MS", "MEGSU": "cg_MS", "DHI": "cg_DHI"}
REP = {"CR": "CR", "PR": "PR", "KTR": "KTR", "PSR": "PSR", "KOR": "KOR", "ST": "ST", "STRR": "ST"}


def _wf_report(h):
    """Nhận loại báo cáo Wayfair từ dòng tiêu đề (không phụ thuộc tên file). None nếu không phải."""
    first = h.lstrip("\ufeff").split("\n", 1)[0]
    cols = {c.strip().strip('"') for c in first.split(",")}
    if "Incidents Number" in cols and "Wayfair SKU" in cols:
        return "SUM"
    if "Class Rank" in cols:
        return "PSR"
    if "supplier_share_of_search_%" in cols:
        return "ST"
    if "keyword_value" in cols:
        return "KTR" if "listing" in cols else "KOR"
    if "campaign_id" in cols and "product_default_bid" in cols:
        return "PR"
    if "campaign_id" in cols and "targeting_type" in cols:
        return "CR"
    return None


def _wf_account(toks, h):
    a = next((t for t in toks if t in ACC), None)
    if a:
        return ACC[a]
    first = h.lstrip("\ufeff").split("\n", 1)[0]
    return "dhi" if "_CAD" in first else None   # file CAD = DHI; USD có 2 tài khoản nên bắt buộc phải có tên


def _fba_slot(toks, h):
    import csv as _csv
    lines = h.lstrip("\ufeff").splitlines()
    if len(lines) > 1:
        delim = "\t" if lines[0].count("\t") > lines[0].count(",") else ","
        hdr = [c.strip().strip('"') for c in next(_csv.reader([lines[0]], delimiter=delim))]
        if "currency" in hdr:
            cur = {(r + [""] * 99)[hdr.index("currency")] for r in _csv.reader(lines[1:], delimiter=delim) if len(r) > hdr.index("currency")}
            cur.discard("")
            if cur and not (cur <= {"USD", "CAD"}):
                return None   # marketplace khác (vd BRL) — không thuộc FBA US/CAN
    if any(t in ("CAN", "CANADA", "DHI", "CA") for t in toks):
        return "fba_CAN"
    if any(t in ("US", "USA", "MEGSU", "MS", "ARZ", "AROZU") for t in toks):
        return "fba_US"
    if "snapshot-date" in h and "\t" in h.split("\n", 1)[0]:
        return None   # .txt không có tên gợi ý: không đoán, để người dùng chọn tay
    return "fba_CAN" if "CAD" in h[:3000] else "fba_US"


def classify(name, head=b""):
    """Trả về key ô upload hoặc None. name = tên file (không thư mục); head = vài KB đầu file (để dò nội dung)."""
    n = name.strip(); low = n.lower(); ext = low.rsplit(".", 1)[-1] if "." in low else ""
    stem = re.sub(r"\s*\(\d+\)\s*$", "", n.rsplit(".", 1)[0]).strip()
    toks = [t for t in re.split(r"[\s_\-]+", stem.upper()) if t]
    if ext == "json":
        return "data_json"
    if ext in ("csv", "txt"):
        h = head.decode("utf-8", "ignore")
        if "Advertiser account name" in h and "Campaign name" in h:
            return "amazon_ads"
        if "snapshot-date" in h or "inventory age" in low or "inventory-age" in low:
            if "castlegate" in low:
                a = next((t for t in toks if t in CG_KEY), None)
                return CG_KEY.get(a)
            return _fba_slot(toks, h)
        if "castlegate" in low:
            a = next((t for t in toks if t in CG_KEY), None)
            return CG_KEY.get(a)
        if h.lstrip("\ufeff").startswith("Brand=[") and "Select week" in h.split("\n", 1)[0]:
            cc = "CA" if any(t in ("CA", "CAN", "CANADA") for t in toks) else "US" if any(t in ("US", "USA") for t in toks) else \
                 ("CA" if "Search query score" in h else "US")
            return f"sqp_{cc}"
        if "(Parent) ASIN" in h and "Featured Offer (Buy Box)" in h:
            return "amazon_br_CAN" if any(t in ("CA", "CAN", "CANADA", "DHI") for t in toks) else "amazon_br_US" if any(t in ("US", "USA") for t in toks) else "amazon_br_?"
        rep = _wf_report(h)
        if rep:
            acc = _wf_account(toks, h)
            return f"wf_{acc}_{rep}" if acc else None
        return None
    if ext in ("xlsx", "xlsm"):
        if low.startswith("data inv") or "inventory unpivot" in low:
            return "master"
        if re.match(r"^p\s*&\s*l", low) or "p&l" in low:
            return "pl5"
        if low.startswith("report_sale_year_to_date") or "year_to_date" in low:
            return "data_ytd"
        if toks and toks[0] in ACC and len(toks) >= 2 and toks[1] in REP:
            return f"wf_{ACC[toks[0]]}_{REP[toks[1]]}"
        if re.match(r"^data\b", low):
            return "data_current"
    return None


def _why(name, head):
    low = name.lower(); h = head.decode("utf-8", "ignore")
    if "Incidents Number" in h.split("\n", 1)[0]:
        return " [Summary-data nhưng không xác định được tài khoản — thêm ARZ/MS/DHI vào tên file]"
    if low.endswith(".txt") and "snapshot-date" in h:
        return " [FBA Inventory Age dạng .txt — cần chọn tay ô FBA US/CAN, không đoán được từ tên]"
    return ""


def extract(blob, log=print):
    """Trả (files {slot: (tên, bytes)}, ghi chú [str]). Không tin đường dẫn trong zip: chỉ dùng tên file."""
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile:
        raise ValueError("File không phải .zip hợp lệ")
    infos = [i for i in z.infolist() if not i.is_dir()]
    if sum(i.file_size for i in infos) > MAX_TOTAL:
        raise ValueError("Zip giải nén quá lớn (> 1,5 GB)")
    found, notes, ignored = {}, [], []
    for i in infos:
        p = PurePosixPath(i.filename.replace("\\", "/"))
        base = p.name
        if "__MACOSX" in p.parts or base.startswith(".") or base.startswith("~$") or i.file_size > MAX_FILE:
            if i.file_size > MAX_FILE:
                ignored.append(f"{base} (quá lớn)")
            continue
        with z.open(i) as f:
            head = f.read(16384)
        slot = classify(base, head)
        if slot is None:
            ignored.append(base + _why(base, head)); continue
        found.setdefault(slot, []).append((base, i))
    out = {}
    # Business Report không ghi rõ thị trường: mặc định US (chưa có CAN). Nếu có nhiều file -> lấy file nhiều phiên truy cập nhất, báo rõ
    if "amazon_br_?" in found:
        lst = found.pop("amazon_br_?")
        def _sess(i):
            import csv as _c
            r = list(_c.DictReader(io.StringIO(z.read(i).decode("utf-8-sig", "ignore"))))
            return sum(int(str(x.get("Sessions - Total", "0")).replace(",", "") or 0) for x in r)
        lst.sort(key=lambda t: -_sess(t[1]))
        found.setdefault("amazon_br_US", []).extend(lst[:1])
        notes.append("Business Report: " + lst[0][0] + " → US (mặc định US; dùng file nhiều phiên truy cập nhất)"
                     + ("; bỏ qua " + ", ".join(b for b, _ in lst[1:]) + " (khoảng thời gian khác — muốn dùng thì đặt tên chứa US/CA)" if len(lst) > 1 else ""))
    for slot, lst in found.items():
        if slot.startswith("sqp_") and len(lst) > 1:   # nhiều tuần Brand Analytics -> gói thành 1 zip cho ô đó
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zo:
                for b, i in lst:
                    zo.writestr(b, z.read(i))
            out[slot] = (f"{slot}.zip", buf.getvalue()); notes.append(f"Ô {slot}: gói {len(lst)} tuần Brand Analytics")
            continue
        if len(lst) > 1:       # nhiều file cùng ô -> lấy file lớn nhất (vd báo cáo đầy đủ hơn), báo rõ cho người dùng
            lst.sort(key=lambda t: -t[1].file_size)
            notes.append(f"Ô {slot} có {len(lst)} file ({', '.join(b for b, _ in lst)}) — dùng file lớn nhất: {lst[0][0]}")
        base, info = lst[0]
        out[slot] = (base, z.read(info))
    if ignored:
        notes.append("Bỏ qua (không nhận ra): " + ", ".join(ignored))
    return out, notes
