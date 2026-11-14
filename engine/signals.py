"""Signal catalogue: every input the smart habitat measures, with no tests needed.

Each signal says:
  device       which habitat device measures it (see DEVICES)
  system       which body system it belongs to (see BODY_SYSTEMS)
  domain       physical or mental
  bad          which direction is unhealthy: "high", "low" or "both"
  hard_low / hard_high   absolute safety limits, checked whatever the personal normal
  min_sd       smallest spread allowed for the personal baseline (avoids false alarms
               when a value barely moves during the baseline days)
  about        one plain sentence an astronaut can read: what it is and why space matters
"""

SIGNALS = {
    # --- Wristband ---
    "heart_rate": {
        "name": "Resting heart rate", "unit": "bpm", "device": "wristband", "system": "heart",
        "domain": "physical", "bad": "high", "decimals": 0,
        "about": "How fast the heart beats at rest. Stress, poor sleep and illness push it up.",
    },
    "hrv": {
        "name": "Heart rate variability", "unit": "ms", "device": "wristband", "system": "heart",
        "domain": "physical", "bad": "low", "decimals": 0,
        "about": "Small changes in time between heartbeats. It drops with stress and fatigue.",
    },
    "spo2": {
        "name": "Blood oxygen", "unit": "%", "device": "wristband", "system": "lungs",
        "domain": "physical", "bad": "low", "decimals": 1, "hard_low": 92.0, "min_sd": 0.3,
        "about": "How much oxygen the blood carries. Low values can mean a breathing problem or bad cabin air.",
    },
    "body_temp": {
        "name": "Wrist skin temperature (body temperature estimate)", "unit": "°C", "device": "wristband",
        "system": "immune", "domain": "physical", "bad": "high", "decimals": 1,
        "hard_high": 38.0, "min_sd": 0.15, "confirm_first": True,
        "about": "Skin temperature at the wrist, corrected to estimate body temperature. It is not core "
                 "temperature: a high reading is only a warning, confirmed with an oral or ear thermometer.",
    },
    "sleep_hours": {
        "name": "Sleep duration", "unit": "h", "device": "wristband", "system": "brain",
        "domain": "physical", "bad": "low", "decimals": 1,
        "about": "Hours of sleep. Odd light cycles, noise and workload make sleep harder in space.",
    },
    # --- Body sensors ---
    "breathing_rate": {
        "name": "Breathing rate", "unit": "/min", "device": "chest", "system": "lungs",
        "domain": "physical", "bad": "high", "decimals": 0,
        "about": "Breaths per minute. It rises with stress, illness, or too much CO2 in the cabin.",
    },
    "bp_systolic": {
        "name": "Blood pressure, systolic", "unit": "mmHg", "device": "bp", "system": "heart",
        "domain": "physical", "bad": "high", "decimals": 0, "hard_high": 180.0,
        "about": "Pressure when the heart beats. Fluids shift toward the head in low gravity, and stress raises it.",
    },
    "bp_diastolic": {
        "name": "Blood pressure, diastolic", "unit": "mmHg", "device": "bp", "system": "heart",
        "domain": "physical", "bad": "high", "decimals": 0, "hard_high": 120.0,
        "about": "Pressure between heartbeats.",
    },
    "glucose": {
        "name": "Blood sugar (daily average)", "unit": "mg/dL", "device": "glucose", "system": "metabolism",
        "domain": "physical", "bad": "both", "decimals": 0, "hard_low": 54.0, "hard_high": 250.0,
        "about": "Sugar in the blood. Less activity and diet changes on long missions can upset it.",
    },
    # --- Cabin cameras ---
    "fatigue_score": {
        "name": "Fatigue score (cameras)", "unit": "/100", "device": "camera", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0,
        "about": "Built from eye closure and microsleeps seen by the cabin cameras during the day.",
    },
    "blink_rate": {
        "name": "Blink rate (cameras)", "unit": "/min", "device": "camera", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0,
        "about": "Blinks per minute. People blink more as they get tired.",
    },
    # --- Derived: used only when the cameras saw too little of someone that day ---
    "wrist_fatigue": {
        "name": "Fatigue estimate (wristband)", "unit": "/100", "device": "wristband", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0, "min_sd": 4.0, "derived": True,
        "about": "Estimated from sleep, heart rate variability and resting heart rate when the cameras could not see the face.",
    },
    # --- Voice and daily log (optional) ---
    "mood_score": {
        "name": "Mood score (self-report)", "unit": "/100", "device": "voice", "system": "brain",
        "domain": "mental", "bad": "low", "decimals": 0,
        "about": "From the astronaut's own optional daily check-in (voice or text). It is self-report, "
                 "not a diagnosis; the astronaut can skip a day, and it is private to them and the flight "
                 "surgeon.",
    },
    "stress_words": {
        "name": "Stress words in daily log", "unit": "/day", "device": "voice", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0,
        "about": "Words like 'tired', 'worried' or 'can't' in the optional daily log. A rough self-report "
                 "proxy only; private to the astronaut and the flight surgeon.",
    },
}

