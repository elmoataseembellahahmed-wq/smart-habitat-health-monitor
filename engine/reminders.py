"""Routine reminders: the few things the "no tests" habitat still needs from the crew.

The challenge suggests the tool can prompt astronauts to take measurements or do
actions as part of the mission routine. In our design almost everything is measured
passively at the workstation, so the reminders are short and few:
  * the morning check-in (sleep, mood, symptoms) and the 60-second reaction test
  * a weekly manual pulse check, to compare with the webcam heart-rate estimate
  * the daily resistance exercise session (the main protection for bones and muscles)
Plus a small motivation element: the streak of days in NORMAL.
"""

PULSE_EVERY = 7
# Pulse checks are staggered so the whole crew doesn't do them on the same day.
PULSE_OFFSET = {"A": 0, "B": 2, "C": 4}

TEXT_AR = {
    "checkin": ("التسجيل الصباحي واختبار رد الفعل", "النوم والمزاج والأعراض، واختبار بالماوس لمدة 60 ثانية."),
    "pulse": ("قياس النبض يدويًا كل أسبوع", "للمقارنة مع تقدير النبض من الكاميرا. دقيقة واحدة."),
    "exercise": ("تمرين المقاومة اليومي", "الحماية الأساسية للعظام والعضلات في انعدام الجاذبية."),
}


def _due_in(day, every, offset=0):
    return (offset - day) % every


def reminders(aid, day):
    """Routine items for one astronaut on one mission day, most urgent first."""
    items = [
        {"id": "checkin", "task": "Morning check-in and 60-second reaction test",
         "why": "Sleep, mood and symptoms, plus the mouse reaction test. About 2 minutes.",
         "due_in_days": 0},
        {"id": "pulse", "task": "Weekly manual pulse check",
         "why": "Compared with the webcam heart-rate estimate to keep it honest. Takes 1 minute.",
         "due_in_days": _due_in(day, PULSE_EVERY, PULSE_OFFSET.get(aid, 0))},
        {"id": "exercise", "task": "Daily resistance exercise",
         "why": "The main protection for bones and muscles in low gravity.",
         "due_in_days": 0},
    ]
    for it in items:
        it["task_ar"], it["why_ar"] = TEXT_AR[it["id"]]
    return sorted(items, key=lambda i: i["due_in_days"])


def normal_streak(states_by_day, day):
    """Days in a row, ending today, with state NORMAL."""
    streak = 0
    d = day
    while d in states_by_day and states_by_day[d] == "NORMAL":
        streak += 1
        d -= 1
    return streak
