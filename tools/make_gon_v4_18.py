"""Gọn v4 – lần 18: thẻ Sessions & chuyển đổi (tab Listing & Rating) dùng Business Report. Chạy sau v4_17."""
import sys,os
here=os.path.dirname(os.path.abspath(__file__))
s=open(sys.argv[1],encoding="utf-8").read()
js=open(os.path.join(here,"p18","sessions.js"),encoding="utf-8").read()
k=s.rfind("</script>"); assert k>0; s=s[:k]+"\n"+js+"\n"+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
