"""Gọn v4 – chỉnh nhỏ (lần 8): khi đang xem khoảng ngày khác kỳ báo cáo mà số liệu không có theo ngày thì GHI RÕ ngay trên thẻ,
   thay vì lặng lẽ giữ số tuần: PL5 ("không có số theo ngày — giữ theo kỳ báo cáo"); chi phí quảng cáo + bảng kênh khi kỳ chưa có D.ads_daily
   ("kỳ này chưa có chi phí QC theo ngày — build lại kỳ cùng file quảng cáo để có").
   Dùng: python3 make_gon_v4_8.py vào.html ra.html (đã áp make_gon_v4_7)."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
dl_=[l for l in s.split("\n") if l.startswith("const D = ")]
a='    host.innerHTML=h;\n'
i=s.index('  function build(force){'); j=s.index(a,i)
assert s.count(a,i,i+60000)>=1
add=a+'''    if(RG){
      host.querySelectorAll(".kd").forEach(k=>{const l=k.querySelector(".kl").textContent,ks=k.querySelector(".ks");
        if(/^Profit PL5/.test(l))ks.insertAdjacentHTML("beforeend","<br><small>không có số theo ngày — giữ theo kỳ báo cáo</small>");
        if(!adR&&/^Chi phí quảng cáo ·/.test(l))ks.insertAdjacentHTML("beforeend","<br><small>kỳ này chưa có chi phí QC theo ngày — build lại kỳ cùng file quảng cáo để có</small>")});
      if(!adR){const t=host.querySelector(".dt2");if(t)t.parentElement.insertAdjacentHTML("beforeend",'<div class="note">Bảng đang là số tuần báo cáo (kỳ này chưa có chi phí QC theo ngày).</div>')}
    }
'''
s=s[:j]+add+s[j+len(a):]
assert [l for l in s.split("\n") if l.startswith("const D = ")]==dl_
open(sys.argv[2],"w",encoding="utf-8").write(s)
