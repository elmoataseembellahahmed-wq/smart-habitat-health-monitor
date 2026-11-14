"""Independent evaluation on NEW labelled missions (not the demo data).

Why this exists: the demo mission (seed 42) was written together with the system, so it
cannot prove much. This script uses a SEPARATE generator with different random seeds,
randomly drawn personal normals (people differ), random noise levels, and events placed
at random days with random sizes. Every day is labelled, so we can count:

  * false alarms per 100 healthy astronaut-days (WATCH and ACT separately)
  * gradual declines: share detected, and days from onset to first WATCH / ACT / AI flag
  * single bad nights: share that wrongly went to ACT
  * input faults: share that were wrongly read as illness
and compare with a simple baseline: fixed "population" limits with no personal normal.

This is still synthetic data. It checks that the logic behaves as designed on data it
has never seen; it is NOT medical validation. Real validation needs real labelled
astronaut or analogue-mission data and clinical review.

Run:  python tools/evaluate.py            (20 missions, about 3 minutes)
      python tools/evaluate.py --missions 5
"""

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.monitor import HealthMonitor  # noqa: E402
from engine import simulate  # noqa: E402

DAYS = range(1, 126)
CREW = [{"id": "A", "name": "P1", "role": "Crew"}, {"id": "B", "name": "P2", "role": "Crew"},
        {"id": "C", "name": "P3", "role": "Crew"}]

# Population ranges personal normals are drawn from.
NORMAL_RANGE = {"heart_rate": (54, 72), "breathing_rate": (12, 16), "fatigue_score": (16, 32),
                "blink_rate": (12, 20), "typing_speed": (40, 85), "typing_errors": (2.5, 7.0),
                "reaction_time": (240, 330), "mouse_tremor": (8, 17), "sleep_hours": (6.4, 7.8),
                "mood_score": (68, 84), "stress_words": (1, 4)}
NOISE = dict(simulate.NOISE)
DECLINE = dict(simulate.BEN_EFFECT)

# A simple comparator with no personal normal: fixed limits for everyone.
POPULATION_LIMITS = {"heart_rate": ("high", 85), "breathing_rate": ("high", 20), "sleep_hours": ("low", 5.0),
                     "typing_speed": ("low", 30), "typing_errors": ("high", 12), "reaction_time": ("high", 420),
                     "mouse_tremor": ("high", 30), "mood_score": ("low", 50), "fatigue_score": ("high", 55)}


def generate(seed):
    rng = random.Random(seed)
    crew, labels = {}, {}
    for m in CREW:
        aid = m["id"]
        normal = {k: rng.uniform(*r) for k, r in NORMAL_RANGE.items()}
        noise_scale = rng.uniform(0.8, 1.3)
        # One event per astronaut: a gradual decline, a single bad night, a sensor fault, or nothing.
        kind = rng.choice(["decline", "decline", "bad_night", "sensor_fault", "none"])
        start = rng.randint(40, 105)
        ramp = rng.randint(5, 14)          # days to reach full effect
        size = rng.uniform(0.3, 1.0)
        affected = set(rng.sample(sorted(DECLINE), rng.randint(6, len(DECLINE))))
        fault_key = rng.choice(["heart_rate", "typing_speed", "reaction_time", "mouse_tremor"])
        days = {}
        for d in DAYS:
            r = {}
            for k, mu in normal.items():
                v = mu + rng.gauss(0, NOISE[k] * noise_scale)
                if kind == "decline" and d >= start and k in affected:
                    v += DECLINE[k] * size * min(1.0, (d - start + 1) / ramp)
                if kind == "bad_night" and d == start:
                    v += simulate.CHEN_BAD_NIGHT.get(k, 0)
                if k == "stress_words":
                    v = round(v)
                r[k] = round(simulate._clamp(k, v), 2)
            r["workstation_minutes"] = round(rng.uniform(150, 360))
            r["exercise_minutes"] = round(rng.gauss(90, 12))
            days[d] = r
        if kind == "sensor_fault":
            for d in range(start, start + 3):
                days[d][fault_key] = None
        crew[aid] = days
        labels[aid] = {"kind": kind, "start": start, "ramp": ramp, "fault_key": fault_key}
    cabin = {d: {"co2": round(2.2 + rng.gauss(0, 0.15), 2), "radiation": round(0.48 + rng.gauss(0, 0.04), 3)}
             for d in DAYS}
    return {"crew": crew, "cabin": cabin}, labels


