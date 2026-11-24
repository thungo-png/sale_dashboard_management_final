"""Gọn v4 – lần 19: rà soát toàn report (nhãn trạng thái dữ liệu, bỏ mục trùng, cập nhật bảng dữ liệu còn thiếu). Chạy sau v4_18."""
import sys,os
here=os.path.dirname(os.path.abspath(__file__))
s=open(sys.argv[1],encoding="utf-8").read()
js=open(os.path.join(here,"p19","audit.js"),encoding="utf-8").read()
k=s.rfind("</script>"); assert k>0; s=s[:k]+"\n"+js+"\n"+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
