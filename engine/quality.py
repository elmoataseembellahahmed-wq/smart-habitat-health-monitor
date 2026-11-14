"""Input quality and fault management.

Bad input data must never be read as physiology. Before any health rule runs, every
reading goes through these checks:

  missing        no value arrived (webcam covered or off, input not recorded)
  out_of_range   the value is physically implausible for a living, conscious person
                 (for example a webcam heart rate of 250 bpm means bad lighting or motion)
  stuck          the exact same value for STUCK_DAYS days in a row: a frozen input or
                 driver (real body signals always move a little)
  skipped        an optional self-report (the daily diary) was not filled in

A failed reading is marked "unavailable". It is not scored, not learned from, and the
AI model gets a neutral value instead. Sensor faults are reported separately from
health alerts ("check the glucose patch"), so a broken sensor never raises a health
alarm and never hides behind a green status: the coverage line says how many signals
the status is based on.
"""

from .signals import SIGNALS, CORE_SIGNALS, DEVICES

STUCK_DAYS = 4  # identical readings this many days in a row = frozen sensor

# Plausible range for each signal. Outside it, the problem is the sensor, not the person.
VALID = {
    "heart_rate": (30, 220), "breathing_rate": (4, 60), "fatigue_score": (0, 100),
    "blink_rate": (0, 80), "typing_speed": (1, 200), "typing_errors": (0, 60),
    "reaction_time": (100, 3000), "mouse_tremor": (0, 100), "sleep_hours": (0, 16),
    "mood_score": (0, 100), "stress_words": (0, 200),
}

# Optional self-report signals: a missing value means "not filled in", not a fault.
SELF_REPORT = ("mood_score", "stress_words")
# Integer counts repeat naturally, so the stuck check does not apply to them.
NO_STUCK_CHECK = ("stress_words",)


def check(key, day, days):
    """Return None if the reading is usable, else {"code": ..., "message": ...}."""
    meta = SIGNALS[key]
    value = days[day].get(key)
    if value is None:
        if key in SELF_REPORT:
            return {"code": "skipped", "message": "No diary entry today (it is optional), "
                                                  "so mood was not assessed."}
        return {"code": "missing", "message": f"No {meta['name'].lower()} reading arrived today "
                                              f"(webcam covered or off, or the input was not recorded)."}
    lo, hi = VALID[key]
    if not lo <= value <= hi:
        return {"code": "out_of_range",
                "message": f"{meta['name']} reading of {value:g} {meta['unit']} is not physically "
                           f"plausible (expected {lo:g}-{hi:g}), so it is treated as an input error."}
    if key not in NO_STUCK_CHECK:
        run = [days.get(d, {}).get(key) for d in range(day - STUCK_DAYS + 1, day + 1)]
        if all(v is not None for v in run) and len(set(run)) == 1:
            return {"code": "stuck",
                    "message": f"{meta['name']} has read exactly {value:g} {meta['unit']} for "
                               f"{STUCK_DAYS} days in a row: the input looks frozen."}
    return None


def scan(crew_data):
    """Find every faulty reading. Returns {(aid, day): {key: issue}}."""
    out = {}
    for aid, days in crew_data.items():
        for day in days:
            issues = {k: c for k in CORE_SIGNALS if (c := check(k, day, days))}
            if issues:
                out[(aid, day)] = issues
    return out


DEVICE_ACTION = {
    "camera": "Check the webcam: is it on, uncovered, and is the face well lit?",
    "keyboard": "Check the keyboard and the NABD workstation app.",
    "mouse": "Check the mouse and redo the 60-second reaction test.",
    "checkin": "Complete today's check-in.",
}


def sensor_faults(issues):
    """Group one day's issues by device, for the 'sensor check' part of the report."""
    by_device = {}
    for key, issue in issues.items():
        if issue["code"] == "skipped":
            continue
        dev = SIGNALS[key]["device"]
        item = by_device.setdefault(dev, {"device": dev, "device_name": DEVICES[dev]["name"],
                                          "signals": [], "codes": [], "messages": [],
                                          "action": DEVICE_ACTION.get(dev, "Check the input.")})
        item["signals"].append(key)
        item["codes"].append(issue["code"])
        item["messages"].append(issue["message"])
    return list(by_device.values())


SAFETY_SIGNALS = [k for k in CORE_SIGNALS if "hard_low" in SIGNALS[k] or "hard_high" in SIGNALS[k]]


def coverage(signals):
    """How much of today's picture is based on real, trusted readings."""
    total = len(signals)
    unavailable = [s["signal"] for s in signals if s.get("missing")]
    estimated = [s["signal"] for s in signals if s.get("source") == "estimate"]
    measured = total - len(unavailable)
    safety_gap = [k for k in unavailable if k in SAFETY_SIGNALS]
    if len(unavailable) >= 5:
        confidence = "low"
    elif unavailable or estimated:
        confidence = "limited"
    else:
        confidence = "full"
    note = f"Status based on {measured} of {total} signals"
    if estimated:
        note += f" ({len(estimated)} estimated)"
    if unavailable:
        note += ". Not available today: " + ", ".join(SIGNALS[k]["name"].lower() for k in unavailable)
    if safety_gap:
        note += ". A safety-limit signal is missing, so 'Normal' cannot rule out a problem in it"
    return {"measured": measured, "total": total, "unavailable": unavailable, "estimated": estimated,
            "safety_gap": safety_gap, "confidence": confidence, "note": note + "."}
