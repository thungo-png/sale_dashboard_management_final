/* ======== PRO: quản trị chuyên sâu · drill-down · tìm kiếm · xuất/chia sẻ · sáng/tối ======== */
(function(){
"use strict";
const P=window.__PRO; if(!P||typeof D==="undefined") return;
/* Gọn v3: thống nhất định dạng số kiểu Việt cho chữ do ETL sinh (4.424 · 39,9% · −11,8%) */
const vn=x=>typeof x!=="string"?x:x.replace(/(^|[^\d.,])(\d{1,3}(?:,\d{3})+)(?!\d)(?!,\d)/g,(m,a,b)=>a+b.replace(/,/g,".")).replace(/(\d)\.(\d)(?=\s?(?:%|điểm|tuần|ngày|lần|x\b))/g,"$1,$2").replace(/(^|[\s(])-(?=\d)/g,"$1−");
(function(){const f=o=>Array.isArray(o)?o.map(vn):vn(o);
  if(Array.isArray(P.issues))P.issues.forEach(i=>{for(const k of ["title","where","detail","fix"])if(i[k]!=null)i[k]=f(i[k])});
  if(typeof P.brief==="string")P.brief=vn(P.brief);})();
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const N=(n,d=0)=>Number(n).toLocaleString("vi-VN",{maximumFractionDigits:d,minimumFractionDigits:d});
const USD=n=>(n<0?"−":"")+"$"+N(Math.abs(n));
const PCT=(n,d=1)=>N(n,d)+"%";
const esc=s=>String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const SH=g=>typeof short==="function"?short(g):g;
const nrm=s=>String(s).normalize("NFD").replace(/[̀-ͯ]/g,"").replace(/đ/g,"d").toLowerCase();
const el=(h)=>{const t=document.createElement("template");t.innerHTML=h.trim();return t.content.firstChild};
const store={get:k=>{try{return localStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}}};
const NOTE_T={deal:"Khuyến mãi",price:"Đổi giá",stock:"Tồn kho",ads:"Quảng cáo",listing:"Listing",other:"Khác"};
const SEV={3:"Ưu tiên cao",2:"Ưu tiên vừa",1:"Theo dõi"};

/* ---------- Giao diện sáng / tối ---------- */
const mq=window.matchMedia?matchMedia("(prefers-color-scheme: light)"):null;
let themePref=store.get("srm_theme")||"auto";
function applyTheme(){const eff=themePref==="auto"?(mq&&mq.matches?"light":"dark"):themePref;document.documentElement.dataset.theme=eff;
  const b=$("#pro-theme");if(b)b.innerHTML=(eff==="light"?"☀":"☾")+'<span class="lb">'+({auto:"Tự động",light:"Sáng",dark:"Tối"}[themePref])+"</span>";
  try{if(typeof rebuild==="function"){}}catch(e){}}
function cycleTheme(){themePref={auto:"light",light:"dark",dark:"auto"}[themePref];store.set("srm_theme",themePref);applyTheme();toast("Giao diện: "+({auto:"theo hệ thống",light:"sáng",dark:"tối"}[themePref]))}
if(mq&&mq.addEventListener)mq.addEventListener("change",()=>{if(themePref==="auto")applyTheme()});

/* ---------- Thanh công cụ ---------- */
const bar=el(`<div id="pro-bar" role="toolbar" aria-label="Công cụ báo cáo">
 <button id="pro-s" title="Tìm kiếm (Ctrl/Cmd+K)">⌕<span class="lb">Tìm</span><kbd class="lb">⌘K</kbd></button>
 <button id="pro-theme" title="Đổi giao diện sáng/tối"></button>
 <button id="pro-print" title="In / lưu PDF bản điều hành">⎙<span class="lb">In / PDF</span></button>
 <button id="pro-copy" title="Sao chép tóm tắt để gửi">⧉<span class="lb">Tóm tắt</span></button>
 <button id="pro-dl" title="Tải bản HTML để gửi đối tác">⤓<span class="lb">Tải HTML</span></button></div>`);
document.body.appendChild(bar);
const ov=el('<div id="pro-ov"></div>'), dr=el('<aside id="pro-drawer" aria-label="Chi tiết"></aside>'), pal=el('<div id="pro-pal" role="dialog" aria-label="Tìm kiếm"><input id="pro-q" placeholder="Tìm nhóm, SKU, tab hoặc lệnh…  (↑↓ chọn · Enter mở · Esc đóng)" autocomplete="off"><ul id="pro-res"></ul></div>'), mod=el('<div id="pro-modal" role="dialog"></div>');
document.body.append(ov,dr,pal,mod);
function toast(t){const x=el(`<div style="position:fixed;left:50%;bottom:76px;transform:translateX(-50%);background:var(--ink);color:var(--paper);padding:8px 16px;border-radius:999px;font-size:12.5px;z-index:120;box-shadow:0 8px 30px rgba(0,0,0,.4)">${esc(t)}</div>`);document.body.appendChild(x);setTimeout(()=>x.remove(),1800)}
function closeAll(){dr.classList.remove("on");pal.classList.remove("on");mod.classList.remove("on");ov.classList.remove("on")}
ov.addEventListener("click",closeAll);
document.addEventListener("keydown",e=>{
  if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openPal();return}
  if(e.key==="/"&&!/INPUT|TEXTAREA|SELECT/.test((document.activeElement||{}).tagName||"")){e.preventDefault();openPal();return}
  if(e.key==="Escape")closeAll()});

/* ---------- Xuất & chia sẻ ---------- */
function printPS(){document.body.classList.add("ps");if(typeof activate==="function"){activate("mg");activate("ov")}setTimeout(()=>{window.print()},250)}
window.addEventListener("afterprint",()=>document.body.classList.remove("ps"));
$("#pro-print").onclick=printPS;
async function copyText(t){try{await navigator.clipboard.writeText(t);return true}catch(e){const a=$("textarea",mod);if(a){a.select();try{return document.execCommand("copy")}catch(x){}}return false}}
$("#pro-copy").onclick=()=>{mod.innerHTML=`<h3 style="margin:0 0 10px">Tóm tắt để gửi (Zalo / email / họp)</h3><textarea readonly>${esc(P.brief)}</textarea>
 <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px"><button class="pbtn" id="pm-x">Đóng</button><button class="pbtn pri" id="pm-c">Sao chép</button></div>`;
 ov.classList.add("on");mod.classList.add("on");$("#pm-x",mod).onclick=closeAll;$("#pm-c",mod).onclick=async()=>{toast(await copyText(P.brief)?"Đã sao chép tóm tắt":"Hãy bôi đen và Ctrl+C")}};
$("#pro-dl").onclick=async()=>{let h;try{h=await (await fetch(location.href,{credentials:"same-origin"})).text();if(h.length<5000)throw 0}catch(e){h="<!doctype html>\n"+document.documentElement.outerHTML}
  const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([h],{type:"text/html;charset=utf-8"}));a.download="Sale-Report-W"+((D.meta||{}).week_no||"")+".html";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),4000);toast("Đã tải bản HTML")};
$("#pro-theme").onclick=cycleTheme;
applyTheme();

