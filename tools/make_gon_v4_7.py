"""Gọn v4 – chỉnh nhỏ (lần 7):
   (1) thêm 2 thẻ vòng tròn "Doanh thu theo thị trường" và "Doanh thu theo nhóm sản phẩm" cạnh "Doanh thu theo sàn" (đều đổi theo ô chọn khoảng ngày);
   (2) thẻ "Chi phí quảng cáo" + bảng "Hiệu quả quảng cáo theo kênh" đổi theo khoảng ngày khi report có D.ads_daily (ETL etl/ads_daily.py);
       kênh nào file quảng cáo phủ < 90% khoảng ngày thì hiện "—" và ghi rõ chưa đủ dữ liệu; phủ 90-99% thì dùng phần có và ghi "thiếu ngày".
   Dùng: python3 make_gon_v4_7.py vào.html ra.html (đã áp make_gon_v4_6). Không đụng dòng const D, không xoá id."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
dl_=[l for l in s.split("\n") if l.startswith("const D = ")]
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]); s=s.replace(a,b)
i=s.index('  function build(force){\n    const host=$$("#dash");'); j=s.index('    host.innerHTML=h;',i)
seg=s[i:j]
def r(a,b,cnt=1):
    global seg
    assert seg.count(a)==cnt,(seg.count(a),a[:80]); seg=seg.replace(a,b)
# ---- (2) dữ liệu quảng cáo theo khoảng ngày
r('    const TT=RG?rngLab+" trước":"tuần trước"',
'''    let adR=null;
    if(RG&&L&&D.ads_daily&&D.ads_daily.cov){
      const AD=D.ads_daily;adR={rows:[],spend:0,rev:0,miss:[],ok:[],part:[]};
      [["Wayfair","US"],["Wayfair","CAN"],["Amazon","US"],["Amazon","CAN"],["Amazon","AUS"]].forEach(([mp,cty])=>{
        const k=mp+"|"+cty,cv=AD.cov[k],days=cv?L.filter(d=>d>=cv[0]&&d<=cv[1]):[];
        if(!cv||days.length/L.length<0.9){adR.rows.push({mp,cty,na:1,spend:0,tacos:null,roas:null});adR.miss.push(mp+" "+cty);return}
        if(days.length<L.length)adR.part.push(mp+" "+cty+": "+days.length+"/"+L.length+" ngày");
        const dd=AD.d[k]||{};let sp=0,sa=0;days.forEach(d=>{const x=dd[d];if(x){sp+=x[0];sa+=x[1]}});
        const rv=sum(days,d=>((((D.ts_ov.D.mpcty||{})[mp+" · "+cty])||{})[d]||{}).r);
        adR.rows.push({mp,cty,spend:sp,tacos:rv?sp/rv*100:null,roas:sp?sa/sp:0});adR.spend+=sp;adR.rev+=rv;adR.ok.push(mp+" "+cty)});
    }
    const TT=RG?rngLab+" trước":"tuần trước"''')
a=seg.index('    h+=kp(IC.tag,'); b=seg.index("\n    h+='</div><div class=\"row r2\">';")
orig=seg[a:b].strip()
assert orig.startswith('h+=kp(IC.tag,"Chi phí quảng cáo"+PW,U(spend)') and orig.endswith(');'),orig[-80:]
expr=orig[len('h+='):-1]
seg=seg[:a]+'''    const adCard=()=>{
      if(!adR)return '''+expr+''';
      if(!adR.ok.length)return kp(IC.tag,"Chi phí quảng cáo "+WT,"—",0,"chưa đủ dữ liệu quảng cáo cho "+rngLab+" (file quảng cáo phủ ngắn hơn)");
      const tc=adR.rev?adR.spend/adR.rev*100:null,mps=[...new Set(adR.ok.map(x=>x.split(" ")[0]))],u=a=>[...new Set(a.map(x=>x.split(" ")[0]))].join(", ");
      return kp(IC.tag,"Chi phí QC "+WT+(adR.miss.length?" · "+mps.join("+"):""),U(adR.spend),0,
        (tc==null?"":`TACoS <b class="${tc>15?"dn":"up"}">${pc0(tc)}</b> · ngưỡng 15%`)
        +(adR.miss.length?`<br><small>chưa gồm ${u(adR.miss)} (thiếu dữ liệu ngày)</small>`:"")
        +(adR.part.length?`<br><small>Amazon thiếu 1-2 ngày đầu khoảng</small>`:""),
        tc==null?"":`<div class="bar" title="TACoS so với ngưỡng 15%"><i style="width:${Math.min(tc/15*100,100)}%;background:${tc>15?"var(--bad)":"var(--accent)"}"></i></div>`);
    };
    h+=adCard();'''+seg[b:]
# so sánh khi không có khoảng trước
r('${arrow(dl(cur.r,prev.r))} so với ${TT}','${dl(cur.r,prev.r)==null?(RG?"chưa có "+rngLab+" trước để so sánh":""):arrow(dl(cur.r,prev.r))+" so với "+TT}')
r('${arrow(dl(cur.q,prev.q))} so với ${TT}','${dl(cur.q,prev.q)==null?(RG?"chưa có "+rngLab+" trước để so sánh":""):arrow(dl(cur.q,prev.q))+" so với "+TT}')
# ---- (1) hàng 3 vòng tròn + chuyển "theo sàn" lên đó
r("    h+='</div><div class=\"row r2\">';","    h+='</div><div class=\"row rD\">';")
a=seg.index('    h+=`<div class="dc"><h3>Doanh thu theo sàn</h3>'); b=seg.index('\n',a)
mpline=seg[a:b]
seg=seg[:a]+'''    const CTYN={US:"Mỹ (US)",CAN:"Canada (CAN)",AUS:"Úc (AUS)"},byC={};
    if(L){Object.keys(D.ts_ov.D.cty).forEach(c=>{byC[c]=sum(L,d=>((D.ts_ov.D.cty[c]||{})[d]||{}).r)})}else D.cell.forEach(c=>{byC[c.cty]=(byC[c.cty]||0)+c.r});
    const cti=Object.keys(byC).filter(k=>byC[k]>0).sort((x,y)=>byC[y]-byC[x]).map((k,i2)=>({l:CTYN[k]||k,v:byC[k],c:`var(${SERIES[i2%8]})`,t:U(byC[k])}));
    const byG={};
    if(L){Object.keys(D.ts_grp.D).forEach(k=>{byG[k]=sum(L,d=>((D.ts_grp.D[k]||{})[d]||{}).r)})}else D.bygrp.forEach(x=>{byG[x.grp]=x.r});
    const gs=Object.keys(byG).filter(k=>byG[k]>0).sort((x,y)=>byG[y]-byG[x]),gtop=gs.slice(0,5);
    const gi=gtop.map((k,i2)=>({l:short(k),v:byG[k],c:`var(${SERIES[i2%8]})`,t:U(byG[k])}));
    if(gs.length>5){const rest=sum(gs.slice(5),k=>byG[k]);gi.push({l:"Nhóm khác ("+(gs.length-5)+")",v:rest,c:"var(--muted)",t:U(rest)})}
'''+mpline+'''
    h+=`<div class="dc"><h3>Doanh thu theo thị trường</h3><div class="dnw">${donut(cti,U(cur.r),(RG?rngLab:"doanh thu tuần"))}${legend(cti,cur.r)}</div></div>`;
    h+=`<div class="dc"><h3>Doanh thu theo nhóm sản phẩm</h3><div class="dnw">${donut(gi,U(cur.r),(RG?rngLab:"doanh thu tuần"))}${legend(gi,cur.r)}</div>${more("Xem theo nhóm","gr")}</div>`;
    h+='</div><div class="row r2 r2b">';'''+seg[b:]
# ---- bảng quảng cáo theo kênh
r('const ad=[...(D.adsum||[])].sort((a,b)=>b.spend-a.spend).slice(0,5);',
  'const ad=adR?[...adR.rows].sort((a,b)=>(a.na?1:0)-(b.na?1:0)||b.spend-a.spend):[...(D.adsum||[])].sort((a,b)=>b.spend-a.spend).slice(0,5);')
r('<td>${U(a.spend)}</td>','<td title="${a.na?"Chưa đủ dữ liệu quảng cáo cho "+rngLab:""}">${a.na?"—":U(a.spend)}</td>')
r('</tbody></table>`:\'<div class="note">Chưa có dữ liệu quảng cáo.</div>\')',
  '</tbody></table>${adR&&(adR.miss.length||adR.part.length)?`<div class="note">${adR.miss.length?"— = chưa đủ dữ liệu cho "+rngLab+": "+adR.miss.join(", ")+". ":""}${adR.part.length?"Thiếu ngày: "+adR.part.join("; ")+".":""}</div>`:""}`:\'<div class="note">Chưa có dữ liệu quảng cáo.</div>\')')
s=s[:i]+seg+s[j:]
rep1('.xc{}\n','.xc{}\n.dash .rD{display:grid;gap:14px;grid-template-columns:repeat(3,minmax(0,1fr))}.dash .r2.r2b{grid-template-columns:minmax(0,1.7fr) minmax(0,1fr)}@media(max-width:1100px){.dash .rD{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:900px){.dash .r2.r2b{grid-template-columns:minmax(0,1fr)}}@media(max-width:640px){.dash .rD{grid-template-columns:minmax(0,1fr)}}\n')
assert [l for l in s.split("\n") if l.startswith("const D = ")]==dl_
open(sys.argv[2],"w",encoding="utf-8").write(s)
