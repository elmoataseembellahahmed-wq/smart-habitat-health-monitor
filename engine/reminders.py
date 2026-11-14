"""Routine reminders: the few things the "no tests" habitat still needs from the crew.

The challenge suggests the tool can prompt astronauts to take measurements or do
actions as part of the mission routine. The astronaut enters the measurements
himself, so the reminders are short and few:
  * the morning measurements (about 5 minutes with the medical kit) and check-in
  * a weekly glucose-meter control check (control solution), so the meter stays accurate
  * the daily resistance exercise session (the main protection for bones and muscles)
Plus a small motivation element: the streak of days in NORMAL.
"""

CUFF_EVERY = 7
PATCH_EVERY = 14
# Patch changes are staggered so the whole crew doesn't change patches on the same day.
PATCH_OFFSET = {"A": 0, "B": 4, "C": 9}

TEXT_AR = {
    "morning": ("القياسات الصباحية والتسجيل اليومي", "النبض والأكسجين والحرارة والتنفس والضغط والسكر، ثم النوم والمزاج. حوالي 5 دقائق."),
    "meter": ("فحص جهاز السكر بمحلول المعايرة كل أسبوع", "يتأكد أن قراءات الجهاز دقيقة. دقيقتان."),
    "exercise": ("تمرين المقاومة اليومي", "الحماية الأساسية للعظام والعضلات في انعدام الجاذبية."),
}


def _due_in(day, every, offset=0):
    return (offset - day) % every


def reminders(aid, day):
    """Routine items for one astronaut on one mission day, most urgent first."""
    items = [
        {"id": "morning", "task": "Morning measurements and check-in",
         "why": "Pulse, oxygen, temperature, breathing, blood pressure and blood sugar, then sleep and mood. About 5 minutes.",
         "due_in_days": 0},
        {"id": "meter", "task": "Weekly glucose meter control check",
         "why": "A drop of control solution confirms the meter reads correctly. Takes 2 minutes.",
         "due_in_days": _due_in(day, CUFF_EVERY, PATCH_OFFSET.get(aid, 0) % CUFF_EVERY)},
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