/* ---------- Khối “Điều cần chú ý” ở Tổng quan ---------- */
(function(){
  const host=$("#p-ov section"); if(!host) return;
  const areas=Array.from(new Set(P.issues.map(i=>i.area)));
  const s=P.summary, by=s.by_sev;
  const sec=el(`<section class="pro-sec" id="pro-ins"><div class="shead"><span class="snum">★</span><h2>Điều cần chú ý tuần này</h2><span class="hint">Tự động từ số liệu · vấn đề nằm ở đâu và hướng xử lý</span></div>
   <div class="pchips" id="pi-chips"></div><div id="pi-list"></div>
   ${P.questions.length?`<div class="qbox"><h3 style="margin:0 0 6px">Câu hỏi gợi ý cho buổi họp</h3><ol style="margin:0 0 0 18px;padding:0">${P.questions.map(q=>`<li>${esc(q)}</li>`).join("")}</ol></div>`:""}</section>`);
  host.after(sec);
  /* Gọn v2: gộp cảnh báo cùng loại (cùng khu vực + cùng dạng) thành một thẻ khi có từ 3 mục trở lên */
  const GT={drop:["cụm (nhóm × sàn × thị trường) chưa giữ được mức doanh thu tuần trước","Doanh số"],margin_grp:["nhóm sản phẩm có margin cần cải thiện"],margin_mc:["kênh có margin cần rà cơ cấu chi phí"],
    camp:["cụm có campaign chưa hiệu quả"],tacos:["cụm có TACoS cao"],lowstock:["nhóm có SKU sắp hết hàng"],deadstock:["nhóm có tồn nhưng chưa phát sinh bán gần đây"]};
  const shortWhere=w=>{let x=String(w||"").replace(/^Nhóm sản phẩm:\s*|^Nhóm:\s*|^Kênh:\s*/,"");(D.meta.groups||[]).forEach(g=>{x=x.split(g).join(SH(g))});return x};
  const issueCard=i=>`<div class="isu s${i.sev}"><span class="sev s${i.sev}">${SEV[i.sev]}</span> <span class="chip">${esc(i.area)}</span>
      <h4>${esc(i.title)}</h4><div class="w">Vấn đề nằm ở: ${esc(i.where)}</div>${i.detail.length?`<ul>${i.detail.map(d=>`<li>${esc(d)}</li>`).join("")}</ul>`:""}
      ${i.fix.length?`<ul class="fx">${i.fix.map(d=>`<li>${esc(d)}</li>`).join("")}</ul>`:""}</div>`;
  function groupIssues(list){const g=new Map(),out=[];
    list.forEach(i=>{const t=String(i.key||"").split("|")[0],k=i.area+"|"+t;if(!GT[t]){out.push({one:i});return}
      if(!g.has(k)){const o={many:[]};g.set(k,o);out.push(o)}g.get(k).many.push(i)});
    return out.map(o=>o.many&&o.many.length<3?o.many.map(x=>({one:x})):[o]).flat()}
  function groupCard(arr){const sev=Math.max(...arr.map(i=>i.sev)),t=String(arr[0].key).split("|")[0],lab=GT[t][0];
    const fixes=[...new Set(arr.flatMap(i=>i.fix))];
    return `<div class="isu s${sev}"><span class="sev s${sev}">${SEV[sev]}</span> <span class="chip">${esc(arr[0].area)}</span> <span class="chip">${arr.length} mục</span>
      <h4>${arr.length} ${esc(lab)}</h4>
      <div class="w">Vấn đề nằm ở: ${arr.slice(0,6).map(i=>esc(shortWhere(i.where))).join(" · ")}${arr.length>6?` · +${arr.length-6} mục khác`:""}</div>
      ${fixes.length?`<ul class="fx">${fixes.slice(0,4).map(d=>`<li>${esc(d)}</li>`).join("")}</ul>`:""}
      <details class="capfold"><summary>Chi tiết từng mục (${arr.length})</summary>${arr.map(i=>`<div class="w" style="margin-top:8px"><b>${esc(shortWhere(i.where))}</b>${i.detail.length?" — "+esc(i.detail.join(" ")):""}</div>`).join("")}</details></div>`}
  let area="",show=5;
  function paint(){
    $("#pi-chips").innerHTML=`<button aria-pressed="${!area}" data-a="">Tất cả (${s.n})</button>`+areas.map(a=>`<button aria-pressed="${area===a}" data-a="${esc(a)}">${esc(a)} (${s.by_area[a]||0})</button>`).join("")+
      `<span style="margin-left:auto;font-size:12px;color:var(--muted)">${["3","2","1"].map(k=>`<span class="sev s${k}" style="margin-left:6px">${SEV[k]} ${by[k]||0}</span>`).join("")}</span>`;
    $$("#pi-chips button").forEach(b=>b.onclick=()=>{area=b.dataset.a;show=5;paint()});
    const l=P.issues.filter(i=>!area||i.area===area);
    const cards=groupIssues(l);
    $("#pi-list").innerHTML=cards.slice(0,show).map(c=>c.many?groupCard(c.many):issueCard(c.one)).join("")||'<p class="cap">Không có điểm cần chú ý ở mục này.</p>';
    if(cards.length>show)$("#pi-list").insertAdjacentHTML("beforeend",`<button class="pbtn" id="pi-more">Xem thêm ${cards.length-show} mục</button>`),$("#pi-more").onclick=()=>{show+=8;paint()};
  }
  paint();
})();

/* ---------- Biểu đồ nhỏ (SVG) ---------- */
function spark(vals,labs,o){o=o||{};const w=o.w||460,h=o.h||90,pad=6;if(!vals.length)return"";const mx=Math.max(...vals,1),mn=Math.min(0,...vals);
  const x=i=>pad+i*(w-2*pad)/Math.max(1,vals.length-1),y=v=>h-pad-(v-mn)/(mx-mn||1)*(h-2*pad);
  const pts=vals.map((v,i)=>x(i)+","+y(v)).join(" ");
  return `<svg class="svgc" viewBox="0 0 ${w} ${h}" role="img"><polygon points="${pad},${h-pad} ${pts} ${w-pad},${h-pad}" fill="var(--accent)" opacity=".12"/><polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round"/>
   ${vals.map((v,i)=>`<circle cx="${x(i)}" cy="${y(v)}" r="${i===vals.length-1?4:2.2}" fill="var(--accent)"><title>${esc(labs[i]||"")}: ${USD(v)}</title></circle>`).join("")}</svg>`}
function weekOfDate(d){const m=D.meta,last=(T0().weeks.length-1);const a=new Date(m.d0+'T00:00:00');for(let i=last;i>=0;i--){const st=new Date(a.getTime()-(last-i)*7*864e5),en=new Date(st.getTime()+7*864e5);const x=new Date(d+'T00:00:00');if(x>=st&&x<en)return i}return -1}
function T0(){return P.trend}
function trendChart(T){const w=900,h=270,L=52,R=14,Tp=14,B=34,n=T.r.length;const mx=Math.max(...T.r,...T.fc,1)*1.08;
  const bw=(w-L-R)/n,y=v=>Tp+(h-Tp-B)*(1-v/mx),cx=i=>L+bw*i+bw/2;
  let g="";for(let k=0;k<=4;k++){const v=mx*k/4;g+=`<line x1="${L}" x2="${w-R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)" stroke-dasharray="3 4"/><text x="${L-8}" y="${y(v)+3}" text-anchor="end">${v>=1000?N(v/1000)+"k":N(v)}</text>`}
  const bars=T.r.map((v,i)=>`<rect x="${cx(i)-bw*.32}" y="${y(v)}" width="${bw*.64}" height="${Math.max(1,y(0)-y(v))}" rx="4" fill="var(--accent)" opacity="${i===n-1?1:.55}"><title>Tuần ${T.weeks[i]} (${T.lab[i]})\nDoanh thu ${USD(v)}\nTB 4 tuần ${USD(T.ma4[i])}\nFC ${USD(T.fc[i])}</title></rect>`).join("");
  const line=(a,c,d)=>`<polyline fill="none" stroke="${c}" stroke-width="2.2" ${d?'stroke-dasharray="5 4"':""} points="${a.map((v,i)=>cx(i)+","+y(v)).join(" ")}"/>`;
  const NT={};(P.notes||[]).forEach(n=>{const i=weekOfDate(n.date);if(i>=0)(NT[i]=NT[i]||[]).push(n)});
  const mk=Object.keys(NT).map(i=>`<g><text x="${cx(+i)}" y="${Tp+4}" text-anchor="middle" style="fill:var(--warn-ink);font-size:13px;cursor:help">◆<title>${NT[i].map(n=>n.date+" · "+n.text).join("\n").replace(/[<&]/g," ")}</title></text></g>`).join("");
  const xl=T.weeks.map((wk,i)=>`<text x="${cx(i)}" y="${h-12}" text-anchor="middle">W${wk}</text>`).join("");
  return `<svg class="svgc" viewBox="0 0 ${w} ${h}" role="img" aria-label="Doanh thu 12 tuần">${g}${bars}${line(T.ma4,"var(--s2)")}${line(T.fc,"var(--muted)",1)}${mk}${xl}</svg>
   <div class="legend" style="margin-top:8px"><span class="chip"><i style="width:10px;height:10px;border-radius:3px;background:var(--accent)"></i>Doanh thu tuần</span><span class="chip"><i style="width:14px;height:3px;background:var(--s2)"></i>Trung bình 4 tuần</span><span class="chip"><i style="width:14px;height:0;border-top:2px dashed var(--muted)"></i>FC</span>${(P.notes||[]).length?`<span class="chip">◆ Sự kiện đã ghi</span>`:""}</div>`}
