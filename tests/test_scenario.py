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
    """Cabin CO2 above the ACT limit puts every crew member in ACT, with a scrubber action."""
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
    """Live camera: normal blinking is NORMAL, faster blinking WATCH, long closures ACT."""
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
    """Live camera readings are filed under the wristband ID, never by face."""
    from engine import live
    live.store({"band": "c", "face_detected": True, "calibrating": False, "blink_rate": 15,
                "perclos": 0.04, "long_closures": 0, "baseline_blink_rate": 15, "baseline_perclos": 0.04})
    out = live.latest()
    chen = [x for x in out["readings"] if x["band"] == "C"]
    assert chen and chen[0]["astronaut"] == "Chen" and chen[0]["state"] == "NORMAL"


def test_body_systems_status():
    """The body figure colours each body system from its own signals."""
    systems = m.assess("B", 124)["systems"]
    assert systems["heart"]["status"] == "act" and systems["bones"]["status"] == "info"
    assert all(s["status"] == "normal" for k, s in m.assess("A", 110)["systems"].items() if k not in ("bones", "immune"))
    # No immune test results: unknown, never shown as normal.
    assert m.assess("A", 110)["systems"]["immune"]["status"] == "info"


def test_routine_reminders_and_streak():
    """Routine reminders (cuff check, patch change, exercise) and the days-in-Normal streak."""
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
    """Every flag on every day carries a plain-language reason (explainability)."""
    for aid in "ABC":
        for day in m.days:
            for f in m.assess(aid, day)["flags"]:
                assert f["reason"], (aid, day, f["signal"])



def test_camera_cannot_see_face_uses_wristband():
    """Too little face time: camera readings are not trusted, fatigue comes from the wristband."""
    b = m.assess("B", 122)                      # Ben worked away from the cameras (15 min)
    fatigue = next(s for s in b["signals"] if s["signal"] == "fatigue_score")
    blink = next(s for s in b["signals"] if s["signal"] == "blink_rate")
    assert fatigue["source"] == "wristband" and fatigue["level"] == "strong"
    assert "estimated from the wristband" in fatigue["reason"]
    assert blink["missing"] and blink["level"] is None
    assert b["state"] == "ACT"
    assert "قُدّر الإرهاق من السوار" in m.report("B", 122, "ar")
    for day in (60, 61):                        # Amira's spacewalk: no camera, still healthy
        a = m.assess("A", day)
        assert a["state"] == "NORMAL"
        assert next(s for s in a["signals"] if s["signal"] == "fatigue_score")["source"] == "wristband"
    normal_day = m.assess("A", 30)
    assert all(s.get("source") is None for s in normal_day["signals"])


def test_swapped_wristbands_are_caught_without_a_health_alarm():
    """Day 50: Amira and Chen wear each other's bands. Spotted from the readings alone."""
    for aid, other in (("A", "C"), ("C", "A")):
        d = m.assess(aid, 50)
        assert d["band_check"]["with"] == other
        assert d["state"] == "NORMAL"                     # no health alarm from a swapped band
        assert d["actions"][0].startswith("Check that you are wearing your own wristband")
        hrv = next(s for s in d["signals"] if s["signal"] == "hrv")
        assert hrv["untrusted"] and hrv["level"] is None
    assert "فحص السوار" in m.report("A", 50, "ar")
    assert 50 not in m.learning_days("A", 57)              # swapped day is never learned from
    others = [(a, d) for a in "ABC" for d in m.days if m.assess(a, d)["band_check"]]
    assert others == [("A", 50), ("C", 50)], others        # no false swap alerts on any other day


def test_slow_drift_is_caught_by_the_fixed_anchor():
    """A decline too slow to show on any single day is caught against the day 1-14 normal."""
    from engine import simulate
    from engine.monitor import HealthMonitor
    assert all(not m.assess(a, d)["drift"] for a in "ABC" for d in m.days)   # none in the demo
    data = simulate.generate()
    for d, r in data["crew"]["A"].items():
        if d >= 15:
            r["heart_rate"] += 0.08 * (d - 14)
            r["hrv"] -= 0.12 * (d - 14)
    slow = HealthMonitor(data=data)
    first = next(d for d in slow.days if slow.assess("A", d)["drift"])
    assert first <= 80, first
    day = slow.assess("A", first)
    assert day["state"] in ("WATCH", "ACT")
    assert any(c["rule"] == "drift" for c in day["rule_codes"])
    assert any("Flight surgeon" in a for a in day["actions"])
    assert "تغيّر بطيء" in slow.report("A", first, "ar")


