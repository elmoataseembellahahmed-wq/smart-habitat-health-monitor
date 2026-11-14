"""Backup server: same API as the FastAPI backend, using only the Python standard library.

Use it if you can't install FastAPI (no internet at the venue, school laptop, etc.):
    python run_offline.py
Then open http://127.0.0.1:8000
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from engine import HealthMonitor, live, access
from engine.manual import QuickCheck, Upload, template_csv

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
TYPES = {".html": "text/html", ".css": "text/css", ".js": "application/javascript"}
monitor = HealthMonitor()
monitor.status(monitor.days[-1])  # learn every week of the mission once, at startup
quick = QuickCheck(monitor)        # manual test: new days typed in by hand
uploaded = Upload()                # manual test: a whole mission from a CSV file
manual_lock = threading.Lock()
MAX_UPLOAD = 5_000_000

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj):
        self._send(200, json.dumps(obj))

    def do_GET(self):
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        q = parse_qs(url.query)
        try:
            day = int(q["day"][0]) if "day" in q else monitor.days[-1]
            role = q.get("role", ["surgeon"])[0]
            if not access.valid_role(role, [m["id"] for m in monitor.crew]):
                raise ValueError(f"Unknown role: {role}")
            if parts == []:
                return self._send(200, (FRONTEND / "index.html").read_bytes(), "text/html")
            if parts == ["manual"]:
                return self._send(200, (FRONTEND / "manual.html").read_bytes(), "text/html")
            if parts[:2] == ["api", "manual"]:
                with manual_lock:
                    if parts[2:] == ["defaults"]:
                        return self._json(quick.defaults(q.get("aid", ["A"])[0]))
                    if parts[2:] == ["template.csv"]:
                        data = template_csv(full=q.get("full", ["0"])[0] == "1").encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "text/csv; charset=utf-8")
                        self.send_header("Content-Disposition", "attachment; filename=mission_template.csv")
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        return self.wfile.write(data)
                    if parts[2:4] == ["upload", "report"] and len(parts) == 5:
                        lang = "ar" if q.get("lang", ["en"])[0] == "ar" else "en"
                        return self._send(200, uploaded.report(parts[4], day, lang), "text/plain")
            if parts[0] == "static" and len(parts) == 2:
                f = FRONTEND / parts[1]
                if f.parent == FRONTEND and f.suffix in TYPES and f.exists():
                    return self._send(200, f.read_bytes(), TYPES[f.suffix])
            if parts[:1] == ["api"]:
                if parts[1:] == ["mission"]:
                    return self._json(monitor.mission())
                if parts[1:] == ["live"]:
                    return self._json(live.latest())
                if parts[1:] == ["status"]:
                    access.log(role, "all", f"status day {day}")
                    return self._json(monitor.status(day, role))
                if parts[1:] == ["audit"]:
                    if role != "surgeon":
                        return self._send(403, json.dumps({"detail": "Flight surgeon only"}))
                    return self._json(access.audit())
                if parts[1] == "astronaut" and len(parts) == 3:
                    m = monitor.member(parts[2])
                    access.log(role, m["id"], f"astronaut day {day}")
                    return self._json(access.view({**m, "day": day, **monitor.assess(m["id"], day),
                                                   "trend": monitor.trend(m["id"], day)}, role))
                if parts[1] == "report" and len(parts) == 3:
                    monitor.member(parts[2])
                    lang = "ar" if q.get("lang", ["en"])[0] == "ar" else "en"
                    access.log(role, parts[2], f"report day {day} ({lang})")
                    return self._send(200, monitor.report(parts[2], day, lang, role), "text/plain")
                if parts[1] == "series" and len(parts) == 4:
                    monitor.member(parts[2])
                    return self._json(access.series_view(monitor.series(parts[2], parts[3]), parts[2], role))
            self._send(404, json.dumps({"detail": "Not found"}))
        except (KeyError, ValueError) as e:
            self._send(404, json.dumps({"detail": str(e)}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith("/api/manual/"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                if length > MAX_UPLOAD:
                    return self._send(413, json.dumps({"detail": "File too large (5 MB max)"}))
                body = self.rfile.read(length).decode("utf-8-sig")
                with manual_lock:
                    if path == "/api/manual/day":
                        b = json.loads(body or "{}")
                        return self._json(quick.add(b.get("aid", "A"), b.get("values", {}), b.get("cabin", {})))
                    if path == "/api/manual/reset":
                        quick.reset()
                        return self._json({"ok": True})
                    if path == "/api/manual/upload":
                        return self._json(uploaded.load(body))
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                return self._send(400, json.dumps({"detail": str(e)}))
        if path == "/api/live":
            try:
                length = int(self.headers.get("Content-Length", 0))
                live.store(json.loads(self.rfile.read(length) or b"{}"))
                return self._json({"ok": True})
            except (ValueError, json.JSONDecodeError) as e:
                return self._send(400, json.dumps({"detail": str(e)}))
        self._send(404, json.dumps({"detail": "Not found"}))

    def log_message(self, *args):
        pass  # keep the console quiet


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Astronaut Health Monitor running at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
