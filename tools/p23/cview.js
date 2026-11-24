/* ===== Gọn v4.2 (nâng cấp): chọn quốc gia → cả báo cáo đổi theo =====
   D0 = số liệu gốc (toàn danh mục, không bao giờ bị sửa). applyCty(c) dựng lại D.* cho một quốc gia từ các chuỗi đã có
   quốc gia sẵn trong D (ts_ov, ts_grpcell, ts_sku, pl5ts, cell, sku, pl5.rows ...). c="" → trả về số gốc. */
(function(){
  const KEYS=["cell","cell_prev","ytd","bygrp","bygrp_prev","bygrp_cell","sku","weekly_grp","monthly","quarterly","weekfc","adsum","campthu","tacos",
    "dgmk_room","grpcmp","askuw_mp","top_sku2","ts_ov","ts_grp","ts_grpcell","ts_sku","pl5","pl5ts","ads_daily","invdet","invacct","lt","amzmkt"];
  const D0={}; KEYS.forEach(k=>D0[k]=D[k]); window.D0=D0;
  const GRPS=(D.meta&&D.meta.groups)||[];
  const skuGrp={}; (D.sku_meta||[]).forEach(m=>skuGrp[m.sku]=m.grp);
  const sepn=" · ";
  const endsC=(k,c)=>k.endsWith(sepn+c), head=(k,c)=>k.slice(0,k.length-(sepn+c).length);
  const addO=(a,b)=>{const o={...a};for(const k in b)if(typeof b[k]==="number")o[k]=(o[k]||0)+b[k];return o};
  const addA=(a,b)=>a.map((v,i)=>(+v||0)+(+b[i]||0));
  const sum=(a,b)=>Array.isArray(a)?addA(a,b):addO(a,b);
  const num=v=>+v||0, rnd=v=>Math.round(v*100)/100;
  function derive(src,pred,keyFn){        // gộp các chuỗi {kỳ: số} theo khóa mới
    const o={}; for(const k in (src||{})){ if(!pred(k))continue; const nk=keyFn(k), s=src[k];
      if(!o[nk]){o[nk]=s;continue}
      const t={}; new Set([...Object.keys(o[nk]),...Object.keys(s)]).forEach(p=>{t[p]=(o[nk][p]&&s[p])?sum(o[nk][p],s[p]):(o[nk][p]||s[p])}); o[nk]=t }
    return o;
  }
  const filt=(src,pred)=>{const o={};for(const k in (src||{}))if(pred(k))o[k]=src[k];return o};
  const ratio=(f,o)=>o>0?f/o:0;

  function build(c){
    const R={};
    const L=a=>(a||[]).filter(x=>x.cty===c);
    ["cell","cell_prev","ytd","bygrp_cell","sku","adsum","campthu","tacos","askuw_mp"].forEach(k=>R[k]=L(D0[k]));
    R.dgmk_room=filt(D0.dgmk_room,k=>k.split("|")[1]===c);
    R.grpcmp={...D0.grpcmp,rows:L(D0.grpcmp&&D0.grpcmp.rows)};
    R.ads_daily={...D0.ads_daily,cov:filt(D0.ads_daily&&D0.ads_daily.cov,k=>k.endsWith("|"+c)),d:filt(D0.ads_daily&&D0.ads_daily.d,k=>k.endsWith("|"+c))};
    /* chuỗi thời gian */
    const ov={}; for(const lv in D0.ts_ov){const s=D0.ts_ov[lv];
      const mpcty=filt(s.mpcty,k=>endsC(k,c)); ov[lv]={mpcty,mp:derive(mpcty,()=>true,k=>head(k,c)),cty:{[c]:(s.cty&&s.cty[c])||{}}}}
    R.ts_ov=ov;
    const sg={},sk={},gc={}; for(const lv in D0.ts_grpcell){
      const gcty=filt(D0.ts_grpcell[lv].grp_cty,k=>endsC(k,c)); sg[lv]={}; GRPS.forEach(g=>sg[lv][g]={}); Object.keys(gcty).forEach(k=>sg[lv][head(k,c)]=gcty[k]);
      const l3=filt(D0.ts_sku[lv].l3,k=>k.endsWith(sepn+c)), l2=filt(D0.ts_sku[lv].l2,k=>endsC(k,c));
      sk[lv]={l3,l2,l1:derive(l2,()=>true,k=>head(k,c))};
      gc[lv]={grp_cty:gcty,grp_mp:derive(l3,k=>skuGrp[k.split(sepn)[0]],k=>{const p=k.split(sepn);return skuGrp[p[0]]+sepn+p[1]})}}
    R.ts_grp=sg; R.ts_sku=sk; R.ts_grpcell=gc;
    /* P&L PL5 theo chuỗi thời gian */
    const p0=D0.pl5ts; if(p0){const P={...p0};["D","W"].forEach(lv=>{const s=p0[lv]||{};
      const mpcty=filt(s.mpcty,k=>endsC(k,c)), l2=filt(s.l2,k=>endsC(k,c)), l3=filt(s.l3,k=>k.endsWith(sepn+c)), gcty=filt(s.grp_cty,k=>endsC(k,c));
      const all=derive(mpcty,()=>true,()=>"Tổng");
      P[lv]={all,mp:derive(mpcty,()=>true,k=>head(k,c)),cty:{[c]:(s.cty&&s.cty[c])||all["Tổng"]||{}},mpcty,
        grp:derive(gcty,()=>true,k=>head(k,c)),grp_cty:gcty,grp_mp:derive(l3,k=>skuGrp[k.split(sepn)[0]],k=>{const p=k.split(sepn);return skuGrp[p[0]]+sepn+p[1]}),
        l1:derive(l2,()=>true,k=>head(k,c)),l2,l3}});R.pl5ts=P}
    /* tuần / tháng / quý theo sàn */
    const tw=(D0.ts_ov.W.cty[c])||{};
    R.weekfc={...D0.weekfc,all:(D0.weekfc.all||[]).filter(w=>tw[w.wk]).map(w=>{const t=tw[w.wk],q=num(t.q),r=num(t.r),f=num(t.rfc);
      return {...w,q,r:rnd(r),rfc:rnd(f),qfc:rnd(w.qfc*ratio(f,w.rfc)),ach:f?rnd(r/f*100):0}})};
    const rowsOf=(lv,key,orig)=>{const out=[],m=D0.ts_ov[lv].mpcty;Object.keys(m).filter(k=>endsC(k,c)).forEach(k=>{const mp=head(k,c);
      Object.keys(m[k]).sort().forEach(p=>{const t=m[k][p],o=(orig||[]).find(x=>x[key]===p&&x.mp===mp)||{};
        out.push({[key]:p,mp,q:num(t.q),r:rnd(num(t.r)),qfc:rnd(num(o.qfc)*ratio(num(t.rfc),num(o.rfc))),rfc:rnd(num(t.rfc))})})});
      return out.sort((a,b)=>(a[key]<b[key]?-1:a[key]>b[key]?1:(a.mp<b.mp?-1:1)))};
    R.monthly=rowsOf("M","M",D0.monthly); R.quarterly=rowsOf("Q","Q",D0.quarterly);
    /* nhóm sản phẩm */
    const gS={}; R.bygrp_cell.forEach(x=>{const a=gS[x.grp]||(gS[x.grp]={grp:x.grp,q:0,r:0,rfc:0});a.q+=x.q;a.r+=x.r;a.rfc+=num(x.rfc)});
    R.bygrp=GRPS.map(g=>{const a=gS[g]||{grp:g,q:0,r:0,rfc:0},o=(D0.bygrp.find(x=>x.grp===g))||{};return {grp:g,q:a.q,r:rnd(a.r),qfc:rnd(num(o.qfc)*ratio(a.rfc,num(o.rfc))),rfc:rnd(a.rfc)}});
    const wks=(D.meta.weeks||[]), wl=wks[wks.length-1], wp=wks[wks.length-2], gW=R.ts_grpcell.W.grp_cty;
    R.bygrp_prev=GRPS.map(g=>{const t=((gW[g+sepn+c]||{})[wp])||{},o=(D0.bygrp_prev.find(x=>x.grp===g))||{};
      return {grp:g,q:num(t.q),r:rnd(num(t.r)),qfc:rnd(num(o.qfc)*ratio(num(t.rfc),num(o.rfc))),rfc:rnd(num(t.rfc))}});
    R.weekly_grp=[];Object.keys(gW).forEach(k=>{const g=head(k,c);Object.keys(gW[k]).forEach(w=>{const t=gW[k][w],o=(D0.weekly_grp.find(x=>x.grp===g&&x.W===+w))||{};
      R.weekly_grp.push({grp:g,W:+w,q:num(t.q),r:rnd(num(t.r)),qfc:rnd(num(o.qfc)*ratio(num(t.rfc),num(o.rfc))),rfc:rnd(num(t.rfc))})})});
    /* top SKU của tuần báo cáo */
    const A={};R.sku.forEach(x=>{const a=A[x.sku]||(A[x.sku]={sku:x.sku,grp:x.grp,q:0,r:0,rfc:0});a.q+=x.q;a.r+=x.r;a.rfc+=num(x.rfc)});
    const nm={};(D.sku_meta||[]).forEach(m=>nm[m.sku]=m.name);
    const SL=Object.values(A).map(a=>({sku:a.sku,name:nm[a.sku]||"",grp:a.grp,q:a.q,r:rnd(a.r),rfc:rnd(a.rfc),asp:a.q?rnd(a.r/a.q):0,ach:a.rfc?rnd(a.r/a.rfc*100):null,gap:rnd(a.rfc-a.r)}));
    R.top_sku2={...D0.top_sku2,best:SL.filter(x=>x.r>0).sort((a,b)=>b.r-a.r).slice(0,10),
      worst:SL.filter(x=>x.rfc>0&&x.r<x.rfc).sort((a,b)=>b.gap-a.gap).slice(0,10),n_scope:SL.length,n_fc:SL.filter(x=>x.rfc>0).length};
    /* PL5 theo SKU */
    const p=D0.pl5, rows=(p.rows||[]).filter(x=>x.cty===c), tot={}; ["r","cogs","ref_fee","sem","return_fee","wh_fee","op_fee","fulfill"].forEach(k=>tot[k]=rnd(rows.reduce((s,x)=>s+num(x[k]),0)));
    tot.profit=rnd(rows.reduce((s,x)=>s+num(x.profit),0)); tot.margin=tot.r?rnd(tot.profit/tot.r*100):0; tot.sem_unalloc=0;
    const bg={};rows.forEach(x=>{const a=bg[x.grp]||(bg[x.grp]={r:0,profit:0,q:0});a.r+=x.r;a.profit+=x.profit;a.q+=x.q});
    Object.keys(bg).forEach(g=>{bg[g].r=rnd(bg[g].r);bg[g].profit=rnd(bg[g].profit);bg[g].margin=bg[g].r?rnd(bg[g].profit/bg[g].r*100):0});
    const wk=p.prev_total&&D0.pl5ts&&D0.pl5ts.W&&D0.pl5ts.W.cty&&D0.pl5ts.W.cty[c];
    R.pl5={...p,rows,total:tot,by_grp:bg,by_mpcty:filt(p.by_mpcty,k=>k.endsWith("|"+c)),below_cogs:(p.below_cogs||[]).filter(x=>x.cty===c),
      missing_sku_fee:(p.missing_sku_fee||[]).filter(x=>x.cty===c),no_formula_mpcty:(p.no_formula_mpcty||[]).filter(t=>t[1]===c),
      prev_total:(wk&&wk[wp])?{r:rnd(wk[wp][1]),profit:rnd(wk[wp][0]),margin:wk[wp][1]?rnd(wk[wp][0]/wk[wp][1]*100):0}:null};
    /* tồn kho: số lượng theo quốc gia; bình quân bán 4 tuần gần nhất của quốc gia để tính số tuần còn bán */
    const i0=D0.invdet; if(i0){
      const lw=((D.ts_labels&&D.ts_labels.W)||[]).map(String).slice(-4), l1=R.ts_sku.W.l1;
      const avg4=s=>lw.length===4?lw.reduce((z,w)=>z+num(((l1[s]||{})[w]||{}).q),0)/4:null;
      const sk=[];(i0.sku_tot||[]).forEach(s=>{const q=num((s.by_cty||{})[c]),a=avg4(s.sku);const sm=a==null?num(s.sold_month):rnd(a);
        if(q>0||sm>0)sk.push({...s,by_cty:{[c]:q},qty:q,sold_month:sm,weeks:(sm>0&&q>0)?Math.round(q/sm*10)/10:null})});
      const rows=(i0.rows||[]).filter(x=>x.cty===c),st={},mx={};
      rows.forEach(x=>{st[x.stlab]=(st[x.stlab]||0)+num(x.qty);const k=x.grp+"\u0001"+x.stlab;mx[k]=(mx[k]||0)+num(x.qty)});
      R.invdet={...i0,sku_tot:sk,rows,st_totals:Object.keys(st).map(k=>({stlab:k,qty:st[k]})),cty_totals:(i0.cty_totals||[]).filter(x=>x.cty===c),
        qty_total:rows.reduce((z,x)=>z+num(x.qty),0),nsku:new Set(rows.filter(x=>num(x.qty)>0).map(x=>x.sku)).size,
        matrix:Object.keys(mx).map(k=>{const p=k.split("\u0001");return {grp:p[0],stlab:p[1],qty:mx[k]}})}}
    const a0=D0.invacct; if(a0){const rr=L(a0.rows);R.invacct={...a0,rows:rr,det:L(a0.det),qty_total:rr.reduce((z,x)=>z+num(x.qty),0)}}
    const l0=D0.lt; if(l0){R.lt={...l0};["amz","wf"].forEach(k=>{const X=l0[k];if(!X)return;const sk=L(X.sku);
      R.lt[k]={...X,summary:L(X.summary),sku:sk,tot:sk.reduce((z,x)=>z+num(x.tot),0),n_sku:new Set(sk.map(x=>x.sku)).size,
        over270:sk.reduce((z,x)=>z+(x.buckets||[]).slice(3).reduce((u,v)=>u+num(v),0),0)}})}
    /* thị trường Amazon (SQP / Business Report) chỉ có US và CA; AUS chưa có báo cáo */
    const m0=D0.amzmkt; if(m0){const key=c==="CAN"?"CA":c,pk=o=>{const r={};if(o&&o[key])r[key]=o[key];return r};
      R.amzmkt={...m0,sqp:pk(m0.sqp),br:pk(m0.br)}}
    return R;
  }

  /* các hằng dẫn xuất từ D lúc tải trang: tính lại tại chỗ */
  function rederive(){
    const wipe=o=>Object.keys(o).forEach(k=>delete o[k]);
    wipe(CELL);D.cell.forEach(c=>CELL[c.cty+"|"+c.mp]=c);
    wipe(PREV);D.cell_prev.forEach(c=>PREV[c.cty+"|"+c.mp]=c);
    wipe(GPREV);D.bygrp_prev.forEach(g=>GPREV[g.grp]=g);
    YTD.r=YTD.rfc=YTD.q=YTD.qfc=0;D.ytd.forEach(c=>{YTD.r+=c.r;YTD.rfc+=c.rfc;YTD.q+=c.q;YTD.qfc+=c.qfc});
    combos.length=0;D.cell.filter(c=>c.r>0||c.rfc>0).forEach(c=>combos.push(c.mp+"|"+c.cty));
    T.r=T.rfc=T.q=T.qfc=0;D.cell.forEach(c=>{T.r+=c.r;T.rfc+=c.rfc;T.q+=c.q;T.qfc+=c.qfc});
    wipe(wkGrp);D.weekly_grp.forEach(x=>{wkGrp[x.grp]=wkGrp[x.grp]||{};wkGrp[x.grp][x.W]=x});
    wipe(PL5ROW);(D.pl5.rows||[]).forEach(x=>{PL5ROW[x.sku+"|"+x.mp+"|"+x.cty]=x});
    wipe(PL5MISS);(D.pl5.missing_sku_fee||[]).forEach(x=>{PL5MISS[x.sku+"|"+x.mp+"|"+x.cty]=true});
    PL5NOFORM.clear();(D.pl5.no_formula_mpcty||[]).forEach(t=>PL5NOFORM.add(t[0]+"|"+t[1]));
  }

  /* các mục Pro tính ở máy chủ (cầu lợi nhuận, KPI): dựng lại từ PL5 đã lọc */
  const PROK=["summary","issues","ads","pareto","inv","price","trend","questions","brief","sku_class"];
  const PRO0=window.__PRO?{bridge:window.__PRO.bridge,kpi:window.__PRO.kpi}:null;
  if(PRO0){PROK.forEach(k=>PRO0[k]=window.__PRO[k]);PRO0.by_cty=window.__PRO.by_cty}
  function proView(c){
    const P=window.__PRO; if(!P||!PRO0)return;
    if(!c){P.bridge=PRO0.bridge;P.kpi=PRO0.kpi;PROK.forEach(k=>{if(PRO0[k]!==undefined)P[k]=PRO0[k]});return}
    const BC=PRO0.by_cty&&PRO0.by_cty[c]; if(BC&&!BC.error)PROK.forEach(k=>{if(BC[k]!==undefined)P[k]=BC[k]});
    const t=D.pl5.total,r=t.r||0, mc={};
    D.pl5.rows.forEach(x=>{const a=mc[x.mp]||(mc[x.mp]={r:0,p:0,s:0});a.r+=x.r;a.p+=x.profit;a.s+=x.sem});
    const sep=((PRO0.bridge&&PRO0.bridge.by_mc&&PRO0.bridge.by_mc[0]&&PRO0.bridge.by_mc[0].mc)||"").includes(" · ")?" · ":" ";
    if(PRO0.bridge)P.bridge={...PRO0.bridge,r:t.r,profit:t.profit,margin:t.margin,
      items:[["Giá vốn",t.cogs],["Phí sàn & dịch vụ",t.ref_fee+t.return_fee+t.op_fee],["Phí tồn kho (Warehouse fee 6%)",t.wh_fee],["Vận chuyển / fulfill",t.fulfill],["Quảng cáo (SEM)",t.sem]]
        .map(([k,v])=>({k,v:rnd(v),pct:r?rnd(v/r*100):0})),
      by_mc:Object.keys(mc).sort((a,b)=>mc[b].r-mc[a].r).map(m=>({mc:m+sep+c,r:rnd(mc[m].r),margin:mc[m].r?mc[m].p/mc[m].r*100:0,pre_ads:mc[m].r?(mc[m].p+mc[m].s)/mc[m].r*100:0,ads:mc[m].r?mc[m].s/mc[m].r*100:0}))};
    const w=D.weekfc.all,l=w[w.length-1],pr=w[w.length-2];
    if(BC&&BC.kpi)P.kpi={...PRO0.kpi,...BC.kpi};
    else if(PRO0.kpi&&l)P.kpi={...PRO0.kpi,r:l.r,ach:l.ach,wow:pr&&pr.r?(l.r/pr.r-1)*100:null};
  }

  window.applyCty=function(c){
    const R=c?build(c):D0;
    KEYS.forEach(k=>{D[k]=R[k]});
    rederive(); proView(c);
  };
})();
