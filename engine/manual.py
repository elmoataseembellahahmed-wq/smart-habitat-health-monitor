"""Manual testing: type readings in by hand, or upload a whole mission as a CSV file.

Two ways to test every part of the system with your own numbers:

1. Quick check (one day at a time)
   Starts from the demo mission (so every astronaut already has a learned personal
   normal) and adds NEW days after its last day. You type one astronaut's readings for
   the next day; the other astronauts get a real normal day of their own, so they stay
   quiet. Add several days in a row to test streaks (ACT needs 2+ days), the frozen-sensor
   check (the same value 4 days running) or a slow change. Leave a box empty to test a
   missing reading.

2. Whole mission (CSV)
   Fill in the template (one row per astronaut per day, your own crew, days 1..N with
   N >= 15) and upload it. The system learns each person's normal from days 1-14 and
   judges every day after that, so you can test anything: swapped bands, crew-wide
   cabin events, slow drift, sensor faults.
"""

import csv
import io

from . import simulate
from .monitor import HealthMonitor
from .signals import CORE_SIGNALS, CABIN_SIGNALS

EXTRA = ["camera_minutes", "exercise_minutes", "personal_dose"]
COLUMNS = (["day", "astronaut_id", "astronaut_name", "role"] + CORE_SIGNALS + EXTRA
           + ["symptoms", "cabin_co2", "radiation"])
MIN_DAYS = 15  # 14 days to learn the normal + at least one day to judge


def _num(text):
    text = (text or "").strip()
    if text == "":
        return None
    return float(text)


def summary(m, aid, day):
    """The parts of one decision the manual page shows."""
    d = m.assess(aid, day)
    return {"day": day, "state": d["state"], "score": d["score"], "ai": d["ai"]["level"],
            "confidence": d["coverage"]["confidence"],
            "sensor_check": [f["device_name"] for f in d["sensor_faults"]],
            "band_check": d["band_check"]["with_name"] if d["band_check"] else None,
            "drift": [x["signal"] for x in d["drift"]]}


# ---------------------------------------------------------------- quick check
class QuickCheck:
    def __init__(self, base_monitor):
        self.base = base_monitor
        self.reset()

    def reset(self):
        self.m = HealthMonitor()
        self.m.share_learning(self.base)
        self.added = []          # [{"day", "aid"}]

    def next_day(self):
        return self.m.days[-1] + 1

    def _normal_day(self, aid, n):
        """A real normal day of this astronaut (a different one each time, so the
        frozen-sensor check is not triggered by repeated identical values)."""
        days = self.m.learning_days(aid, self.next_day())
        src = days[-1 - (n % len(days))]
        r = self.m.data["crew"][aid][src]
        return {k: r.get(k) for k in CORE_SIGNALS + EXTRA}

    def defaults(self, aid):
        self.m.member(aid)
        base = self.m.baseline_for(aid, self.next_day())
        return {"day": self.next_day(), "aid": aid,
                "values": self._normal_day(aid, len(self.added)),
                "normal": {k: round(base[k]["mean"], 2) for k in CORE_SIGNALS},
                "cabin": {"co2": 2.2, "radiation": 0.48}}

    def add(self, aid, values, cabin):
        self.m.member(aid)
        day = self.next_day()
        reading = {}
        for k in CORE_SIGNALS + EXTRA:
            v = values.get(k)
            reading[k] = None if v in (None, "") else float(v)
        if reading["camera_minutes"] is None:
            reading["camera_minutes"] = 240.0
        reading["symptoms"] = [s for s in (values.get("symptoms") or []) if s]
        readings = {m["id"]: self._normal_day(m["id"], len(self.added)) for m in self.m.crew if m["id"] != aid}
        readings[aid] = reading
        co2, rad = cabin.get("co2"), cabin.get("radiation")
        self.m.add_day(day, readings, {"co2": float(2.2 if co2 in (None, "") else co2),
                                       "radiation": float(0.48 if rad in (None, "") else rad)})
        self.added.append({"day": day, "aid": aid})
        return self.result(aid, day)

    def result(self, aid, day):
        d = self.m.assess(aid, day)
        return {"day": day, "aid": aid, "decision": {k: v for k, v in d.items()},
                "report_en": self.m.report(aid, day), "report_ar": self.m.report(aid, day, "ar"),
                "history": [summary(self.m, x["aid"], x["day"]) | {"aid": x["aid"]} for x in self.added]}