function paretoChart(c,n80){const w=520,h=220,L=40,R=10,Tp=10,B=28,n=c.length;const x=i=>L+(w-L-R)*i/Math.max(1,n-1),y=v=>Tp+(h-Tp-B)*(1-v/100);
  const pts=c.map((v,i)=>x(i)+","+y(v)).join(" ");let g="";[0,20,40,60,80,100].forEach(v=>g+=`<line x1="${L}" x2="${w-R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)" stroke-dasharray="3 4"/><text x="${L-6}" y="${y(v)+3}" text-anchor="end">${v}%</text>`);
  return `<svg class="svgc" viewBox="0 0 ${w} ${h}" role="img" aria-label="Đường tích luỹ doanh thu theo SKU">${g}<polygon points="${x(0)},${y(0)} ${pts} ${x(n-1)},${y(0)}" fill="var(--accent)" opacity=".13"/><polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="2.4"/>
   ${n80?`<line x1="${x(n80-1)}" x2="${x(n80-1)}" y1="${y(0)}" y2="${y(80)}" stroke="var(--warn)" stroke-dasharray="4 3"/><circle cx="${x(n80-1)}" cy="${y(80)}" r="5" fill="var(--warn)"/><text x="${x(n80-1)+8}" y="${y(80)+14}" style="fill:var(--warn-ink)">${n80} SKU = 80%</text>`:""}
   <text x="${L}" y="${h-8}">SKU xếp theo doanh thu →</text></svg>`}

/* ---------- Drill-down (ngăn bên) ---------- */
function openDrawer(title,sub,body){dr.innerHTML=`<div class="dh"><div style="flex:1;min-width:0"><div class="eyebrow">${esc(sub)}</div><h2 style="margin:4px 0 0;font-size:20px">${esc(title)}</h2></div><button class="pbtn" id="dr-x">Đóng ✕</button></div><div class="db">${body}</div>`;
  ov.classList.add("on");dr.classList.add("on");$("#dr-x",dr).onclick=closeAll;$$("[data-sku]",dr).forEach(e=>e.onclick=()=>drillSku(e.dataset.sku));$$("[data-grp]",dr).forEach(e=>e.onclick=()=>drillGrp(e.dataset.grp));dr.scrollTop=0;wiInit(dr)}
const tsOf=(blk,key)=>{const t=(blk&&blk[key])||{};return (D.ts_labels.W||[]).map(w=>(t[String(w)]||{}).r||0)};
const wkLab=()=>(D.ts_labels.W||[]).map(w=>"W"+w);
function issuesFor(txt,max){return P.issues.filter(i=>(i.where+" "+i.detail.join(" ")).includes(txt)).slice(0,max||4)}
function issuesHtml(l){return l.length?`<h3>Điểm cần chú ý</h3>`+l.map(i=>`<div class="isu s${i.sev}"><span class="sev s${i.sev}">${SEV[i.sev]}</span><h4>${esc(i.title)}</h4>${i.fix.length?`<ul class="fx">${i.fix.map(d=>`<li>${esc(d)}</li>`).join("")}</ul>`:""}</div>`).join(""):""}
function tile(k,v,s,c){return `<div class="ptile" style="--tc:${c||"var(--accent)"}"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s||""}</div></div>`}

/* ---------- Mô phỏng giá & quảng cáo (What-if) ----------
   Mô hình theo từng dòng P&L (SKU × sàn × quốc gia): phí sàn, hoàn trả, kho, vận hành tính theo % doanh thu;
   giá vốn và phí fulfill tính theo đơn vị; quảng cáo đổi theo thanh kéo. SL = SL gốc × (1+Δgiá)^e_giá × (1+Δqc)^e_qc. */
const WI={n:0,reg:{}};
function wiRows(f){return (D.pl5.rows||[]).filter(x=>x.r>0&&x.q>0&&(!f||f(x)))}
function wiCalc(rows,dp,da,ep,ea){
  const f=Math.pow(1+dp,ep)*Math.pow(1+da,ea);const T={a:{r:0,q:0,p:0,sem:0},b:{r:0,q:0,p:0,sem:0},ch:{}};
  rows.forEach(x=>{
    const pct=x.ref_fee+x.return_fee+x.wh_fee+x.op_fee, unit=x.cogs+x.fulfill;
    const rr=x.r*(1+dp)*f, k=(1+dp)*f, pb=x.r-pct-unit-x.sem, pn=rr-pct*k-unit*f-x.sem*(1+da);
    const prof=x.profit+(pn-pb), key=x.mp+" "+x.cty, c=T.ch[key]||(T.ch[key]={r0:0,p0:0,r1:0,p1:0});
    T.a.r+=x.r;T.a.q+=x.q;T.a.p+=x.profit;T.a.sem+=x.sem;T.b.r+=rr;T.b.q+=x.q*f;T.b.p+=prof;T.b.sem+=x.sem*(1+da);
    c.r0+=x.r;c.p0+=x.profit;c.r1+=rr;c.p1+=prof});
  return T}
function wiSolve(rows,da,ep,ea,ok){for(let i=-50;i<=100;i++){const T=wiCalc(rows,i/100,da,ep,ea);if(T.b.r>0&&ok(T)){return i}}return null}
function wiHtml(rows,label){
  const id="wi"+(++WI.n);WI.reg[id]=rows;
  if(!rows.length)return `<div class="card"><p style="color:var(--muted);margin:0">${label?esc(label)+": ":""}Chưa có dòng P&L (giá vốn và phí) để mô phỏng — cần bổ sung công thức phí vào file P&L.</p></div>`;
  const nAll=(D.pl5.rows||[]).length;
  return `<div class="wi card" data-wi="${id}"><div class="wi-ctl">
   <label>Giá bán <b data-o="dp">0%</b><input type="range" min="-30" max="30" step="1" value="0" data-k="dp"></label>
   <label>Chi quảng cáo <b data-o="da">0%</b><input type="range" min="-100" max="100" step="5" value="0" data-k="da"></label>
   <label>Độ co giãn SL theo giá<input type="number" step="0.1" min="-5" max="2" value="0" data-k="ep" title="0 = đổi giá nhưng SL không đổi. −1,5 = tăng giá 10% làm SL giảm khoảng 14%.">
   </label><label>Độ nhạy SL theo quảng cáo<input type="number" step="0.05" min="0" max="1" value="0" data-k="ea" title="0 = đổi quảng cáo nhưng SL không đổi. 0,2 = giảm 50% quảng cáo làm SL giảm khoảng 13%."></label></div>
   <div class="wi-out"></div><p class="cap" style="margin-top:10px">Ước tính theo cấu trúc phí kỳ này (${rows.length}/${nAll} dòng P&L có doanh thu). Phí sàn, hoàn trả, kho, vận hành đổi theo % doanh thu; giá vốn và phí fulfill đổi theo số lượng. Độ co giãn mặc định 0 nên số liệu là <b>giả định SL không đổi</b>; nhập độ co giãn thật nếu bạn có.
   <button class="pbtn" data-wireset style="float:right">Đặt lại</button></p></div>`}
