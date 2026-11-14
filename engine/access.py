"""Who can see what (role-based access) and an audit log of who looked.

Roles:
  surgeon    flight surgeon: sees everything for every astronaut.
  commander  sees every astronaut's health status, vital signs and actions, but NOT the
             private self-report (mood and diary words): those stay between the astronaut
             and the flight surgeon.
  A / B / C  an astronaut: sees their own data in full; for crewmates, only the status
             (Normal / Watch / Act), nothing else.

This is the access POLICY, enforced by the server for every status and report request.
Real login (passwords, badges) is out of scope for the prototype: the role is chosen
in the dashboard, and every view is written to the audit log.
"""

import copy
import time

ROLES = ("surgeon", "commander")
PRIVATE_SIGNALS = ("mood_score", "stress_words")
PRIVATE_NOTE = "Private self-report: shared only with the astronaut and the flight surgeon."
CREWMATE_NOTE = "Only the status is shared with crewmates. Details stay private."

_audit = []  # (time, role, astronaut, what)


def valid_role(role, crew_ids):
    return role in ROLES or role in crew_ids


def log(role, aid, what):
    _audit.append({"time": round(time.time()), "role": role, "astronaut": aid, "what": what})
    del _audit[:-1000]


def audit():
    return list(_audit)


def series_view(series, aid, role):
    """History charts follow the same rules: private self-report and crewmates' data are hidden."""
    if role in ("surgeon", aid) or (role == "commander" and series["signal"] not in PRIVATE_SIGNALS):
        return series
    return {**series, "private": True, "baseline_mean": None,
            "points": [{"day": p["day"], "value": None} for p in series["points"]]}


def view(entry, role):
    """Return the part of one astronaut's assessment that `role` may see."""
    aid = entry["id"]
    if role in ("surgeon", aid):
        return {**entry, "access": "full"}
    if role == "commander":
        e = copy.deepcopy(entry)
        for s in e.get("signals", []):
            if s["signal"] in PRIVATE_SIGNALS:
                s.update(value=None, missing=True, private=True, note=PRIVATE_NOTE, baseline=None)
        for f in e.get("flags", []):
            if f["signal"] in PRIVATE_SIGNALS:
                f.update(value=None, private=True, reason="A private self-report signal is outside this astronaut's "
                                            "normal (details: flight surgeon only).")
        e["access"] = "commander"
        return e
    # A crewmate: status only.
    keep = {k: entry[k] for k in ("id", "name", "role", "state", "trend") if k in entry}
    return {**keep, "access": "crewmate", "restricted": True, "note": CREWMATE_NOTE,
            "score": None, "flags": [], "patterns": [], "signals": [], "rules_fired": [], "actions": [],
            "systems": {}, "ai": None, "routine": None, "coverage": None, "drift": [], "band_check": None,
            "sensor_faults": []}
