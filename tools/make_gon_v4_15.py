"""Gọn v4 – lần 15: tái cấu trúc menu thành 9 mục (Điều hành: Tổng quan · Doanh thu & Kế hoạch · Lợi nhuận | Vận hành: Sản phẩm · Quảng cáo · Tồn kho & Cung ứng · Listing & Giá | Quản trị: Việc cần làm · Dữ liệu & Giả định).
   - Lợi nhuận = A (cầu lợi nhuận, phân loại SKU, dư địa QC, PL5, mô phỏng) + B (Dòng tiền & vốn lưu động: giá trị tồn kho theo giá vốn, vốn tồn chậm/≥271 ngày, chi phí giữ hàng).
   - Việc cần làm: bảng từ P.issues (+ P.tasks nếu server cung cấp), Dữ liệu & Giả định: nguồn, phương pháp, dữ liệu còn thiếu, chú thích gom về một chỗ.
   Dùng: python3 make_gon_v4_15.py vào.html ra.html (đã áp make_gon_v4_14). Mã JS ở p15/reorg.js (nạp cùng thư mục)."""
import sys,os
here=os.path.dirname(os.path.abspath(__file__))
s=open(sys.argv[1],encoding="utf-8").read()
js=open(os.path.join(here,"p15","reorg.js"),encoding="utf-8").read()
css='''.sub-grp{margin:34px 0 0;font:600 11px/1 "IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding-left:2px}
.panel>.sub-grp:first-child,.pf-nav+.sub-grp{margin-top:14px}
.pf-nav{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 6px}
.pf-nav button{font:600 12px "Public Sans",system-ui,sans-serif;padding:6px 13px;border-radius:99px;border:1px solid var(--line);background:var(--card);color:var(--ink-2);cursor:pointer}
.pf-nav button:hover{border-color:var(--accent);color:var(--accent)}
.nt-item{margin:0 0 10px;padding:9px 14px;border:1px solid var(--line);border-radius:12px;background:var(--card)}
.nt-h{font:600 11.5px "Public Sans",system-ui,sans-serif;color:var(--muted);margin-bottom:2px}
#p-dd details.capfold,#pro-ins details.capfold{display:block!important}
.muted{color:var(--muted)}
table.tl th,table.tl td{text-align:left!important;white-space:normal;vertical-align:top}
table.tl td .sev{white-space:nowrap}
.tabbar .tab[data-p="mg"]::before{-webkit-mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 3v18'/%3E%3Cpath d='M17 7H9.5a2.5 2.5 0 0 0 0 5h5a2.5 2.5 0 0 1 0 5H6'/%3E%3C/svg%3E")!important;mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 3v18'/%3E%3Cpath d='M17 7H9.5a2.5 2.5 0 0 0 0 5h5a2.5 2.5 0 0 1 0 5H6'/%3E%3C/svg%3E")!important}
.tab[data-p="fc"]::before{-webkit-mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 3v18h18'/%3E%3Cpath d='M7 15l4-5 3 3 5-7'/%3E%3C/svg%3E");mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 3v18h18'/%3E%3Cpath d='M7 15l4-5 3 3 5-7'/%3E%3C/svg%3E")}
.tab[data-p="td"]::before{-webkit-mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 6l2 2 3-3'/%3E%3Cpath d='M4 13l2 2 3-3'/%3E%3Cpath d='M12 7h8M12 14h8M4 20h16'/%3E%3C/svg%3E");mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 6l2 2 3-3'/%3E%3Cpath d='M4 13l2 2 3-3'/%3E%3Cpath d='M12 7h8M12 14h8M4 20h16'/%3E%3C/svg%3E")}
.tab[data-p="dd"]::before{-webkit-mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cellipse cx='12' cy='5' rx='8' ry='3'/%3E%3Cpath d='M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5'/%3E%3Cpath d='M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3'/%3E%3C/svg%3E");mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cellipse cx='12' cy='5' rx='8' ry='3'/%3E%3Cpath d='M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5'/%3E%3Cpath d='M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3'/%3E%3C/svg%3E")}
'''
# huy hiệu trạng thái (v4_14): theo vị trí mới của mục
assert s.count('"#p-dt section"')==2
s=s.replace('"#p-dt section"','"section"').replace('["#p-mg section",/^Mô phỏng giá & quảng cáo/,"test"],','["section",/^Mô phỏng giá & quảng cáo/,"test"],["section",/^Dòng tiền/,"dev"],["#p-mg .card",/^Tiền sắp ra/,"nw"],')
k=s.index('.xc{'); e=s.index('}\n',k)+2; s=s[:e]+css+s[e:]
k=s.rfind("</script>"); assert k>0; s=s[:k]+"\n"+js+"\n"+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
