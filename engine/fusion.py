"""Layer 3: fuse the per-signal flags into ONE state with reasons.

The decision is rule-based on purpose: every rule is readable, and the output
lists which rules fired and which signals caused them. A crew far from Earth
must be able to check WHY the system says what it says.

States:  NORMAL  ->  WATCH (keep an eye, small actions)  ->  ACT (do something now)
"""

POINTS = {"mild": 1, "strong": 2, "critical": 5}
WATCH_SCORE = 3
ACT_SCORE = 8
MAX_ACTIONS = 7
# Patterns that affect safety or the whole crew come first, so their actions are
# never cut off the list.
PATTERN_PRIORITY = ["fast_breathing", "cabin_air", "slowed_reactions", "unsteady_hand",
                    "stress_fatigue", "sleep_debt", "mental_strain"]

PATTERNS = {
    "stress_fatigue": {
        "title": "Combined physical and mental stress",
        "explain": "Body signals (heart) and mental signals (mood, fatigue) are off together with poor sleep.",
        "actions": [
            "Reduce workload for the next 48 hours and reschedule non-critical tasks.",
            "Protect an 8-hour sleep window tonight.",
            "Book a private conversation with the flight psychologist at the next contact window.",
        ],
    },
    "sleep_debt": {
        "title": "Sleep debt building up",
        "explain": "Sleep has been shorter than normal for several nights.",
        "actions": [
            "Shift the sleep schedule back to the usual time and limit screen light before bed.",
            "Avoid scheduling demanding tasks at the start of the next shift.",
        ],
    },
    "mental_strain": {
        "title": "Mental strain",
        "explain": "Mood is down and stress language in the daily log is up.",
        "actions": [
            "Schedule personal time and a call or recorded message from family.",
            "Check in with the crew member in a short private conversation.",
        ],
    },
    "fast_breathing": {
        "title": "Fast breathing",
        "explain": "Breathing rate has been clearly above this astronaut's normal for 2 or more days, or is above the safety limit.",
        "actions": [
            "Rest for 10 minutes, then re-check breathing with a manual count (breaths in 1 minute).",
            "Check cabin air (CO2) and notify the flight surgeon if it stays high.",
        ],
    },
    "slowed_reactions": {
        "title": "Slower reactions and focus",
        "explain": "Reaction time and typing (speed or corrections) are worse than this astronaut's "
                   "normal: an early sign of fatigue that matters for safety-critical tasks.",
        "actions": [
            "Postpone safety-critical tasks (robotics, docking, spacewalk preparation) until a repeat test is normal.",
            "Repeat the 60-second reaction test after a rest break.",
        ],
    },
    "unsteady_hand": {
        "title": "Unsteady hand",
        "explain": "Hand steadiness on the mouse test has been clearly worse than this astronaut's normal for 2 or more days.",
        "actions": [
            "Repeat the steadiness test after rest; note caffeine, fatigue and any medication.",
            "Tell the flight surgeon if it lasts more than a day.",
        ],
    },
    "cabin_air": {
        "title": "Cabin air quality",
        "explain": "Cabin CO2 is above its limit. This affects the whole crew and can cause headaches and fatigue.",
        "actions": [
            "Inspect and service the CO2 scrubber.",
            "Treat crew fatigue and headache today as possibly caused by CO2, not only by stress.",
        ],
    },
}

GENERAL_ACTIONS = {
    "heart_rate": "Rest 10 minutes, then check the pulse by hand to confirm the webcam estimate; hydrate.",
    "breathing_rate": "Rest for 10 minutes and re-count breaths by hand; check cabin CO2.",
    "sleep_hours": "Protect tonight's sleep window.",
    "fatigue_score": "Take a short break before the next demanding task.",
    "blink_rate": "Take a screen break and rest the eyes.",
    "typing_speed": "Take a short break; avoid long precision work until rested.",
    "typing_errors": "Take a short break; double-check important commands before sending them.",
    "reaction_time": "Repeat the 60-second reaction test after a rest break.",
    "mouse_tremor": "Repeat the steadiness test after rest.",
    "mood_score": "Make time for a short check-in conversation.",
    "stress_words": "Make time for a short check-in conversation.",
}


def action_type(text):
    """What kind of step an action is. The system only observes and suggests: medical
    decisions stay with the flight surgeon and mission-approved procedures."""
    t = text.lower()
    if any(w in t for w in ("flight surgeon", "psychologist", "commander", "notify")):
        return "escalate"
    if any(w in t for w in ("re-check", "re-measure", "re-count", "repeat the", "by hand", "confirm",
                            "check-in", "check in")):
        return "confirm"
    if any(w in t for w in ("scrubber", "sensor", "webcam", "camera", "keyboard", "mouse")):
        return "equipment"
    if "no action" in t or "nothing to do" in t:
        return "none"
    return "self-care"


def _flagged(signals, *keys, min_streak=1):
    return [s for s in signals if s["signal"] in keys and s["level"] and s["streak_days"] >= min_streak]


