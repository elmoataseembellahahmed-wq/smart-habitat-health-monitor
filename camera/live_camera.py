"""Cabin camera, all-day mode: measures blinking and eye closure whenever an astronaut
faces it, and files the result under the astronaut logged in to that workstation.

Start the server first (python run_offline.py, or uvicorn backend.main:app), then:
    pip install opencv-python
    python camera/live_camera.py --astronaut B

--astronaut is the ID of the astronaut logged in to this workstation (A, B or C). The
login tells the system who is in front of the webcam, so
the camera never needs to recognize a face. Here you choose it by hand:
A = Amira, B = Ben, C = Chen.

The first time an astronaut uses it, the camera learns that person's normal blinking over
60 seconds of face time and saves it in camera/baselines/. Later sessions load it and
start measuring at once. Use --reset-baseline to learn it again.

Keys in the camera window:  q = quit.
Other options:  --camera 1   --calibrate 30   --server http://127.0.0.1:8001   --no-window

How it works: OpenCV finds the face, then looks for open eyes in the upper half of
the face. The eye detector does not find CLOSED eyes, so "face found but no eyes"
means the eyes are closed. Those observations go into BlinkTracker.
Everything runs on this computer; no video is stored or sent anywhere, only numbers.
"""

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

try:
    import cv2
except ImportError:
    sys.exit("OpenCV is not installed. Run:  pip install opencv-python")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blink_tracker import BlinkTracker  # noqa: E402

MODELS = HERE / "models"
BASELINES = HERE / "baselines"
CASCADES = {
    "face": "haarcascade_frontalface_default.xml",
    "eyes": "haarcascade_eye_tree_eyeglasses.xml",  # also works with glasses
}
CASCADE_URL = "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/"


def load_cascade(name):
    """Use OpenCV's bundled detector file, or download it once into camera/models/."""
    filename = CASCADES[name]
    candidates = []
    if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
        candidates.append(Path(cv2.data.haarcascades) / filename)
    candidates.append(MODELS / filename)
    for path in candidates:
        if path.exists():
            return cv2.CascadeClassifier(str(path))
    MODELS.mkdir(exist_ok=True)
    target = MODELS / filename
    print(f"Downloading {filename} (one time only)...")
    try:
        urllib.request.urlretrieve(CASCADE_URL + filename, target)
    except Exception as e:
        sys.exit(f"Could not download {filename}: {e}\n"
                 f"Download it manually from {CASCADE_URL + filename} into {MODELS}")
    return cv2.CascadeClassifier(str(target))


def send(server, reading):
    req = urllib.request.Request(server.rstrip("/") + "/api/live", data=json.dumps(reading).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=2).read()
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="Cabin camera: all-day blink and eye-closure monitor")
    ap.add_argument("--astronaut", "--band", dest="band", default="B", help="ID of the astronaut logged in here (A, B or C)")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--calibrate", type=float, default=60.0,
                    help="seconds of face time to learn this person's normal (first use only)")
    ap.add_argument("--reset-baseline", action="store_true", help="learn this astronaut's normal again")
    ap.add_argument("--server", default="http://127.0.0.1:8000")
    ap.add_argument("--no-window", action="store_true")
    args = ap.parse_args()
    band = args.band.strip().upper()

    BASELINES.mkdir(exist_ok=True)
    baseline_file = BASELINES / f"band_{band}.json"
    saved = None if args.reset_baseline else BlinkTracker.load_baseline(baseline_file)

    face_det, eye_det = load_cascade("face"), load_cascade("eyes")
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        sys.exit(f"Could not open camera {args.camera}. Close other apps using it, or try --camera 1")

    tracker = BlinkTracker(calibration_s=args.calibrate, baseline=saved)
    last_send, server_ok, saved_now = 0.0, None, saved is not None
    print(f"Workstation webcam running for astronaut {band}.")
    if saved:
        print(f"Loaded this astronaut's normal: {saved['blink_rate']:.0f} blinks/min. Measuring now.")
    else:
        print(f"Learning astronaut {band}'s normal for {args.calibrate:.0f} s of face time: "
              "look at the screen and blink normally.")
    print("Press q in the camera window (or Ctrl+C here) to stop.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera stopped sending frames.")
                break
            now = time.time()
            gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            faces = face_det.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(120, 120))
            many = len(faces) > 1   # two or more people: don't guess whose eyes these are
            face_found, eyes_open = len(faces) == 1, False
            if many and not args.no_window:
                for fx, fy, fw, fh in faces:
                    cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (80, 80, 240), 2)
            if face_found:
                x, y, w, h = faces[0]
                upper = gray[y + int(h * 0.15): y + int(h * 0.55), x: x + w]
                eyes = eye_det.detectMultiScale(upper, scaleFactor=1.1, minNeighbors=6,
                                                minSize=(int(w * 0.12), int(w * 0.12)))
                eyes_open = len(eyes) > 0
                if not args.no_window:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 170, 80), 2)
                    for ex, ey, ew, eh in eyes:
                        oy = y + int(h * 0.15)
                        cv2.rectangle(frame, (x + ex, oy + ey), (x + ex + ew, oy + ey + eh), (80, 200, 120), 2)
            tracker.update(now, face_found, eyes_open, hour=time.localtime(now).tm_hour,
                           faces=len(faces))

            if not saved_now and tracker.baseline():
                tracker.save_baseline(baseline_file)
                saved_now = True
                print(f"Learned and saved astronaut {band}'s normal "
                      f"({tracker.baseline_blink_rate:.0f} blinks/min). Measuring now.")

            r = tracker.reading()
            if now - last_send >= 1.0:
                ok_send = send(args.server, {**r, "band": band})
                if ok_send != server_ok:
                    print("Connected to the dashboard server." if ok_send else
                          f"Can't reach the server at {args.server}. Is it running?")
                    server_ok = ok_send
                last_send = now

            if not args.no_window:
                t = r["today"]
                if r["calibrating"]:
                    text = f"Astronaut {band} - learning normal... {r['calibration_left']:.0f}s"
                elif many:
                    text = f"Astronaut {band} - {len(faces)} faces in view (paused until one remains)"
                elif not face_found:
                    text = f"Astronaut {band} - no face in view (not measuring)"
                else:
                    text = (f"Astronaut {band}  Blinks {r['blink_rate']:.0f}/min  Closed {r['perclos'] * 100:.0f}%  "
                            f"Fatigue {r['fatigue_score']}")
                cv2.putText(frame, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, f"Today: {t['face_minutes']} min in view, {t['microsleeps']} microsleeps",
                            (12, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
                cv2.putText(frame, "eyes open" if eyes_open else ("eyes closed" if face_found else ""),
                            (12, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 200, 120) if eyes_open else (80, 80, 240), 2)
                cv2.imshow("Smart habitat - cabin camera (q to quit)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
