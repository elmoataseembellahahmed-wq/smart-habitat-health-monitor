"""Backup demo camera: plays a realistic "astronaut getting tired" sequence into the
dashboard, with no webcam needed. Use it if the webcam or the lighting fails at the venue.

Start the server first, then:
    python camera/demo_camera.py --band B

It runs the same BlinkTracker as the real camera on simulated eye observations:
    1. alert       about 15 blinks/min, short blinks           -> NORMAL
    2. tired       about 30 blinks/min, slower blinks           -> WATCH
    3. drowsy      slower blinks plus 0.8 s microsleeps         -> ACT
Each phase lasts --phase seconds (default 40). The dashboard labels it as simulated.
Only the Python standard library is needed. Press Ctrl+C to stop.
"""

import argparse
import json
import random
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blink_tracker import BlinkTracker  # noqa: E402

FPS = 15
PHASES = [
    # name, seconds between blinks, blink length (s), microsleeps per phase
    ("alert", 4.0, 0.15, 0),
    ("tired", 2.0, 0.25, 0),
    ("drowsy", 2.0, 0.30, 3),
]


def send(server, reading):
    req = urllib.request.Request(server.rstrip("/") + "/api/live", data=json.dumps(reading).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=2).read()
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="Backup demo camera (no webcam needed)")
    ap.add_argument("--band", default="B", help="wristband ID to report as (A, B or C)")
    ap.add_argument("--phase", type=float, default=40.0, help="seconds per phase")
    ap.add_argument("--loop", action="store_true", help="repeat the sequence until stopped")
    ap.add_argument("--server", default="http://127.0.0.1:8000")
    args = ap.parse_args()
    band = args.band.strip().upper()

    rng = random.Random(1)
    # The demo person's saved normal, as if learned on earlier days.
    tracker = BlinkTracker(baseline={"blink_rate": 15.0, "perclos": 0.04})
    t, last_send, server_ok = 0.0, 0.0, None
    print(f"Demo camera for wristband {band}: alert -> tired -> drowsy, {args.phase:.0f} s each. Ctrl+C to stop.")

    try:
        while True:
            for name, every, length, sleeps in PHASES:
                print(f"Phase: {name}")
                start = t
                next_blink = t + rng.uniform(0.5, every)
                sleep_times = sorted(start + rng.uniform(5, args.phase - 5) for _ in range(sleeps))
                while t - start < args.phase:
                    closed = next_blink <= t < next_blink + length
                    if t >= next_blink + length:
                        next_blink += every * rng.uniform(0.7, 1.3)
                    if any(s <= t < s + 0.8 for s in sleep_times):
                        closed = True
                    tracker.update(t, True, not closed, hour=time.localtime().tm_hour)
                    if t - last_send >= 1.0:
                        ok = send(args.server, {**tracker.reading(), "band": band, "simulated": True})
                        if ok != server_ok:
                            print("Connected to the dashboard server." if ok else
                                  f"Can't reach the server at {args.server}. Is it running?")
                            server_ok = ok
                        last_send = t
                    t += 1 / FPS
                    time.sleep(1 / FPS)
            if not args.loop:
                break
    except KeyboardInterrupt:
        pass
    print("Demo camera stopped.")


if __name__ == "__main__":
    main()
