"""Daily health tasks with points: a small gamification layer.

The challenge suggests "a gamification system to help astronauts engage with tasks that
support their health". Each day the astronaut gets a short list of tasks, built from his
routine (morning measurements, exercise) and from today's guidance ("do now" steps). He
ticks them off; each done task gives points, and a day with every task done extends the
streak. Ticks are kept in memory and written to the audit log, so the flight surgeon can
see what was done on board.
"""

POINTS_PER_TASK = 10
BONUS_ALL_DONE = 20


class TaskBoard:
    def __init__(self):
        self.done = {}      # (aid, day) -> set of task ids

    @staticmethod
    def tasks_for(decision):
        """Today's tasks: routine first, then up to 3 'do now' steps from the guidance."""
        items = [{"id": "morning", "text": "Morning measurements and check-in", "kind": "routine"},
                 {"id": "exercise", "text": "Daily exercise session", "kind": "routine"}]
        n = 0
        for g in decision.get("guidance") or []:
            for step in g["do_now"]:
                if n < 3:
                    items.append({"id": f"{g['id']}-{n}", "text": step, "kind": "guidance"})
                    n += 1
        return items

    def tick(self, aid, day, task_id, decision):
        ids = {t["id"] for t in self.tasks_for(decision)}
        if task_id not in ids:
            raise ValueError(f"Unknown task for this day: {task_id}")
        self.done.setdefault((aid, day), set()).add(task_id)
        return self.board(aid, day, decision)

    def board(self, aid, day, decision, past=None):
        """Tasks with their state, today's points, total points and the all-done streak.
        past: {day: decision} for earlier days (for the total and the streak)."""
        tasks = self.tasks_for(decision)
        mine = self.done.get((aid, day), set())
        out = [{**t, "done": t["id"] in mine} for t in tasks]
        points = POINTS_PER_TASK * sum(t["done"] for t in out)
        all_done = all(t["done"] for t in out)
        if all_done:
            points += BONUS_ALL_DONE
        total, streak, counting = points, int(all_done), all_done
        for d in sorted(past or {}, reverse=True):
            dec = past[d]
            ids = {t["id"] for t in self.tasks_for(dec)}
            got = self.done.get((aid, d), set()) & ids
            total += POINTS_PER_TASK * len(got) + (BONUS_ALL_DONE if got == ids else 0)
            if counting and got == ids:
                streak += 1
            else:
                counting = False
        return {"day": day, "tasks": out, "points_today": points, "points_total": total,
                "all_done_streak": streak}