function wiPaint(w){
  const rows=WI.reg[w.dataset.wi]||[];const g=k=>parseFloat(w.querySelector(`[data-k=${k}]`).value)||0;
  const dp=g("dp")/100,da=g("da")/100,ep=g("ep"),ea=g("ea");
  w.querySelector('[data-o=dp]').textContent=(dp>0?"+":"")+Math.round(dp*100)+"%";w.querySelector('[data-o=da]').textContent=(da>0?"+":"")+Math.round(da*100)+"%";
  const T=wiCalc(rows,dp,da,ep,ea),a=T.a,b=T.b,m0=a.r?a.p/a.r*100:0,m1=b.r?b.p/b.r*100:0,tg=P.target_margin||10;
  const d=(x,y,usd)=>{const v=y-x;return `<span style="color:${v>=0?"var(--good-ink)":"var(--warn-ink)"}">${v>=0?"+":"−"}${usd?"$"+N(Math.abs(v)):N(Math.abs(v),1)+(usd===0?"":"")}</span>`};
  const tgt=wiSolve(rows,da,ep,ea,t=>t.b.p/t.b.r*100>=tg), be=wiSolve(rows,da,ep,ea,t=>t.b.p>=0);
  const hint=(x,lbl)=>x===null?`${lbl}: không đạt trong khoảng −50%…+100% giá`:`${lbl}: ${x>0?"giá +"+x+"%":x===0?"đang vừa đạt ở giá hiện tại":"đã đạt; có thể giảm giá tới khoảng "+x+"%"}`;
  const ch=Object.entries(T.ch).sort((x,y)=>y[1].r0-x[1].r0);
  w.querySelector(".wi-out").innerHTML=`<div class="pro-grid g4" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">
   ${tile("Doanh thu",USD(b.r),"hiện tại "+USD(a.r)+" · "+d(a.r,b.r,1))}${tile("Lợi nhuận PL5",USD(b.p),"hiện tại "+USD(a.p)+" · "+d(a.p,b.p,1),b.p>=a.p?"var(--good)":"var(--warn)")}
   ${tile("Margin PL5",PCT(m1),"hiện tại "+PCT(m0)+" · "+(m1-m0>=0?"+":"−")+N(Math.abs(m1-m0),1)+" điểm","var(--s4)")}${tile("Số lượng",N(b.q,0),"hiện tại "+N(a.q,0)+" · "+(b.q-a.q>=0?"+":"−")+N(Math.abs(b.q-a.q),0),"var(--s5)")}</div>
   <p style="margin:10px 0;font-size:13px;color:var(--ink-2)"><b>Gợi ý:</b> ${hint(tgt,"để đạt margin mục tiêu "+tg+"%")} · ${hint(be,"để hoà vốn lợi nhuận")} (theo mức quảng cáo và độ co giãn đang chọn). Chi quảng cáo: ${USD(a.sem)} → ${USD(b.sem)}; TACoS ${a.r?PCT(a.sem/a.r*100):"—"} → ${b.r?PCT(b.sem/b.r*100):"—"}.</p>
   <div class="scroll"><table><thead><tr><th>Kênh</th><th>Doanh thu</th><th>Margin hiện tại</th><th>Margin mới</th><th>Lợi nhuận mới</th></tr></thead><tbody>${ch.map(([k,c])=>`<tr><td>${esc(k)}</td><td>${USD(c.r1)}</td><td>${c.r0?PCT(c.p0/c.r0*100):"—"}</td><td>${c.r1?PCT(c.p1/c.r1*100):"—"}</td><td>${USD(c.p1)}</td></tr>`).join("")}</tbody></table></div>`}
document.addEventListener("input",e=>{const w=e.target.closest&&e.target.closest(".wi");if(w)wiPaint(w)});
document.addEventListener("click",e=>{const b=e.target.closest&&e.target.closest("[data-wireset]");if(!b)return;const w=b.closest(".wi");w.querySelectorAll("[data-k]").forEach(i=>i.value=0);wiPaint(w)});
function wiInit(root){$$(".wi",root).forEach(wiPaint)}
function wiMount(){const host=$("#wi-host");if(!host)return;
  const groups=[...new Set((D.pl5.rows||[]).map(x=>x.grp))].sort();
  host.innerHTML=`<div class="row-flex" style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px"><select id="wi-scope" class="pbtn" style="min-width:220px"><option value="">Toàn danh mục</option>${groups.map(g=>`<option value="g:${esc(g)}">Nhóm: ${esc(SH(g))}</option>`).join("")}</select><input id="wi-sku" class="pbtn" list="wi-skus" placeholder="Hoặc nhập mã SKU" style="min-width:160px"><datalist id="wi-skus">${[...new Set((D.pl5.rows||[]).map(x=>x.sku))].sort().map(k=>`<option value="${k}">`).join("")}</datalist></div><div id="wi-box"></div>`;
  const draw=()=>{const sc=$("#wi-scope").value,sk=$("#wi-sku").value.trim().toUpperCase();const rows=sk?wiRows(x=>x.sku===sk):sc?wiRows(x=>x.grp===sc.slice(2)):wiRows();
    $("#wi-box").innerHTML=wiHtml(rows,sk?"SKU "+sk:"");wiInit($("#wi-box"))};
  $("#wi-scope").onchange=()=>{$("#wi-sku").value="";draw()};$("#wi-sku").oninput=draw;draw()}
function drillSku(sku){
  const meta=(D.sku_meta||[]).find(x=>x.sku===sku)||{}, rows=D.sku.filter(x=>x.sku===sku);
  const q=rows.reduce((a,x)=>a+x.q,0), r=rows.reduce((a,x)=>a+x.r,0), ser=tsOf(((D.ts_sku||{}).W||{}).l1,sku);
  const inv=((D.invdet||{}).sku_tot||[]).find(x=>x.sku===sku), pl=(D.pl5.rows||[]).filter(x=>x.sku===sku), prof=pl.reduce((a,x)=>a+x.profit,0), plr=pl.reduce((a,x)=>a+x.r,0);
  const asp=(D.askuw_mp||[]).filter(a=>a.sku===sku&&a.avg4);
  openDrawer(meta.name||sku,"SKU · "+sku+(meta.grp?" · "+SH(meta.grp):""),`
   <div class="pro-grid g4" style="grid-template-columns:repeat(2,1fr)">${tile("Doanh thu tuần",USD(r),q+" sản phẩm")}${tile("Margin PL5",plr?PCT(prof/plr*100):"n/a",plr?"Lợi nhuận "+USD(prof):"Chưa có công thức phí","var(--s3)")}
   ${tile("Tồn kho",inv?N(inv.qty):"n/a",inv?(inv.weeks!=null?"đủ ~"+N(inv.weeks,1)+" tuần":"chưa có đơn gần đây"):"","var(--s4)")}${tile("Số kênh bán",String(rows.filter(x=>x.r>0).length),"sàn × thị trường có doanh thu","var(--s7)")}</div>
   <h3>Doanh thu 12 tuần</h3><div class="card">${spark(ser,wkLab())}</div>
   <h3>Theo kênh (tuần này)</h3><div class="scroll"><table><thead><tr><th>Kênh</th><th>SL</th><th>Doanh thu</th><th>Margin</th></tr></thead><tbody>${rows.filter(x=>x.q>0||x.r>0).map(x=>{const p=pl.find(y=>y.mp===x.mp&&y.cty===x.cty);return `<tr><td>${esc(x.mp)} ${esc(x.cty)}</td><td>${x.q}</td><td>${USD(x.r)}</td><td>${p&&p.r?PCT(p.profit/p.r*100):"—"}</td></tr>`}).join("")||'<tr><td colspan="4">Không có doanh thu tuần này</td></tr>'}</tbody></table></div>
   ${asp.length?`<h3>Giá bán thực hiện</h3><div class="scroll"><table><thead><tr><th>Kênh</th><th>ASP tuần</th><th>TB 4 tuần</th><th>Chênh</th></tr></thead><tbody>${asp.map(a=>{const c=(a.cells||{})[String(D.meta.week_no)]||{};const ch=c.asp&&a.avg4?(c.asp/a.avg4-1)*100:null;return `<tr><td>${esc(a.mp)} ${esc(a.cty)}</td><td>${c.asp?N(c.asp,2)+" "+a.cur:"—"}</td><td>${N(a.avg4||0,2)}</td><td>${ch==null?"—":(ch>0?"+":"")+N(ch,1)+"%"}</td></tr>`}).join("")}</tbody></table></div>`:""}
   ${inv?`<h3>Tồn kho theo thị trường</h3><div class="pchips">${Object.entries(inv.by_cty||{}).map(([c,v])=>`<span class="chip">${c}: ${N(v)}</span>`).join("")}</div>`:""}
   <h3>Mô phỏng giá &amp; quảng cáo</h3>${wiHtml(wiRows(x=>x.sku===sku))}
   ${issuesHtml(issuesFor(sku))}${meta.grp?`<h3>Nhóm sản phẩm</h3><button class="pbtn" data-grp="${esc(meta.grp)}">Mở ${esc(SH(meta.grp))} →</button>`:""}`)}