# ---------------------------------------------------------------- whole mission
def template_csv(full=False):
    """A CSV to fill in. full=False: days 1-20 of the demo crew as an example to extend;
    full=True: the whole demo mission, to edit and re-upload."""
    data = simulate.generate()
    last = simulate.MISSION_END if full else 20
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(COLUMNS)
    for day in range(1, last + 1):
        for m in simulate.CREW:
            r = data["crew"][m["id"]][day]
            w.writerow([day, m["id"], m["name"], m["role"]]
                       + ["" if r.get(k) is None else r[k] for k in CORE_SIGNALS + EXTRA]
                       + [";".join(r.get("symptoms") or [])]
                       + [data["cabin"][day]["co2"], data["cabin"][day]["radiation"]])
    return out.getvalue()


def parse_csv(text):
    """Return (data, crew, errors). Errors name the row and column."""
    errors = []
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    missing = [c for c in ["day", "astronaut_id"] + CORE_SIGNALS + ["cabin_co2", "radiation"]
               if c not in (reader.fieldnames or [])]
    if missing:
        return None, None, [f"Missing columns: {', '.join(missing)}. Download the template to see them all."]
    crew, data = {}, {"crew": {}, "cabin": {}}
    for i, row in enumerate(reader, start=2):
        try:
            day = int(float(row["day"]))
        except (TypeError, ValueError):
            errors.append(f"Row {i}: 'day' must be a whole number.")
            continue
        aid = (row.get("astronaut_id") or "").strip()
        if not aid:
            errors.append(f"Row {i}: 'astronaut_id' is empty.")
            continue
        crew.setdefault(aid, {"id": aid, "name": (row.get("astronaut_name") or aid).strip() or aid,
                              "role": (row.get("role") or "Crew member").strip() or "Crew member"})
        reading = {}
        for k in CORE_SIGNALS + EXTRA:
            try:
                reading[k] = _num(row.get(k))
            except ValueError:
                errors.append(f"Row {i}: '{k}' is not a number ({row.get(k)!r}).")
                reading[k] = None
        if reading["camera_minutes"] is None:
            reading["camera_minutes"] = 240.0
        reading["symptoms"] = [s.strip().lower() for s in (row.get("symptoms") or "").split(";") if s.strip()]
        if day in data["crew"].setdefault(aid, {}):
            errors.append(f"Row {i}: astronaut {aid} already has a row for day {day}.")
        data["crew"][aid][day] = reading
        try:
            co2, rad = _num(row.get("cabin_co2")), _num(row.get("radiation"))
        except ValueError:
            errors.append(f"Row {i}: cabin_co2 and radiation must be numbers.")
            continue
        if co2 is not None and rad is not None:
            data["cabin"].setdefault(day, {"co2": co2, "radiation": rad})
    if errors:
        return None, None, errors[:20]
    if not data["crew"]:
        return None, None, ["The file has no data rows."]
    days = sorted(data["cabin"])
    if days != list(range(1, len(days) + 1)) or len(days) < MIN_DAYS:
        errors.append(f"Days must run 1, 2, 3 ... without gaps, with at least {MIN_DAYS} days "
                      f"(14 to learn each person's normal). Found {len(days)} day(s) with cabin values.")
    for aid, days_of in data["crew"].items():
        gap = sorted(set(days) - set(days_of))
        if gap:
            errors.append(f"Astronaut {aid} has no row for day(s) {gap[:10]}.")
        for d in range(1, 15):
            r = days_of.get(d, {})
            empty = [k for k in CORE_SIGNALS if r.get(k) is None]
            if len(empty) > 3:
                errors.append(f"Astronaut {aid}, day {d}: too many empty values during the learning days.")
                break
    if errors:
        return None, None, errors[:20]
    return data, list(crew.values()), []


class Upload:
    def __init__(self):
        self.m = None

    def load(self, text):
        data, crew, errors = parse_csv(text)
        if errors:
            return {"ok": False, "errors": errors}
        self.m = HealthMonitor(data=data, crew=crew)
        grid = {m["id"]: [summary(self.m, m["id"], d) for d in self.m.days if d > 14] for m in crew}
        wide = {d: self.m.status(d)["crew_wide"]["notes"] for d in self.m.days if d > 14}
        return {"ok": True, "crew": crew, "days": [self.m.days[0], self.m.days[-1]], "grid": grid,
                "crew_wide": {d: n for d, n in wide.items() if n}}

    def report(self, aid, day, lang="en"):
        if not self.m:
            raise KeyError("No mission uploaded yet")
        return self.m.report(aid, day, lang)


CABIN_NAMES = {k: v["name"] for k, v in CABIN_SIGNALS.items()}