def test_camera_pauses_when_two_faces_are_in_view():
    """Two people in front of a camera: don't guess whose eyes they are, just pause."""
    from camera.blink_tracker import BlinkTracker
    from engine.live import assess
    tr = BlinkTracker(calibration_s=5)
    t = _feed(tr, 0.0, 10, blink_every=4)
    face_before = tr.day_face_s
    for i in range(30):                                     # two faces for 2 seconds
        tr.update(t + i / 15, True, False, hour=10, faces=2)
    r = tr.reading()
    assert r["multiple_faces"] and not r["face_detected"]
    assert tr.day_face_s == face_before                     # nothing was measured
    assert r["today"]["skipped_multi_face_frames"] == 30
    assert assess(r)["state"] == "PAUSED"
    tr.update(t + 3, True, True, hour=10, faces=1)          # back to one face: measuring again
    assert not tr.reading()["multiple_faces"]


def test_sensor_faults_are_never_read_as_illness():
    """Disconnected, frozen or implausible readings are 'unavailable', reported as a sensor
    check, and never scored, learned from or shown as a health problem."""
    cases = {("A", 40): ("wristband", "spo2", "missing"), ("C", 34): ("glucose", "glucose", "stuck"),
             ("B", 35): ("wristband", "body_temp", "out_of_range")}
    for (aid, day), (device, key, code) in cases.items():
        d = m.assess(aid, day)
        assert d["state"] == "NORMAL", (aid, day)
        assert not any(f["signal"] == key for f in d["flags"])
        fault = next(f for f in d["sensor_faults"] if f["device"] == device)
        assert key in fault["signals"] and code in fault["codes"]
        sig = next(s for s in d["signals"] if s["signal"] == key)
        assert sig["missing"] and sig["fault"] == code
        assert d["coverage"]["confidence"] == "limited" and key in d["coverage"]["safety_gap"]
        assert m.data["crew"][aid][day][key] is None   # set aside: baselines and the AI skip it
    assert "Sensor check" in m.report("C", 34) and "فحص الحساسات" in m.report("C", 34, "ar")
    # No sensor faults on clean days, and no false 'stuck' readings anywhere else.
    found = sorted({(a, d) for (a, d), issues in m.faults.items()
                    if any(i["code"] != "skipped" for i in issues.values())})
    assert found == [("A", 40), ("A", 41), ("B", 35), ("C", 33), ("C", 34), ("C", 35)], found


def test_quality_checks_on_injected_faults():
    """Quality rules on hand-made faults: 4 identical days = frozen, impossible value, missing value."""
    from engine.quality import check
    days = {1: {"heart_rate": 60}, 2: {"heart_rate": 60}, 3: {"heart_rate": 60}, 4: {"heart_rate": 60},
            5: {"heart_rate": 300}, 6: {}}
    assert check("heart_rate", 3, days) is None              # 3 equal days: still fine
    assert check("heart_rate", 4, days)["code"] == "stuck"   # 4 equal days: frozen sensor
    assert check("heart_rate", 5, days)["code"] == "out_of_range"
    assert check("heart_rate", 6, days)["code"] == "missing"


def test_skipped_diary_is_not_a_problem():
    """The diary is optional self-report: a skipped day is not a fault and not a mood flag."""
    d = m.assess("A", 55)
    assert d["self_report_skipped"] and not d["sensor_faults"] and d["state"] == "NORMAL"
    assert "mood_score" in d["coverage"]["unavailable"]


def test_no_green_without_saying_what_is_missing():
    """Every decision says how many signals it is based on."""
    for aid in "ABC":
        for day in (30, 40, 61, 122):
            cov = m.assess(aid, day)["coverage"]
            assert cov["measured"] + len(cov["unavailable"]) == cov["total"] == 13
            assert cov["note"].startswith("Status based on")


