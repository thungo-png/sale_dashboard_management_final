"""Gọn v4 – chỉnh nhỏ (lần 6): ô chọn khoảng ngày giờ đổi cả Bảng điều khiển Tổng quan (thẻ Doanh thu / Số lượng / Đạt FC,
   doanh thu theo sàn, xu hướng, top nhóm) và biểu đồ "Diễn biến theo thời gian". PL5, quảng cáo, tồn kho, cảnh báo giữ theo kỳ báo cáo
   (ghi rõ "tuần Wxx" trên thẻ khi đang xem khoảng khác). Dữ liệu ngày có 84 ngày gần nhất.
   Dùng: python3 make_gon_v4_6.py vào.html ra.html (đã áp make_gon_v4_5). Không đụng dòng const D, không xoá id."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
dl_=[l for l in s.split("\n") if l.startswith("const D = ")]
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]); s=s.replace(a,b)
# --- 1) ô chọn ngày: lưu khoảng đang chọn + dựng lại dashboard
rep1('    if(first)return;\n','    if(first)return;\n    window.__FULLD=FULLD;window.__RNG=def?null:{a:a,b:b};\n')
rep1('    ovTrend();\n  }\n  const sel=','    ovTrend();if(window.__dashRebuild)window.__dashRebuild();\n  }\n  const sel=')
# nhãn trục X thưa bớt khi có nhiều ngày
rep1('const xl=labels.map((x,i)=>`<text x="${X(i)}" y="${H-8}" text-anchor="middle">${x}</text>`).join("");',
     'const stp=Math.ceil(n/10),xl=labels.map((x,i)=>(i%stp===0||i===n-1)&&(n-1-i>=stp||i===n-1)?`<text x="${X(i)}" y="${H-8}" text-anchor="middle">${x}</text>`:"").join("");')
# --- 2) dashboard
i=s.index('  function build(){\n    const host=$$("#dash");'); j=s.index('    host.innerHTML=h;',i)
seg=s[i:j]
def r(a,b,cnt=1):
    global seg
    assert seg.count(a)==cnt,(seg.count(a),a[:80]); seg=seg.replace(a,b)
r('function build(){\n    const host=$$("#dash"); if(!host||host.dataset.built)return;','function build(force){\n    const host=$$("#dash"); if(!host||(host.dataset.built&&!force))return;')
r('const wr=wsum("r"),wq=wsum("q"),wl=wk.map(w=>"W"+w);','let wr=wsum("r"),wq=wsum("q"),wl=wk.map(w=>"W"+w);')
r('const ach=wk.map(','let ach=wk.map(')
r('const cur={r:sum(D.cell,c=>c.r),q:sum(D.cell,c=>c.q),rfc:sum(D.cell,c=>c.rfc)}, prev=','let cur={r:sum(D.cell,c=>c.r),q:sum(D.cell,c=>c.q),rfc:sum(D.cell,c=>c.rfc)}, prev=')
r('const dl=(a,b)=>',
'''const RG=window.__RNG||null; let fcR=null,L=null,rngLab="";
    if(RG&&window.__FULLD){
      const FD=window.__FULLD,dm=D.ts_ov.D.mp,dmk=Object.keys(dm),dsum=(labs,k)=>sum(labs,d=>sum(dmk,m=>((dm[m]||{})[d]||{})[k]));
      L=FD.slice(RG.a,RG.b+1); const n=L.length; rngLab=n+" ngày";
      wl=L.map(d=>d.slice(8)+"/"+d.slice(5,7)); wr=L.map(d=>dsum([d],"r")); wq=L.map(d=>dsum([d],"q")); fcR=L.map(d=>dsum([d],"rfc"));
      ach=L.map((d,i)=>fcR[i]?wr[i]/fcR[i]*100:0);
      cur={r:sum(wr,x=>x),q:sum(wq,x=>x),rfc:sum(fcR,x=>x)};
      const pL=RG.a-n>=0?FD.slice(RG.a-n,RG.a):null; prev=pL?{r:dsum(pL,"r"),q:dsum(pL,"q"),rfc:dsum(pL,"rfc")}:{r:0,q:0,rfc:0};
    }
    const TT=RG?rngLab+" trước":"tuần trước", WT=RG?rngLab:"tuần", PW=RG?" · W"+D.meta.week_no:"";
    const dl=(a,b)=>''')
r('"Doanh thu tuần"','"Doanh thu "+WT')
r('so với tuần trước','so với ${TT}',3)
r('"Profit PL5",U(pl.profit)','"Profit PL5"+PW,U(pl.profit)')
r('"Chi phí quảng cáo",U(spend)','"Chi phí quảng cáo"+PW,U(spend)')
r('const byMp={}; D.cell.forEach(c=>{byMp[c.mp]=(byMp[c.mp]||0)+c.r});',
  'const byMp={}; if(L){Object.keys(D.ts_ov.D.mp).forEach(m=>{byMp[m]=sum(L,d=>((D.ts_ov.D.mp[m]||{})[d]||{}).r)})}else D.cell.forEach(c=>{byMp[c.mp]=(byMp[c.mp]||0)+c.r});')
r('"doanh thu tuần"','(RG?rngLab:"doanh thu tuần")')
r('Xu hướng ${wk.length} tuần<span','Xu hướng ${RG?rngLab:wk.length+" tuần"}<span')
r('const g=[...D.bygrp].sort(','const g=(L?Object.keys(D.ts_grp.D).map(k=>({grp:k,r:sum(L,d=>((D.ts_grp.D[k]||{})[d]||{}).r)})):[...D.bygrp]).sort(')
s=s[:i]+seg+s[j:]
rep1('    const fcw=wk.map(w=>','    const fcw=RG&&fcR?fcR:wk.map(w=>')
rep1('  const _ov=builders.ov;','  window.__dashRebuild=()=>{try{build(true)}catch(e){console.warn("dash",e)}};\n  const _ov=builders.ov;')
s=s.replace('của từng tuần.','của từng ${RG?"ngày":"tuần"}.') if False else s
assert [l for l in s.split("\n") if l.startswith("const D = ")]==dl_
open(sys.argv[2],"w",encoding="utf-8").write(s)
