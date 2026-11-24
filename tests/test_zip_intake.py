"""Test nhận zip: python3 -I tests/test_zip_intake.py "<thư mục Data_W39>" """
import sys, zipfile, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import zipintake
root = Path(sys.argv[1]); buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
    for f in root.rglob("*"):
        if f.is_file():
            z.write(f, f.relative_to(root.parent))
files, notes = zipintake.extract(buf.getvalue())
from slots import all_slots
need = [s["key"] for s in all_slots() if s["required"] and s["key"] != "wf_senno_CR"]
print(sorted(files)); print(*notes, sep="\n")
miss = [k for k in need if k not in files and not k.startswith("wf_senno")]
print("Thiếu ô bắt buộc:", miss)
assert files["amazon_ads"][0].endswith("Copy.csv"), files["amazon_ads"][0]
assert files["fba_CAN"][0].startswith("DHI Amazon") and files["fba_US"][0].startswith("353391")
assert not miss
print("OK")
