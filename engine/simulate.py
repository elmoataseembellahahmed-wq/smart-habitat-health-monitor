"""Simulated mission data.

Real day-by-day in-flight astronaut data is not public, so this module generates a
realistic, repeatable scenario (fixed random seed) for the demo. All personal inputs
come from the astronaut's workstation: the webcam, the keyboard, the mouse and a
typed daily check-in. No wearables or added hardware.

* Mission days 1-125 on the way to Mars.
* Days 1-14 are the baseline window: the system learns each astronaut's normal.
  Everyone stays healthy until day 118.
* Astronaut A ("Amira") stays healthy the whole time.
* Astronaut B ("Ben") slowly develops stress and fatigue from day 119: sleep drifts,
  heart and breathing rate (webcam) rise, typing slows with more corrections, reaction
  time and hand steadiness get worse, mood falls, stress words rise. The main story.
* Astronaut C ("Chen") has ONE bad night on day 121 and recovers. The system
  should notice it without raising a false alarm.
* Cabin CO2 creeps up on days 123-125 (a scrubber problem) and affects everyone.
* Workstation time: each astronaut works 3-6 hours a day at their workstation. On days
  60-61 Amira is preparing for and doing a spacewalk (in a suit, away from the
  workstation), so no webcam, keyboard or mouse data that day: said plainly, not guessed.
* Login swap: on day 50 Amira and Chen work under each other's workstation login by
  mistake. The system should spot it from typing, reaction time and webcam signals
  alone and ask them to check their login, without raising a health alarm.
* Input faults (days 30-55): Amira's webcam is covered on days 40-41 (no webcam data),
  Chen's mouse driver freezes on days 30-35 (the same steadiness value every day), Ben's
  webcam reads a heart rate of 250 bpm on day 35 (bad lighting), and some optional diary
  days are skipped. The system must label these "unavailable" and ask for an input
  check, never read them as illness.
* Exercise log: minutes of daily resistance and treadmill exercise (exercise adherence,
  which protects bones and muscles; it is not a bone measurement).

Replace this module with the real workstation feed to use the system for real.
"""

import random

MISSION_START = 1
MISSION_END = 125
BASELINE_DAYS = range(1, 15)  # days 1..14: learn each astronaut's normal
STORY_START = 100  # days 100-125 keep the original demo scenario (same random stream)

# Days an astronaut barely used the workstation: (astronaut, day) -> minutes at it.
WORKSTATION_GAPS = {("A", 60): 5, ("A", 61): 0}

# Days two astronauts worked under each other's login: day -> (astronaut, astronaut).
SWAPPED_LOGINS = {50: ("A", "C")}
SESSION_KEYS = ("heart_rate", "breathing_rate", "fatigue_score", "blink_rate",
                "typing_speed", "typing_errors", "reaction_time", "mouse_tremor")

# Input faults (all before day 69, so the demo days 100-125 are not affected).
INPUT_FAULTS = [
    ("A", "heart_rate", range(40, 42), "missing"),       # webcam covered
    ("A", "breathing_rate", range(40, 42), "missing"),
    ("A", "fatigue_score", range(40, 42), "missing"),
    ("A", "blink_rate", range(40, 42), "missing"),
    ("C", "mouse_tremor", range(30, 36), "stuck"),       # mouse driver frozen
    ("B", "heart_rate", range(35, 36), 250.0),           # bad lighting: impossible webcam reading
]
SKIPPED_DIARY = [("A", 55), ("C", 56), ("C", 57)]  # optional daily diary not filled in
EXERCISE_PLAN = 90      # planned exercise minutes a day
SHORT_EXERCISE = {("B", d) for d in range(90, 97)}  # Ben skips most exercise for a week

CREW = [
    {"id": "A", "name": "Amira", "role": "Commander"},
    {"id": "B", "name": "Ben", "role": "Flight engineer"},
    {"id": "C", "name": "Chen", "role": "Mission specialist"},
]

# Each astronaut's personal "normal" (people differ, which is why baselines are personal).
PERSONAL_NORMAL = {
    "A": {"heart_rate": 60, "breathing_rate": 13, "fatigue_score": 22, "blink_rate": 15,
          "typing_speed": 58, "typing_errors": 5.0, "reaction_time": 290, "mouse_tremor": 13,
          "sleep_hours": 7.2, "mood_score": 78, "stress_words": 2},
    "B": {"heart_rate": 66, "breathing_rate": 14, "fatigue_score": 25, "blink_rate": 17,
          "typing_speed": 48, "typing_errors": 6.0, "reaction_time": 310, "mouse_tremor": 15,
          "sleep_hours": 6.9, "mood_score": 74, "stress_words": 3},
    "C": {"heart_rate": 63, "breathing_rate": 15, "fatigue_score": 24, "blink_rate": 16,
          "typing_speed": 78, "typing_errors": 3.0, "reaction_time": 250, "mouse_tremor": 9,
          "sleep_hours": 7.0, "mood_score": 76, "stress_words": 2},
}

# Day-to-day natural noise (standard deviation) for each signal.
NOISE = {"heart_rate": 2.0, "breathing_rate": 0.8, "fatigue_score": 3.0, "blink_rate": 1.5,
         "typing_speed": 2.5, "typing_errors": 0.5, "reaction_time": 12.0, "mouse_tremor": 1.2,
         "sleep_hours": 0.35, "mood_score": 3.0, "stress_words": 1.0}