def fuse(signal_results, cabin_results):
    """Combine one astronaut's signal analyses (plus cabin) into a decision."""
    flags = [s for s in signal_results if s["level"]]

    score = 0
    for s in flags:
        score += POINTS[s["level"]]
        if s["streak_days"] >= 3:
            score += 1  # a problem that persists matters more than a one-off

    patterns = []
    heart = _flagged(signal_results, "heart_rate")
    sleep = _flagged(signal_results, "sleep_hours")
    mind = _flagged(signal_results, "mood_score", "stress_words", "fatigue_score")
    if heart and sleep and mind:
        patterns.append(("stress_fatigue", heart + sleep + mind))
    if _flagged(signal_results, "sleep_hours", min_streak=2):
        patterns.append(("sleep_debt", sleep))
    mood = _flagged(signal_results, "mood_score", "stress_words")
    if len(mood) == 2 or _flagged(signal_results, "mood_score", "stress_words", min_streak=2):
        patterns.append(("mental_strain", mood))
    # One noisy webcam day is not a pattern: fast breathing needs 2+ days, or the safety limit.
    breath = [s for s in _flagged(signal_results, "breathing_rate") if s["level"] in ("strong", "critical")
              and (s["streak_days"] >= 2 or s.get("limit"))]
    if breath:
        patterns.append(("fast_breathing", breath))
    # Reaction time plus a typing signal off together (or reaction time off 3+ days).
    react = _flagged(signal_results, "reaction_time")
    typing = _flagged(signal_results, "typing_speed", "typing_errors")
    if (react and typing) or _flagged(signal_results, "reaction_time", min_streak=3):
        patterns.append(("slowed_reactions", react + typing))
    tremor = [s for s in _flagged(signal_results, "mouse_tremor")
              if s["level"] in ("strong", "critical") and s["streak_days"] >= 2]
    if tremor:
        patterns.append(("unsteady_hand", tremor))
    cabin_flags = [c for c in cabin_results if c["level"] and c["signal"] == "co2"]
    if cabin_flags:
        patterns.append(("cabin_air", []))

    patterns.sort(key=lambda p: PATTERN_PRIORITY.index(p[0]))

    # ----- Decision rules (each one is listed in the output when it fires) -----
    # `rules` is the readable text; `codes` is the same list in machine form, used to
    # write the report in other languages (see arabic.py).
    rules, codes = [], []
    state = "NORMAL"
    if any(s["level"] == "critical" for s in flags):
        state = "ACT"
        rules.append("A signal is below its absolute safety limit.")
        codes.append({"rule": "safety_limit"})
    persistent = [s for s in flags if s["streak_days"] >= 2]
    if score >= ACT_SCORE and persistent:
        # A single bad day is WATCH; ACT needs the problem to last at least 2 days.
        state = "ACT"
        rules.append(f"Total deviation score {score} reached the ACT level ({ACT_SCORE}) "
                     f"and {len(persistent)} signal(s) have been off for 2+ days.")
        codes.append({"rule": "act_score", "score": score, "limit": ACT_SCORE, "persistent": len(persistent)})
    stress = next((p for p in patterns if p[0] == "stress_fatigue"), None)
    if stress and max(s["streak_days"] for s in stress[1]) >= 3:
        state = "ACT"
        rules.append("Combined physical and mental stress has lasted 3 days or more.")
        codes.append({"rule": "stress_3_days"})
    if any(c["level"] == "act" for c in cabin_flags):
        state = "ACT"
        rules.append("Cabin CO2 is above the ACT limit.")
        codes.append({"rule": "cabin_act"})
    if state == "NORMAL":
        if score >= ACT_SCORE:
            state = "WATCH"
            rules.append(f"Total deviation score {score} is high, but it is a one-day change: "
                         "WATCH, and ACT if it continues tomorrow.")
            codes.append({"rule": "one_day_high", "score": score})
        elif score >= WATCH_SCORE:
            state = "WATCH"
            rules.append(f"Total deviation score {score} reached the WATCH level ({WATCH_SCORE}).")
            codes.append({"rule": "watch_score", "score": score, "limit": WATCH_SCORE})
        if patterns:
            state = "WATCH"
            rules.append("A known risk pattern was detected: "
                         + ", ".join(PATTERNS[p[0]]["title"].lower() for p in patterns) + ".")
            codes.append({"rule": "pattern", "patterns": [p[0] for p in patterns]})

    # ----- Recommended actions -----
    # Take the first action of every pattern, then the second of every pattern, and so
    # on, so each detected problem gets at least one action before the list is capped.
    actions = []
    for rank in range(max((len(PATTERNS[k]["actions"]) for k, _ in patterns), default=0)):
        for key, _ in patterns:
            options = PATTERNS[key]["actions"]
            if rank < len(options) and options[rank] not in actions:
                actions.append(options[rank])
    if not actions:
        for s in flags:
            a = GENERAL_ACTIONS.get(s["signal"])
            if a and a not in actions:
                actions.append(a)
    actions = actions[:MAX_ACTIONS]
    if state == "ACT":
        actions.append("Notify the flight surgeon with this report at the next contact window.")
    if not actions:
        actions.append("No action needed. Keep the normal schedule.")

    return {
        "state": state,
        "score": score,
        "flags": sorted(flags, key=lambda s: -s["z"]),
        "patterns": [{"id": k, "title": PATTERNS[k]["title"], "explain": PATTERNS[k]["explain"],
                      "signals": [s["signal"] for s in sig]} for k, sig in patterns],
        "rules_fired": rules,
        "rule_codes": codes,
        "actions": actions,
    }
