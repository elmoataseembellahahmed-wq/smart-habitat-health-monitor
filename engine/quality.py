"""Entry quality and error management.

A typing mistake or a skipped entry must never be read as physiology. Before any health rule runs, every
reading goes through these checks:

  missing        no value was entered (or the webcam saw nothing)
  out_of_range   the value is physically implausible for a living, conscious person
                 (for example 3.67 °C is a typo for 36.7 °C)
  stuck          the exact same value for STUCK_DAYS days in a row: probably copied from a
                 previous day (real body signals always move a little)
  skipped        an optional self-report (the daily diary) was not filled in

A failed reading is marked "unavailable". It is not scored, not learned from, and the
AI model gets a neutral value instead. Entry errors are reported separately from
health alerts ("re-enter your blood sugar"), so a typo never raises a health
alarm and never hides behind a green status: the coverage line says how many signals
the status is based on.
"""

from .signals import SIGNALS, CORE_SIGNALS, DEVICES

STUCK_DAYS = 4  # identical values this many days in a row = probably copied

# Plausible range for each signal. Outside it, the problem is the entry, not the person.
VALID = {
    "heart_rate": (25, 220), "spo2": (60, 100), "body_temp": (34.0, 42.0),
    "sleep_hours": (0, 16), "breathing_rate": (4, 60), "bp_systolic": (60, 260),
    "bp_diastolic": (30, 160), "glucose": (20, 600), "fatigue_score": (0, 100),
    "blink_rate": (0, 80), "mood_score": (0, 100), "stress_words": (0, 200),
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
                                              f"(not entered)."}
    lo, hi = VALID[key]
    if not lo <= value <= hi:
        return {"code": "out_of_range",
                "message": f"{meta['name']} reading of {value:g} {meta['unit']} is not physically "
                           f"plausible (expected {lo:g}-{hi:g}), so it is treated as a typing error."}
    if key not in NO_STUCK_CHECK:
        run = [days.get(d, {}).get(key) for d in range(day - STUCK_DAYS + 1, day + 1)]
        if all(v is not None for v in run) and len(set(run)) == 1:
            return {"code": "stuck",
                    "message": f"{meta['name']} has read exactly {value:g} {meta['unit']} for "
                               f"{STUCK_DAYS} days in a row: it looks copied from an earlier day."}
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
    "entry": "Re-take the measurement with the medical kit and type it again (check the decimal point).",
    "checkin": "Complete today's check-in.",
    "camera": "Check the laptop webcam: is it on, uncovered, and is the face well lit?",
}


def sensor_faults(issues):
    """Group one day's issues by device, for the "entry check" part of the report."""
    by_device = {}
    for key, issue in issues.items():
        if issue["code"] == "skipped":
            continue
        dev = SIGNALS[key]["device"]
        item = by_device.setdefault(dev, {"device": dev, "device_name": DEVICES[dev]["name"],
                                          "signals": [], "codes": [], "messages": [],
                                          "action": DEVICE_ACTION.get(dev, "Check the entry.")})
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
    if len(unavailable) >= 4:
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
