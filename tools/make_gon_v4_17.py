"""Gọn v4 – lần 17: thêm menu "Thị trường & Đối thủ" (p17/market.js). Chạy sau make_gon_v4_16:
   python3 make_gon_v4_17.py vào.html ra.html   (D.market do etl/market.py tạo; thiếu thì tab tự dựng từ D.ads)"""
import sys,os
here=os.path.dirname(os.path.abspath(__file__))
s=open(sys.argv[1],encoding="utf-8").read()
svg="%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 17l5-5 4 4 8-9'/%3E%3Cpath d='M15 7h5v5'/%3E%3C/svg%3E"
css=('.tab[data-p="mk"]::before{-webkit-mask-image:url("data:image/svg+xml;utf8,'+svg+'");mask-image:url("data:image/svg+xml;utf8,'+svg+'")}\n'
     '.mk-al th,.mk-al td{text-align:left!important;white-space:normal!important;vertical-align:top;line-height:1.5}.mk-al td:nth-child(1){white-space:nowrap!important}.mk-al td:nth-child(2){min-width:120px}\n'
     '.mk-sec{margin-bottom:26px}.mk-sec .cap{font-size:12.5px;color:var(--muted)}\n')
k=s.rfind("</style>"); assert k>0; s=s[:k]+css+s[k:]
js=open(os.path.join(here,"p17","market.js"),encoding="utf-8").read()
k=s.rfind("</script>"); assert k>0; s=s[:k]+"\n"+js+"\n"+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
