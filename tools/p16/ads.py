# B/C: tab Quảng cáo — bỏ cảnh báo trùng, gộp cụm chi QC chưa có doanh thu, điều kiện cho lời khuyên tăng ngân sách (exec trong make_gon_v4_16.py)
rep("""const nolow=CP.filter(c=>c.spend>=100&&(c.roas||0)<3).sort((a,b)=>b.spend-a.spend);""",
    """const nolow=CP.filter(c=>c.spend>=100&&(c.roas||0)<3&&!(c.spend>=50&&c.orders===0)).sort((a,b)=>b.spend-a.spend); // chiến dịch click mà chưa ra đơn đã nằm ở cảnh báo riêng, không lặp lại""")
rep(""" Đây đều là chiến dịch dạng PT/PAT (nhắm theo sản phẩm). Việc cần làm: so với chiến dịch Kw của cùng nhóm, giữ lại nhóm sản phẩm nhắm đang ra đơn và bỏ phần còn lại.</div>""",
    """ Việc cần làm: so với các chiến dịch cùng nhóm đang ra đơn, giữ phần nhắm đang ra đơn và bỏ phần còn lại.</div>""")
rep("""trong khi chiến dịch từ khoá cùng nhóm đạt 5–14 — giữ nhóm sản phẩm nhắm đang ra đơn, bỏ phần còn lại""",
    """trong khi các chiến dịch còn lại có ROAS trung vị ${(()=>{const a=CP.filter(c=>(c.roas||0)>=3).map(c=>c.roas).sort((x,y)=>x-y);return a.length?(a[Math.floor(a.length/2)]).toFixed(1).replace(".",","):"—"})()} — giữ phần nhắm đang ra đơn, bỏ phần còn lại""")
rep("""So chiến dịch PT/PAT với chiến dịch từ khoá của cùng nhóm""","""So chiến dịch ROAS thấp với chiến dịch cùng nhóm đang ra đơn""")
old_cheap="""const cheap=T2.filter(t=>t.tacos!==null&&t.tacos<6&&t.rev>5000).sort((a,b)=>a.tacos-b.tacos);
  if(cheap[0]) iss+=`<div class="alert ok"><div class="stripe"></div><div class="body"><div class="t">${short(cheap[0].grp)} · ${cheap[0].mp} ${cheap[0].cty} đang hiệu quả nhất: TACoS ${pc0(cheap[0].tacos)} <span class="chip g">chỗ nên tăng ngân sách</span></div>
   <div class="d">Spend ${N(cheap[0].spend)} ${cheap[0].cur} đi cùng ${N(cheap[0].rev)} ${cheap[0].cur} doanh thu. Đây là nơi thêm tiền quảng cáo có khả năng ra thêm doanh thu cao nhất.</div></div></div>`;"""
new_cheap="""const PRE16={};(D.pl5.rows||[]).forEach(x=>{const k=x.grp+"|"+x.mp+"|"+x.cty,a=PRE16[k]||(PRE16[k]={r:0,p:0});a.r+=x.r||0;a.p+=(x.profit||0)+(x.sem||0)});
  const pre16=t=>{const a=PRE16[t.grp+"|"+t.mp+"|"+t.cty];return a&&a.r>0?a.p/a.r*100:null};   // biên trước quảng cáo của cụm nhóm × sàn × thị trường
  const cheapAll=T2.filter(t=>t.tacos!==null&&t.tacos<6&&t.rev>5000).sort((a,b)=>a.tacos-b.tacos);
  const cheap=cheapAll.filter(t=>{const m=pre16(t);return m!==null&&m>=5});     // chỉ khuyên tăng ngân sách khi biên trước QC >= 5%
  const cheapHold=cheapAll.filter(t=>{const m=pre16(t);return m===null||m<5})[0];
  const fm16=v=>v==null?"chưa có":pc0(v).replace("-","−");
  if(cheap[0]) iss+=`<div class="alert ok"><div class="stripe"></div><div class="body"><div class="t">${short(cheap[0].grp)} · ${cheap[0].mp} ${cheap[0].cty} đang hiệu quả nhất: TACoS ${pc0(cheap[0].tacos)} <span class="chip g">chỗ nên tăng ngân sách</span></div>
   <div class="d">Spend ${N(cheap[0].spend)} ${cheap[0].cur} đi cùng ${N(cheap[0].rev)} ${cheap[0].cur} doanh thu, biên trước quảng cáo ${fm16(pre16(cheap[0]))}. Đây là nơi thêm tiền quảng cáo có khả năng ra thêm doanh thu và vẫn còn biên.</div></div></div>`;
  else if(cheapHold) iss+=`<div class="alert warn"><div class="stripe"></div><div class="body"><div class="t">${short(cheapHold.grp)} · ${cheapHold.mp} ${cheapHold.cty}: quảng cáo hiệu quả (TACoS ${pc0(cheapHold.tacos)}) nhưng biên trước quảng cáo ${fm16(pre16(cheapHold))} <span class="chip w">chỉnh giá trước khi tăng ngân sách</span></div>
   <div class="d">Bán thêm ở mức biên này sẽ làm phần chênh lớn hơn. Việc cần làm: rà giá bán, giá vốn và chi phí vận chuyển/fulfill của cụm này trước; chỉ tăng ngân sách khi biên trước quảng cáo từ 5% trở lên.</div></div></div>`;"""