# Cabin environment is shared by the whole crew and judged against fixed limits.
CABIN_SIGNALS = {
    "co2": {
        "name": "Cabin CO2", "unit": "mmHg", "device": "cabin",
        "watch": 3.0, "act": 4.0, "decimals": 1,
    },
    "radiation": {
        "name": "Radiation dose (cabin dosimeter, effective dose)", "unit": "mSv/day", "device": "cabin",
        "watch": 1.0, "act": 2.0, "decimals": 2,
    },
}

# Mission-level radiation references (NASA-STD-3001 Vol 1 Rev C, via OCHMO-TB-020):
# career effective dose < 600 mSv; a single solar particle event < 250 mSv.
CAREER_DOSE_LIMIT = 600.0
SPE_DOSE_LIMIT = 250.0
# CO2 references (NASA-STD-3001 Vol 2 Rev D [V2 6004] and OCHMO-TB-004): 1-hour average
# no more than 3 mmHg; a 7-day average below 2.5 mmHg keeps headache risk below about 1%.
CO2_7DAY_REFERENCE = 2.5

DEVICES = {
    "wristband": {"name": "Wristband", "measures": "heart rate, HRV, blood oxygen, temperature, sleep; also the astronaut's ID",
                  "how_often": "continuous"},
    "chest": {"name": "Chest strap", "measures": "breathing rate", "how_often": "continuous"},
    "bp": {"name": "Cuffless blood pressure sensor", "measures": "blood pressure",
           "how_often": "several times a day (weekly cuff check)"},
    "glucose": {"name": "Glucose patch", "measures": "blood sugar",
                "how_often": "every few minutes (patch changed every 10-14 days)"},
    "camera": {"name": "Cabin cameras (work areas)", "measures": "blinks, eye closure, microsleeps",
               "how_often": "all day, when a face is in view"},
    "voice": {"name": "Voice and daily log (optional)", "measures": "mood, stress words", "how_often": "daily"},
    "cabin": {"name": "Cabin sensors", "measures": "CO2, radiation", "how_often": "continuous"},
}

# Body systems for the clickable body figure. `hazards` are the NASA Human Research
# Program spaceflight hazards named in the challenge.
BODY_SYSTEMS = {
    "brain": {
        "name": "Brain and mind",
        "does": "Thinking, focus, mood and sleep.",
        "space": "Isolation, confinement, distance from Earth and broken light cycles disturb sleep and mood.",
        "hazards": ["Isolation and confinement", "Distance from Earth"],
    },
    "heart": {
        "name": "Heart and blood vessels",
        "does": "Pumps blood and oxygen to the whole body.",
        "space": "In low gravity, fluids shift toward the head and the heart works differently. Stress raises heart rate and blood pressure.",
        "hazards": ["Altered gravity", "Hostile closed environment"],
    },
    "lungs": {
        "name": "Lungs and breathing",
        "does": "Brings oxygen in and takes CO2 out.",
        "space": "Cabin air is recycled. If CO2 builds up, breathing speeds up and people get headaches and fatigue.",
        "hazards": ["Hostile closed environment"],
    },
    "metabolism": {
        "name": "Metabolism",
        "does": "Turns food into energy and keeps blood sugar steady.",
        "space": "Less movement and a limited diet on long missions can upset blood sugar control.",
        "hazards": ["Altered gravity", "Distance from Earth"],
    },
    "immune": {
        "name": "Immune system",
        "does": "Fights infection.",
        "space": "The immune system can change in space, and radiation adds risk. A fever is an early warning.",
        "hazards": ["Space radiation", "Hostile closed environment"],
        "measured": "Not monitored directly. Only a warning from wrist skin temperature (possible fever). "
                    "No immune lab data in this prototype.",
    },
    "bones": {
        "name": "Bones and muscles",
        "does": "Hold the body up and let it move.",
        "space": "Without gravity, bones and muscles weaken. No sensor measures this day to day: daily resistance exercise is the main protection.",
        "hazards": ["Altered gravity"],
        "measured": "Not measured: we track exercise adherence only (from the exercise log). This is not a "
                    "bone-density or muscle measurement.",
    },
}


# Signals measured directly (the derived wristband fatigue estimate is a backup, not an extra vote).
CORE_SIGNALS = [k for k, v in SIGNALS.items() if not v.get("derived")]
CAMERA_SIGNALS = ("fatigue_score", "blink_rate")
MIN_CAMERA_MINUTES = 30  # less face time than this in a day = camera readings not trusted


def wrist_fatigue(reading):
    """Fatigue 0-100 from the wristband alone: short sleep, low HRV and a raised resting
    heart rate all point to fatigue. Used when the cameras did not see the face enough."""
    if any(reading.get(k) is None for k in ("sleep_hours", "hrv", "heart_rate")):
        return None
    score = (25 + 12 * (7.0 - reading["sleep_hours"]) + 0.8 * (60 - reading["hrv"])
             + 0.8 * (reading["heart_rate"] - 60))
    return round(min(100.0, max(0.0, score)), 1)
