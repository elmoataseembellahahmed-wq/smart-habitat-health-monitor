"""Routine reminders: the few things the "no tests" habitat still needs from the crew.

The challenge suggests the tool can prompt astronauts to take measurements or do
actions as part of the mission routine. In our design almost everything is measured
passively, so the reminders are short and few:
  * a weekly cuff check, to keep the cuffless blood pressure sensor calibrated
  * a glucose patch change every 14 days
  * the daily resistance exercise session (the main protection for bones and muscles)
Plus a small motivation element: the streak of days in NORMAL.
"""

CUFF_EVERY = 7
PATCH_EVERY = 14
# Patch changes are staggered so the whole crew doesn't change patches on the same day.
PATCH_OFFSET = {"A": 0, "B": 4, "C": 9}

TEXT_AR = {
    "cuff": ("فحص ضغط الدم الأسبوعي بالكُمّ", "يُبقي مستشعر الضغط بدون كُمّ دقيقًا. دقيقتان."),
    "patch": ("تغيير لاصقة قياس السكر", "تعمل اللاصقة من 10 إلى 14 يومًا."),
    "exercise": ("تمرين المقاومة اليومي", "الحماية الأساسية للعظام والعضلات في انعدام الجاذبية."),
}


def _due_in(day, every, offset=0):
    return (offset - day) % every


def reminders(aid, day):
    """Routine items for one astronaut on one mission day, most urgent first."""
    items = [
        {"id": "cuff", "task": "Weekly blood pressure cuff check",
         "why": "Keeps the cuffless blood pressure sensor accurate. Takes 2 minutes.",
         "due_in_days": _due_in(day, CUFF_EVERY)},
        {"id": "patch", "task": "Change the glucose patch",
         "why": "The patch works for 10 to 14 days.",
         "due_in_days": _due_in(day, PATCH_EVERY, PATCH_OFFSET.get(aid, 0))},
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
