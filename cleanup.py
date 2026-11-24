"""Dọn dẹp định kỳ file raw đã upload (data/periods/<kỳ>/uploads/).

Chỉ xoá FILE RAW upload của các kỳ đã build xong. KHÔNG đụng tới: data.json, report.html, meta.json,
build.log, adsopt_cache.pkl (nên biểu đồ / trend các kỳ vẫn còn), cũng như tài khoản, task, ghi chú, mẫu report, P&L.

Quy tắc mặc định (chỉnh trong ⚙ Cấu hình, khoá "cleanup"):
  enabled=true, interval_days=7 (chạy tối đa 1 lần / 7 ngày), keep_latest=1 (giữ raw của 1 kỳ build mới nhất),
  min_age_days=7 (chỉ dọn kỳ đã build từ 7 ngày trở lên).
Trước khi xoá, app làm mới cache quảng cáo (adsopt) của kỳ đó để trang Tối ưu QC vẫn có lịch sử.

Cách chạy:
  - Tự động: mở app (trang chính) sẽ kiểm tra, quá hạn thì tự dọn. Lần đầu chỉ bắt đầu tính 7 ngày, chưa xoá gì.
  - Thủ công trong app: ⚙ Cấu hình → "Dọn dẹp file raw".
  - Dòng lệnh / PythonAnywhere Tasks (đặt hằng ngày cũng được, tự bỏ qua nếu chưa đủ 7 ngày):
        python3 cleanup.py            # chạy nếu đến hạn
        python3 cleanup.py --dry-run  # chỉ liệt kê, không xoá
        python3 cleanup.py --force    # chạy ngay, bất kể hạn
"""
import json, os, sys, threading
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent
PERIODS = BASE / "data" / "periods"
STATE = BASE / "data" / "cleanup_state.json"
DEFAULTS = {"enabled": True, "interval_days": 7, "keep_latest": 1, "min_age_days": 7}
LOCK = threading.Lock()


def settings(cfg=None):
    s = dict(DEFAULTS)
    user = (cfg or {}).get("cleanup") or {}
    if isinstance(user, dict):
        for k, dv in DEFAULTS.items():
            if k in user:
                try:
                    s[k] = bool(user[k]) if isinstance(dv, bool) else max(0, int(user[k]))
                except (TypeError, ValueError):
                    pass
    return s


def _read(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def _write(p, obj):
    p = Path(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def state():
    return _read(STATE) or {}


def _built_at(pdir, meta):
    try:
        return datetime.fromisoformat(meta.get("built"))
    except (TypeError, ValueError):
        try:
            return datetime.fromtimestamp((pdir / "data.json").stat().st_mtime)
        except OSError:
            return None


def _raw_files(up):
    """File thường trong uploads/ (bỏ qua symlink và thư mục)."""
    out = []
    if up.is_dir():
        for f in up.iterdir():
            if f.is_file() and not f.is_symlink():
                out.append(f)
    return out


def plan(cfg=None, now=None):
    s = settings(cfg)
    now = now or datetime.now()
    built = []
    if PERIODS.exists():
        for d in PERIODS.iterdir():
            meta = _read(d / "meta.json")
            if meta and meta.get("status") == "built" and (d / "data.json").exists():
                built.append((_built_at(d, meta) or datetime.min, d, meta))
    built.sort(key=lambda x: x[0], reverse=True)
    cands, skipped = [], []
    for i, (bt, d, meta) in enumerate(built):
        files = _raw_files(d / "uploads")
        if not files:
            continue
        if i < s["keep_latest"]:
            skipped.append({"period": d.name, "reason": f"giữ lại: nằm trong {s['keep_latest']} kỳ build mới nhất"})
        elif now - bt < timedelta(days=s["min_age_days"]):
            skipped.append({"period": d.name, "reason": f"giữ lại: build chưa đủ {s['min_age_days']} ngày"})
        else:
            cands.append({"period": d.name, "files": [f.name for f in files], "n": len(files), "bytes": sum(f.stat().st_size for f in files)})
    return {"settings": s, "candidates": cands, "skipped": skipped}


def run(cfg=None, dry=False, refresh=None, log=print):
    """Dọn các kỳ đủ điều kiện. refresh(pid) -> bool: làm mới cache QC trước khi xoá (nếu lỗi → bỏ qua kỳ đó)."""
    with LOCK:
        pl = plan(cfg)
        res = {"dry": dry, "at": datetime.now().isoformat(timespec="seconds"), "periods": [], "skipped": list(pl["skipped"]), "files": 0, "bytes": 0}
        for c in pl["candidates"]:
            pid, d = c["period"], PERIODS / c["period"]
            if dry:
                res["periods"].append(c); res["files"] += c["n"]; res["bytes"] += c["bytes"]
                continue
            if refresh is not None:
                try:
                    ok = refresh(pid)
                except Exception as e:
                    ok = False; log(f"[cleanup] {pid}: lỗi làm mới cache — {e}")
                if not ok:
                    res["skipped"].append({"period": pid, "reason": "không làm mới được cache QC nên chưa xoá raw"})
                    continue
            n = b = 0
            for f in _raw_files(d / "uploads"):
                try:
                    sz = f.stat().st_size; f.unlink(); n += 1; b += sz
                except OSError as e:
                    log(f"[cleanup] {pid}/{f.name}: không xoá được — {e}")
            meta = _read(d / "meta.json") or {}
            meta["uploads_cleaned"] = {"at": res["at"], "files": n, "bytes": b}
            _write(d / "meta.json", meta)
            res["periods"].append({"period": pid, "n": n, "bytes": b}); res["files"] += n; res["bytes"] += b
            log(f"[cleanup] {pid}: xoá {n} file raw, giải phóng {b/1048576:.1f} MB")
        if not dry:
            st = state(); st["last_run"] = res["at"]; st["last_result"] = {k: res[k] for k in ("at", "files", "bytes")} | {"periods": [p["period"] for p in res["periods"]]}
            _write(STATE, st)
        return res


def maybe_run(cfg=None, refresh=None, log=print):
    """Gọi mỗi khi mở app: chỉ chạy khi đến hạn. Lần đầu (chưa có mốc) chỉ đặt mốc, chưa xoá gì."""
    s = settings(cfg)
    if not s["enabled"]:
        return None
    st = state()
    try:
        last = datetime.fromisoformat(st.get("last_run"))
    except (TypeError, ValueError):
        _write(STATE, {**st, "last_run": datetime.now().isoformat(timespec="seconds"), "note": "mốc bắt đầu, chưa dọn lần nào"})
        return None
    if datetime.now() - last < timedelta(days=s["interval_days"]):
        return None
    try:
        return run(cfg, False, refresh, log)
    except Exception as e:                       # lỗi cũng đặt mốc để không lặp lại mỗi lần mở app
        log(f"[cleanup] lỗi: {e}")
        st = state(); st["last_run"] = datetime.now().isoformat(timespec="seconds"); _write(STATE, st)
        return None


def status(cfg=None):
    return {"settings": settings(cfg), "state": state(), "plan": plan(cfg)}


if __name__ == "__main__":
    sys.path.insert(0, str(BASE))
    import server, adsopt
    cfg = server.load_config()
    args = sys.argv[1:]
    refresh = adsopt.refresh_cache
    if "--dry-run" in args:
        r = run(cfg, True)
    elif "--force" in args:
        r = run(cfg, False, refresh)
    else:
        r = maybe_run(cfg, refresh) or {"note": "chưa đến hạn hoặc đã tắt (xem cleanup_state.json)"}
    print(json.dumps(r, ensure_ascii=False, indent=2))
