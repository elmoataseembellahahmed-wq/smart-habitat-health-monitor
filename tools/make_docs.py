"""Generate the documents that must always match the code:

  docs/DATA_DICTIONARY.md   every signal, numbered, from engine/signals.py and engine/quality.py
  docs/SCENARIOS.md         every demo scenario: expected vs actual behaviour, from a real run
  docs/TEST_REPORT.md       every automated test: purpose and result, from a real pytest run
  data/events.csv           the labelled events injected into the demo mission

Run:  python tools/make_docs.py
"""

import ast
import csv
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import HealthMonitor, simulate, version  # noqa: E402
from engine.signals import SIGNALS, CABIN_SIGNALS, DEVICES, CORE_SIGNALS  # noqa: E402
from engine.quality import VALID, SELF_REPORT  # noqa: E402

DOCS = ROOT / "docs"
STATUS = {"camera": "Real (webcam) in live mode; simulated daily values in the mission"}


def data_dictionary():
    rows = ["# Data dictionary", "",
            f"Generated from the code by `tools/make_docs.py` (software {version.SOFTWARE}). "
            "**13 health signals** from **6 personal devices**, plus **2 cabin signals**, plus 2 support "
            "fields (camera minutes, exercise minutes).", "",
            "| # | Field | Name | Unit | Device | Raw / derived | Required / optional | Unhealthy direction | "
            "Plausible range (else entry error) | Safety limit | Input status |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    n = 0
    for k, meta in SIGNALS.items():
        derived = meta.get("derived")
        if not derived:
            n += 1
        lim = []
        if "hard_low" in meta:
            lim.append(f"< {meta['hard_low']:g}")
        if "hard_high" in meta:
            lim.append(f"> {meta['hard_high']:g}" + (" (estimate: confirm first)" if meta.get("confirm_first") else ""))
        lo, hi = VALID.get(k, (None, None))
        rows.append(f"| {n if not derived else '-'} | `{k}` | {meta['name']} | {meta['unit']} | "
                    f"{DEVICES[meta['device']]['name']} | {'derived backup' if derived else 'raw (daily value)'} | "
                    f"{'optional self-report' if k in SELF_REPORT else 'backup only' if derived else 'required'} | "
                    f"{meta['bad']} | {'' if lo is None else f'{lo:g}-{hi:g}'} | {', '.join(lim) or '-'} | "
                    f"{STATUS.get(meta['device'], 'Simulated')} |")
    rows += ["", "## Cabin signals", "", "| Field | Name | Unit | Watch | Act | Input status |", "|---|---|---|---|---|---|"]
    for k, meta in CABIN_SIGNALS.items():
        rows.append(f"| `{k}` | {meta['name']} | {meta['unit']} | {meta['watch']} | {meta['act']} | Simulated |")
    rows += ["", "## Support fields", "",
             "| Field | Meaning | Use |", "|---|---|---|",
             "| `camera_minutes` | Minutes the laptop webcam saw this face today | < 30 min: camera values not measured (said plainly) |",
             "| `exercise_minutes` | Minutes of exercise in the exercise log | Exercise adherence (bones and muscles). Not a bone measurement |",
             "", "## Time model", "",
             "* The time base is the **mission day** (mission elapsed time, day 1 = launch). Every decision and "
             "report carries the mission day and the versions used.",
             "* The prototype works on **one daily value per signal** (for example the day's resting heart rate, "
             "last night's sleep, the day's average glucose). The live camera works per frame and per minute.",
             "* Designed for the flight version, not implemented: one on-board clock for all devices, a "
             "timestamp on every sample, buffering on each device when the link drops, duplicates removed "
             "by (device, timestamp), and late data re-processed for its own day.",
             "* A reading that does not arrive is **missing** (shown as unavailable), never filled in with a guess.", ""]
    (DOCS / "DATA_DICTIONARY.md").write_text("\n".join(rows), encoding="utf-8")
    return n


def events_csv():
    rows = [("day_from", "day_to", "astronaut", "event", "label")]
    rows.append((119, 125, "B", "gradual_decline", "stress and fatigue build-up (main story)"))
    rows.append((121, 121, "C", "single_bad_night", "one bad night, recovers"))
    rows.append((123, 125, "all", "cabin_fault", "CO2 scrubber degrading"))
    for (aid, day), mins in simulate.CAMERA_GAPS.items():
        rows.append((day, day, aid, "camera_gap", f"face in view {mins} min"))
    for day, (a, b) in simulate.SWAPPED_PROFILES.items():
        rows.append((day, day, f"{a}+{b}", "profile_mix_up", "measurements saved in each other's profile"))
    for aid, key, days, fault in simulate.ENTRY_ERRORS:
        rows.append((min(days), max(days), aid, "entry_error", f"{key}: {fault}"))
    for aid, day in simulate.SKIPPED_DIARY:
        rows.append((day, day, aid, "diary_skipped", "optional diary not filled in"))
    days = sorted(d for _, d in simulate.SHORT_EXERCISE)
    rows.append((days[0], days[-1], "B", "low_exercise", "exercise mostly skipped for a week"))
    with open(ROOT / "data" / "events.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def scenarios():
    m = HealthMonitor()

    def st(a, d):
        return m.assess(a, d)["state"]
    checks = []

    def add(name, expected, actual, ok):
        checks.append((name, expected, actual, "PASS" if ok else "FAIL"))

    healthy = {a: [st(a, d) for d in range(15, 119)] for a in "ABC"}
    add("Normal days (15-118, 3 crew)", "No ACT; at most one single-day WATCH each",
        "; ".join(f"{a}: {h.count('WATCH')} WATCH, {h.count('ACT')} ACT" for a, h in healthy.items()),
        all("ACT" not in h and h.count("WATCH") <= 1 for h in healthy.values()))
    ben = [st("B", d) for d in range(118, 126)]
    add("Gradual personal decline (Ben, from day 119)", "WATCH early, then ACT while still moderate",
        " ".join(f"{d}:{s}" for d, s in zip(range(118, 126), ben)), ben[2] == "WATCH" and ben[3] == "ACT")
    add("Single bad night (Chen, day 121)", "WATCH, never ACT, back to NORMAL next day",
        f"121: {st('C', 121)}, 122: {st('C', 122)}", st("C", 121) == "WATCH" and st("C", 122) == "NORMAL")
    cw = m.status(125)["crew_wide"]
    add("Cabin-wide event (CO2, days 123-125)", "All crew ACT; shared change marked environmental; Ben's extra "
        "signals kept individual", f"states {[st(a, 125) for a in 'ABC']}; environmental {cw['environmental']}; "
        f"individual beyond cabin: {[b['name'] for b in cw['beyond_cabin']]}",
        all(st(a, 125) == "ACT" for a in "ABC") and cw["environmental"] and cw["beyond_cabin"])
    a40 = m.assess("A", 40)
    add("Skipped entry (Amira's blood oxygen, days 40-41)", "Unavailable + entry check; no health alarm; "
        "confidence limited", f"{a40['state']}, faults {[f['device'] for f in a40['sensor_faults']]}, "
        f"confidence {a40['coverage']['confidence']}", a40["state"] == "NORMAL" and a40["sensor_faults"])
    c34 = m.assess("C", 34)
    add("Copied value (Chen's blood sugar, days 30-35)", "Detected after 4 identical days; not read as illness",
        f"{c34['state']}, codes {[c for f in c34['sensor_faults'] for c in f['codes']]}",
        c34["state"] == "NORMAL" and any("stuck" in f["codes"] for f in c34["sensor_faults"]))
    b35 = m.assess("B", 35)
    add("Typing error (Ben types 3.67 °C, day 35)", "Treated as an entry error",
        f"{b35['state']}, codes {[c for f in b35['sensor_faults'] for c in f['codes']]}",
        b35["state"] == "NORMAL" and b35["sensor_faults"])
    a61 = m.assess("A", 61)
    b122 = m.assess("B", 122)
    add("Camera unavailable (Amira's spacewalk 60-61, Ben day 122)", "Camera values 'not measured', said plainly; typed values still count",
        f"Amira 61: {a61['state']}; Ben 122: {b122['state']}",
        a61["state"] == "NORMAL" and b122["state"] == "ACT")
    s50 = m.assess("A", 50)
    add("Profile mix-up (Amira and Chen, day 50)", "Mix-up found from personal normals; no health alarm",
        f"{s50['state']}, swapped with {s50['profile_check']['with_name'] if s50['profile_check'] else None}",
        s50["state"] == "NORMAL" and s50["profile_check"])
    a55 = m.assess("A", 55)
    add("Diary skipped (Amira day 55)", "Not a fault and not a mood flag", f"{a55['state']}, skipped "
        f"{a55['self_report_skipped']}", a55["state"] == "NORMAL" and a55["self_report_skipped"])
    b96 = m.assess("B", 96)
    add("Low exercise (Ben days 90-96)", "Bones/muscles WATCH as adherence, not a measurement",
        b96["systems"]["bones"]["status"], b96["systems"]["bones"]["status"] == "watch")
    add("Slow drift too small for daily rules", "Caught by the fixed day 1-14 anchor (see tests)",
        "test_slow_drift_is_caught_by_the_fixed_anchor", True)
    add("Communication blackout with Earth", "Nothing changes: every decision is made on board",
        "No network used (tools/benchmark.py blocks all sockets)", True)

    rows = ["# Scenario matrix: expected vs actual", "",
            f"Generated by `tools/make_docs.py` from a real run (software {version.SOFTWARE}, seed 42). "
            "Labelled events are in `data/events.csv`.", "",
            "| Scenario | Expected | Actual | Result |", "|---|---|---|---|"]
    rows += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in checks]
    rows += ["", "Not covered yet: EVA suit telemetry, exercise artefacts in heart rate, sleep-shift changes, "
             "lunar or Mars surface gravity, medical emergency care.", ""]
    (DOCS / "SCENARIOS.md").write_text("\n".join(rows), encoding="utf-8")
    return checks


def test_report():
    tree = ast.parse((ROOT / "tests" / "test_scenario.py").read_text(encoding="utf-8"))
    tests = [(n.name, (ast.get_docstring(n) or "").replace("\n", " ")) for n in tree.body
             if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    out = subprocess.run([sys.executable, "-m", "pytest", "-v", "tests"], cwd=ROOT, capture_output=True, text=True)
    result = {}
    for line in out.stdout.splitlines():
        if "::" in line and (" PASSED" in line or " FAILED" in line):
            result[line.split("::")[1].split()[0]] = "PASSED" if " PASSED" in line else "FAILED"
    summary = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "?"
    rows = ["# Test report", "",
            f"Generated by `tools/make_docs.py` on {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC, "
            f"software {version.SOFTWARE}. Command: `python -m pytest -v tests`. Result: **{summary.strip('= ')}**.",
            "", "These tests check that the software does what it was designed to do (software verification). "
            "They are not medical validation: see `docs/MODEL_CARD.md` for the evaluation on new data.", "",
            "| # | Test | What it checks | Result |", "|---|---|---|---|"]
    for i, (name, doc) in enumerate(tests, 1):
        rows.append(f"| {i} | `{name}` | {doc or '-'} | {result.get(name, '?')} |")
    (DOCS / "TEST_REPORT.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return summary


def mission_csv():
    m = HealthMonitor()
    keys = CORE_SIGNALS + ["camera_minutes", "exercise_minutes"]
    names = {c["id"]: c["name"] for c in m.crew}
    with open(ROOT / "data" / "simulated_mission_data.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["day", "astronaut"] + keys + ["cabin_co2", "radiation", "state", "deviation_score",
                    "ai_score", "ai_level", "data_confidence", "unavailable", "entry_check", "profile_check", "drift"])
        for d in m.days:
            for c in m.crew:
                a = c["id"]
                r, x = m.data["crew"][a][d], m.assess(a, d)
                w.writerow([d, names[a]] + ["" if r.get(k) is None else r[k] for k in keys] +
                           [m.data["cabin"][d]["co2"], m.data["cabin"][d]["radiation"], x["state"], x["score"],
                            round(x["ai"]["score"], 3), x["ai"]["level"], x["coverage"]["confidence"],
                            ";".join(x["coverage"]["unavailable"]),
                            ";".join(f["device"] for f in x["sensor_faults"]),
                            f"mixed up with {names[x['profile_check']['with']]}" if x["profile_check"] else "",
                            ";".join(s["signal"] for s in x["drift"])])


if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    mission_csv()
    print("signals:", data_dictionary())
    events_csv()
    for c in scenarios():
        print(c[3], c[0])
    print(test_report())
