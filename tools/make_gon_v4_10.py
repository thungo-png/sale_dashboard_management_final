"""Gọn v4 – lần 10: thay thẻ "Top nhóm sản phẩm" (trùng với vòng tròn doanh thu theo nhóm) bằng thẻ "Chất lượng sản phẩm".
   Nguồn: D.pl5 (rows/total/prev_total) – chỉ báo gián tiếp qua phí Return/Refund; chưa có dữ liệu đánh giá/lý do trả hàng.
   Dùng: python3 make_gon_v4_10.py vào.html ra.html (đã áp make_gon_v4_9). Không đụng const D, không xoá id."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
i=s.index('    // top nhóm\n'); j=s.index('    // quảng cáo\n',i)
new='''    // chất lượng sản phẩm (chỉ báo gián tiếp: phí hoàn trả PL5, theo tuần báo cáo)
    {const T=D.pl5&&D.pl5.available?D.pl5.total:null, T0=D.pl5&&D.pl5.prev_total;
     if(!T||!(T.r>0)) h+='<div class="dc"><h3>Chất lượng sản phẩm</h3><div class="note">Chưa có dữ liệu PL5 cho kỳ này.</div></div>';
     else{
      const rt=T.return_fee/T.r*100, rt0=T0&&T0.r>0?T0.return_fee/T0.r*100:null, dd=rt0==null?null:rt-rt0;
      const G={}; (D.pl5.rows||[]).forEach(x=>{const o=G[x.grp]||(G[x.grp]={r:0,f:0,q:0});o.r+=x.r;o.f+=x.return_fee||0;o.q+=x.q||0;});
      const gl=Object.keys(G).map(k=>({grp:k,r:G[k].r,f:G[k].f,p:G[k].r>0?G[k].f/G[k].r*100:0})).filter(x=>x.r>=500).sort((a,b)=>b.p-a.p).slice(0,5);
      const pm=Math.max(...gl.map(x=>x.p),1);
      const col=p=>p>=rt*1.5?"var(--bad)":p>=rt?"var(--warn)":"var(--accent)";
      const cl=dd==null?"":dd>0.05?"var(--bad-ink)":dd<-0.05?"var(--ok-ink,var(--accent))":"var(--muted)";
      h+=`<div class="dc"><h3>Chất lượng sản phẩm<span class="pk" style="font-weight:400;font-size:11px;color:var(--muted)">${D.meta&&D.meta.week_no?"Tuần "+D.meta.week_no:"tuần báo cáo"}</span></h3>`
        +`<div class="qk"><div><div class="ql">Phí hoàn trả</div><div class="qv">${U(T.return_fee)}</div></div><div><div class="ql">% doanh thu</div><div class="qv">${rt.toFixed(1).replace(".",",")}%</div>${dd==null?"":`<div class="qd" style="color:${cl}">${Math.abs(dd)<0.05?"≈ không đổi so tuần trước":(dd>0?"▲ ":"▼ ")+Math.abs(dd).toFixed(1).replace(".",",")+" đ.% so tuần trước"}</div>`}</div></div>`
        +`<div class="ql" style="margin:8px 0 6px">Nhóm có tỷ lệ hoàn trả cao nhất</div><div class="hb">${gl.map(x=>`<div class="r"><span title="${x.grp}">${short(x.grp)}</span><b>${x.p.toFixed(1).replace(".",",")}% <small style="font-weight:400;color:var(--muted)">· ${U(x.f)}</small></b><div class="tr"><i style="width:${x.p/pm*100}%;background:${col(x.p)}"></i></div></div>`).join("")}</div>`
        +`<div class="note" style="margin-top:8px">Chỉ báo gián tiếp từ phí Return/Refund (PL5, độ phủ ${String(D.pl5.coverage_pct).replace(".",",")}%). Chưa có dữ liệu đánh giá sao hay lý do trả hàng; bổ sung báo cáo đó để đo chất lượng đầy đủ hơn.</div>${more("Xem PL5","pl5")}</div>`;
     }}
'''
s=s[:i]+new+s[j:]
css='''.qk{display:grid;grid-template-columns:1fr 1fr;gap:10px}.ql{font-size:11.5px;color:var(--muted)}.qv{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums}.qd{font-size:11px}
'''
a='.xc{'; k=s.index(a); e=s.index('}\n',k)+2
s=s[:e]+css+s[e:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
