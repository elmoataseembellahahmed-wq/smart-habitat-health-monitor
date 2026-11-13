"""Layer 4: write the daily status report in plain language.

The report is built ONLY from the computed analysis (states, flags, reasons,
actions), so it cannot invent anything. It runs offline. If you later add a
language model to polish the wording, give it this text as its only input.
"""

ICON = {"NORMAL": "[NORMAL]", "WATCH": "[WATCH]", "ACT": "[ACT NOW]"}


def build_report(member, day, decision, trend, cabin):
    lines = []
    lines.append(f"DAILY HEALTH REPORT  -  Mission day {day}")
    lines.append(f"Crew member: {member['name']} ({member['role']})")
    lines.append(f"Status: {ICON[decision['state']]}  (deviation score {decision['score']})")
    lines.append("")

    trend_text = "  ->  ".join(f"day {t['day']}: {t['state']}" for t in trend)
    lines.append(f"Trend, last {len(trend)} days: {trend_text}")
    lines.append("")

    if decision["state"] == "NORMAL" and not decision["flags"]:
        lines.append("All monitored signals are within this crew member's normal range.")
    else:
        if decision["patterns"]:
            lines.append("What is happening:")
            for p in decision["patterns"]:
                lines.append(f"  - {p['title']}: {p['explain']}")
            lines.append("")
        if decision["flags"]:
            lines.append("Why (signals outside personal normal):")
            for f in decision["flags"]:
                lines.append(f"  - [{f['level']}] {f['reason']}")
            lines.append("")
        if decision["rules_fired"]:
            lines.append("Decision rules that fired:")
            for r in decision["rules_fired"]:
                lines.append(f"  - {r}")
            lines.append("")

    ai = decision.get("ai")
    if ai:
        lines.append(f"AI anomaly check (Isolation Forest): score {ai['score']:.2f} "
                     f"(unusual above {ai['threshold']:.2f}) -> {ai['level'].upper()}")
        lines.append(f"  {ai['note']}")
        lines.append("")

    cabin_flags = [c for c in cabin if c["level"]]
    if cabin_flags:
        lines.append("Cabin environment:")
        for c in cabin_flags:
            lines.append(f"  - {c['reason']}")
        lines.append("")

    lines.append("Recommended actions:")
    for i, a in enumerate(decision["actions"], 1):
        lines.append(f"  {i}. {a}")
    lines.append("")

    routine = decision.get("routine")
    if routine:
        lines.append("Routine:")
        for r in routine["reminders"]:
            due = "due today" if r["due_in_days"] == 0 else f"in {r['due_in_days']} day(s)"
            lines.append(f"  - {r['task']}: {due}")
        lines.append(f"  - Days in a row in NORMAL: {routine['normal_streak']}")
        lines.append("")

    lines.append("Generated on board from simulated data. Decision support only; "
                 "the flight surgeon makes medical decisions.")
    return "\n".join(lines)
