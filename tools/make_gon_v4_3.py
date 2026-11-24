"""Gọn v4 – chỉnh nhỏ (lần 3): bỏ tiêu đề + nhãn "Báo cáo cấp CEO" + dòng "n kênh có dữ liệu" ở đầu Tổng quan;
   thay hàng chip kỳ/thời gian bằng một ô chọn khoảng ngày (7 / 14 / 30 / 90 ngày / chọn ngày).
   Ô này điều khiển biểu đồ "Diễn biến theo thời gian" và dòng tổng doanh thu/số lượng (dữ liệu ngày có 84 ngày gần nhất).
   Dùng: python3 make_gon_v4_3.py vào.html ra.html (đã áp make_gon_v4_2). Không đụng dòng const D, không xoá id."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
dl=[l for l in s.split("\n") if l.startswith("const D = ")]
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
i=s.index('document.getElementById("mmeta").innerHTML=`'); j=s.index('`;',i)+2
new='''document.getElementById("mmeta").innerHTML=`
 <select id="rng" aria-label="Khoảng ngày" title="Khoảng ngày cho biểu đồ Diễn biến theo thời gian và dòng tổng bên cạnh. PL5, quảng cáo, tồn kho giữ theo kỳ báo cáo.">
  <option value="7">7 ngày (kỳ báo cáo W${D.meta.week_no})</option><option value="14">14 ngày</option><option value="30">30 ngày</option><option value="90">90 ngày</option><option value="c">Chọn ngày…</option></select>
 <span id="rngc" hidden><input type="date" id="rngf" aria-label="Từ ngày"> – <input type="date" id="rngt" aria-label="Đến ngày"></span>
 <span id="rngsum" class="rngsum"></span>`;
(function(){
  const FULLD=D.ts_labels.D.slice(), mps=Object.keys(D.ts_ov.D.mp), fm=x=>x.split("-").reverse().join("/");
  const sumR=(a,b)=>{const o={r:0,q:0,rfc:0};for(let k=a;k<=b;k++){mps.forEach(m=>{const c=D.ts_ov.D.mp[m][FULLD[k]];if(c){o.r+=c.r||0;o.q+=c.q||0;o.rfc+=c.rfc||0;}});}return o;};
  const sg=p=>(p>=0?"+":"−")+Math.abs(p).toFixed(1).replace(".",",")+"%";
  let first=true;
  function apply(a,b,def){
    a=Math.max(0,a);b=Math.min(FULLD.length-1,b);if(b<a)return;
    const n=b-a+1,cur=sumR(a,b);let t=fm(FULLD[a])+" – "+fm(FULLD[b])+" · "+n+" ngày · $"+N(cur.r)+" · "+N(cur.q)+" sản phẩm";
    if(cur.rfc>0)t+=" · đạt "+Math.round(cur.r/cur.rfc*100)+"% FC";
    if(a-n>=0){const pv=sumR(a-n,a-1);if(pv.r>0)t+=" · "+sg((cur.r/pv.r-1)*100)+" so với "+n+" ngày trước";}
    document.getElementById("rngsum").textContent=t;
    if(first)return;
    if(def){D.ts_labels.D=FULLD.slice();OVG="W";}else{D.ts_labels.D=FULLD.slice(a,b+1);OVG="D";}
    ovTrend();
  }
  const sel=document.getElementById("rng"),box=document.getElementById("rngc"),f=document.getElementById("rngf"),t=document.getElementById("rngt");
  f.min=t.min=FULLD[0];f.max=t.max=FULLD[FULLD.length-1];f.value=FULLD[Math.max(0,FULLD.length-30)];t.value=FULLD[FULLD.length-1];
  function go(){
    if(sel.value==="c"){box.hidden=false;const a=FULLD.indexOf(f.value),b=FULLD.indexOf(t.value);if(a>=0&&b>=a)apply(a,b,false);return;}
    box.hidden=true;const n=+sel.value;apply(FULLD.length-n,FULLD.length-1,n===7);
  }
  sel.addEventListener("change",go);f.addEventListener("change",go);t.addEventListener("change",go);
  apply(FULLD.length-7,FULLD.length-1,true);first=false;
})();'''
s=s[:i]+new+s[j:]
rep1('`12 tuần gần nhất theo từng ngày.`','`${D.ts_labels.D.length} ngày, theo từng ngày (tối đa 84 ngày gần nhất).`')
rep1('.xc{}\n','.xc{}\n.mast .eyebrow,.mast h1,#p-ov>.plvl:first-child,#ovhint{display:none}.mast{padding-bottom:0}.meta{align-items:center}.meta select,.meta input[type=date]{font:inherit;font-size:13px;padding:5px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}.meta select{font-weight:600}.rngsum{font-size:12.5px;color:var(--ink-2,var(--muted))}\n')
assert [l for l in s.split("\n") if l.startswith("const D = ")]==dl
open(sys.argv[2],"w",encoding="utf-8").write(s)
