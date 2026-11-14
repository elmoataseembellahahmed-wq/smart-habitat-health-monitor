"""Live cabin-camera assessment, filed per wristband.

The camera script (camera/live_camera.py) measures, from a real webcam:
  * blink rate (blinks per minute)
  * PERCLOS: the share of time the eyes are closed, a standard drowsiness measure
  * long eye closures (0.5 s or more), a sign of microsleep
  * a whole-day summary: minutes in view, overall eye closure, microsleeps, worst hour
Each reading carries the ID of the wristband nearest the camera. The wristband says
WHO is in front of the camera, so no face recognition is needed.

This module turns the latest reading for each band into a state with reasons, using
the same idea as the rest of the system: compare to the person's OWN normal.
"""

import time

from .simulate import CREW

STALE_SECONDS = 10  # no reading for this long = that camera is disconnected

_latest = {}  # band -> {"reading": ..., "received_at": ...}


def store(reading):
    band = str(reading.get("band", "B")).upper()
    _latest[band] = {"reading": {**reading, "band": band}, "received_at": time.time()}


def assess(reading):
    if reading.get("calibrating"):
        return {"state": "CALIBRATING", "reasons": [
            f"Learning this person's normal blinking and eye closure "
            f"({reading.get('calibration_left', 0):.0f} s of face time left). Look at the screen normally."],
            "actions": []}
    if reading.get("multiple_faces"):
        return {"state": "PAUSED", "reasons": [
            "Two or more faces are in front of this camera. The system cannot be sure whose eyes "
            "it is watching, so it does not guess: it pauses until only one face is in view.",
            "No face recognition is used. The cameras run all day, so a few paused moments "
            "don't affect the daily fatigue picture."], "actions": []}
    if not reading.get("face_detected"):
        return {"state": "NOT IN VIEW", "reasons": [
            "Nobody is facing this camera right now. That's normal: the cameras measure "
            "whenever a face is in view.",
            "If the cameras see someone for less than 30 minutes in a day, the system does not "
            "guess from the camera: it estimates fatigue from their wristband (sleep, heart rate "
            "variability, heart rate) and says so in the report."], "actions": []}

    base_rate = reading.get("baseline_blink_rate") or 0
    base_perclos = reading.get("baseline_perclos") or 0
    rate = reading.get("blink_rate", 0)
    perclos = reading.get("perclos", 0)
    long_closures = reading.get("long_closures", 0)

    reasons, points = [], 0
    if rate > max(base_rate * 1.5, base_rate + 6):
        points += 1
        reasons.append(f"Blink rate is {rate:.0f}/min, up from this person's normal of "
                       f"{base_rate:.0f}/min (a fatigue sign).")
    perclos_limit = max(0.15, base_perclos * 2)
    if perclos > perclos_limit:
        points += 2
        reasons.append(f"Eyes are closed {perclos * 100:.0f}% of the time "
                       f"(normal {base_perclos * 100:.0f}%, alert above {perclos_limit * 100:.0f}%).")
    if long_closures >= 1:
        points += 2 if long_closures >= 2 else 1
        reasons.append(f"{long_closures} long eye closure(s) of 0.5 s or more in the last minute "
                       "(possible microsleep).")

    if long_closures >= 2 or points >= 4:
        state = "ACT"
    elif points >= 1:
        state = "WATCH"
    else:
        state = "NORMAL"
        reasons.append("Blinking and eye closure are within this person's normal.")
    if reading.get("confidence") == "low":
        # Too little face time in the last minute: the camera alone never triggers ACT.
        reasons.append(f"Low confidence: the face was in view only {reading.get('face_seconds_last_window', 0):.0f} s "
                       "of the last minute.")
        if state == "ACT":
            state = "WATCH"

    actions = {
        "NORMAL": [],
        "WATCH": ["Take a short break and rest the eyes before the next demanding task."],
        "ACT": ["Check in with the astronaut now. If they confirm they are drowsy, pause safety-critical "
                "work (robotic arm, docking, EVA prep) and rest. The camera is a warning, not a diagnosis.",
                "Notify the commander and log the event for the flight surgeon."],
    }[state]
    return {"state": state, "reasons": reasons, "actions": actions}


def _owner(band):
    return next((m for m in CREW if m["id"] == band), None)


def latest():
    """Live readings from every camera that reported in the last few seconds."""
    now = time.time()
    out = []
    for band, item in sorted(_latest.items()):
        if now - item["received_at"] > STALE_SECONDS:
            continue
        r = item["reading"]
        owner = _owner(band)
        out.append({"band": band, "astronaut": owner["name"] if owner else f"band {band}",
                    "age_seconds": round(now - item["received_at"], 1), **r, **assess(r)})
    return {"connected": bool(out), "readings": out}
