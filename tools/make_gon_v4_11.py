"""Gọn v4 – lần 11: thẻ "Hiệu quả quảng cáo" có nút chuyển Theo kênh / Theo quốc gia.
   Theo quốc gia = gộp các kênh cùng thị trường (US/CAN/AUS): Chi phí, tỷ trọng chi phí, TACoS, ROAS; theo ô chọn khoảng ngày như bản theo kênh.
   Dùng: python3 make_gon_v4_11.py vào.html ra.html (đã áp make_gon_v4_10). Không đụng const D, không xoá id."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
def rep1(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]); s=s.replace(a,b)
i=s.index('    h+=`<div class="dc"><h3>Hiệu quả quảng cáo theo kênh</h3>`'); j=s.index('    // cảnh báo\n',i)
old=s[i:j]
# phần thân bảng theo kênh giữ nguyên: lấy từ sau <h3> tới hết
body_start=old.index('`+(ad.length?')
chan=old[body_start:old.rindex("+more(")]   # '`+(ad.length? ... )' biểu thức nối chuỗi theo kênh
new='''    const adHtml=()=>{
      const mode=window.__ADV==="cty"?"cty":"ch";
      const tb=`<span class="pk" id="adv"><button type="button" data-m="ch" aria-pressed="${mode==="ch"}">Theo kênh</button><button type="button" data-m="cty" aria-pressed="${mode==="cty"}">Theo quốc gia</button></span>`;
      let inner;
      if(mode==="ch"){ inner=''' + chan.lstrip('`+')  + ''';
      }else{
        const G={};
        ad.forEach(a=>{const o=G[a.cty]||(G[a.cty]={sp:0,spR:0,rv:0,spS:0,sa:0,miss:[],n:0});
          if(a.na){o.miss.push(a.mp);return}
          const sa=adR?(a.roas||0)*a.spend:(a.whl||0), rv=adR?(a.tacos?a.spend/a.tacos*100:0):(a.rev||0);
          o.sp+=a.spend;o.n++; if(rv>0){o.spR+=a.spend;o.rv+=rv} if(sa>0){o.spS+=a.spend;o.sa+=sa}});
        const ks=Object.keys(G).sort((x,y)=>G[y].sp-G[x].sp), tot=ks.reduce((t,k)=>t+G[k].sp,0);
        inner=ks.length?`<table class="dt2"><thead><tr><th>Quốc gia</th><th>Chi phí</th><th>Tỷ trọng</th><th>TACoS</th><th>ROAS</th></tr></thead><tbody>${ks.map(k=>{const o=G[k],tc=o.rv>0?o.spR/o.rv*100:null,ro=o.spS>0?o.sa/o.spS:null,full=(CTYN&&CTYN[k])||k;
          return `<tr><td title="${full}${o.miss.length?" · thiếu dữ liệu: "+o.miss.join(", "):""}">${k}${o.miss.length?" *":""}</td><td>${o.n?U(o.sp):"—"}</td><td>${o.n&&tot?pc0(o.sp/tot*100):"—"}</td><td class="${tc==null?"":(tc>15?"b":(tc>10?"m":"g"))}">${tc==null?"—":pc0(tc)}</td><td class="${ro==null?"":(ro>=5?"g":(ro>=3?"m":"b"))}">${ro==null?"—":String(ro.toFixed(1)).replace(".",",")}</td></tr>`}).join("")}</tbody></table><div class="note">Gộp các kênh cùng quốc gia. TACoS tính trên doanh thu của kênh có quảng cáo; "—" = chưa có doanh thu quảng cáo/ghi nhận để tính${ks.some(k=>G[k].miss.length)?"; * thiếu dữ liệu ở một số kênh trong "+rngLab:""}.</div>`:'<div class="note">Chưa có dữ liệu quảng cáo.</div>';
      }
      return `<h3>Hiệu quả quảng cáo${tb}</h3><div id="adbody">${inner}</div>`+more("Xem tất cả","cp");
    };
    h+=`<div class="dc" id="adcard">${adHtml()}</div>`;
'''
s=s[:i]+new+s[j:]
rep1('    host.innerHTML=h;\n','''    host.innerHTML=h;
    const wireAd=()=>{const c=host.querySelector("#adcard");if(!c)return;
      c.querySelectorAll("#adv button").forEach(b=>b.addEventListener("click",()=>{window.__ADV=b.dataset.m;c.innerHTML=adHtml();wireAd()}));
      c.querySelectorAll("[data-go]").forEach(a=>a.addEventListener("click",()=>{activate(a.dataset.go);window.scrollTo({top:0,behavior:"smooth"})}))};
    wireAd();
''')
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
