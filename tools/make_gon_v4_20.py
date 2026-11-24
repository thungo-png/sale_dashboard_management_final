"""Gọn v4 – lần 20: sửa lời giải thích SEM trong PL5 (SEM là chi phí quảng cáo THẬT, phân bổ đủ 100%, không còn là 'số tạm tính theo %'). Chạy sau v4_19."""
import sys
s=open(sys.argv[1],encoding="utf-8").read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(a[:60],s.count(a)); s=s.replace(a,b)
rep('["Chi phí quảng cáo trong PL5","Cột SEM trong file P&amp;L là số tạm tính theo tỷ lệ %; khi có chi phí thực tế sẽ tính theo thực tế"],',
    '["Chi phí quảng cáo trong PL5","Cột SEM lấy chi phí quảng cáo thật theo báo cáo, chia đủ 100% cho các SKU có bán trong từng nhóm × sàn × quốc gia (phần của ô không có SKU bán chia theo doanh thu cho cùng sàn × quốc gia)"],')
rep('      ["Chi phí quảng cáo thực tế để thay cột SEM tạm tính","Số thực tế theo kênh/SKU (xem đối chiếu ở Quảng cáo › mục 02)","Biên PL5 phản ánh đúng chi phí quảng cáo"],\n','')
rep("""'; cột SEM trong file P&amp;L (dùng tính PL5) đang là số tạm tính theo tỷ lệ % và ghi '+USD(t.sem)+'. Phần chênh '+USD(t.diff)+' sẽ được phản ánh khi file P&amp;L cập nhật chi phí thực tế; với mức chi như tuần này, biên PL5 sẽ thấp hơn khoảng '+fN(R.pp,1)+' điểm %.</div>'""",
    """'; PL5 dùng đúng số này (cột SEM '+USD(t.sem)+'), chia đủ cho các SKU có bán. '+(t.diff>1?'Phần chênh '+USD(t.diff)+' là chi phí của ô chưa có sheet P&amp;L (vd Amazon Úc), đã trừ thẳng vào tổng PL5 nên chưa hiện ở từng ô.':'Hai số khớp nhau.')+'</div>'""")
rep("""Đối chiếu: chi phí quảng cáo trong PL5 là số tạm tính theo tỷ lệ % ('+USD(R.t.sem)+'), chi phí thực tế theo báo cáo quảng cáo là '+USD(R.t.sp)+' (chênh '+USD(R.t.diff)+', khoảng '+fN(R.pp,1)+' điểm % biên). Xem chi tiết ở Quảng cáo › mục 02.""",
    """Đối chiếu: chi phí quảng cáo trong PL5 là '+USD(R.t.sem)+', chi phí theo báo cáo quảng cáo là '+USD(R.t.sp)+(R.t.diff>1?' (chênh '+USD(R.t.diff)+': ô chưa có sheet P&amp;L, đã trừ thẳng vào tổng)':' (khớp)')+'. Xem chi tiết ở Quảng cáo › mục 02.""")
rep("""var R=adRecon();if(R.t.diff>1)rows.push([""","""var R=adRecon();if(R.t.diff>1&&!(D.pl5&&D.pl5.sem_full))rows.push([""")
import os
js=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"p20","ovcompact.js"),encoding="utf-8").read()
k=s.rfind("</script>"); assert k>0; s=s[:k]+"\n"+js+"\n"+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("built")
