"""Checks that the system tells the right story on the simulated mission.

Run:  python -m pytest tests      (or)      python tests/test_scenario.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import HealthMonitor  # noqa: E402

m = HealthMonitor()


def state(aid, day):
    return m.assess(aid, day)["state"]


def test_baseline_days_are_quiet():
    """No false alarms while everyone is healthy (days 100-118)."""
    for aid in "ABC":
        for day in range(100, 119):
            if aid == "C" and day == 121:
                continue
            assert state(aid, day) == "NORMAL", (aid, day)


def test_ben_escalates_early():
    """Ben's slow decline is caught: WATCH first, then ACT, before it's severe."""
    assert state("B", 120) == "WATCH"
    for day in range(121, 126):
        assert state("B", day) == "ACT"


def test_one_bad_night_is_not_an_emergency():
    """Chen's single bad night gives WATCH, not ACT, and he returns to NORMAL."""
    assert state("C", 121) == "WATCH"
    assert state("C", 122) == "NORMAL"


def test_cabin_co2_affects_everyone():
    for aid in "ABC":
        assert state(aid, 125) == "ACT"
        assert any("CO2" in a for a in m.assess(aid, 125)["actions"])


def test_ai_model_finds_ben():
    """The Isolation Forest flags every day of Ben's decline."""
    for day in range(120, 126):
        assert m.assess("B", day)["ai"]["level"] != "normal", day


def test_no_false_alarms_over_the_long_mission():
    """Days 15-118, everyone healthy: never ACT, and at most one single-day WATCH each."""
    for aid in "ABC":
        states = [m.assess(aid, d)["state"] for d in range(15, 119)]
        assert "ACT" not in states, aid
        assert states.count("WATCH") <= 1, aid


def test_ai_model_quiet_on_healthy_astronaut():
    """Amira stays healthy: at most one AI flag in the whole mission, none in the demo
    days (cabin CO2 is not a personal signal)."""
    flags = [d for d in m.days if m.assess("A", d)["ai"]["level"] != "normal"]
    assert len(flags) <= 1, flags
    assert all(d < 100 for d in flags), flags


def test_personal_normal_keeps_learning():
    """Every 7 days the personal normal is re-learned from recent NORMAL days only."""
    assert m.learning_days("A", 10) == list(range(1, 15))
    assert m.update_day(125) == 120
    learned = m.learning_days("B", 125)
    assert len(learned) >= 20 and max(learned) <= 119
    assert 48 not in m.learning_days("A", 50)   # Amira's one WATCH day is not learned from


def test_live_camera_assessment():
    from engine.live import assess
    calm = {"face_detected": True, "calibrating": False, "blink_rate": 15, "perclos": 0.04,
            "long_closures": 0, "baseline_blink_rate": 15, "baseline_perclos": 0.04}
    assert assess(calm)["state"] == "NORMAL"
    assert assess({**calm, "blink_rate": 30})["state"] == "WATCH"
    assert assess({**calm, "perclos": 0.25, "long_closures": 3})["state"] == "ACT"


def _feed(tracker, t, seconds, blink_every, blink_len=0.15, face=True, fps=15, long_at=()):
    end, nb = t + seconds, t + blink_every
    while t < end:
        closed = nb <= t < nb + blink_len or any(a <= t < a + 0.8 for a in long_at)
        if t >= nb + blink_len:
            nb += blink_every
        tracker.update(t, face, not closed, hour=10)
        t += 1 / fps
    return t


def test_all_day_camera_tracker(tmp_path=None):
    """Calibrates on face time only, skips gaps, keeps a daily summary, saves the baseline."""
    import tempfile
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "camera"))
    from blink_tracker import BlinkTracker
    from engine.live import assess

    tr = BlinkTracker(calibration_s=30)
    t = _feed(tr, 0.0, 20, 4.0)                 # 20 s in view
    t = _feed(tr, t, 60, 4.0, face=False)       # looks away for a minute: not counted
    assert tr.reading()["calibrating"]           # only 20 s of face time so far
    t = _feed(tr, t, 15, 4.0)                   # 35 s of face time: calibrated
    assert not tr.reading()["calibrating"]
    t = _feed(tr, t, 60, 2.0, 0.3, long_at=(t + 10, t + 30))  # drowsy minute
    r = tr.reading()
    assert assess(r)["state"] == "ACT"
    today = r["today"]
    assert today["microsleeps"] == 2 and 1.5 < today["face_minutes"] < 2.0

    path = Path(tempfile.mkdtemp()) / "band_B.json"
    tr.save_baseline(path)
    tr2 = BlinkTracker(baseline=BlinkTracker.load_baseline(path))
    assert not tr2.reading()["calibrating"]      # next session starts measuring at once


def test_camera_ignores_single_frame_misses():
    """A one-frame detector miss is not a blink; a real 0.2 s blink still counts."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "camera"))
    from blink_tracker import BlinkTracker
    tr = BlinkTracker(calibration_s=5)
    fps, t = 15, 0.0
    for i in range(15 * 20):               # 20 s, a fake one-frame miss every 2 s
        tr.update(t, True, i % 30 != 0, hour=10)
        t += 1 / fps
    assert tr.day_blinks == 0
    for i in range(15 * 10):               # 10 s, a real 3-frame blink every 2 s
        tr.update(t, True, i % 30 not in (0, 1, 2), hour=10)
        t += 1 / fps
    assert tr.day_blinks == 5


def test_live_readings_filed_by_wristband():
    from engine import live
    live.store({"band": "c", "face_detected": True, "calibrating": False, "blink_rate": 15,
                "perclos": 0.04, "long_closures": 0, "baseline_blink_rate": 15, "baseline_perclos": 0.04})
    out = live.latest()
    chen = [x for x in out["readings"] if x["band"] == "C"]
    assert chen and chen[0]["astronaut"] == "Chen" and chen[0]["state"] == "NORMAL"


def test_body_systems_status():
    systems = m.assess("B", 124)["systems"]
    assert systems["heart"]["status"] == "act" and systems["bones"]["status"] == "info"
    assert all(s["status"] == "normal" for k, s in m.assess("A", 110)["systems"].items() if k != "bones")


def test_routine_reminders_and_streak():
    r = m.routine("A", 110)
    ids = [x["id"] for x in r["reminders"]]
    assert set(ids) == {"cuff", "patch", "exercise"}
    assert r["normal_streak"] == 62            # Amira: Normal on days 49-110
    assert m.routine("B", 124)["normal_streak"] == 0
    assert "Routine:" in m.report("A", 110) and "المهام الروتينية" in m.report("A", 110, "ar")


def test_arabic_report_covers_everything():
    """Every action has an Arabic version and the Arabic report builds for every day."""
    from engine.arabic import ACTION_AR
    for aid in "ABC":
        for day in m.days:
            for a in m.assess(aid, day)["actions"]:
                assert a in ACTION_AR, a
            text = m.report(aid, day, "ar")
            assert "التقرير الصحي اليومي" in text


def test_every_flag_has_a_reason():
    for aid in "ABC":
        for day in m.days:
            for f in m.assess(aid, day)["flags"]:
                assert f["reason"], (aid, day, f["signal"])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("passed:", name)
