"""Periodic clinical results, personal dosimetry and reported symptoms.

Daily wearables cannot measure bone density, muscle mass or immune function. Those
come from periodic medical tests (for example a bone scan, a strength test, a blood
test). This module lets those results be ENTERED or IMPORTED with their date, unit,
source and the lab's own reference range, and shows them as a trend. It never infers
them from the wristband, never calls a domain "normal" when no result exists, and
leaves interpretation to the flight surgeon.

It also keeps a PERSONAL radiation dose per astronaut (a dosimeter linked to the
wristband ID), separate from the cabin radiation monitor, and the severe symptoms an
astronaut can report, which trigger an immediate ACT without waiting for any streak.
"""

import random

# Which kinds of periodic result each body domain accepts.
TESTS = {
    "bone_density": {"domain": "bones", "name": "Bone mineral density (hip, bone scan)", "unit": "g/cm²", "bad": "low"},
    "grip_strength": {"domain": "bones", "name": "Grip strength", "unit": "kg", "bad": "low"},
    "leg_lean_mass": {"domain": "bones", "name": "Leg lean (muscle) mass", "unit": "kg", "bad": "low"},
    "white_cells": {"domain": "immune", "name": "White blood cell count", "unit": "10⁹/L", "bad": "both"},
    "lymphocytes": {"domain": "immune", "name": "Lymphocyte count", "unit": "10⁹/L", "bad": "both"},
}

# Data status labels shown for every body domain.
MEASURED, ESTIMATED, IMPORTED, SELF, INDIRECT, UNAVAILABLE = (
    "measured daily", "estimated", "imported clinical result", "self-reported", "indirect indicator", "unavailable")

DOMAIN_DATA = {
    "brain": [MEASURED, SELF],
    "heart": [MEASURED],
    "lungs": [MEASURED],
    "metabolism": [MEASURED],
    "immune": [INDIRECT],          # + IMPORTED when a lab result exists
    "bones": [INDIRECT],           # exercise adherence; + IMPORTED when a test result exists
}

# Severe symptoms an astronaut can report: any one means ACT now.
SEVERE_SYMPTOMS = ["chest pain", "shortness of breath", "confusion", "fainting", "severe headache",
                   "vision changes"]
SYMPTOM_ACTION = ("Reported severe symptom: stop current work, follow the mission emergency procedure and "
                  "contact the flight surgeon now. Do not wait for the next contact window.")

EVA_EXTRA_DOSE = 0.6  # mSv on a spacewalk day (simulation value)


class ClinicalStore:
    """Clinical results per astronaut: entered by hand or imported."""

    def __init__(self):
        self.records = []

    def add(self, aid, test, value, day, source="entered by hand", ref_low=None, ref_high=None):
        if test not in TESTS:
            raise ValueError(f"Unknown test '{test}'. Known: {', '.join(TESTS)}")
        rec = {"aid": aid, "test": test, "value": float(value), "day": int(day), "source": source,
               "ref_low": None if ref_low in (None, "") else float(ref_low),
               "ref_high": None if ref_high in (None, "") else float(ref_high),
               **{k: TESTS[test][k] for k in ("domain", "name", "unit")}}
        self.records.append(rec)
        return rec

    def for_domain(self, aid, domain, day):
        """Each test's results up to `day`: latest value, change since the first, range check."""
        out = []
        for test, meta in TESTS.items():
            if meta["domain"] != domain:
                continue
            recs = sorted((r for r in self.records if r["aid"] == aid and r["test"] == test and r["day"] <= day),
                          key=lambda r: r["day"])
            if not recs:
                continue
            first, last = recs[0], recs[-1]
            change = (last["value"] - first["value"]) / first["value"] * 100 if first["value"] and len(recs) > 1 else None
            outside = ((last["ref_low"] is not None and last["value"] < last["ref_low"]) or
                       (last["ref_high"] is not None and last["value"] > last["ref_high"]))
            text = f"{meta['name']}: {last['value']:g} {meta['unit']} on day {last['day']} ({last['source']})"
            if change is not None:
                text += f", {change:+.1f}% since day {first['day']}"
            if outside:
                text += ", outside the lab's reference range"
            out.append({"test": test, "name": meta["name"], "unit": meta["unit"], "latest": last["value"],
                        "day": last["day"], "source": last["source"], "change_pct": change,
                        "outside_range": outside, "history": [(r["day"], r["value"]) for r in recs], "text": text})
        return out


def demo_clinical(crew_ids):
    """Simulated periodic results for the demo: a bone scan and a strength test before
    launch and on day 90. No immune lab results, on purpose: the immune domain must
    then say 'unavailable', not 'normal'."""
    store = ClinicalStore()
    base = {"A": (0.98, 34.0), "B": (1.05, 46.0), "C": (1.01, 41.0)}
    for aid in crew_ids:
        bmd, grip = base.get(aid, (1.0, 40.0))
        src = "simulated clinical result"
        store.add(aid, "bone_density", bmd, 1, src)
        store.add(aid, "bone_density", round(bmd * (1 - 0.012 * 3), 3), 90, src)  # simulation value
        store.add(aid, "grip_strength", grip, 1, src)
        store.add(aid, "grip_strength", round(grip * 0.96, 1), 90, src)
    return store


def add_personal_dose(crew_data, cabin, seed=42, eva_days=None):
    """Simulated personal dosimeter per astronaut (own random stream: nothing else changes).
    Close to the cabin dose, plus extra on spacewalk days."""
    rng = random.Random(seed + 5)
    eva_days = eva_days or {}
    for aid, days in crew_data.items():
        for day in sorted(days):
            dose = cabin[day]["radiation"] * rng.uniform(0.9, 1.1)
            if day in eva_days.get(aid, ()):
                dose += EVA_EXTRA_DOSE
            days[day].setdefault("personal_dose", round(dose, 3))


def dosimetry(days, day, career_limit=600.0):
    """Personal dose today and the mission total so far, from this astronaut's own dosimeter."""
    today = days[day].get("personal_dose")
    vals = [days[d].get("personal_dose") for d in days if d <= day]
    have = [v for v in vals if v is not None]
    if today is None and not have:
        return {"available": False, "note": "Personal dosimeter: no reading (unavailable)."}
    total = sum(have)
    return {"available": True, "today": today, "mission_total": round(total, 1),
            "pct_career": round(total / career_limit * 100, 1), "missing_days": len(vals) - len(have),
            "note": (f"Personal dosimeter (simulated, linked to this astronaut's ID): "
                     f"{'no reading today' if today is None else f'{today:.2f} mSv today'}, "
                     f"{total:.1f} mSv this mission ({total / career_limit * 100:.0f}% of the 600 mSv career limit)."
                     + (f" {len(vals) - len(have)} day(s) without a reading." if len(vals) != len(have) else ""))}