def test_wrist_temperature_is_an_estimate_to_confirm():
    from engine.analysis import analyse_signal
    base = m.baseline_for("A", 30)
    days = {30: {**m.data["crew"]["A"][30], "body_temp": 38.4}}
    a = analyse_signal("body_temp", 30, days, base)
    assert a["level"] == "strong"                            # a warning, not 'critical'
    assert "confirm with a core temperature" in a["reason"]


def test_crew_wide_vs_individual():
    """Cabin CO2 + the same change in several astronauts = environmental; a shared change
    with no cabin cause is not blamed on the air; extra signals stay individual."""
    s125 = m.status(125)["crew_wide"]
    assert "breathing_rate" in s125["environmental"]
    assert any(b["id"] == "B" for b in s125["beyond_cabin"])
    s121 = m.status(121)["crew_wide"]
    assert not s121["environmental"] and s121["shared_no_cabin_cause"]


def test_radiation_and_co2_context():
    cab = {c["signal"]: c for c in m.assess("A", 125)["cabin"]}
    total = sum(m.data["cabin"][d]["radiation"] for d in m.days)
    assert abs(cab["radiation"]["mission_total"] - round(total, 1)) < 0.05
    assert cab["radiation"]["career_limit"] == 600.0
    assert "avg_7d" in cab["co2"]


def test_every_decision_is_versioned():
    """Any past alert can be traced to the exact rules, thresholds, model and personal normal."""
    v = m.assess("B", 121)["versions"]
    assert v["personal_normal"] == "B-day120" and v["learned_from_days"][1] <= 119
    assert {"software", "rules", "thresholds", "model"} <= set(v)
    assert "Versions:" in m.report("B", 121) and "الإصدارات" in m.report("B", 121, "ar")


def test_role_based_access():
    from engine import access
    cmd = {c["id"]: c for c in m.status(122, "commander")["crew"]}
    mood = next(s for s in cmd["B"]["signals"] if s["signal"] == "mood_score")
    assert mood["value"] is None and mood["private"]
    assert "private self-report" in m.report("B", 122, "en", "commander")
    assert str(m.assess("B", 122)["signals"][0]["value"]) in str(cmd["B"]["signals"][0]["value"])
    mate = {c["id"]: c for c in m.status(122, "A")["crew"]}
    assert mate["A"]["access"] == "full"
    assert mate["B"]["restricted"] and mate["B"]["state"] == "ACT" and not mate["B"]["signals"]
    assert "Only the status" in m.report("B", 122, "en", "A")
    full = m.status(122, "surgeon")["crew"][1]
    assert next(s for s in full["signals"] if s["signal"] == "mood_score")["value"] is not None
    hidden = access.series_view(m.series("B", "mood_score"), "B", "commander")
    assert all(p["value"] is None for p in hidden["points"])
    access.log("commander", "B", "test")
    assert access.audit()[-1]["role"] == "commander"


