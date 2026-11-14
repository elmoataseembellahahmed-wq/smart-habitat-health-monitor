"""Act like the ESP32 wristband, to test the ingestion layer without hardware.

Sends one sample a minute (faster in --fast mode) to http://127.0.0.1:8000/api/ingest,
the same JSON the ESP32 code sends. It can also simulate the faults the server must
handle: --drop (link loss: samples are buffered, then sent late in one batch),
--dup (the same sample sent twice), --bad (an impossible value).

Run the server first (python run_offline.py), then:
    python tools/fake_device.py --device WB-B --minutes 30 --fast --drop --dup --bad
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
    ap.add_argument("--device", default="WB-B")
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
        msg = {"device_id": a.device, "timestamp": round(start + i * 60),
               "readings": {"heart_rate": round(rng.gauss(64, 2), 1), "spo2": round(rng.gauss(97.8, 0.4), 1),
                            "body_temp": round(rng.gauss(36.6, 0.1), 2)}}
        if a.bad and i == 3:
            msg["readings"]["body_temp"] = 31.0          # band off the skin
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