def _ben_decline(day):
    """How far Ben has drifted from normal on a given day (0 = normal, 1 = worst)."""
    if day < 119:
        return 0.0
    return min(1.0, (day - 118) / 6.0)  # day 119 -> 0.17 ... day 124+ -> 1.0


# Size of the change at full decline (positive = value goes up).
BEN_EFFECT = {"heart_rate": +12, "breathing_rate": +4, "fatigue_score": +30, "blink_rate": +8,
              "typing_speed": -12, "typing_errors": +4.0, "reaction_time": +90, "mouse_tremor": +8,
              "sleep_hours": -2.4, "mood_score": -30, "stress_words": +9}

# Effect of the CO2 failure (days 123-125) on every crew member, per day of exposure.
CO2_EFFECT = {"breathing_rate": +1.0, "reaction_time": +15, "fatigue_score": +3}

# Chen's single bad night on day 121.
CHEN_BAD_NIGHT = {"sleep_hours": -3.0, "fatigue_score": +18, "heart_rate": +5, "reaction_time": +40,
                  "typing_errors": +1.5}


def _clamp(key, value):
    limits = {"fatigue_score": (0, 100), "mood_score": (0, 100), "stress_words": (0, 50),
              "sleep_hours": (0, 12), "typing_errors": (0, 60), "mouse_tremor": (0, 100)}
    lo, hi = limits.get(key, (0, 5000))
    return max(lo, min(hi, value))


def _value(aid, key, day, rng):
    value = PERSONAL_NORMAL[aid][key] + rng.gauss(0, NOISE[key])
    if aid == "B":
        value += BEN_EFFECT[key] * _ben_decline(day)
    if aid == "C" and day == 121:
        value += CHEN_BAD_NIGHT.get(key, 0)
    if day >= 123:
        # Rising CO2 affects everyone: faster breathing, slower reactions, more fatigue.
        value += CO2_EFFECT.get(key, 0) * (day - 122)
    if key == "stress_words":
        value = round(value)
    return round(_clamp(key, value), 2)


def generate(seed=42):
    """Return {"crew": {...}, "cabin": {...}} with one reading per signal per day."""
    rng = random.Random(seed)
    crew_data = {}
    for member in CREW:
        aid = member["id"]
        crew_data[aid] = {day: {key: _value(aid, key, day, rng) for key in PERSONAL_NORMAL[aid]}
                          for day in range(MISSION_START, MISSION_END + 1)}

    cabin = {}
    rng3 = random.Random(seed + 2)
    for day in range(MISSION_START, MISSION_END + 1):
        co2 = 2.2 + rng3.gauss(0, 0.15)
        if day >= 123:
            co2 += 0.7 * (day - 122)  # scrubber degrading: about 2.9, 3.6, 4.3
        cabin[day] = {"co2": round(co2, 2), "radiation": round(0.48 + rng3.gauss(0, 0.04), 3)}

    # Minutes each astronaut used their workstation (own random stream).
    rng4 = random.Random(seed + 3)
    for member in CREW:
        aid = member["id"]
        for day in range(MISSION_START, MISSION_END + 1):
            minutes = rng4.uniform(180, 360)
            if (aid, day) in WORKSTATION_GAPS:
                minutes = WORKSTATION_GAPS[(aid, day)]
            crew_data[aid][day]["workstation_minutes"] = round(minutes)

    # Swapped logins: each session reports the other person.
    for day, (a, b) in SWAPPED_LOGINS.items():
        for k in SESSION_KEYS:
            crew_data[a][day][k], crew_data[b][day][k] = crew_data[b][day][k], crew_data[a][day][k]

    # Input faults and skipped diary entries.
    for aid, key, days, fault in INPUT_FAULTS:
        first = None
        for day in days:
            if fault == "missing":
                crew_data[aid][day][key] = None
            elif fault == "stuck":
                first = crew_data[aid][day][key] if first is None else first
                crew_data[aid][day][key] = first
            else:
                crew_data[aid][day][key] = fault
    for aid, day in SKIPPED_DIARY:
        crew_data[aid][day]["mood_score"] = None
        crew_data[aid][day]["stress_words"] = None

    # Cabin temperature and humidity (own random stream).
    rng6 = random.Random(seed + 6)
    for day in range(MISSION_START, MISSION_END + 1):
        cabin[day]["temperature"] = round(rng6.gauss(22.0, 0.6), 1)
        cabin[day]["humidity"] = round(rng6.gauss(45.0, 4.0))

    # Exercise log (own random stream).
    rng5 = random.Random(seed + 4)
    for member in CREW:
        aid = member["id"]
        for day in range(MISSION_START, MISSION_END + 1):
            minutes = rng5.gauss(EXERCISE_PLAN, 12)
            if rng5.random() < 0.05 or (aid, day) in SHORT_EXERCISE:
                minutes = rng5.uniform(0, 30)        # a missed or cut-short session
            crew_data[aid][day]["exercise_minutes"] = round(max(0, minutes))

    for aid in crew_data:
        crew_data[aid] = dict(sorted(crew_data[aid].items()))
    cabin = dict(sorted(cabin.items()))
    return {"crew": crew_data, "cabin": cabin}
