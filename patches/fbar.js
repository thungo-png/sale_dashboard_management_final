// ============ BO LOC GON: chuyen hang nut .pick thanh dropdown (fbar) ============
(function(){
  const LAB={ovgran:"Độ chi tiết",ovmetric:"Chỉ số",ovdim:"Phân tách",grgran:"Độ chi tiết",grmetric:"Chỉ số",grpick:"Nhóm sản phẩm",
    gdgran:"Độ chi tiết",gdmetric:"Chỉ số",gddim:"Phân tách",cmpgrp:"Nhóm sản phẩm",cmpmp:"Sàn",cmpcty:"Thị trường",cmpmetric:"Chỉ số",
    dtpick:"Sàn & thị trường",sklv:"Cấp độ",skgran:"Độ chi tiết",skmetric:"Chỉ số","campthupick|m":"Sàn","campthupick|g":"Nhóm sản phẩm",
    invdpick:"Thị trường",invstpick:"Trạng thái tồn",ltpick:"Kênh lưu kho",iaccpick:"Tài khoản","b-mppick":"Sàn · thị trường","b-asppick":"Nhóm sản phẩm",
    scpick:"Nhóm sản phẩm",mcacct:"Tài khoản",ttfilter:"Lọc việc"};
  const TOGGLE=new Set(["campthupick","b-asppick","i-asppick"]);
  const ids=[...document.querySelectorAll(".pickrow[id]")].map(e=>e.id).filter(id=>id in LAB||Object.keys(LAB).some(k=>k.startsWith(id+"|")));
  const txt=b=>{const c=b.cloneNode(true);const sm=c.querySelector("small");const s=sm?sm.textContent.trim():"";if(sm)sm.remove();const t=c.textContent.replace(/\s+/g," ").trim();return s?t+" ("+s+")":t;};
  const attrOf=b=>{for(const a of b.attributes){if(a.name.startsWith("data-"))return a.name.slice(5);}return "k";};
  const bars=new Map();
  function barFor(host){
    // gom cac pickrow lien tiep nhau vao cung 1 thanh loc
    let prev=host.previousElementSibling;
    while(prev&&prev.classList.contains("pickrow")&&prev.classList.contains("fb-hidden")) prev=prev.previousElementSibling;
    if(prev&&prev.classList.contains("fbar")) return prev;
    const bar=document.createElement("div"); bar.className="fbar"; host.parentNode.insertBefore(bar,host); return bar;
  }
  function build(id){
    const host=document.getElementById(id); if(!host) return;
    const btns=[...host.querySelectorAll("button.pick")];
    if(!bars.has(id)){ const bar=barFor(host); bars.set(id,{bar,sels:{}}); host.classList.add("fb-hidden"); bar.after(host); }
    const st=bars.get(id);
    const groups={}; btns.forEach(b=>{const a=attrOf(b);(groups[a]=groups[a]||[]).push(b);});
    Object.keys(st.sels).forEach(a=>{if(!groups[a]){st.sels[a].remove();delete st.sels[a];}});
    Object.entries(groups).forEach(([a,list])=>{
      let w=st.sels[a];
      if(!w){ w=document.createElement("label"); w.className="fsel"; w.innerHTML=`<span></span><select></select>`; st.bar.appendChild(w); st.sels[a]=w;
        w.querySelector("select").addEventListener("change",e=>{
          const v=e.target.value, cur=[...host.querySelectorAll("button.pick")].filter(b=>attrOf(b)===a);
          if(v==="__all__"){const on=cur.find(b=>b.getAttribute("aria-pressed")==="true"); if(on) on.click(); return;}
          const t=cur[+v]; if(t&&t.getAttribute("aria-pressed")!=="true") t.click();
        });}
      w.querySelector("span").textContent=LAB[id+"|"+a]||LAB[id]||"Lọc";
      const sel=w.querySelector("select"); const on=list.findIndex(b=>b.getAttribute("aria-pressed")==="true");
      const addAll=TOGGLE.has(id)||on<0;
      sel.innerHTML=(addAll?`<option value="__all__">Tất cả</option>`:"")+list.map((b,i)=>`<option value="${i}">${txt(b).replace(/</g,"&lt;")}</option>`).join("");
      sel.value=on>=0?String(on):"__all__";
      w.classList.toggle("on",on>=0&&addAll);
      w.style.display=list.length?"":"none";
    });
  }
  ids.forEach(id=>{const host=document.getElementById(id); build(id);
    new MutationObserver(()=>build(id)).observe(host,{childList:true,subtree:true,attributes:true,attributeFilter:["aria-pressed"]});});
})();