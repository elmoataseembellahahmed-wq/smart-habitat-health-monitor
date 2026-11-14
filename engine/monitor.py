"""The HealthMonitor ties the four layers together:

    inputs (simulate.py)  ->  per-signal analysis (analysis.py)
                          ->  fusion and decision (fusion.py)
                          ->  daily report (report.py)
"""

from . import simulate
from .analysis import compute_baseline, analyse_signal, analyse_cabin
from .anomaly import AnomalyModel
from .fusion import fuse, GENERAL_ACTIONS
from .report import build_report
from .arabic import build_report_ar
from .reminders import reminders, normal_streak
from .integrity import band_swap, drift, WRIST_SIGNALS
from . import quality
from . import version
from . import access
from .nasa_resources import risks_for
from .signals import (SIGNALS, CABIN_SIGNALS, DEVICES, BODY_SYSTEMS, CORE_SIGNALS,
                      CAMERA_SIGNALS, MIN_CAMERA_MINUTES, wrist_fatigue)

TREND_DAYS = 5
LEARN_EVERY = 7    # the personal normal (and the AI model) is updated once a week...
LEARN_WINDOW = 30  # ...from the last 30 days that this astronaut was in NORMAL
MIN_LEARN_DAYS = 7  # fewer usable days than this: keep the previous week's normal

BAND_ACTION = "Check that you are wearing your own wristband (the ID is on the band), then swap back if needed."
DRIFT_ACTION = ("Flight surgeon: review the slow change in this astronaut's normal since the start "
                "of the mission (it is too gradual to show on any single day).")


