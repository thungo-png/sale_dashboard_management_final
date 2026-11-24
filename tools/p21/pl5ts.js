/* Gọn v4.1 — Profit PL5 theo khoảng thời gian (đọc D.pl5ts do etl/pl5ts.py tạo). Chèn ngay trước function pl5Panel. */
const PL5C={};
function pl5x(g,fam){            // mở khối nén D.pl5ts[g][fam] -> {tên:{kỳ:{p,r}}}
  const T=D.pl5ts; if(!T||!T[g]||!T[g][fam]) return null;
  const ck=g+"|"+fam; if(PL5C[ck]) return PL5C[ck];
  const o={},src=T[g][fam];
  Object.keys(src).forEach(n=>{const t={};Object.keys(src[n]).forEach(k=>{const v=src[n][k];t[k]={p:v[0],r:v[1]}});o[n]=t});
  return PL5C[ck]=o;
}
window.__pl5r=function(L,pL){    // PL5 cộng theo danh sách ngày L (và kỳ trước pL); null nếu chưa đủ ≥ 50% số ngày có số
  const a=pl5x("D","all"); if(!a||!a["Tổng"]) return null;
  const s=a["Tổng"], sum=days=>{let p=0,r=0,n=0;days.forEach(d=>{const x=s[d];if(x){p+=x.p;r+=x.r;n++}});return{p:p,r:r,n:n}};
  const c=sum(L); if(!c.n||c.n/L.length<0.5) return null;
  c.tot=L.length;
  if(pL&&pL.length){const q=sum(pL); if(q.n===pL.length&&q.r>0) c.prev=q}
  return c;
};
function pl5Panel(hostId,capId,o){
  const h=document.getElementById(hostId); if(!h) return;
  const c=document.getElementById(capId), T=D.pl5ts;
  const box=(t,sub)=>{h.innerHTML=`<div style="padding:26px 20px;text-align:center;border:1px dashed var(--line);border-radius:9px">
    <div style="font-family:'IBM Plex Mono',ui-monospace,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace;font-size:10px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)">Profit PL5</div>
    <div style="font-size:18px;font-weight:600;margin:7px 0 5px">${t}</div>
    <div style="font-size:12.5px;color:var(--ink-2);max-width:620px;margin:0 auto;line-height:1.7">${sub}</div></div>`; if(c) c.innerHTML="";};
  if(!T||!o){
    box("Chưa có chuỗi nhiều kỳ để vẽ xu hướng",`Tuần ${D.meta.week_no}: Profit PL5 <b class="${cls(D.pl5.total.profit)}">${N(D.pl5.total.profit)}</b> USD trên ${N(D.pl5.total.r)} doanh thu đã tính được (biên <b class="${cls(D.pl5.total.margin)}">${pc0(D.pl5.total.margin)}</b>, độ phủ ${String(D.pl5.coverage_pct).replace(".",",")}% toàn danh mục). Xem chi tiết theo SKU ở tab "Hiệu quả theo SKU", mục 04.<br>${D.pl5.why}`);
    return;}
  const g=o.g, wk=T.labels.W, wkTxt="W"+wk[0]+(wk.length>1?"–W"+wk[wk.length-1]:"");
  if(g!=="D"&&g!=="W"){box("PL5 chưa vẽ được theo "+(g==="M"?"tháng":"quý"),`PL5 chỉ có ở các tuần đủ chi phí quảng cáo thật (${wkTxt}), chưa đủ kỳ để gộp tháng/quý. Hãy chọn <b>Ngày</b> hoặc <b>Tuần</b>.`);return;}
  let labs=T.labels[g];
  if(g==="D"){const cur=new Set(D.ts_labels.D); labs=labs.filter(d=>cur.has(d))}   // theo khoảng ngày đang chọn
  const all=pl5x(g,o.fam)||{}, sm=o.pick?o.pick(all):all;
  if(!labs.length||!Object.keys(sm).length){box("Khoảng ngày này chưa có số PL5",`PL5 chỉ có ở các tuần đủ chi phí quảng cáo thật (${wkTxt}). Chọn khoảng ngày nằm trong các tuần đó, hoặc chọn <b>Tuần</b>.`);return;}
  tsChart(hostId,o.tip,sm,labs,"pl5",{color:o.colorOf?Object.fromEntries(Object.keys(sm).map(k=>[k,o.colorOf(k)])):null,mr:o.mr});
  if(c) c.innerHTML=`<b>Profit PL5</b> theo <b>${g==="D"?"ngày":"tuần"}</b>${o.what||""}. Gồm ${wk.length} tuần có chi phí quảng cáo thật (${wkTxt}); công thức theo file P&amp;L đã lưu, SEM là chi phí quảng cáo thật. `
    +(g==="D"?`Mức ngày = profit tuần chia theo tỷ trọng doanh thu ngày của từng SKU × sàn × thị trường${labs.length<D.ts_labels.D.length?` — khoảng đang chọn có số ${labs.length}/${D.ts_labels.D.length} ngày`:""}. `:"")
    +`Đơn vị: USD.`;
}