def test_camera_never_stores_or_sends_images():
    """Privacy test: no camera code writes images or video, and what is sent to the server
    is only numbers and short labels."""
    import re
    from camera.blink_tracker import BlinkTracker
    root = Path(__file__).resolve().parent.parent
    for f in (root / "camera").glob("*.py"):
        code = f.read_text(encoding="utf-8")
        for banned in ("imwrite", "VideoWriter", "imencode", "pickle", "np.save"):
            assert banned not in code, (f.name, banned)
        assert not re.search(r"open\([^)]*['\"]wb['\"]", code), f.name
    tr = BlinkTracker(calibration_s=5)
    _feed(tr, 0.0, 20, blink_every=4)
    payload = {**tr.reading(), "band": "B"}

    def leaves(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from leaves(v)
        else:
            yield x
    for v in leaves(payload):
        assert v is None or isinstance(v, (bool, int, float)) or (isinstance(v, str) and len(v) < 20), v


def test_camera_low_confidence_never_acts_alone():
    from engine.live import assess
    r = {"face_detected": True, "calibrating": False, "blink_rate": 30, "perclos": 0.4, "long_closures": 3,
         "baseline_blink_rate": 15, "baseline_perclos": 0.04}
    assert assess(r)["state"] == "ACT"
    low = assess({**r, "confidence": "low", "face_seconds_last_window": 12})
    assert low["state"] == "WATCH" and any("Low confidence" in x for x in low["reasons"])


def test_exercise_adherence_is_not_a_bone_measurement():
    ex = m.exercise("B", 96)
    assert ex["low"] and "not a bone or muscle measurement" in ex["note"]
    assert m.assess("B", 96)["systems"]["bones"]["status"] == "watch"
    assert "Not measured" in m.mission()["body_systems"]["bones"]["measured"]


def test_actions_are_typed():
    from engine.fusion import action_type
    assert action_type("Notify the flight surgeon with this report at the next contact window.") == "escalate"
    assert action_type("Confirm with a finger-prick glucose check.") == "confirm"
    assert action_type("Inspect and service the CO2 scrubber.") == "equipment"
    assert action_type("Protect tonight's sleep window.") == "self-care"


def test_manual_quick_check():
    """Manual test: days typed in by hand go through the same rules (2 bad days = ACT)."""
    from engine.manual import QuickCheck
    q = QuickCheck(m)
    first = q.add("A", q.defaults("A")["values"], {})
    assert first["day"] == 126 and first["decision"]["state"] == "NORMAL"
    bad = dict(q.defaults("A")["values"], heart_rate=85, hrv=30, sleep_hours=4.0, mood_score=40, spo2=None)
    assert q.add("A", bad, {})["decision"]["state"] == "WATCH"
    two = q.add("A", bad, {})
    assert two["decision"]["state"] == "ACT"
    assert any(f["device"] == "wristband" for f in two["decision"]["sensor_faults"])
    low = q.add("A", dict(bad, spo2=89), {})
    assert any(c["rule"] == "safety_limit" for c in low["decision"]["rule_codes"])
    assert m.days[-1] == 125                    # the demo mission itself is untouched
    q.reset()
    assert q.next_day() == 126


def test_manual_csv_upload():
    """Manual test: a whole mission from CSV. Bad files get clear errors; the demo
    mission uploaded as CSV gives the same decisions."""
    from engine.manual import Upload, template_csv
    assert "Missing columns" in Upload().load("day,astronaut_id\n1,A")["errors"][0]
    short = "\n".join(template_csv().splitlines()[:1 + 3 * 10])   # only 10 days
    assert any("at least 15 days" in e for e in Upload().load(short)["errors"])
    u = Upload()
    res = u.load(template_csv(full=True))
    assert res["ok"]
    states = {x["day"]: x["state"] for x in res["grid"]["B"]}
    assert states[120] == "WATCH" and states[121] == "ACT"
    assert "DAILY HEALTH REPORT" in u.report("B", 121)


def test_findings_link_to_nasa_hrp_risks():
    """Every finding names the NASA Human Research Program risk it relates to."""
    from engine.nasa_resources import RISK_BY_SIGNAL, RISK_BY_PATTERN
    from engine.signals import CORE_SIGNALS
    from engine.fusion import PATTERNS
    assert set(CORE_SIGNALS) <= set(RISK_BY_SIGNAL) and set(PATTERNS) <= set(RISK_BY_PATTERN)
    names = [r["risk"] for r in m.assess("B", 121)["nasa_risks"]]
    assert "Risk of Behavioral Changes and Psychiatric Disorders" in names
    assert "Risk of Inadequate Sleep and Irregular Schedules" in names
    assert m.assess("A", 30)["nasa_risks"] == []          # a normal day links to nothing
    assert "Linked NASA Human Research Program risks" in m.report("B", 121)


def test_severe_symptom_is_immediate_act():
    """A reported severe symptom is ACT at once, with no two-day streak."""
    from engine.manual import QuickCheck
    q = QuickCheck(m)
    vals = dict(q.defaults("C")["values"], symptoms=["chest pain"])
    d = q.add("C", vals, {})["decision"]
    assert d["state"] == "ACT" and d["rule_codes"][0]["rule"] == "symptom"
    assert d["actions"][0].startswith("Reported severe symptom")


def test_clinical_results_and_personal_dose():
    """Bone and muscle results come from periodic tests with their source; immune has none
    in the demo, so it says unavailable; each astronaut has a personal dose of their own."""
    bones = m.assess("A", 100)["systems"]["bones"]
    assert "imported clinical result" in bones["data_status"]
    assert any("Bone mineral density" in r["text"] and "simulated clinical result" in r["text"] for r in bones["clinical"])
    assert m.assess("A", 50)["systems"]["bones"]["clinical"][0]["day"] == 1   # day-90 scan not seen yet
    immune = m.assess("A", 100)["systems"]["immune"]
    assert any("unavailable" in x for x in immune["data_status"])
    a, c = m.assess("A", 61)["dosimetry"], m.assess("C", 61)["dosimetry"]
    assert a["available"] and a["today"] > c["today"]     # Amira's spacewalk day adds dose
    assert a["mission_total"] != m.assess("A", 61)["cabin"][1]["mission_total"]


def test_ingestion_layer(tmp_path):
    """Real-device path: paired devices only, duplicates dropped, late samples kept on
    their own day, impossible values dropped, everything saved locally and reloaded."""
    from engine.ingest import Ingest
    t0 = 1_800_000_000.0
    clock = [t0 + 3 * 3600]
    ing = Ingest({"WB-B": "B"}, log_path=tmp_path / "log.jsonl", mission_start=t0, now=lambda: clock[0])
    assert ing.accept({"device_id": "WB-X", "timestamp": t0, "readings": {"heart_rate": 60}})["status"] == "rejected"
    for i in range(10):
        r = ing.accept({"device_id": "WB-B", "timestamp": t0 + 600 + i * 60,
                        "readings": {"heart_rate": 64 + i % 3, "spo2": 98, "body_temp": 31.0}})
        assert r["status"] == "accepted" and r["day"] == 1 and "body_temp: 31 outside 34-42 (sensor error)" in r["dropped"]
    assert ing.accept({"device_id": "WB-B", "timestamp": t0 + 600, "readings": {"heart_rate": 64}})["status"] == "duplicate"
    late = ing.accept({"device_id": "WB-B", "timestamp": t0 + 300, "readings": {"heart_rate": 63}})
    assert late["status"] == "accepted" and late["late"]
    future = ing.accept({"device_id": "WB-B", "timestamp": clock[0] + 3600, "readings": {"heart_rate": 63}})
    assert future["status"] == "rejected" and "clock" in future["reason"]
    day = ing.daily("B", 1)
    assert day["samples"] == 11 and day["reading"]["heart_rate"] == 65 and "body_temp" not in day["reading"]
    assert day["quality"]["heart_rate"]["ok"]
    again = Ingest({"WB-B": "B"}, log_path=tmp_path / "log.jsonl", mission_start=t0, now=lambda: clock[0])
    assert again.daily("B", 1)["samples"] == 11                 # reloaded after a restart


def test_cabin_temperature_and_humidity():
    """NASA-STD-3001 [V2 6012] envelope; a missing optional sensor says unavailable."""
    from engine.analysis import analyse_cabin
    cab = {1: {"co2": 2.0, "radiation": 0.5, "temperature": 28.5, "humidity": 20}}
    out = {c["signal"]: c for c in analyse_cabin(1, cab)}
    assert out["temperature"]["level"] == "watch" and "above" in out["temperature"]["reason"]
    assert out["humidity"]["level"] == "watch" and "below" in out["humidity"]["reason"]
    none = {c["signal"]: c for c in analyse_cabin(1, {1: {"co2": 2.0, "radiation": 0.5}})}
    assert none["temperature"]["unavailable"] and none["temperature"]["value"] is None
    assert all(c["level"] is None for c in m.assess("A", 60)["cabin"] if c["signal"] in ("temperature", "humidity"))


if __name__ == "__main__":
    import inspect
    import tempfile
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            if "tmp_path" in inspect.signature(fn).parameters:
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            print("passed:", name)
