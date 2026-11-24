"""Cầu nối WSGI cho Sale Report Manager (để chạy trên PythonAnywhere và các dịch vụ dùng WSGI).
Không đổi cách chạy trên máy: vẫn `python3 server.py`. Trên dịch vụ, trỏ WSGI tới `application` trong file này.

Cơ chế: mỗi request dựng một đối tượng `server.H` (không mở socket), nạp sẵn header/body từ WSGI,
gọi đúng do_GET/do_POST/..., rồi đọc lại phần HTTP mà handler đã ghi để trả về cho WSGI.
"""
import io
import sys
from email.message import Message
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import server  # noqa: E402

server.seed_if_empty()
_METHODS = ("GET", "POST", "PUT", "DELETE")


class _Req(server.H):
    def __init__(self, environ, body):          # cố ý không gọi super().__init__ (không có socket)
        self.command = environ["REQUEST_METHOD"]
        qs = environ.get("QUERY_STRING", "")
        self.path = environ.get("PATH_INFO", "/") + ("?" + qs if qs else "")
        self.request_version = "HTTP/1.1"
        self.requestline = f"{self.command} {self.path} HTTP/1.1"
        self.headers = Message()
        for k, v in environ.items():
            if k.startswith("HTTP_"):
                self.headers[k[5:].replace("_", "-").title()] = v
        for k, h in (("CONTENT_TYPE", "Content-Type"), ("CONTENT_LENGTH", "Content-Length")):
            if environ.get(k):
                self.headers[h] = environ[k]
        self.headers.replace_header("Content-Length", str(len(body))) if "Content-Length" in self.headers else self.headers.add_header("Content-Length", str(len(body)))
        if "X-Forwarded-Proto" not in self.headers and environ.get("wsgi.url_scheme") == "https":
            self.headers["X-Forwarded-Proto"] = "https"
        # IP khách: dùng phần tử CUỐI của X-Forwarded-For (do proxy của dịch vụ thêm, khó giả), nếu không có thì REMOTE_ADDR
        xff = [x.strip() for x in (environ.get("HTTP_X_FORWARDED_FOR") or "").split(",") if x.strip()]
        self.client_address = ((xff[-1] if xff else environ.get("REMOTE_ADDR", "0.0.0.0")), 0)
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()

    def log_message(self, *a, **k):
        pass


def application(environ, start_response):
    method = environ["REQUEST_METHOD"]
    if method not in _METHODS:
        start_response("405 Method Not Allowed", [("Allow", ", ".join(_METHODS)), ("Content-Length", "0")])
        return [b""]
    try:
        n = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        n = 0
    body = environ["wsgi.input"].read(n) if n > 0 else b""
    req = _Req(environ, body)
    getattr(req, "do_" + method)()
    raw = req.wfile.getvalue()
    head, _, payload = raw.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n")
    code = lines[0].split(" ", 1)[1] if " " in lines[0] else "500 Internal Server Error"
    hdrs = [tuple(x.split(": ", 1)) for x in lines[1:] if ": " in x and x.split(": ", 1)[0].lower() not in ("server", "date", "connection")]
    start_response(code, hdrs)
    return [payload]