function drillGrp(g){
  const cells=(D.bygrp_cell||[]).filter(x=>x.grp===g), cur=cells.reduce((a,x)=>a+x.r,0), q=cells.reduce((a,x)=>a+x.q,0), fc=cells.reduce((a,x)=>a+(x.rfc||0),0);
  const ser=tsOf(D.ts_grp.W,g), p5=(D.pl5.by_grp||{})[g], ads=P.ads.filter(a=>a.grp===g);
  const by={};D.sku.filter(x=>x.grp===g).forEach(x=>{by[x.sku]=(by[x.sku]||0)+x.r});const top=Object.entries(by).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const stock=((D.invdet||{}).sku_tot||[]).filter(s=>s.grp===g||SH(s.grp)===SH(g)), units=stock.reduce((a,s)=>a+s.qty,0), low=stock.filter(s=>s.weeks!=null&&s.weeks<6).length;
  const name=sku=>((D.sku_meta||[]).find(m=>m.sku===sku)||{}).name||sku;
  openDrawer(SH(g),"Nhóm sản phẩm",`
   <div class="pro-grid g4" style="grid-template-columns:repeat(2,1fr)">${tile("Doanh thu tuần",USD(cur),q+" sản phẩm"+(fc?" · đạt "+PCT(cur/fc*100)+" FC":""))}${tile("Margin PL5",p5?PCT(p5.margin):"n/a",p5?"Lợi nhuận "+USD(p5.profit):"","var(--s3)")}
   ${tile("Tồn kho",N(units),low?low+" SKU dưới 6 tuần":"không SKU nào dưới 6 tuần","var(--s4)")}${tile("SKU bán ra",String(top.length),"có doanh thu tuần này","var(--s7)")}</div>
   <h3>Doanh thu 12 tuần</h3><div class="card">${spark(ser,wkLab())}</div>
   <h3>SKU đóng góp lớn nhất</h3><div class="scroll"><table><thead><tr><th>SKU</th><th>Tên</th><th>Doanh thu</th></tr></thead><tbody>${top.map(([s,v])=>`<tr style="cursor:pointer" data-sku="${s}"><td><b>${s}</b></td><td>${esc(name(s))}</td><td>${USD(v)}</td></tr>`).join("")}</tbody></table></div>
   ${ads.length?`<h3>Dư địa quảng cáo</h3><div class="scroll"><table><thead><tr><th>Kênh</th><th>TACoS</th><th>Hoà vốn</th><th>Trạng thái</th></tr></thead><tbody>${ads.map(a=>`<tr><td>${a.mp} ${a.cty}</td><td>${PCT(a.tacos)}</td><td>${PCT(a.breakeven)}</td><td>${stt(a.st)}</td></tr>`).join("")}</tbody></table></div>`:""}
   ${issuesHtml(issuesFor(g,5))}`)}
window.proDrillSku=drillSku;window.proDrillGrp=drillGrp;
const STT={pre:"Biên trước QC chưa dương",over:"Vượt hoà vốn",tight:"Sát ngưỡng",room:"Còn dư địa"};
const stt=s=>`<span class="stt ${s}">${STT[s]}</span>`;

