"""Layer 4: write the daily status report in plain language.

The report is built ONLY from the computed analysis (states, flags, reasons,
actions), so it cannot invent anything. It runs offline. If you later add a
language model to polish the wording, give it this text as its only input.
"""

from .fusion import action_type

ICON = {"NORMAL": "[NORMAL]", "WATCH": "[WATCH]", "ACT": "[ACT NOW]"}
TYPE = {"escalate": "escalate", "equipment": "equipment", "confirm": "confirm first",
        "self-care": "self-care", "none": "-"}


def build_report(member, day, decision, trend, cabin):
    lines = []
    lines.append(f"DAILY HEALTH REPORT  -  Mission day {day}")
    lines.append(f"Crew member: {member['name']} ({member['role']})")
    lines.append(f"Status: {ICON[decision['state']]}  (deviation score {decision['score']})")
    cov = decision.get("coverage")
    if cov:
        lines.append(f"Data coverage: {cov['confidence'].upper()} - {cov['note']}")
    if decision.get("alert_path_note"):
        lines.append(f"Alert path: {decision['alert_path_note']}")
    for a in decision.get("immediate_alerts") or []:
        val = "" if a["value"] is None else f" = {a['value']}{' ' + a['unit'] if a['unit'] else ''}"
        lines.append(f"  - Immediate alert, mission day {a['mission_day']}: {a['trigger']}{val}; "
                     f"limit: {a['limit_rule']}; source: {a['source']} [{a['data_status']}]; "
                     f"trusted because: {a['why_trusted']}.")
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

    faults = decision.get("sensor_faults") or []
    if faults or decision.get("self_report_skipped"):
        lines.append("Entry check (entry mistakes, not health):")
        for f in faults:
            for msg in f["messages"]:
                lines.append(f"  - {f['device_name']}: {msg}")
            lines.append(f"    -> {f['action']}")
        if decision.get("self_report_skipped"):
            lines.append("  - Daily diary skipped (optional): mood was not assessed today. That is fine.")
        lines.append("")

    band = decision.get("profile_check")
    if band:
        lines.append("Profile check:")
        lines.append(f"  - {band['message']}")
        lines.append("")
    if decision.get("drift"):
        lines.append("Slow change since the start of the mission (for the flight surgeon):")
        for x in decision["drift"]:
            lines.append(f"  - {x['reason']}")
        lines.append("")

    if decision.get("insufficient_data"):
        lines.append("Not enough data to confirm this status: too many signals are unavailable today.")
        lines.append("")
    dose = decision.get("dosimetry")
    if dose:
        lines.append("Radiation, this astronaut (personal dose, kept apart from the cabin reading):")
        lines.append(f"  - {dose['note']}")
        if decision.get("cabin_radiation"):
            lines.append(f"  - {decision['cabin_radiation']['note']}")
        lines.append("")
    sysd = decision.get("systems") or {}
    clin_lines = [r["text"] for k in ("bones", "immune") for r in (sysd.get(k) or {}).get("clinical", [])]
    lines.append("Periodic clinical results (not measured by wearables):")
    for t in clin_lines:
        lines.append(f"  - {t}. Interpretation is for the flight surgeon.")
    if not (sysd.get("immune") or {}).get("clinical"):
        lines.append("  - Immune: no test results, so immune status is unknown (not assumed normal).")
    lines.append("")

    risks = decision.get("nasa_risks") or []
    if risks:
        lines.append("Linked NASA Human Research Program risks (nasa.gov/hrp/risks):")
        for r in risks:
            lines.append(f"  - {r['risk']} (hazard: {r['hazard']})")
        lines.append("")

    ai = decision.get("ai")
    if ai:
        lines.append(f"AI anomaly check (Isolation Forest): score {ai['score']:.2f} "
                     f"(unusual above {ai['threshold']:.2f}) -> {ai['level'].upper()}")
        lines.append(f"  {ai['note']}")
        lines.append("")

    lines.append("Cabin environment:")
    for c in cabin:
        if c["level"]:
            lines.append(f"  - {c['reason']}")
        if c.get("note"):
            lines.append(f"  - {c['note']}")
    for n in (decision.get("crew_wide") or {}).get("notes", []):
        lines.append(f"  - Crew-wide: {n}")
    lines.append("")

    lines.append("Suggested actions (prototype list; follow mission-approved procedures and the flight surgeon):")
    for i, a in enumerate(decision["actions"], 1):
        lines.append(f"  {i}. [{TYPE[action_type(a)]}] {a}")
    lines.append("")

    for g in decision.get("guidance") or []:
        lines.append(f"Guidance: {g['title']} (NASA HRP: {g['hazard']}; {g['risk']})")
        lines.append(f"  What it means: {g['means']}")
        lines.append("  Do now: " + " ".join(g["do_now"]))
        lines.append("  Improve and prevent: " + " ".join(g["improve"]))
        lines.append("  Call the flight surgeon if: " + " ".join(g["call_if"]))
        lines.append(f"  {g['medicine']}  Source: {g['source']}")
        lines.append("")

    routine = decision.get("routine")
    if routine:
        lines.append("Routine:")
        for r in routine["reminders"]:
            due = "due today" if r["due_in_days"] == 0 else f"in {r['due_in_days']} day(s)"
            lines.append(f"  - {r['task']}: {due}")
        lines.append(f"  - Days in a row in NORMAL: {routine['normal_streak']}")
        lines.append("")

    v = decision.get("versions")
    if v:
        lines.append(f"Versions: software {v['software']}, {v['rules']}, {v['thresholds']}, {v['model']}, "
                     f"personal normal {v['personal_normal']} (learned from days {v['learned_from_days'][0]}-"
                     f"{v['learned_from_days'][1]}, {v['learned_from_days'][2]} days used).")
    lines.append("Generated on board from simulated data. Prototype thresholds, not for medical decisions. "
                 "Decision support only; the flight surgeon makes medical decisions.")
    return "\n".join(lines)