rep(old_cheap,new_cheap)
old_sol="""${cheap[0]?`<li><div><div class="t">Tăng ngân sách cho ${short(cheap[0].grp)} · ${cheap[0].mp} ${cheap[0].cty}</div><div class="m"><em>Việc:</em> nâng ngân sách ngày thêm 30% cho nhóm chiến dịch đang ra đơn · <em>Đo bằng:</em> TACoS giữ dưới 8% sau khi tăng</div></div></li>`:""}
   <li><div><div class="t">Xin báo cáo quảng cáo Shopify và Walmart, và số cấp SKU của Amazon</div><div class="m"><em>Việc:</em> file spend theo ngày · theo SKU cho hai sàn còn thiếu; với Amazon xin thêm báo cáo cấp SKU và từ khoá · <em>Kết quả cần có:</em> TACoS phủ hết bốn sàn, và Amazon soi được tới SKU như Wayfair</div></div></li>`;"""
new_sol="""${cheap[0]?`<li><div><div class="t">Tăng ngân sách cho ${short(cheap[0].grp)} · ${cheap[0].mp} ${cheap[0].cty}</div><div class="m"><em>Việc:</em> nâng ngân sách ngày thêm 30% cho nhóm chiến dịch đang ra đơn · <em>Điều kiện:</em> biên trước quảng cáo từ 5% trở lên (hiện ${fm16(pre16(cheap[0]))}) · <em>Đo bằng:</em> TACoS giữ dưới 8% sau khi tăng</div></div></li>`:(cheapHold?`<li><div><div class="t">Chỉnh giá/giá vốn ${short(cheapHold.grp)} · ${cheapHold.mp} ${cheapHold.cty} trước khi tăng quảng cáo</div><div class="m"><em>Việc:</em> đưa biên trước quảng cáo từ ${fm16(pre16(cheapHold))} lên tối thiểu 5%, sau đó mới nâng ngân sách · <em>Hạn:</em> ${hlab(14)}</div></div></li>`:"")}`;"""
rep(old_sol,new_sol)
old_ns="""nosale.forEach(t=>{iss+=`<div class="alert warn"><div class="stripe"></div><div class="body"><div class="t">${short(t.grp)} · ${t.mp} ${t.cty}: có chi quảng cáo ${N(t.spend)} ${t.cur} nhưng kênh chưa phát sinh doanh thu <span class="chip w">kiểm listing</span></div>
   <div class="d">Việc cần làm: kiểm listing đã live và còn hàng tại ${t.cty} chưa. Nếu chưa bán được thì tạm dừng chiến dịch cho tới khi listing sẵn sàng.</div></div></div>`;});"""
new_ns="""if(nosale.length){const tot=nosale.reduce((s,t)=>s+t.spend,0);nosale.sort((a,b)=>b.spend-a.spend);iss+=`<div class="alert warn"><div class="stripe"></div><div class="body"><div class="t">${nosale.length} cụm đang chi quảng cáo ở nơi chưa phát sinh doanh thu — tổng ${N(tot)} USD <span class="chip w">kiểm listing</span></div>
   <div class="d">${nosale.map(t=>short(t.grp)+" · "+t.mp+" "+t.cty+" ("+N(t.spend)+")").join(" · ")}. Việc cần làm: kiểm listing đã live và còn hàng tại thị trường đó chưa; nếu chưa bán được thì tạm dừng chiến dịch cho tới khi listing sẵn sàng.</div></div></div>`;}"""
rep(old_ns,new_ns)
