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
from .signals import SIGNALS, CABIN_SIGNALS, DEVICES, BODY_SYSTEMS

TREND_DAYS = 5


class HealthMonitor:
    def __init__(self, data=None, crew=None, baseline_days=None):
        self.data = data or simulate.generate()
        self.crew = crew or simulate.CREW
        self.baseline_days = baseline_days or simulate.BASELINE_DAYS
        self.days = sorted(self.data["cabin"].keys())
        self.baselines = {
            m["id"]: compute_baseline(self.data["crew"][m["id"]], self.baseline_days)
            for m in self.crew
        }
        # AI layer: one Isolation Forest per astronaut, trained on their baseline days.
        self.models = {
            m["id"]: AnomalyModel(self.data["crew"][m["id"]], self.baseline_days,
                                  self.baselines[m["id"]], SIGNALS)
            for m in self.crew
        }
        self._ai_cache = {}

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
        signals = [analyse_signal(k, day, days, self.baselines[aid]) for k in SIGNALS]
        cabin = analyse_cabin(day, self.data["cabin"])
        decision = fuse(signals, cabin)
        decision["signals"] = signals
        decision["cabin"] = cabin
        decision["ai"] = self.ai(aid, day, decision)
        decision["systems"] = body_systems(signals, cabin)
        return decision

    def ai(self, aid, day, decision):
        """Isolation Forest result for one day, compared with the rule-based state."""
        key = (aid, day)
        if key not in self._ai_cache:
            self._ai_cache[key] = self.models[aid].assess(self.data["crew"][aid][day])
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

    def status(self, day):
        """Whole-crew status for the dashboard."""
        crew = []
        for m in self.crew:
            d = self.assess(m["id"], day)
            crew.append({**m, **d, "trend": self.trend(m["id"], day), "routine": self.routine(m["id"], day)})
        return {"day": day, "crew": crew, "cabin": analyse_cabin(day, self.data["cabin"])}

    def report(self, aid, day, lang="en"):
        m = self.member(aid)
        d = {**self.assess(aid, day), "routine": self.routine(aid, day)}
        build = build_report_ar if lang == "ar" else build_report
        return build(m, day, d, self.trend(aid, day), d["cabin"])

    def series(self, aid, signal):
        """All values of one signal for one astronaut, plus the baseline, for charts."""
        if signal not in SIGNALS:
            raise KeyError(f"Unknown signal: {signal}")
        base = self.baselines[aid][signal]
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
            "crew": self.crew,
            "signals": SIGNALS,
            "cabin_signals": CABIN_SIGNALS,
            "devices": DEVICES,
            "body_systems": BODY_SYSTEMS,
        }


LEVEL_RANK = {None: 0, "mild": 1, "strong": 2, "critical": 3}
SYSTEM_STATUS = {0: "normal", 1: "watch", 2: "act", 3: "act"}


def body_systems(signals, cabin):
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