/* ---------- Tab “Quản trị chuyên sâu” ---------- */
(function(){
  const gr=$('.tab[data-p="gr"]'),pg=$("#p-gr"); if(!gr||!pg) return;
  const b=document.createElement("button");b.className="tab";b.setAttribute("role","tab");b.setAttribute("aria-selected","false");b.dataset.p="mg";b.textContent="Quản trị chuyên sâu";gr.after(b);
  b.addEventListener("click",()=>activate("mg"));
  const panel=el('<div class="panel" id="p-mg" role="tabpanel"></div>');pg.after(panel);
  builders.mg=function(){
    const B=P.bridge,I=P.inv,PA=P.pareto,K=P.kpi,T=P.trend,nRoom=P.ads.filter(a=>a.st==="room").length,nPre=P.ads.filter(a=>a.st==="pre"||a.st==="over").length;
    const lvl='<span class="lvl ceo">Báo cáo cấp CEO · góc nhìn quản trị</span>';
    const OPEN={"01":1,"02":1,"03":1,"04":1};   /* mẫu Gọn v2: mục 05-09 (tập trung, tồn kho, giá, sức khỏe dữ liệu, mô phỏng) gập mặc định */
    const sec=(n,t,h,body,cap)=>`<section class="pro-sec"><details class="fold"${OPEN[n]?" open":""}><summary><div class="shead"><span class="snum">${n}</span><h2>${t}</h2><span class="hint">${h||""}</span></div></summary><div class="foldbody">${body}${cap?`<p class="cap">${cap}</p>`:""}</div></details></section>`;
    let html=`<section>${lvl}<div class="pro-grid g4">
      ${tile("Doanh thu tuần",USD(K.r),(K.wow!=null?(K.wow>0?"+":"")+N(K.wow,1)+"% so tuần trước · ":"")+"đạt "+PCT(K.ach)+" FC")}
      ${tile("Margin PL5",B?PCT(B.margin):"n/a",B?"độ phủ dữ liệu "+PCT(B.coverage,0):"chưa có P&L","var(--s3)")}
      ${tile("Dư địa quảng cáo",nRoom+" cụm",nPre+" cụm cần rà trước khi tăng chi","var(--s4)")}
      ${tile("Rủi ro tồn kho",I.n_low+" SKU","dưới 6 tuần tồn · "+I.dead_n+" SKU chưa có đơn","var(--s2)")}</div></section>`;
    if(B){const lo=Math.min(0,B.profit),span=B.r-lo,X=v=>(v-lo)/span*100;let rem=B.r;
      const rows=[`<div class="hl"><span>Doanh thu</span><div class="bar2"><i style="left:${X(0)}%;width:${X(B.r)-X(0)}%;background:var(--accent)"></i></div><b>${USD(B.r)}</b></div>`];
      B.items.forEach((it,i)=>{const a=rem-it.v;rows.push(`<div class="hl"><span>− ${it.k}</span><div class="bar2"><i style="left:${X(Math.min(a,rem))}%;width:${Math.abs(X(rem)-X(a))}%;background:var(--s${[2,4,5,7][i]||2})"></i></div><span><b>${USD(it.v)}</b> <small style="color:var(--muted)">${PCT(it.pct)}</small></span></div>`);rem=a});
      rows.push(`<div class="hl" style="border-top:1px solid var(--line);margin-top:4px;padding-top:9px"><span><b>Lợi nhuận PL5</b></span><div class="bar2"><i style="left:${X(Math.min(0,B.profit))}%;width:${Math.abs(X(B.profit)-X(0))}%;background:${B.profit>=0?"var(--good)":"var(--bad)"}"></i></div><span><b>${USD(B.profit)}</b> <small style="color:var(--muted)">${PCT(B.margin)}</small></span></div>`);
      html+=sec("01","Cầu lợi nhuận","từ doanh thu đến lợi nhuận PL5",`<div class="pro-grid g2"><div class="card"><h3>Doanh thu → lợi nhuận</h3>${rows.join("")}</div>
        <div class="scroll"><table><thead><tr><th>Kênh</th><th>Doanh thu</th><th>Margin</th><th>Biên trước QC</th><th>QC / DT</th></tr></thead><tbody>${B.by_mc.map(c=>`<tr><td>${esc(c.mc)}</td><td>${USD(c.r)}</td><td>${PCT(c.margin)}</td><td>${PCT(c.pre_ads)}</td><td>${PCT(c.ads)}</td></tr>`).join("")}</tbody></table></div></div>`,
        "Cách đọc: nhìn khoản chiếm tỷ trọng lớn nhất trước. Nếu <b>biên trước quảng cáo</b> (margin + tỷ lệ chi quảng cáo) đã thấp, vấn đề nằm ở giá bán / giá vốn / vận chuyển; quảng cáo chỉ là phần nhỏ nên cắt quảng cáo không giải quyết được gốc.")}
    html+=sec("02","Xu hướng 12 tuần","doanh thu · TB 4 tuần · FC",`<div class="chartbox">${trendChart(T)}</div>${(P.notes||[]).length?`<div class="card" style="margin-top:12px"><h3>Sự kiện đã ghi trong kỳ</h3>${P.notes.map(n=>`<div class="hl" style="grid-template-columns:90px 120px 1fr"><span>${esc(n.date)}</span><span class="chip">${esc(NOTE_T[n.type]||n.type)}</span><span>${esc(n.text)}</span></div>`).join("")}</div>`:""}`,"Cột sáng là tuần hiện tại. Đường TB 4 tuần giúp lọc nhiễu theo tuần; so khoảng cách tới đường FC để biết nhịp tăng cần thiết.");
    const SC=P.sku_class;const CCOL={star:"var(--good)",fix:"var(--warn)",potential:"var(--accent)",exit:"var(--bad)",idle:"var(--muted)",nodata:"var(--s7)"};
    function scatter(){const rows=SC.rows.filter(x=>x.margin!=null&&x.r>0);if(!rows.length)return"";const w=560,h=300,L=44,R=12,Tp=12,B=32,mxr=Math.max(...rows.map(x=>x.r)),X=v=>L+(w-L-R)*Math.sqrt(v/mxr),Y=m=>Tp+(h-Tp-B)*(1-(Math.max(-30,Math.min(30,m))+30)/60);
      return `<svg class="svgc" viewBox="0 0 ${w} ${h}" role="img" aria-label="Ma trận doanh thu và margin theo SKU"><line x1="${L}" x2="${w-R}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--line)"/><line x1="${L}" x2="${w-R}" y1="${Y(SC.margin_good)}" y2="${Y(SC.margin_good)}" stroke="var(--good)" stroke-dasharray="4 3" opacity=".7"/><line x1="${X(SC.median_r)}" x2="${X(SC.median_r)}" y1="${Tp}" y2="${h-B}" stroke="var(--warn)" stroke-dasharray="4 3" opacity=".7"/>
      ${[-30,-15,0,15,30].map(m=>`<text x="${L-6}" y="${Y(m)+3}" text-anchor="end">${m}%</text>`).join("")}<text x="${L}" y="${h-8}">Doanh thu tuần →</text><text x="${X(SC.median_r)+4}" y="${Tp+10}" style="fill:var(--warn-ink)">trung vị</text><text x="${w-R}" y="${Y(SC.margin_good)-4}" text-anchor="end" style="fill:var(--good-ink)">margin ${SC.margin_good}%</text>
      ${rows.map(x=>`<circle data-sku="${x.sku}" cx="${X(x.r)}" cy="${Y(x.margin)}" r="${4+Math.min(6,x.r/mxr*8)}" fill="${CCOL[x.cls]}" fill-opacity=".72" stroke="var(--card)" style="cursor:pointer"><title>${esc(x.sku)} · ${esc(x.name)}\nDT ${USD(x.r)} · margin ${PCT(x.margin)}\n${SC.classes[x.cls].name}</title></circle>`).join("")}</svg>`}
    html+=sec("03","Phân loại SKU","doanh thu × margin → hành động",`<div class="pro-grid g2"><div class="chartbox">${scatter()}</div><div class="card"><h3>Hành động theo nhóm</h3>${Object.keys(SC.classes).filter(k=>SC.counts[k]).map(k=>`<div style="margin:0 0 10px"><span class="stt" style="color:${CCOL[k]};background:color-mix(in srgb,${CCOL[k]} 14%,transparent)">${SC.classes[k].name} · ${SC.counts[k]} SKU</span><div style="font-size:12.5px;color:var(--ink-2);margin-top:4px">${esc(SC.classes[k].action)}</div></div>`).join("")}</div></div>
      <div class="pchips" id="mg-sf" style="margin-top:14px"><button data-k="all" aria-pressed="true">Tất cả (${SC.rows.length})</button>${Object.keys(SC.classes).filter(k=>SC.counts[k]).map(k=>`<button data-k="${k}" aria-pressed="false">${SC.classes[k].name} (${SC.counts[k]})</button>`).join("")}</div>
      <div class="scroll"><table id="mg-sku"><thead><tr><th>SKU</th><th>Tên</th><th>Doanh thu</th><th>Margin</th><th>4 tuần</th><th>Tồn (tuần)</th><th>Nhóm</th></tr></thead><tbody></tbody></table></div>`,
      `Mốc phân loại: doanh thu từ trung vị ${USD(SC.median_r)} trở lên là “bán nhiều”; margin từ ${SC.margin_good}% trở lên là “tốt”. Cột “4 tuần” so doanh thu 4 tuần gần nhất với 4 tuần trước đó. SKU chưa có công thức phí không được xếp loại margin.`);
    const fl=(k)=>P.ads.filter(a=>k==="all"||a.st===k).length;
    html+=sec("04","Dư địa quảng cáo","TACoS so với ngưỡng hoà vốn",`<div class="pchips" id="mg-af">${[["all","Tất cả"],["pre",STT.pre],["over",STT.over],["tight",STT.tight],["room",STT.room]].map(([k,l],i)=>`<button data-k="${k}" aria-pressed="${i===0}">${l} (${fl(k)})</button>`).join("")}</div><div class="scroll"><table id="mg-ads"><thead><tr><th>Nhóm</th><th>Kênh</th><th>Doanh thu</th><th>TACoS</th><th>Hoà vốn</th><th>Dư địa (pp)</th><th>Trạng thái</th></tr></thead><tbody></tbody></table></div>`,
      `<b>TACoS hoà vốn</b> = tỷ lệ chi quảng cáo trên doanh thu mà tại đó lợi nhuận về 0 (= margin hiện tại + tỷ lệ quảng cáo). “Biên trước QC chưa dương” nghĩa là chưa có dư địa để chi quảng cáo: ưu tiên chỉnh giá/giá vốn/vận chuyển, giữ quảng cáo ở mức tối thiểu. “Còn dư địa” là nơi nên thử tăng ngân sách có kiểm soát (mục tiêu margin ${P.target_margin}%).`);
    html+=sec("05","Mức độ tập trung doanh thu","Pareto SKU · HHI",`<div class="pro-grid g2"><div class="chartbox">${paretoChart(PA.curve,PA.n80)}</div><div>
      <div class="pro-grid" style="grid-template-columns:repeat(2,1fr);margin-bottom:12px">${tile("Top 5 SKU",PCT(PA.top5,0),"tổng doanh thu tuần")}${tile("Top 10 SKU",PCT(PA.top10,0),PA.n80+"/"+PA.n+" SKU tạo 80%","var(--s4)")}</div>
      <div class="scroll"><table><thead><tr><th>SKU</th><th>Tên</th><th>Doanh thu</th><th>%</th></tr></thead><tbody>${PA.top.map(x=>`<tr style="cursor:pointer" data-sku="${x.sku}"><td><b>${x.sku}</b></td><td>${esc(x.name)}</td><td>${USD(x.r)}</td><td>${PCT(x.share)}</td></tr>`).join("")}</tbody></table></div></div></div>
      <div class="pchips" style="margin-top:12px"><span class="chip">HHI sàn: ${N(PA.hhi_mp)} · ${PA.hhi_mp>2500?"tập trung cao":PA.hhi_mp>1500?"tập trung vừa":"phân tán"} (lớn nhất: ${esc(PA.top_mp[0])} ${PCT(PA.top_mp[1],0)})</span><span class="chip">HHI nhóm: ${N(PA.hhi_grp)} · ${PA.hhi_grp>2500?"tập trung cao":PA.hhi_grp>1500?"tập trung vừa":"phân tán"} (lớn nhất: ${esc(SH(PA.top_grp[0]))} ${PCT(PA.top_grp[1],0)})</span></div>`,
      "Doanh thu càng dồn vào ít SKU/sàn thì rủi ro càng lớn khi một SKU hết hàng, bị hạ listing hoặc một sàn đổi chính sách. HHI dưới 1.500 là phân tán, trên 2.500 là tập trung cao.");
    const mxb=Math.max(...I.bins,1);
    html+=sec("06","Rủi ro tồn kho","số tuần bán được theo tốc độ hiện tại",`<div class="pro-grid g2"><div class="card"><h3>Phân bố SKU theo độ phủ tồn</h3>${I.bins.map((v,i)=>`<div class="hl"><span>${I.labels[i]}</span><div class="bar2"><i style="width:${v/mxb*100}%;background:${["var(--bad)","var(--warn)","var(--good)","var(--s7)","var(--muted)"][i]}"></i></div><b>${v} SKU</b></div>`).join("")}
      <div class="pchips" style="margin-top:10px"><span class="chip">Tồn kho tổng: ${N(I.units)} sản phẩm</span><span class="chip">Chưa có đơn: ${N(I.dead_units)} sản phẩm / ${I.dead_n} SKU</span><span class="chip">FBA &gt; 270 ngày: ${N(I.lt_over270)}</span></div></div>
      <div class="scroll"><table><thead><tr><th>SKU cần bổ sung</th><th>Tồn</th><th>Bán/tuần</th><th>Đủ (tuần)</th></tr></thead><tbody>${I.low.map(s=>`<tr style="cursor:pointer" data-sku="${s.sku}"><td><b>${s.sku}</b> <small style="color:var(--muted)">${esc(SH(s.grp))}</small></td><td>${N(s.qty)}</td><td>${N(s.sold)}</td><td><b>${N(s.weeks,1)}</b></td></tr>`).join("")||'<tr><td colspan="4">Không có SKU nào dưới 6 tuần</td></tr>'}</tbody></table></div></div>`,
      "Quy tắc thực hành: lead time nhập hàng + 2 tuần an toàn là mức tối thiểu. SKU dưới mức này nên giảm quảng cáo hoặc chốt ngày hàng về; phần tồn không có đơn nên xử lý (giá, khuyến mãi, listing) trước khi phát sinh phí lưu kho dài hạn.");
    html+=sec("07","Giá bán thực hiện","so với trung bình 4 tuần trước",P.price.length?`<div class="scroll"><table><thead><tr><th>SKU</th><th>Tên</th><th>Kênh</th><th>ASP tuần</th><th>TB 4 tuần</th><th>Chênh</th><th>SL</th></tr></thead><tbody>${P.price.map(x=>`<tr style="cursor:pointer" data-sku="${x.sku}"><td><b>${x.sku}</b></td><td>${esc(x.name)}</td><td>${x.mp} ${x.cty}</td><td>${N(x.asp,2)} ${x.cur}</td><td>${N(x.avg4,2)}</td><td style="color:${x.chg<0?"var(--bad-ink)":"var(--good-ink)"}"><b>${x.chg>0?"+":""}${N(x.chg,1)}%</b></td><td>${x.q}</td></tr>`).join("")}</tbody></table></div>`:'<p class="cap">Không có SKU nào lệch giá từ 5% trở lên.</p>',
      "Giá bán thấp hơn nền 4 tuần có thể do khuyến mãi chủ động hoặc bị đối thủ kéo giá. Cần phân biệt hai trường hợp trước khi điều chỉnh, vì chúng kéo margin theo hai hướng khác nhau.");
    html+=sec("08","Sức khỏe dữ liệu","độ tin cậy của báo cáo",`<div class="card">${P.health.map(h=>`<div class="hl hl3"><span>${esc(h.k)}</span><b style="color:${h.ok?"var(--good-ink)":"var(--warn-ink)"}">${h.ok?"✓":"!"} ${esc(h.v)}</b><span style="color:var(--muted);font-size:12px">${esc(h.hint||"")}</span></div>`).join("")}</div>`);
    html+=sec("09","Mô phỏng giá &amp; quảng cáo","What-if theo cấu trúc phí hiện có",`<div id="wi-host"></div>`,"Kéo thanh giá hoặc chi quảng cáo để xem margin thay đổi thế nào trước khi quyết định nâng giá hay giảm quảng cáo. Có thể chọn cả danh mục, một nhóm, hoặc một mã SKU.");
    panel.innerHTML=html;wiMount();
    // lọc bảng dư địa
    const tb=$("#mg-ads tbody");let flt="all";
    function paintAds(){tb.innerHTML=P.ads.filter(a=>flt==="all"||a.st===flt).map(a=>`<tr style="cursor:pointer" data-grp="${esc(a.grp)}"><td>${esc(SH(a.grp))}</td><td>${a.mp} ${a.cty}</td><td>${USD(a.r)}</td><td>${PCT(a.tacos)}</td><td>${PCT(a.breakeven)}</td><td>${(a.headroom>0?"+":"")+N(a.headroom,1)}</td><td>${stt(a.st)}</td></tr>`).join("")||'<tr><td colspan="7">Không có cụm nào</td></tr>'}
    $$("#mg-af button").forEach(x=>x.onclick=()=>{flt=x.dataset.k;$$("#mg-af button").forEach(y=>y.setAttribute("aria-pressed",y===x));paintAds()});paintAds();
    const tbs=$("#mg-sku tbody");let cf="all";
    function paintSku(){tbs.innerHTML=SC.rows.filter(x=>cf==="all"||x.cls===cf).map(x=>`<tr style="cursor:pointer" data-sku="${x.sku}"><td><b>${x.sku}</b></td><td>${esc(x.name)}</td><td>${USD(x.r)}</td><td>${x.margin==null?"—":PCT(x.margin)}</td><td>${x.trend4==null?"—":(x.trend4>0?"+":"")+x.trend4+"%"}</td><td>${x.stock==null?"—":N(x.stock)+(x.weeks!=null?" ("+N(x.weeks,1)+")":"")}</td><td><span class="stt" style="color:${CCOL[x.cls]};background:color-mix(in srgb,${CCOL[x.cls]} 14%,transparent)">${SC.classes[x.cls].name}</span></td></tr>`).join("")}
    $$("#mg-sf button").forEach(x=>x.onclick=()=>{cf=x.dataset.k;$$("#mg-sf button").forEach(y=>y.setAttribute("aria-pressed",y===x));paintSku()});paintSku();
    panel.addEventListener("click",e=>{const r=e.target.closest("[data-sku],[data-grp]");if(!r)return;r.dataset.sku?drillSku(r.dataset.sku):drillGrp(r.dataset.grp)});
    enhance();
  };
})();

