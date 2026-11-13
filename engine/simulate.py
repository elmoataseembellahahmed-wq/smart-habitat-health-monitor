"""Simulated mission data.

Real day-by-day in-flight astronaut data is not public, so this module generates a
realistic, repeatable scenario (fixed random seed) for the demo:

* Mission days 1-125 on the way to Mars.
* Days 1-14 are the baseline window: the system learns each astronaut's normal.
  Everyone stays healthy until day 118.
* Astronaut A ("Amira") stays healthy the whole time.
* Astronaut B ("Ben") slowly develops stress and fatigue from day 119:
  sleep drifts, HRV drops, blood pressure and blood sugar rise, mood falls, stress
  words rise. This is the main story.
* Astronaut C ("Chen") has ONE bad night on day 121 and recovers. The system
  should notice it without raising a false alarm.
* Cabin CO2 creeps up on days 123-125 (a scrubber problem) and affects everyone.
* Camera time: the cameras usually see each face for 3-6 hours a day. On days 60-61 Amira
  is preparing for and doing a spacewalk (in a suit, away from cameras), and on day 122 Ben
  works in a module without cameras. Then fatigue is estimated from the wristband.

Replace this module with real sensor feeds to use the system for real.
"""

import random

MISSION_START = 1
MISSION_END = 125
BASELINE_DAYS = range(1, 15)  # days 1..14: learn each astronaut's normal
STORY_START = 100  # days 100-125 keep the original demo scenario (same random stream)

# Days a camera could not see someone: (astronaut, day) -> minutes in view.
CAMERA_GAPS = {("A", 60): 5, ("A", 61): 0, ("B", 122): 15}

CREW = [
    {"id": "A", "name": "Amira", "role": "Commander"},
    {"id": "B", "name": "Ben", "role": "Flight engineer"},
    {"id": "C", "name": "Chen", "role": "Mission specialist"},
]

# Each astronaut's personal "normal" (people differ, which is why baselines are personal).
PERSONAL_NORMAL = {
    "A": {"heart_rate": 58, "hrv": 62, "spo2": 98.0, "sleep_hours": 7.2,
          "fatigue_score": 22, "blink_rate": 15, "mood_score": 78, "stress_words": 2},
    "B": {"heart_rate": 64, "hrv": 55, "spo2": 97.6, "sleep_hours": 6.9,
          "fatigue_score": 25, "blink_rate": 17, "mood_score": 74, "stress_words": 3},
    "C": {"heart_rate": 61, "hrv": 48, "spo2": 97.8, "sleep_hours": 7.0,
          "fatigue_score": 24, "blink_rate": 16, "mood_score": 76, "stress_words": 2},
}

# Day-to-day natural noise (standard deviation) for each signal.
NOISE = {"heart_rate": 2.0, "hrv": 3.0, "spo2": 0.4, "sleep_hours": 0.35,
         "fatigue_score": 3.0, "blink_rate": 1.5, "mood_score": 3.0, "stress_words": 1.0}


def _ben_decline(day):
    """How far Ben has drifted from normal on a given day (0 = normal, 1 = worst)."""
    if day < 119:
        return 0.0
    return min(1.0, (day - 118) / 6.0)  # day 119 -> 0.17 ... day 124+ -> 1.0


# Size of the change at full decline (positive = value goes up).
BEN_EFFECT = {"heart_rate": +12, "hrv": -22, "spo2": -0.6, "sleep_hours": -2.4,
              "fatigue_score": +30, "blink_rate": +8, "mood_score": -30, "stress_words": +9}

# Chen's single bad night on day 121.
CHEN_BAD_NIGHT = {"sleep_hours": -3.0, "fatigue_score": +18, "hrv": -8, "heart_rate": +5}

# Vital signs from the newer habitat devices (chest strap, blood pressure sensor,
# glucose patch, wrist temperature). They use their own random stream so adding them
# does not change the original story above.
VITALS_NORMAL = {
    "A": {"body_temp": 36.6, "breathing_rate": 13, "bp_systolic": 112, "bp_diastolic": 72, "glucose": 92},
    "B": {"body_temp": 36.7, "breathing_rate": 14, "bp_systolic": 118, "bp_diastolic": 76, "glucose": 97},
    "C": {"body_temp": 36.6, "breathing_rate": 15, "bp_systolic": 115, "bp_diastolic": 74, "glucose": 94},
}
VITALS_NOISE = {"body_temp": 0.1, "breathing_rate": 0.8, "bp_systolic": 3.5, "bp_diastolic": 2.5,
                "glucose": 4.0}
