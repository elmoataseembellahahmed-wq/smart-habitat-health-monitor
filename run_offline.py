"""Backup server: same API as the FastAPI backend, using only the Python standard library.

Use it if you can't install FastAPI (no internet at the venue, school laptop, etc.):
    python run_offline.py
Then open http://127.0.0.1:8000
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from engine import HealthMonitor, live

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
TYPES = {".html": "text/html", ".css": "text/css", ".js": "application/javascript"}
monitor = HealthMonitor()
monitor.status(monitor.days[-1])  # learn every week of the mission once, at startup


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
            if parts == []:
                return self._send(200, (FRONTEND / "index.html").read_bytes(), "text/html")
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
                    return self._json(monitor.status(day))
                if parts[1] == "astronaut" and len(parts) == 3:
                    m = monitor.member(parts[2])
                    return self._json({**m, "day": day, **monitor.assess(m["id"], day),
                                       "trend": monitor.trend(m["id"], day)})
                if parts[1] == "report" and len(parts) == 3:
                    monitor.member(parts[2])
                    lang = "ar" if q.get("lang", ["en"])[0] == "ar" else "en"
                    return self._send(200, monitor.report(parts[2], day, lang), "text/plain")
                if parts[1] == "series" and len(parts) == 4:
                    monitor.member(parts[2])
                    return self._json(monitor.series(parts[2], parts[3]))
            self._send(404, json.dumps({"detail": "Not found"}))
        except (KeyError, ValueError) as e:
            self._send(404, json.dumps({"detail": str(e)}))

    def do_POST(self):
        if urlparse(self.path).path == "/api/live":
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
