"""A short message to the flight surgeon, ready for the next contact window.

From Mars a message takes up to 20 minutes each way (NASA HRP, Distance from Earth), so
contact is precious. NABD writes one short, prioritised message per astronaut: status,
the most important findings with values, what was already done on board, and what the
crew needs from the ground. It is sent by the crew; NABD sends nothing by itself.
"""

from .signals import SIGNALS


def _v(key, value):
    d = SIGNALS[key]["decimals"] if key in SIGNALS else 1
    return f"{value:.{d}f}" if d else f"{round(value)}"


STATE_AR = {"NORMAL": "طبيعي", "WATCH": "مراقبة", "ACT": "تدخّل"}


def message(member, day, decision, done_tasks=None, selfchecks=None, lang="en"):
    en = lang != "ar"
    name = member["name"]
    lines = []
    if en:
        lines.append(f"NABD to flight surgeon | {name} ({member['role']}) | mission day {day} | {decision['state']}")
    else:
        lines.append(f"من نبض إلى طبيب الرحلة | {name} | يوم المهمة {day} | {STATE_AR[decision['state']]}")
    # 1. Most important first: immediate alerts, then flags by severity.
    top = []
    for a in decision.get("immediate_alerts") or []:
        v = "" if a["value"] is None else f" {a['value']}{' ' + a['unit'] if a.get('unit') else ''}"
        top.append(f"{a['trigger']}{v} ({'confirmed' if a.get('confirmed') else 'immediate'})")
    order = {"critical": 0, "strong": 1, "mild": 2}
    alerted = {a["trigger"] for a in decision.get("immediate_alerts") or []}
    for f in sorted(decision["flags"], key=lambda f: order.get(f["level"], 3)):
        if f.get("private") or f["value"] is None or f["signal"] in alerted:
            continue
        top.append(f"{f['name']} {_v(f['signal'], f['value'])} {f['unit']} "
                   f"(normal {_v(f['signal'], f['baseline'])}, {f['level']}"
                   + (f", {f['streak_days']} days" if f["streak_days"] >= 2 else "") + ")")
    if decision.get("unconfirmed"):
        top.append(("not confirmed on re-measure: " if en else "لم يتأكد بإعادة القياس: ")
                   + ", ".join(decision["unconfirmed"]))
    lines.append(("Findings: " if en else "النتائج: ") + ("; ".join(top[:4]) if top else ("none" if en else "لا شيء")))
    # 2. What was done on board.
    done = list(done_tasks or [])
    for s in selfchecks or []:
        done.append(("self-check: " if en else "فحص ذاتي: ") + ", ".join(c["id"] for c in s["cards"]))
    lines.append(("Done on board: " if en else "ما تم على متن المركبة: ")
                 + ("; ".join(done[:5]) if done else ("nothing logged yet" if en else "لم يُسجَّل شيء بعد")))
    # 3. What the crew needs from the ground.
    if decision["state"] == "ACT":
        ask = ("Please review today and advise on next steps; reply expected next window."
               if en else "برجاء مراجعة اليوم والإرشاد بالخطوات التالية في نافذة الاتصال القادمة.")
    elif decision["state"] == "WATCH":
        ask = ("For information; no reply needed unless you see a concern."
               if en else "للعلم؛ لا حاجة للرد إلا لو عندك ملاحظة.")
    else:
        ask = "Routine: no action needed." if en else "روتيني: لا حاجة لأي إجراء."
    lines.append(("Request: " if en else "المطلوب: ") + ask)
    cov = decision.get("coverage") or {}
    lines.append((f"Data: {cov.get('measured')}/{cov.get('total')} values, AI {decision['ai']['level']}, "
                  f"rules {decision['versions']['rules']}") if en else
                 f"البيانات: {cov.get('measured')}/{cov.get('total')} قيمة، الذكاء الاصطناعي: {decision['ai']['level']}")
    return "\n".join(lines)
