"""Turns a stream of "eyes open / eyes closed" observations into fatigue measures.

Kept separate from the webcam code so it can be tested without a camera.

All-day mode: the cabin cameras watch whenever an astronaut faces them, so the
tracker keeps two views:
  * the last minute (default 60 s), for instant alerts:
      blink_rate     blinks per minute (a closure of 0.05-0.5 s between two open states)
      perclos        share of time the eyes are closed (standard drowsiness measure)
      long_closures  closures of 0.5 s or more (possible microsleep)
  * the whole day so far, for the daily fatigue picture:
      minutes the face was in view, overall eye closure, blinks, microsleeps,
      and the hour when eye closure was highest.
The personal baseline is learned once (calibration) and can be saved and loaded,
so it carries over between sessions instead of being re-learned every time.
"""

import json
from collections import deque, defaultdict
from datetime import datetime

BLINK_MIN_S = 0.05
BLINK_MAX_S = 0.5


class BlinkTracker:
    def __init__(self, calibration_s=60.0, window_s=60.0, baseline=None, min_closed_frames=2):
        self.calibration_s = calibration_s
        self.window_s = window_s
        # Smoothing: the eye detector sometimes misses an open eye for a single frame.
        # A closure only counts once it has lasted `min_closed_frames` frames in a row,
        # and is then timed from its first frame.
        self.min_closed_frames = max(1, int(min_closed_frames))
        self._miss_run = 0
        self._first_miss_t = None
        self.start = None
        self.samples = deque()        # (t, eyes_open) for face-visible frames, last window
        self.events = deque()         # (t_end, kind) kind in {"blink", "long"}, last window
        self.closed_since = None
        self.last_t = None
        self.last_face_t = None
        self.face_detected = False
        self.multiple_faces = False     # two or more faces in view: frame is not measured
        self.day_multi_face_frames = 0
        self.baseline_blink_rate = None
        self.baseline_perclos = None
        self.calibration_face_s = 0.0
        # whole-day totals
        self.day_face_s = 0.0
        self.day_closed_s = 0.0
        self.day_blinks = 0
        self.day_microsleeps = 0
        self.hourly = defaultdict(lambda: [0.0, 0.0])   # hour -> [closed_s, face_s]
        if baseline:
            self.baseline_blink_rate = baseline["blink_rate"]
            self.baseline_perclos = baseline["perclos"]

    # ---------- feeding frames ----------
    def update(self, t, face_detected, eyes_open, hour=None, faces=None):
        """Feed one frame observation at time t (seconds). `hour` = clock hour of the frame.

        `faces` = number of faces the camera found. With two or more people in view the
        system cannot be sure whose eyes it is watching, so it does not guess: the frame
        is skipped, exactly as if nobody were in view, until only one face remains.
        """
        if self.start is None:
            self.start = t
        self.multiple_faces = faces is not None and faces > 1
        if self.multiple_faces:
            self.day_multi_face_frames += 1
            face_detected = False
        dt = 0.0 if self.last_face_t is None else min(t - self.last_face_t, 1.0)
        self.last_t = t
        self.face_detected = face_detected
        if not face_detected:
            # The astronaut is not facing a camera: nothing to measure. This is normal
            # in all-day mode; the gap is simply skipped.
            self.closed_since = None
            self.last_face_t = None
            self._miss_run = 0
            return
        if hour is None:
            hour = datetime.now().hour
        # Smoothing (see __init__): hold a possible closure until it is confirmed.
        confirmed_start = None
        if eyes_open:
            self._miss_run = 0
        else:
            self._miss_run += 1
            if self._miss_run == 1:
                self._first_miss_t = t
            if self._miss_run < self.min_closed_frames:
                eyes_open = True              # not confirmed yet: treat as open
            elif self._miss_run == self.min_closed_frames:
                confirmed_start = self._first_miss_t
        # whole-day time accounting (time since the previous face frame)
        self.day_face_s += dt
        self.hourly[hour][1] += dt
        if self.samples and not self.samples[-1][1]:
            self.day_closed_s += dt
            self.hourly[hour][0] += dt
        if self.baseline_blink_rate is None:
            self.calibration_face_s += dt
        self.last_face_t = t

        self.samples.append((t, eyes_open))
        if not eyes_open and self.closed_since is None:
            self.closed_since = confirmed_start if confirmed_start is not None else t
        elif eyes_open and self.closed_since is not None:
            duration = t - self.closed_since
            if BLINK_MIN_S <= duration < BLINK_MAX_S:
                self.events.append((t, "blink"))
                self.day_blinks += 1
            elif duration >= BLINK_MAX_S:
                self.events.append((t, "long"))
                self.day_microsleeps += 1
            self.closed_since = None
        self._trim(t)
        # Calibrate on face-visible time, so looking away doesn't count.
        if self.baseline_blink_rate is None and self.calibration_face_s >= self.calibration_s:
            m = self._measure()
            # Floors avoid a baseline of zero if the person barely blinked while calibrating.
            self.baseline_blink_rate = max(m["blink_rate"], 8.0)
            self.baseline_perclos = max(m["perclos"], 0.02)

    def _trim(self, t):
        while self.samples and t - self.samples[0][0] > self.window_s:
            self.samples.popleft()
        while self.events and t - self.events[0][0] > self.window_s:
            self.events.popleft()

    def _measure(self):
        if len(self.samples) < 2:
            return {"blink_rate": 0.0, "perclos": 0.0, "long_closures": 0}
        span = max(self.samples[-1][0] - self.samples[0][0], 1e-6)
        closed = 0.0
        prev = None
        for t, is_open in self.samples:
            if prev is not None and not prev[1]:
                closed += min(t - prev[0], 1.0)  # ignore gaps when the face was out of view
            prev = (t, is_open)
        blinks = sum(1 for _, k in self.events if k == "blink")
        return {
            "blink_rate": blinks * 60.0 / span,
            "perclos": min(closed / span, 1.0),
            "long_closures": sum(1 for _, k in self.events if k == "long"),
        }

    # ---------- baseline persistence ----------
    def baseline(self):
        if self.baseline_blink_rate is None:
            return None
        return {"blink_rate": round(self.baseline_blink_rate, 2), "perclos": round(self.baseline_perclos, 4)}

    def save_baseline(self, path):
        b = self.baseline()
        if b:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(b, f)

    @staticmethod
    def load_baseline(path):
        try:
            with open(path, encoding="utf-8") as f:
                b = json.load(f)
            return {"blink_rate": float(b["blink_rate"]), "perclos": float(b["perclos"])}
        except (OSError, ValueError, KeyError):
            return None

    # ---------- output ----------
    def today(self):
        """The whole-day fatigue picture so far."""
        peak = None
        rows = [(h, c / f) for h, (c, f) in self.hourly.items() if f >= 60]  # hours with 1+ min in view
        if rows:
            h, p = max(rows, key=lambda r: r[1])
            peak = {"hour": h, "perclos": round(p, 3)}
        return {
            "face_minutes": round(self.day_face_s / 60, 1),
            "perclos": round(self.day_closed_s / self.day_face_s, 3) if self.day_face_s else 0.0,
            "blinks": self.day_blinks,
            "microsleeps": self.day_microsleeps,
            "skipped_multi_face_frames": self.day_multi_face_frames,
            "peak_hour": peak,
        }

    def reading(self):
        """Current reading, ready to send to the backend."""
        m = self._measure()
        calibrating = self.baseline_blink_rate is None
        left = max(0.0, self.calibration_s - self.calibration_face_s) if calibrating else 0.0
        # Fatigue score 0-100: eye closure carries most weight, long closures add more.
        fatigue = min(100.0, m["perclos"] / 0.15 * 50 + m["long_closures"] * 15
                      + max(0.0, m["blink_rate"] - (self.baseline_blink_rate or m["blink_rate"])) * 1.5)
        return {
            "face_detected": self.face_detected,
            "multiple_faces": self.multiple_faces,
            "calibrating": calibrating,
            "calibration_left": round(left, 1),
            "blink_rate": round(m["blink_rate"], 1),
            "perclos": round(m["perclos"], 3),
            "long_closures": m["long_closures"],
            "fatigue_score": round(fatigue),
            "baseline_blink_rate": None if calibrating else round(self.baseline_blink_rate, 1),
            "baseline_perclos": None if calibrating else round(self.baseline_perclos, 3),
            "today": self.today(),
        }
