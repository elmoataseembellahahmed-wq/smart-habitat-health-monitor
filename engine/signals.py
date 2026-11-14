"""Signal catalogue: every input NABD uses. No wearables or added hardware: only the
workstation webcam, keyboard and mouse, a typed daily check-in, and the habitat's own
environment data.

Each signal says:
  device       which input it comes from (see DEVICES)
  system       which body system it belongs to (see BODY_SYSTEMS)
  domain       physical or mental
  bad          which direction is unhealthy: "high", "low" or "both"
  hard_low / hard_high   absolute safety limits, checked whatever the personal normal
  min_sd       smallest spread allowed for the personal baseline (avoids false alarms
               when a value barely moves during the baseline days)
  about        one plain sentence an astronaut can read: what it is and why space matters
"""

SIGNALS = {
    # --- Workstation webcam (the camera already on every crew laptop / workstation) ---
    "heart_rate": {
        "name": "Heart rate (webcam estimate)", "unit": "bpm", "device": "camera", "system": "heart",
        "domain": "physical", "bad": "high", "decimals": 0, "hard_low": 40.0, "hard_high": 130.0,
        "confirm_first": True,
        "about": "Measured from tiny colour changes in the face with each heartbeat (remote "
                 "photoplethysmography, rPPG). It is an estimate: a value past the safety limit is "
                 "confirmed with a manual pulse check.",
    },
    "breathing_rate": {
        "name": "Breathing rate (webcam estimate)", "unit": "/min", "device": "camera", "system": "lungs",
        "domain": "physical", "bad": "high", "decimals": 0, "hard_high": 30.0, "confirm_first": True,
        "about": "Breaths per minute, from the small up-and-down movement of the shoulders and chest on "
                 "video. It rises with stress, illness, or too much CO2 in the cabin.",
    },
    "fatigue_score": {
        "name": "Fatigue score (webcam)", "unit": "/100", "device": "camera", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0,
        "about": "Built from eye closure (PERCLOS), yawns and microsleeps seen by the webcam during work.",
    },
    "blink_rate": {
        "name": "Blink rate (webcam)", "unit": "/min", "device": "camera", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0,
        "about": "Blinks per minute. People blink more as they get tired.",
    },
    # --- Keyboard (normal daily work; only timing is used, never the text typed) ---
    "typing_speed": {
        "name": "Typing speed", "unit": "wpm", "device": "keyboard", "system": "brain",
        "domain": "mental", "bad": "low", "decimals": 0, "min_sd": 2.0,
        "about": "Words per minute during normal work. Fatigue, stress and poor sleep slow it down. "
                 "Only key timing is recorded, never what was typed.",
    },
    "typing_errors": {
        "name": "Typing error rate", "unit": "%", "device": "keyboard", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 1, "min_sd": 0.4,
        "about": "Share of keystrokes that are corrections (backspace/delete). It rises when focus drops.",
    },
    # --- Mouse (a 60-second reaction test each morning, plus normal use) ---
    "reaction_time": {
        "name": "Reaction time (mouse test)", "unit": "ms", "device": "mouse", "system": "brain",
        "domain": "mental", "bad": "high", "decimals": 0, "min_sd": 8.0,
        "about": "Time to click when a target appears, in a 60-second test each morning (like NASA's "
                 "Psychomotor Vigilance Test). Slower reactions are an early sign of fatigue.",
    },
    "mouse_tremor": {
        "name": "Hand steadiness (mouse tremor)", "unit": "/100", "device": "mouse", "system": "brain",
        "domain": "physical", "bad": "high", "decimals": 0, "min_sd": 1.0,
        "about": "Small shaking in mouse movement while pointing at a target (0 = steady). Fatigue, "
                 "stress and some illnesses make the hand less steady.",
    },
    # --- Daily check-in, typed on the keyboard (about one minute) ---
    "sleep_hours": {
        "name": "Sleep duration (check-in)", "unit": "h", "device": "checkin", "system": "brain",
        "domain": "physical", "bad": "low", "decimals": 1,
        "about": "Hours slept, entered in the morning check-in. Odd light cycles, noise and workload "
                 "make sleep harder in space.",
    },
    "mood_score": {
        "name": "Mood score (self-report)", "unit": "/100", "device": "checkin", "system": "brain",
        "domain": "mental", "bad": "low", "decimals": 0,
        "about": "From the astronaut's own optional daily check-in. It is self-report, not a diagnosis; "
                 "the astronaut can skip a day, and it is private to them and the flight surgeon.",
    },
    "stress_words": {
        "name": "Stress words in daily log", "unit": "/day", "device": "checkin", "system": "brain",
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
        "name": "Radiation dose (habitat monitor, effective dose)", "unit": "mSv/day", "device": "cabin",
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
    "camera": {"name": "Workstation webcam", "measures": "heart rate and breathing (estimates), blinks, eye closure, fatigue",
               "how_often": "while the astronaut works at the workstation"},
    "keyboard": {"name": "Workstation keyboard", "measures": "typing speed and corrections (timing only, never the text)",
                 "how_often": "during normal work"},
    "mouse": {"name": "Workstation mouse", "measures": "reaction time (60-second morning test), hand steadiness",
              "how_often": "daily test + normal use"},
    "checkin": {"name": "Daily check-in (typed)", "measures": "sleep, mood, stress words, symptoms", "how_often": "daily"},
    "cabin": {"name": "Habitat environment data", "measures": "CO2, radiation, temperature, humidity "
              "(read from the habitat's own life-support systems; NABD adds no sensors)", "how_often": "continuous"},
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
        "space": "In low gravity, fluids shift toward the head and the heart works differently. Stress raises heart rate.",
        "hazards": ["Altered gravity", "Hostile closed environment"],
    },
    "lungs": {
        "name": "Lungs and breathing",
        "does": "Brings oxygen in and takes CO2 out.",
        "space": "Cabin air is recycled. If CO2 builds up, breathing speeds up and people get headaches and fatigue.",
        "hazards": ["Hostile closed environment"],
    },
    "immune": {
        "name": "Immune-related warning indicators",
        "does": "Fights infection.",
        "space": "The immune system can change in space, and radiation adds risk. A fever is an early warning.",
        "hazards": ["Space radiation", "Hostile closed environment"],
        "measured": "Not measured by the workstation. Fever and other symptoms reported in the check-in, plus "
                    "periodic blood-test results when they are entered or imported. No results = unknown, never 'normal'.",
    },
    "bones": {
        "name": "Bones and muscles",
        "does": "Hold the body up and let it move.",
        "space": "Without gravity, bones and muscles weaken. No sensor measures this day to day: daily resistance exercise is the main protection.",
        "hazards": ["Altered gravity"],
        "measured": "Not measured by the workstation. Exercise adherence (indirect), plus periodic bone-scan and "
                    "strength-test results when entered or imported, with date and source.",
    },
}


CORE_SIGNALS = list(SIGNALS)
# Signals measured at the workstation (webcam, keyboard, mouse). They need the astronaut to
# have used their workstation that day, and they identify who was really at it.
WORKSTATION_SIGNALS = tuple(k for k, v in SIGNALS.items() if v["device"] in ("camera", "keyboard", "mouse"))
MIN_WORKSTATION_MINUTES = 30  # less workstation time than this in a day = not enough to measure