/* ---------- Liên kết sâu từ app: #mg, #sku=CODE, #grp=NHÓM ---------- */
function hashGo(){const h=decodeURIComponent(location.hash.slice(1));if(!h)return;
  if(h==="mg"){activate("mg");return}
  const m=h.match(/^(sku|grp)=(.+)$/);if(!m)return;if(m[1]==="sku"&&skuSet.has(m[2]))drillSku(m[2]);else if(m[1]==="grp"&&D.meta.groups.includes(m[2]))drillGrp(m[2])}
setTimeout(()=>{try{hashGo()}catch(e){}},400);window.addEventListener("hashchange",hashGo);

/* ---------- Tìm kiếm / lệnh (Ctrl+K) ---------- */
let items=[],sel=0;
function buildIndex(){
  const tabs=$$(".tab").map(t=>({t:"Tab",l:t.textContent.trim(),do:()=>{closeAll();activate(t.dataset.p);scrollTo({top:0,behavior:"smooth"})}}));
  const grps=(D.meta.groups||[]).map(g=>({t:"Nhóm",l:SH(g),s:g,do:()=>drillGrp(g)}));
  const skus=(D.sku_meta||[]).map(m=>({t:"SKU",l:m.sku+" — "+(m.name||""),s:SH(m.grp||""),do:()=>drillSku(m.sku)}));
  const acts=[{t:"Lệnh",l:"Đổi giao diện sáng / tối",do:()=>{closeAll();cycleTheme()}},{t:"Lệnh",l:"In / lưu PDF bản điều hành",do:()=>{closeAll();printPS()}},{t:"Lệnh",l:"Sao chép tóm tắt để gửi",do:()=>{closeAll();$("#pro-copy").click()}},{t:"Lệnh",l:"Tải bản HTML",do:()=>{closeAll();$("#pro-dl").click()}}];
  items=[...acts,...tabs,...grps,...skus].map(x=>({...x,k:nrm(x.l+" "+(x.s||""))}));
}
function paintRes(){const q=nrm($("#pro-q").value).trim().split(/\s+/).filter(Boolean);
  const r=items.filter(x=>q.every(w=>x.k.includes(w))).slice(0,40);sel=0;$("#pro-res").innerHTML=r.map((x,i)=>`<li data-i="${i}" aria-selected="${i===0}"><span class="t">${x.t}</span><span>${esc(x.l)}</span>${x.s?`<small>${esc(x.s)}</small>`:""}</li>`).join("")||'<li><span class="t"></span>Không có kết quả</li>';
  $$("#pro-res li[data-i]").forEach(li=>{li.onclick=()=>run(r[+li.dataset.i]);li.onmouseenter=()=>{sel=+li.dataset.i;mark()}});pal._r=r}
