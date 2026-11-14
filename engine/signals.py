"""Signal catalogue: every health indicator NABD uses. The astronaut enters them
himself (keyboard and mouse) from the onboard medical kit and a daily check-in, and the
laptop webcam adds fatigue and blinking. NABD adds no wearables or other hardware.

Each signal says:
  device       where the value comes from (see DEVICES)
  system       which body system it belongs to (see BODY_SYSTEMS)
  domain       physical or mental
  bad          which direction is unhealthy: "high", "low" or "both"
  hard_low / hard_high   absolute safety limits, checked whatever the personal normal
  how          plain instructions for taking the measurement
  min_sd       smallest spread allowed for the personal baseline (avoids false alarms
               when a value barely moves during the baseline days)
  about        one plain sentence an astronaut can read: what it is and why space matters
"""

SIGNALS = {
    # --- Typed in by the astronaut (keyboard and mouse), measured with the onboard medical kit ---
    "heart_rate": {
        "name": "Resting heart rate", "unit": "bpm", "device": "entry", "system": "heart",
        "domain": "physical", "bad": "high", "decimals": 0, "hard_low": 40.0, "hard_high": 130.0,
        "how": "Sit still for 5 minutes, then count the pulse at the wrist for 60 seconds (or read it from the pulse oximeter).",
        "about": "How fast the heart beats at rest. Stress, poor sleep and illness push it up.",
    },
    "spo2": {
        "name": "Blood oxygen", "unit": "%", "device": "entry", "system": "lungs",
        "domain": "physical", "bad": "low", "decimals": 1, "hard_low": 92.0, "min_sd": 0.3,
        "how": "Clip the finger pulse oximeter on, keep the hand still for 30 seconds, type the steady value.",
        "about": "How much oxygen the blood carries. Low values can mean a breathing problem or bad cabin air.",
    },
    "body_temp": {
        "name": "Body temperature", "unit": "°C", "device": "entry", "system": "immune",
        "domain": "physical", "bad": "high", "decimals": 1, "hard_high": 38.0, "min_sd": 0.15,
        "how": "Oral or ear thermometer, before eating or drinking.",
        "about": "A raised temperature can be the first sign of an infection.",
    },
    "breathing_rate": {
        "name": "Breathing rate", "unit": "/min", "device": "entry", "system": "lungs",
        "domain": "physical", "bad": "high", "decimals": 0, "hard_high": 30.0,
        "how": "Sit still and count breaths for 60 seconds (one rise and fall = one breath).",
        "about": "Breaths per minute. It rises with stress, illness, or too much CO2 in the cabin.",
    },
    "bp_systolic": {
        "name": "Blood pressure, systolic", "unit": "mmHg", "device": "entry", "system": "heart",
        "domain": "physical", "bad": "high", "decimals": 0, "hard_high": 180.0,
        "how": "Upper-arm cuff, seated, arm at heart level, after 5 minutes of rest. Type the top number.",
        "about": "Pressure when the heart beats. Fluids shift toward the head in low gravity, and stress raises it.",
    },
    "bp_diastolic": {
        "name": "Blood pressure, diastolic", "unit": "mmHg", "device": "entry", "system": "heart",
        "domain": "physical", "bad": "high", "decimals": 0, "hard_high": 120.0,
        "how": "Same cuff reading: type the bottom number.",
        "about": "Pressure between heartbeats.",
    },
    "glucose": {
        "name": "Blood sugar (morning)", "unit": "mg/dL", "device": "entry", "system": "metabolism",
        "domain": "physical", "bad": "both", "decimals": 0, "hard_low": 54.0, "hard_high": 250.0,
        "how": "Finger-prick glucose meter, in the morning before breakfast.",
        "about": "Sugar in the blood. Less activity and diet changes on long missions can upset it.",
    },
    # --- Daily check-in, typed or clicked ---
    "sleep_hours": {
        "name": "Sleep duration", "unit": "h", "device": "checkin", "system": "brain",
        "domain": "physical", "bad": "low", "decimals": 1,
        "how": "Hours slept last night, entered in the morning check-in.",
        "about": "Hours of sleep. Odd light cycles, noise and workload make sleep harder in space.",
    },
    "mood_score": {
        "name": "Mood score (self-report)", "unit": "/100", "device": "checkin", "system": "brain",
        "domain": "mental", "bad": "low", "decimals": 0,
        "how": "Move the mood slider in the daily check-in (optional).",
        "about": "From the astronaut's own optional daily check-in. It is self-report, not a diagnosis; "
                 "the astronaut can skip a day, and it is private to them and the flight surgeon.",
    },
    "stress_words": {
        "name": "Stress words in daily log", "unit": "/day", "device": "checkin", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0,
        "how": "Counted automatically from the optional daily log text the astronaut types.",
        "about": "Words like 'tired', 'worried' or 'can't' in the optional daily log. A rough self-report "
                 "proxy only; private to the astronaut and the flight surgeon.",
    },
    # --- Camera (webcam images while the astronaut works at the laptop) ---
    "fatigue_score": {
        "name": "Fatigue score (camera)", "unit": "/100", "device": "camera", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0,
        "how": "Measured by the laptop webcam from eye closure while the astronaut works. Nothing to do.",
        "about": "Built from eye closure and microsleeps seen by the webcam during the day.",
    },
    "blink_rate": {
        "name": "Blink rate (camera)", "unit": "/min", "device": "camera", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0,
        "how": "Measured by the laptop webcam. Nothing to do.",
        "about": "Blinks per minute. People blink more as they get tired.",
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
    # NASA-STD-3001 Vol. 2 [V2 6012] crew health environmental limits (OCHMO-TB-002): operating
    # envelope 18 °C / 75% humidity to 27 °C / 25% humidity. Outside it = WATCH (published);
    # the ACT values further out are project assumptions. Oxygen partial pressure is NOT added:
    # its limits are in Table 6.2-1 of [V2 6003], which we have not yet sourced.
    "temperature": {
        "name": "Cabin temperature", "unit": "°C", "device": "cabin",
        "low_watch": 18.0, "watch": 27.0, "low_act": 15.0, "act": 30.0, "decimals": 1, "optional": True,
    },
    "humidity": {
        "name": "Cabin relative humidity", "unit": "%", "device": "cabin",
        "low_watch": 25.0, "watch": 75.0, "low_act": 15.0, "act": 85.0, "decimals": 0, "optional": True,
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
    "entry": {"name": "Typed measurement (onboard medical kit)",
              "measures": "heart rate, blood oxygen, temperature, breathing, blood pressure, blood sugar",
              "how_often": "each morning (about 5 minutes), or any time the astronaut feels unwell"},
    "checkin": {"name": "Daily check-in (keyboard and mouse)", "measures": "sleep, mood, symptoms, optional log",
                "how_often": "daily"},
    "camera": {"name": "Laptop webcam", "measures": "eye closure, blinks, microsleeps (fatigue)",
               "how_often": "while the astronaut works at the laptop"},
    "cabin": {"name": "Habitat environment data", "measures": "CO2, radiation, temperature, humidity "
              "(read from the habitat's own systems)", "how_often": "continuous"},
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
        "name": "Immune-related warning indicators",
        "does": "Fights infection.",
        "space": "The immune system can change in space, and radiation adds risk. A fever is an early warning.",
        "hazards": ["Space radiation", "Hostile closed environment"],
        "measured": "Body temperature typed in each morning and symptoms from the check-in, plus periodic "
                    "blood-test results when they are entered or imported. No results = unknown, never 'normal'.",
    },
    "bones": {
        "name": "Bones and muscles",
        "does": "Hold the body up and let it move.",
        "space": "Without gravity, bones and muscles weaken. No sensor measures this day to day: daily resistance exercise is the main protection.",
        "hazards": ["Altered gravity"],
        "measured": "Not measured daily. Exercise adherence (indirect), plus periodic bone-scan and "
                    "strength-test results when entered or imported, with date and source.",
    },
}


CORE_SIGNALS = list(SIGNALS)
CAMERA_SIGNALS = ("fatigue_score", "blink_rate")
# Measurements typed in from the medical kit: they belong to whoever's profile they are saved in.
ENTRY_SIGNALS = tuple(k for k, v in SIGNALS.items() if v["device"] == "entry")
MIN_CAMERA_MINUTES = 30  # less face time than this in a day = camera readings not trusted