# Ben's stress also shows in blood pressure, breathing and blood sugar.
BEN_VITALS_EFFECT = {"body_temp": +0.15, "breathing_rate": +4, "bp_systolic": +18,
                     "bp_diastolic": +10, "glucose": +22}
CHEN_BAD_NIGHT_VITALS = {"bp_systolic": +6}


def _clamp(key, value):
    limits = {"spo2": (85, 100), "fatigue_score": (0, 100), "mood_score": (0, 100),
              "stress_words": (0, 50), "sleep_hours": (0, 12)}
    lo, hi = limits.get(key, (0, 1000))
    return max(lo, min(hi, value))


def generate(seed=42):
    """Return {"crew": {...}, "cabin": {...}} with one reading per signal per day."""
    rng = random.Random(seed)
    crew_data = {}
    for member in CREW:
        aid = member["id"]
        days = {}
        for day in range(STORY_START, MISSION_END + 1):
            reading = {}
            for key, normal in PERSONAL_NORMAL[aid].items():
                value = normal + rng.gauss(0, NOISE[key])
                if aid == "B":
                    value += BEN_EFFECT[key] * _ben_decline(day)
                if aid == "C" and day == 121:
                    value += CHEN_BAD_NIGHT.get(key, 0)
                if key == "stress_words":
                    value = round(value)
                reading[key] = round(_clamp(key, value), 2)
            days[day] = reading
        crew_data[aid] = days

    cabin = {}
    for day in range(STORY_START, MISSION_END + 1):
        co2 = 2.2 + rng.gauss(0, 0.15)
        if day >= 123:
            co2 += 0.7 * (day - 122)  # scrubber degrading: 2.9, 3.6, 4.3
        cabin[day] = {
            "co2": round(co2, 2),
            "radiation": round(0.48 + rng.gauss(0, 0.04), 3),
        }

    # Newer habitat devices, on their own random stream (see VITALS_NORMAL).
    rng2 = random.Random(seed + 1)
    for member in CREW:
        aid = member["id"]
        for day in range(STORY_START, MISSION_END + 1):
            reading = crew_data[aid][day]
            for key, normal in VITALS_NORMAL[aid].items():
                value = normal + rng2.gauss(0, VITALS_NOISE[key])
                if aid == "B":
                    value += BEN_VITALS_EFFECT[key] * _ben_decline(day)
                if aid == "C" and day == 121:
                    value += CHEN_BAD_NIGHT_VITALS.get(key, 0)
                if key == "breathing_rate" and day >= 123:
                    value += 0.3 * (day - 122)  # everyone breathes a little faster as CO2 rises
                reading[key] = round(value, 2 if key == "body_temp" else 1)

    # Early mission, days 1-99: everyone healthy, on a separate random stream so the
    # demo days (100-125) stay exactly the same.
    rng3 = random.Random(seed + 2)
    for member in CREW:
        aid = member["id"]
        for day in range(MISSION_START, STORY_START):
            reading = {}
            for key, normal in PERSONAL_NORMAL[aid].items():
                value = normal + rng3.gauss(0, NOISE[key])
                if key == "stress_words":
                    value = round(value)
                reading[key] = round(_clamp(key, value), 2)
            for key, normal in VITALS_NORMAL[aid].items():
                value = normal + rng3.gauss(0, VITALS_NOISE[key])
                reading[key] = round(value, 2 if key == "body_temp" else 1)
            crew_data[aid][day] = reading
    for day in range(MISSION_START, STORY_START):
        cabin[day] = {"co2": round(2.2 + rng3.gauss(0, 0.15), 2),
                      "radiation": round(0.48 + rng3.gauss(0, 0.04), 3)}

    # Minutes the cabin cameras saw each face (own random stream: other values unchanged).
    rng4 = random.Random(seed + 3)
    for member in CREW:
        aid = member["id"]
        for day in range(MISSION_START, MISSION_END + 1):
            minutes = rng4.uniform(180, 360)
            if (aid, day) in CAMERA_GAPS:
                minutes = CAMERA_GAPS[(aid, day)]
            crew_data[aid][day]["camera_minutes"] = round(minutes)

    for aid in crew_data:
        crew_data[aid] = dict(sorted(crew_data[aid].items()))
    cabin = dict(sorted(cabin.items()))
    return {"crew": crew_data, "cabin": cabin}