function mark(){$$("#pro-res li[data-i]").forEach((li,i)=>li.setAttribute("aria-selected",i===sel));const a=$("#pro-res li[aria-selected=true]");a&&a.scrollIntoView({block:"nearest"})}
function run(x){if(x){closeAll();setTimeout(x.do,10)}}
function openPal(){if(!items.length)buildIndex();closeAll();ov.classList.add("on");pal.classList.add("on");$("#pro-q").value="";paintRes();$("#pro-q").focus()}
$("#pro-q").addEventListener("input",paintRes);
$("#pro-q").addEventListener("keydown",e=>{const n=(pal._r||[]).length;if(e.key==="ArrowDown"){sel=Math.min(n-1,sel+1);mark();e.preventDefault()}else if(e.key==="ArrowUp"){sel=Math.max(0,sel-1);mark();e.preventDefault()}else if(e.key==="Enter"){run((pal._r||[])[sel])}});
$("#pro-s").onclick=openPal;

/* ---------- Bảng: sắp xếp, xuất CSV, bấm SKU/nhóm để xem chi tiết ---------- */
const skuSet=new Set((D.sku_meta||[]).map(m=>m.sku)),grpMap=new Map();(D.meta.groups||[]).forEach(g=>{grpMap.set(g,g);grpMap.set(SH(g),g)});
function num(t){t=String(t).replace(/[\s$%×x▲▼+]/g,"").replace(/−/g,"-");if(!/\d/.test(t))return NaN;if(t.includes(","))t=t.replace(/\./g,"").replace(",",".");else if(/^-?\d{1,3}(\.\d{3})+$/.test(t))t=t.replace(/\./g,"");const m=t.match(/-?\d+(\.\d+)?/);return m?parseFloat(m[0]):NaN}
function sortTable(tb,idx,dir){const body=tb.tBodies[0];if(!body)return;const rows=Array.from(body.rows);if(rows.some(r=>r.cells.length!==tb.tHead.rows[0].cells.length))return;
  const v=rows.map(r=>r.cells[idx].textContent.trim()),isNum=v.filter(t=>!isNaN(num(t))).length>=v.length*.6;
  rows.sort((a,b)=>{const x=a.cells[idx].textContent.trim(),y=b.cells[idx].textContent.trim();const c=isNum?((isNaN(num(x))?-Infinity:num(x))-(isNaN(num(y))?-Infinity:num(y))):x.localeCompare(y,"vi");return dir==="asc"?c:-c});rows.forEach(r=>body.appendChild(r))}
function toCSV(tb){const rows=[];const row=r=>Array.from(r.cells).map(c=>'"'+c.textContent.replace(/\s+/g," ").trim().replace(/"/g,'""')+'"').join(",");
  if(tb.tHead)Array.from(tb.tHead.rows).forEach(r=>rows.push(row(r)));Array.from(tb.tBodies).forEach(b=>Array.from(b.rows).forEach(r=>rows.push(row(r))));if(tb.tFoot)Array.from(tb.tFoot.rows).forEach(r=>rows.push(row(r)));return"﻿"+rows.join("\r\n")}
function reorderCol(){
  const R=P.reorder||{};const tb=document.getElementById("tbl-invsku");if(!tb||!tb.tHead)return;
  const host=tb.closest(".scroll")||tb;
  if(!Object.keys(R).length){if(!document.getElementById("ro-banner")&&host.parentElement){const b=document.createElement("div");b.id="ro-banner";b.className="card";b.style.cssText="margin:0 0 10px;padding:10px 14px;font-size:13px;border-left:3px solid var(--warn)";b.textContent="Chưa tính được điểm đặt hàng"+(P.reorder_err?" ("+P.reorder_err+")":"")+". Mở app → 📥 Đầu vào để kiểm tra, hoặc xem cửa sổ chạy server.py.";host.parentElement.insertBefore(b,host)}return}
  if(!document.getElementById("ro-banner")&&host.parentElement){const v=Object.values(R),n1=v.filter(x=>x.st==="now").length,n2=v.filter(x=>x.st==="soon").length,sim=v.some(x=>x.sim);
    const b=document.createElement("div");b.id="ro-banner";b.className="card";b.style.cssText="margin:0 0 10px;padding:10px 14px;font-size:13px;border-left:3px solid var(--warn)";
    b.innerHTML=`<b>Điểm đặt hàng theo lead time:</b> ${n1} SKU cần đặt ngay, ${n2} SKU sắp tới điểm đặt. Trong cột <b>Trạng thái</b> bên dưới, mỗi SKU có thêm dòng nhỏ: điểm đặt · lead time · số lượng đề xuất · ngày nên đặt trước.${sim?" <span style='color:var(--warn)'>Lead time/MOQ đang là số giả lập (dấu *)</span> — nhập số thật ở app → 📥 Đầu vào.":""}`;host.parentElement.insertBefore(b,host)}
  const CL={now:["Đặt ngay","var(--bad)"],soon:["Sắp tới","var(--warn)"]};
  $$("tbody tr",tb).forEach(tr=>{const c=tr.cells;if(c.length<12||tr.querySelector(".ro"))return;const r=R[c[0].textContent.trim()];const td=c[c.length-1];const d=document.createElement("div");d.className="ro";d.style.cssText="font-size:11px;margin-top:3px;white-space:nowrap";
    if(!r)return;const k=CL[r.st];
    d.innerHTML=(k?`<span class="stt" style="color:${k[1]};background:color-mix(in srgb,${k[1]} 14%,transparent)">${k[0]} · đặt ${r.qty}</span><br>`:"")+`<span style="color:var(--muted)">điểm đặt ${r.rop} · LT ${Math.round(r.lead)}d${r.sim?"*":""}${k&&r.by?" · trước "+r.by.slice(5):""}</span>`;
    td.appendChild(d)});
}
function enhance(){
  reorderCol();
  $$("table").forEach(tb=>{
    if(!tb.dataset.pro&&tb.tHead&&tb.tHead.rows.length===1&&tb.closest(".panel")){tb.dataset.pro=1;
      Array.from(tb.tHead.rows[0].cells).forEach((th,i)=>{th.classList.add("srt");th.title="Bấm để sắp xếp";th.addEventListener("click",()=>{const d=th.classList.contains("asc")?"desc":"asc";Array.from(tb.tHead.rows[0].cells).forEach(x=>x.classList.remove("asc","desc"));th.classList.add(d);sortTable(tb,i,d)})});
      const host=tb.closest(".scroll")||tb;if(host.parentElement&&!host.parentElement.classList.contains("pro-grid")&&!(host.previousElementSibling&&host.previousElementSibling.classList.contains("tbtools"))){const t=el('<div class="tbtools"><button class="pbtn" type="button">⤓ CSV</button></div>');$("button",t).onclick=()=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([toCSV(tb)],{type:"text/csv;charset=utf-8"}));a.download=(tb.id||"bang")+".csv";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),3000)};host.before(t)}}
    $$("tbody td",tb).forEach(td=>{if(td.classList.contains("drill")||td.children.length>2)return;const t=td.textContent.trim();if(t.length>90||!t)return;const g=grpMap.get(t);if(skuSet.has(t)){td.classList.add("drill");td.dataset.dsku=t}else if(g){td.classList.add("drill");td.dataset.dgrp=g}})});
}
document.addEventListener("click",e=>{const c=e.target.closest("td.drill");if(!c)return;c.dataset.dsku?drillSku(c.dataset.dsku):drillGrp(c.dataset.dgrp)});
let tmr;new MutationObserver(()=>{clearTimeout(tmr);tmr=setTimeout(enhance,300)}).observe($(".wrap:last-of-type")||document.body,{childList:true,subtree:true});
enhance();
})();
