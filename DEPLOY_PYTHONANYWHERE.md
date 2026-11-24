# Đưa Sale Report Manager lên PythonAnywhere

App chạy theo chuẩn WSGI qua file `wsgi.py` (đã thử bằng máy chủ WSGI thử nghiệm: đăng nhập, report, phân quyền, API). **Chưa thử trên chính PythonAnywhere** — các bước dưới đây theo cách cấu hình thông thường của dịch vụ, giao diện của họ có thể khác chút.

## Các bước
1. **Tải code lên.** Nén thư mục `report_manager` thành zip → tab **Files** → upload → mở Bash console: `unzip report_manager.zip` (kết quả: `/home/<tên bạn>/report_manager`). Không tải kèm `data/users.json`, `data/secret.key` từ máy bạn (tài khoản sẽ tạo mới trên server).
2. **Tạo môi trường Python.** Bash console:
   ```
   mkvirtualenv --python=python3.12 srm
   pip install pandas openpyxl
   ```
   (chọn đúng phiên bản Python mà PythonAnywhere đang hỗ trợ; nhớ dùng cùng phiên bản ở bước 3).
3. **Tạo web app.** Tab **Web** → *Add a new web app* → **Manual configuration** → chọn cùng phiên bản Python.
   - *Virtualenv*: `/home/<tên bạn>/.virtualenvs/srm`
   - *Source code*: `/home/<tên bạn>/report_manager`
   - Bấm vào *WSGI configuration file*, xoá toàn bộ nội dung, dán:
     ```python
     import sys
     sys.path.insert(0, "/home/<tên bạn>/report_manager")
     from wsgi import application
     ```
4. **Bật HTTPS.** Tab Web → *Force HTTPS* = Enabled (để mật khẩu không đi dưới dạng văn bản thường).
5. **Tạo tài khoản quản trị đầu tiên.** Bash console:
   ```
   cd ~/report_manager
   python3 manage_users.py add <tên>
   ```
   Người chỉ cần xem report: `python3 manage_users.py add <tên> viewer`.
6. **Reload** (nút xanh ở tab Web) rồi mở `https://<tên bạn>.pythonanywhere.com`.

## Cần lưu ý
- **Dữ liệu** nằm trong `~/report_manager/data/` (kỳ, task, ghi chú, tài khoản). Nên sao lưu thư mục này định kỳ (tải về hoặc nén lại).
- **Cập nhật code:** upload đè file mới rồi bấm Reload.
- **Build chạy ngay trong một request web.** Nếu báo cáo thật nặng, có thể bị ngắt do giới hạn thời gian của dịch vụ — hãy thử build một kỳ thật sau khi cài. Nếu bị ngắt, build trên máy rồi tải `data/periods/<kỳ>` lên.
- **Giới hạn kích thước upload** (zip dữ liệu) và **truy cập internet ra ngoài** phụ thuộc gói tài khoản. Gói miễn phí thường chỉ cho kết nối tới một danh sách site cho phép, nên gửi email/webhook từ `alerts.py` có thể không chạy; bản tin vẫn xem được ở 🏠 Hôm nay.
- **Lệnh định kỳ** (`alerts.py weekly --send`) dùng tab **Tasks** của PythonAnywhere (nếu gói của bạn có).
- **Khoá đăng nhập sai nhiều lần** tính theo IP khách (phần tử cuối của `X-Forwarded-For` do proxy của dịch vụ thêm vào). Nếu thấy mọi người bị khoá cùng lúc, báo lại để chỉnh.
- Ai có đường dẫn đều thấy trang đăng nhập; hãy đặt mật khẩu mạnh (app kiểm tra độ mạnh) và để người ngoài nhóm ở quyền **Chỉ xem report**.