class HealthMonitor:
    def __init__(self, data=None, crew=None, baseline_days=None):
        self.data = data or simulate.generate()
        self.crew = crew or simulate.CREW
        self.baseline_days = baseline_days or simulate.BASELINE_DAYS
        self.days = sorted(self.data["cabin"].keys())
        # Sensor quality first: faulty readings are kept aside and never analysed.
        self.faults = quality.scan(self.data["crew"])
        self.raw_values = {}
        for (aid, day), issues in self.faults.items():
            for key in issues:
                self.raw_values[(aid, day, key)] = self.data["crew"][aid][day].get(key)
                self.data["crew"][aid][day][key] = None
        for crew_days in self.data["crew"].values():
            for reading in crew_days.values():
                reading["wrist_fatigue"] = wrist_fatigue(reading)
        self.baselines = {
            m["id"]: compute_baseline(self.data["crew"][m["id"]], self.baseline_days)
            for m in self.crew
        }
        # AI layer: one Isolation Forest per astronaut, trained on their baseline days.
        self.models = {
            m["id"]: AnomalyModel(self.data["crew"][m["id"]], self.baseline_days,
                                  self.baselines[m["id"]], CORE_SIGNALS)
            for m in self.crew
        }
        self._ai_cache = {}
        self._learned = {}      # update day -> per-astronaut baseline and AI model
        self._rule_states = {}  # (aid, day) -> rule-based state, used to pick learning days
        self._band = {}         # (aid, day) -> wristband swap check result

    # ---------- adding data (manual entry, or a live feed) ----------
    def add_day(self, day, readings, cabin):
        """Add one new mission day: {astronaut id: reading} and the cabin values.
        The new readings go through the same quality checks as everything else."""
        if day in self.data["cabin"]:
            raise ValueError(f"Day {day} already exists")
        for aid, reading in readings.items():
            self.data["crew"][aid][day] = dict(reading)
        self.data["cabin"][day] = dict(cabin)
        self.days.append(day)
        for aid in readings:
            days = self.data["crew"][aid]
            issues = {k: c for k in CORE_SIGNALS if (c := quality.check(k, day, days))}
            if issues:
                self.faults[(aid, day)] = issues
                for key in issues:
                    self.raw_values[(aid, day, key)] = days[day].get(key)
                    days[day][key] = None
            days[day]["wrist_fatigue"] = wrist_fatigue(days[day])

    def share_learning(self, other):
        """Reuse another monitor's learned weeks (same data up to its last day), so a
        copy for manual testing starts instantly instead of re-learning the mission."""
        self._learned.update(other._learned)
        self._rule_states.update(other._rule_states)
        self._band.update(other._band)
        self._ai_cache.update(other._ai_cache)

    # ---------- continuous learning ----------
    def update_day(self, day):
        """The day the personal normal in use on `day` was last updated."""
        first = max(self.baseline_days) + 1
        if day < first:
            return first
        return first + LEARN_EVERY * ((day - first) // LEARN_EVERY)

    def learning_days(self, aid, day):
        """Days the personal normal in use on `day` was learned from."""
        u = self.update_day(day)
        if u == max(self.baseline_days) + 1:
            return list(self.baseline_days)
        window = [d for d in range(u - LEARN_WINDOW, u) if d in self.data["crew"][aid]]
        days = [d for d in window if not self.band_check(aid, d)
                and (d in self.baseline_days or self._rule_state(aid, d) == "NORMAL")]
        if len(days) < MIN_LEARN_DAYS:
            return self.learning_days(aid, u - 1)   # too few healthy days: keep last week's normal
        return days

    def _learned_for(self, aid, day):
        key = (aid, self.update_day(day))
        if key not in self._learned:
            days = self.learning_days(aid, day)
            crew_days = self.data["crew"][aid]
            base = compute_baseline(crew_days, days)
            self._learned[key] = {"days": days, "baseline": base,
                                  "model": AnomalyModel(crew_days, days, base, CORE_SIGNALS)}
        return self._learned[key]

    def baseline_for(self, aid, day):
        return self._learned_for(aid, day)["baseline"]

    def band_check(self, aid, day):
        """Swap check: does this astronaut's band read like another astronaut's normal today?"""
        key = (aid, day)
        if key not in self._band:
            self._band[key] = None   # placeholder while computing
            if day in self.baseline_days:
                res = None           # the normal is still being learned: nothing to compare with
            else:
                res = band_swap(aid, day, self.data["crew"], self.baseline_for,
                                [m["id"] for m in self.crew])
            self._band[key] = res
        return self._band[key]

    def camera_seen(self, aid, day):
        return self.data["crew"][aid][day].get("camera_minutes", 999) >= MIN_CAMERA_MINUTES

    def _signals(self, aid, day, base):
        """Layer 2 for every signal. If the cameras saw too little of this astronaut today,
        the camera readings are not trusted and fatigue comes from the wristband instead."""
        days = self.data["crew"][aid]
        seen = self.camera_seen(aid, day)
        swap = self.band_check(aid, day)
        issues = self.faults.get((aid, day), {})
        out = []
        for k in CORE_SIGNALS:
            if k in issues:
                entry = self._not_trusted(k, base, issues[k]["message"])
                entry.update(untrusted=False, fault=issues[k]["code"])
                out.append(entry)
            elif swap and k in WRIST_SIGNALS:
                out.append(self._not_trusted(k, base, f"This band seems to be on another astronaut's wrist "
                                             f"today, so its {SIGNALS[k]['name'].lower()} reading was not used."))
            elif k in CAMERA_SIGNALS and not seen:
                if swap and k == "fatigue_score":
                    out.append(self._not_trusted(k, base, "The cameras saw too little today and the wristband "
                                                 "seems swapped, so fatigue could not be measured."))
                else:
                    out.append(self._camera_fallback(k, day, days, base))
            else:
                out.append(analyse_signal(k, day, days, base))
        return out

    @staticmethod
    def _not_trusted(key, base, note):
        meta = SIGNALS[key]
        return {"signal": key, "name": meta["name"], "unit": meta["unit"], "device": meta["device"],
                "system": meta["system"], "domain": meta["domain"], "value": None,
                "baseline": round(base[key]["mean"], 2), "z": 0.0, "level": None, "streak_days": 0,
                "limit": None, "reason": None, "missing": True, "untrusted": True, "note": note}

    def _camera_fallback(self, key, day, days, base):
        minutes = days[day].get("camera_minutes", 0)
        note = (f"The cameras saw this astronaut for only {minutes} min today "
                f"(at least {MIN_CAMERA_MINUTES} min needed)")
        if key == "fatigue_score" and days[day].get("wrist_fatigue") is None:
            return self._not_trusted(key, base, note + ", and the wristband readings needed for an "
                                     "estimate are unavailable, so fatigue was not measured.")
        if key == "fatigue_score":
            a = analyse_signal("wrist_fatigue", day, days, base)
            a.update(signal="fatigue_score", source="wristband", camera_minutes=minutes,
                     note=note + ", so fatigue was estimated from the wristband (sleep, HRV, heart rate).")
            if a["reason"]:
                a["reason"] = note + ", so fatigue was estimated from the wristband. " + a["reason"]
            return a
        meta = SIGNALS[key]
        return {"signal": key, "name": meta["name"], "unit": meta["unit"], "device": meta["device"],
                "system": meta["system"], "domain": meta["domain"], "value": None,
                "baseline": round(base[key]["mean"], 2), "z": 0.0, "level": None, "streak_days": 0,
                "limit": None, "reason": None, "missing": True, "camera_minutes": minutes,
                "note": note + ", so this was not measured."}

    def _rule_state(self, aid, day):
        key = (aid, day)
        if key not in self._rule_states:
            signals = self._signals(aid, day, self.baseline_for(aid, day))
            self._rule_states[key] = fuse(signals, analyse_cabin(day, self.data["cabin"]))["state"]
        return self._rule_states[key]

    # ---------- helpers ----------
    def member(self, aid):
        for m in self.crew:
            if m["id"] == aid:
                return m
        raise KeyError(f"Unknown crew member: {aid}")

    def _check_day(self, day):
        if day not in self.data["cabin"]:
            raise KeyError(f"No data for day {day}. Available: {self.days[0]}-{self.days[-1]}")

    # ---------- core ----------
    def assess(self, aid, day):
        """Run layers 2 and 3 for one astronaut on one day."""
        self._check_day(day)
        days = self.data["crew"][aid]
        signals = self._signals(aid, day, self.baseline_for(aid, day))
        cabin = analyse_cabin(day, self.data["cabin"])
        decision = fuse(signals, cabin)
        decision["signals"] = signals
        decision["cabin"] = cabin
        self._integrity(aid, day, decision)
        issues = self.faults.get((aid, day), {})
        decision["sensor_faults"] = quality.sensor_faults(issues)
        decision["self_report_skipped"] = any(i["code"] == "skipped" for i in issues.values())
        decision["coverage"] = quality.coverage(signals)
        decision["nasa_risks"] = risks_for(decision)
        learned = self.learning_days(aid, day)
        decision["versions"] = {**version.stamp(),
                                "personal_normal": f"{aid}-day{self.update_day(day)}",
                                "learned_from_days": [min(learned), max(learned), len(learned)]}
        decision["ai"] = self.ai(aid, day, decision)
        decision["systems"] = body_systems(signals, cabin, self.exercise(aid, day))
        return decision

    def _integrity(self, aid, day, decision):
        """Add the wristband swap check and the slow-drift check to a day's decision."""
        swap = self.band_check(aid, day)
        decision["band_check"] = None
        if swap:
            other = self.member(swap["with"])
            decision["band_check"] = {
                "with": swap["with"], "with_name": other["name"],
                "message": (f"Today's wristband readings match {other['name']}'s normal, and "
                            f"{other['name']}'s band matches this astronaut's. The bands were probably "
                            "swapped. No health alarm is raised from them: the wristband readings were "
                            "set aside for today."),
            }
            decision["actions"] = [BAND_ACTION] + [a for a in decision["actions"]
                                                   if a != "No action needed. Keep the normal schedule."]
        drifted = drift(self.baselines[aid], self.baseline_for(aid, day)) if day not in self.baseline_days else []
        decision["drift"] = drifted
        if drifted:
            if decision["state"] == "NORMAL":
                decision["state"] = "WATCH"
                if decision["actions"] == ["No action needed. Keep the normal schedule."]:
                    decision["actions"] = []
            decision["rules_fired"].append(
                "Slow drift: this astronaut's normal has moved far from the start of the mission in: "
                + ", ".join(x["name"].lower() for x in drifted) + ".")
            decision["rule_codes"].append({"rule": "drift", "signals": [x["signal"] for x in drifted]})
            decision["actions"].append(DRIFT_ACTION)

    def ai(self, aid, day, decision):
        """Isolation Forest result for one day, compared with the rule-based state."""
        key = (aid, day)
        if key not in self._ai_cache:
            learned = self._learned_for(aid, day)
            reading = dict(self.data["crew"][aid][day])
            if not self.camera_seen(aid, day):
                # Camera values weren't measured: give the model a neutral value for them.
                for k in CAMERA_SIGNALS:
                    reading[k] = learned["baseline"][k]["mean"]
            if self.band_check(aid, day):
                # Swapped band: its readings belong to someone else, so they are neutralised too.
                for k in WRIST_SIGNALS:
                    reading[k] = learned["baseline"][k]["mean"]
            for k in CORE_SIGNALS:
                if reading.get(k) is None:     # unavailable reading: neutral value for the model
                    reading[k] = learned["baseline"][k]["mean"]
            self._ai_cache[key] = learned["model"].assess(reading)
        res = dict(self._ai_cache[key])
        ai_flag = res["level"] != "normal"
        # Cabin-only alerts are about the environment, not the person, so the model
        # (which only sees personal signals) is compared with the personal flags.
        rules_flag = bool(decision["flags"])
        if ai_flag == rules_flag:
            res["agreement"] = "agree"
            res["note"] = ("The AI model and the rules agree: this day is unusual for this astronaut."
                           if ai_flag else "The AI model and the rules agree: this day looks normal.")
        elif ai_flag:
            res["agreement"] = "ai_only"
            res["note"] = ("The AI model finds this day unusual although no single signal crossed a rule. "
                           "Worth a closer look: it may be an unusual combination of small changes.")
        else:
            res["agreement"] = "rules_only"
            res["note"] = ("The rules flagged a signal, but the AI model sees the day as a whole as close "
                           "to normal. Likely a small, isolated change.")
        return res

    def trend(self, aid, day):
        start = max(self.days[0], day - TREND_DAYS + 1)
        return [{"day": d, "state": self.assess(aid, d)["state"]} for d in range(start, day + 1)]

    def routine(self, aid, day):
        """Routine reminders and the streak of days in NORMAL."""
        states = {d: self.assess(aid, d)["state"] for d in self.days if d <= day}
        return {"reminders": reminders(aid, day), "normal_streak": normal_streak(states, day)}

    def status(self, day, role="surgeon"):
        """Whole-crew status for the dashboard, as `role` is allowed to see it."""
        crew = []
        for m in self.crew:
            d = self.assess(m["id"], day)
            crew.append({**m, **d, "trend": self.trend(m["id"], day), "routine": self.routine(m["id"], day),
                         "exercise": self.exercise(m["id"], day)})
        cabin = analyse_cabin(day, self.data["cabin"])
        wide = crew_wide(crew, cabin)
        return {"day": day, "role": role, "crew": [access.view(c, role) for c in crew],
                "cabin": cabin, "crew_wide": wide}

    def exercise(self, aid, day):
        """Exercise adherence over the last 7 days. This protects bones and muscles, but it is
        NOT a measurement of bone density or muscle mass (no daily sensor can measure those)."""
        from .simulate import EXERCISE_PLAN
        week = [self.data["crew"][aid][d].get("exercise_minutes") for d in range(day - 6, day + 1)
                if d in self.data["crew"][aid]]
        met = sum(1 for v in week if v is not None and v >= 60)
        return {"today": self.data["crew"][aid][day].get("exercise_minutes"), "plan": EXERCISE_PLAN,
                "days_met_last_7": met, "days_counted": len(week), "low": met < 4,
                "note": (f"Exercise done on {met} of the last {len(week)} days (60+ min). "
                         "This is adherence only, not a bone or muscle measurement.")}

    def report(self, aid, day, lang="en", role="surgeon"):
        m = self.member(aid)
        if role not in ("surgeon", "commander", aid):
            return ("الحالة فقط تُشارك مع زملاء الطاقم. التفاصيل خاصة."
                    if lang == "ar" else access.CREWMATE_NOTE) + f"  ({m['name']}: {self.assess(aid, day)['state']})"
        d = {**self.assess(aid, day), "routine": self.routine(aid, day),
             "crew_wide": crew_wide([{**x, **self.assess(x["id"], day)} for x in self.crew],
                                    analyse_cabin(day, self.data["cabin"]))}
        d = access.view({**m, **d}, role)
        build = build_report_ar if lang == "ar" else build_report
        return build(m, day, d, self.trend(aid, day), d["cabin"])

    def series(self, aid, signal):
        """All values of one signal for one astronaut, plus the baseline, for charts."""
        if signal not in SIGNALS:
            raise KeyError(f"Unknown signal: {signal}")
        base = self.baseline_for(aid, self.days[-1])[signal]
        return {
            "signal": signal, **SIGNALS[signal],
            "baseline_mean": round(base["mean"], 2),
            "baseline_sd": round(base["sd"], 2),
            "points": [{"day": d, "value": self.data["crew"][aid][d][signal]} for d in self.days],
        }

    def mission(self):
        return {
            "first_day": self.days[0],
            "last_day": self.days[-1],
            "baseline_days": [min(self.baseline_days), max(self.baseline_days)],
            "learning": {"every_days": LEARN_EVERY, "window_days": LEARN_WINDOW},
            "crew": self.crew,
            "signals": SIGNALS,
            "cabin_signals": CABIN_SIGNALS,
            "devices": DEVICES,
            "body_systems": BODY_SYSTEMS,
        }


# Signals that cabin CO2 can change in everyone (faster breathing, fatigue, headache-related).
CO2_SENSITIVE = {"breathing_rate", "heart_rate", "fatigue_score", "blink_rate", "spo2", "sleep_hours"}


def crew_wide(crew, cabin):
    """Separate a cabin problem that affects everyone from individual health problems.

    A signal off in 2+ crew members on the same day is a shared change. If the cabin is
    also off and the signal is one cabin air can change, it is likely environmental.
    Without a cabin cause it is reported as a shared change to check (schedule, workload,
    an infection passing between crew), not blamed on the air. On a cabin-alert day, an
    astronaut whose changes go beyond what cabin air explains is flagged as individual too.
    """
    cabin_off = any(c["level"] for c in cabin if c["signal"] == "co2")
    counts = {}
    for m in crew:
        for f in m["flags"]:
            counts.setdefault(f["signal"], []).append(m["id"])
    shared = {k: v for k, v in counts.items() if len(v) >= 2}
    env = sorted(k for k in shared if cabin_off and k in CO2_SENSITIVE)
    other = sorted(k for k in shared if k not in env)
    beyond = []
    if cabin_off:
        for m in crew:
            extra = sorted({f["signal"] for f in m["flags"]} - CO2_SENSITIVE)
            if extra:
                beyond.append({"id": m["id"], "name": m["name"], "signals": extra})
    notes = []
    if env:
        notes.append(f"Shared by {len(set(sum((shared[k] for k in env), [])))} crew members with cabin CO2 "
                     f"raised: {', '.join(SIGNALS[k]['name'].lower() for k in env)}. Likely environmental: "
                     "fix the air first.")
    if other:
        notes.append("Shared change with no cabin cause found: "
                     + ", ".join(SIGNALS[k]["name"].lower() for k in other)
                     + ". Treated as individual issues; check shared causes (schedule, workload, infection).")
    for b in beyond:
        notes.append(f"{b['name']}: changes beyond what cabin air explains "
                     f"({', '.join(SIGNALS[k]['name'].lower() for k in b['signals'])}), so this is also an "
                     "individual health pattern, not only the air.")
    return {"environmental": env, "shared_no_cabin_cause": other, "beyond_cabin": beyond, "notes": notes}


LEVEL_RANK = {None: 0, "mild": 1, "strong": 2, "critical": 3}
SYSTEM_STATUS = {0: "normal", 1: "watch", 2: "act", 3: "act"}


def body_systems(signals, cabin, exercise=None):
    """Status of each body system for the body figure: the worst of its signals.

    One mild flag gives 'watch'; a strong or safety-limit flag gives 'act'. Lungs also
    turn 'watch'/'act' with the cabin CO2 level, since that is what they breathe.
    Bones and muscles have no daily sensor, so they show 'info'.
    """
    out = {}
    for key, meta in BODY_SYSTEMS.items():
        mine = [s for s in signals if s["system"] == key]
        rank = max((LEVEL_RANK[s["level"]] for s in mine), default=0)
        status = SYSTEM_STATUS[rank] if mine else "info"
        if key == "lungs":
            co2 = next((c for c in cabin if c["signal"] == "co2"), None)
            if co2 and co2["level"] == "act":
                status = "act"
            elif co2 and co2["level"] == "watch" and status == "normal":
                status = "watch"
        actions = []
        for s in mine:
            a = GENERAL_ACTIONS.get(s["signal"]) if s["level"] else None
            if a and a not in actions:
                actions.append(a)
        if key == "lungs" and status != "normal" and not actions:
            actions.append("Check cabin CO2 and the air scrubber.")
        if key == "bones":
            if exercise and exercise["low"]:
                status = "watch"
                actions.append(exercise["note"] + " Get back to the daily exercise plan: it is the main "
                               "protection for bones and muscles.")
            else:
                if exercise:
                    actions.append(exercise["note"])
                actions.append("Keep the daily resistance exercise session: it is the main protection for bones and muscles.")
        if not actions:
            actions.append("Nothing to do. Keep the normal routine.")
        out[key] = {
            "status": status,
            "signals": [s["signal"] for s in mine],
            "flags": [s["signal"] for s in mine if s["level"]],
            "actions": actions,
        }
    return out
