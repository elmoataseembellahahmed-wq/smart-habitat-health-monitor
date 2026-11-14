"""Act like the NABD workstation app, to test the ingestion layer without a real crew.

The real app measures typing, the mouse reaction test and webcam signals locally and
sends only numbers. This script sends the same JSON, one sample a minute (faster with
--fast), to http://127.0.0.1:8000/api/ingest. It can also simulate the faults the server
must handle: --drop (link loss: samples are buffered, then sent late in one batch),
--dup (the same sample sent twice), --bad (an impossible value).

Run the server first (python run_offline.py), then:
    python tools/fake_workstation.py --workstation WS-B --minutes 30 --fast --drop --dup --bad
    open http://127.0.0.1:8000/api/devices
"""

import argparse
import json
import random
import time
import urllib.request


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workstation", default="WS-B")
    ap.add_argument("--url", default="http://127.0.0.1:8000/api/ingest")
    ap.add_argument("--minutes", type=int, default=20)
    ap.add_argument("--fast", action="store_true", help="send 1 sample per 0.2 s instead of per minute")
    ap.add_argument("--drop", action="store_true", help="lose the link for a third of the run")
    ap.add_argument("--dup", action="store_true", help="send one sample twice")
    ap.add_argument("--bad", action="store_true", help="send one impossible value")
    a = ap.parse_args()
    rng = random.Random(1)
    start = time.time() - a.minutes * 60
    buffer, results = [], {}
    for i in range(a.minutes):
        msg = {"device_id": a.workstation, "timestamp": round(start + i * 60),
               "readings": {"heart_rate": round(rng.gauss(64, 2), 1), "blink_rate": round(rng.gauss(16, 1.5), 1),
                            "typing_speed": round(rng.gauss(50, 3), 1),
                            "typing_errors": round(rng.gauss(6, 0.6), 1)}}
        if a.bad and i == 3:
            msg["readings"]["heart_rate"] = 250.0         # bad lighting on the webcam
        buffer.append(msg)
        offline = a.drop and a.minutes // 3 <= i < 2 * a.minutes // 3
        if not offline:
            for r in post(a.url, buffer)["results"]:
                results[r["status"]] = results.get(r["status"], 0) + 1
            if a.dup and i == 5:
                r = post(a.url, buffer[-1:])["results"][0]
                results[r["status"]] = results.get(r["status"], 0) + 1
            buffer = []
        time.sleep(0.2 if a.fast else 60)
    print("sent:", results)


if __name__ == "__main__":
    main()