def population_flag(reading):
    for k, (side, lim) in POPULATION_LIMITS.items():
        v = reading.get(k)
        if v is None:
            continue
        if (side == "high" and v > lim) or (side == "low" and v < lim):
            return True
    return False


def run(n_missions, first_seed=1000):
    healthy = watch_fa = act_fa = pop_fa = 0
    declines, bad_nights, faults = [], [], []
    for seed in range(first_seed, first_seed + n_missions):
        data, labels = generate(seed)
        raw = {a: {d: dict(r) for d, r in days.items()} for a, days in data["crew"].items()}
        m = HealthMonitor(data=data, crew=CREW)
        for aid, lab in labels.items():
            states = {d: m.assess(aid, d) for d in DAYS if d >= 15}
            for d, x in states.items():
                in_event = lab["kind"] in ("decline",) and d >= lab["start"]
                near_night = lab["kind"] == "bad_night" and lab["start"] <= d <= lab["start"] + 2
                near_fault = lab["kind"] == "sensor_fault" and lab["start"] <= d <= lab["start"] + 2
                if not (in_event or near_night or near_fault):
                    healthy += 1
                    watch_fa += x["state"] == "WATCH"
                    act_fa += x["state"] == "ACT"
                    pop_fa += population_flag(raw[aid][d])
            if lab["kind"] == "decline":
                s = lab["start"]
                after = [d for d in DAYS if d >= s]
                first = lambda pred: next((d - s for d in after if pred(d)), None)  # noqa: E731
                declines.append({
                    "watch": first(lambda d: states[d]["state"] in ("WATCH", "ACT")),
                    "act": first(lambda d: states[d]["state"] == "ACT"),
                    "ai": first(lambda d: states[d]["ai"]["level"] != "normal"),
                    "population": first(lambda d: population_flag(raw[aid][d])),
                    "days_observed": len(after)})
            elif lab["kind"] == "bad_night":
                d = lab["start"]
                bad_nights.append({"state": states[d]["state"], "next_day_act": states.get(d + 1, {}).get("state") == "ACT"})
            elif lab["kind"] == "sensor_fault":
                k = lab["fault_key"]
                for d in range(lab["start"], lab["start"] + 3):
                    x = states[d]
                    faults.append({"read_as_illness": any(f["signal"] == k for f in x["flags"]),
                                   "reported": any(k in f["signals"] for f in x["sensor_faults"])})
        print(f"mission seed {seed} done", file=sys.stderr)

    def stats(key):
        vals = [x[key] for x in declines if x[key] is not None]
        return {"detected": f"{len(vals)}/{len(declines)}",
                "median_delay_days": statistics.median(vals) if vals else None,
                "max_delay_days": max(vals) if vals else None}

    return {
        "missions": n_missions, "seeds": f"{first_seed}-{first_seed + n_missions - 1}",
        "healthy_astronaut_days": healthy,
        "false_watch_per_100_days": round(100 * watch_fa / healthy, 2),
        "false_act_per_100_days": round(100 * act_fa / healthy, 2),
        "population_limits_false_flags_per_100_days": round(100 * pop_fa / healthy, 2),
        "gradual_declines": len(declines),
        "decline_first_watch": stats("watch"), "decline_first_act": stats("act"),
        "decline_first_ai_flag": stats("ai"), "decline_population_limits": stats("population"),
        "bad_nights": len(bad_nights),
        "bad_night_went_to_act": sum(b["state"] == "ACT" for b in bad_nights),
        "bad_night_act_next_day": sum(b["next_day_act"] for b in bad_nights),
        "sensor_fault_days": len(faults),
        "sensor_fault_read_as_illness": sum(f["read_as_illness"] for f in faults),
        "sensor_fault_reported_as_sensor_check": sum(f["reported"] for f in faults),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--missions", type=int, default=20)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "docs" / "evaluation_results.json"))
    args = ap.parse_args()
    res = run(args.missions)
    Path(args.out).parent.mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
