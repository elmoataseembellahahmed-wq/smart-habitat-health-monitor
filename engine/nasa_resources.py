"""The NASA and Canadian Space Agency resources of the Space Apps 2026 challenge
"Create Health Monitoring Software for Astronauts on Space Missions", and how the
system uses them.

These resources are knowledge pages, not numeric datasets, so nothing is "trained" on
them. They are built in as the system's domain knowledge:
  * every signal and every risk pattern is linked to the NASA Human Research Program
    (HRP) risk it relates to, and today's report names the risks behind its findings;
  * the five HRP hazards label the body figure (engine/signals.py BODY_SYSTEMS);
  * the CSA radiation article shapes the radiation design note (a personal dosimeter
    must also count neutrons, about 30% of ISS radiation).
"""

SOURCES = {
    "hazards": {"title": "NASA HRP: 5 Hazards of Human Spaceflight", "agency": "NASA",
                "url": "https://www.nasa.gov/hrp/hazards/"},
    "risks": {"title": "NASA HRP: Risks of Human Spaceflight", "agency": "NASA",
              "url": "https://www.nasa.gov/hrp/risks/"},
    "research": {"title": "NASA HRP: Ongoing HRP Research in Space", "agency": "NASA",
                 "url": "https://www.nasa.gov/hrp/ongoing-hrp-research/"},
    "csa_radiation": {"title": "CSA: Monitoring radiation for astronaut health", "agency": "CSA",
                      "url": "https://www.asc-csa.gc.ca/eng/news/articles/2026/2026-02-26-monitoring-radiation-astronaut-health.asp"},
    "csa_science": {"title": "CSA: Why do we conduct science experiments in space?", "agency": "CSA",
                    "url": "https://www.asc-csa.gc.ca/eng/iss/science/why-do-we-conduct-science-experiments-in-space.asp"},
}

# Risk names exactly as NASA HRP lists them.
CARDIO = "Risk of Cardiovascular Adaptations"
HYPOXIA = "Risk of Hypoxia"
IMMUNE = "Risk of Altered Immune System Responses"
MICROBES = "Risk of Host-Microorganism Interactions"
SLEEP = "Risk of Inadequate Sleep and Irregular Schedules"
BEHAVIOR = "Risk of Behavioral Changes and Psychiatric Disorders"
NUTRITION = "Risk of Inadequate Food and Nutrition"
FITNESS = "Risk of Reduced Cardiorespiratory and Musculoskeletal Fitness"
BONE = "Risk of Spaceflight-Induced Bone Changes"
CANCER = "Risk of Radiation-Induced Cancers"
SUPPORT = "Risk of Inadequate Systems Operations Support"

RISK_BY_SIGNAL = {
    "heart_rate": [CARDIO], "breathing_rate": [HYPOXIA],
    "sleep_hours": [SLEEP], "fatigue_score": [SLEEP], "blink_rate": [SLEEP],
    "typing_speed": [SLEEP, BEHAVIOR], "typing_errors": [SLEEP, BEHAVIOR],
    "reaction_time": [SLEEP, BEHAVIOR], "mouse_tremor": [SLEEP],
    "mood_score": [BEHAVIOR], "stress_words": [BEHAVIOR],
    "exercise": [FITNESS, BONE], "radiation": [CANCER],
}

RISK_BY_PATTERN = {
    "stress_fatigue": [BEHAVIOR, SLEEP, CARDIO], "sleep_debt": [SLEEP], "mental_strain": [BEHAVIOR],
    "fast_breathing": [HYPOXIA], "slowed_reactions": [SLEEP, BEHAVIOR], "unsteady_hand": [SLEEP],
    "cabin_air": [HYPOXIA],
}

HAZARD_BY_RISK = {
    CARDIO: "Gravity fields", HYPOXIA: "Hostile/closed environments", IMMUNE: "Hostile/closed environments",
    MICROBES: "Hostile/closed environments", SLEEP: "Isolation and confinement",
    BEHAVIOR: "Isolation and confinement", NUTRITION: "Distance from Earth", FITNESS: "Gravity fields",
    BONE: "Gravity fields", CANCER: "Space radiation", SUPPORT: "Distance from Earth",
}

# How each resource is used, for the README and the submission.
USE = [
    ("hazards", "Each body system in the dashboard names the HRP hazards behind it (radiation, isolation and "
                "confinement, distance from Earth, gravity fields, hostile/closed environments). The distance "
                "hazard (Mars about 140 million miles away on average) is why every decision is made on board, offline."),
    ("risks", "We chose the 13 signals to cover HRP risks that daily passive monitoring can watch (cardiovascular, "
              "hypoxia, immune/microbial, sleep and schedules, behavioral health, nutrition, fitness and bone, "
              "radiation cancer). Every flag and pattern is linked to its HRP risk by name, and the report lists the "
              "risks behind today's findings. The project itself answers the Risk of Inadequate Systems Operations "
              "Support: crews far from Earth need clear information at the right time. Risks we cannot monitor "
              "passively (SANS, decompression sickness, dynamic loads) are stated as out of scope."),
    ("research", "ARCHeR on Artemis II monitored well-being, activity and sleep, and Standard Measures collect a "
                 "consistent set of physiological and psychological data: this supports our choice of sleep, "
                 "activity and mood signals and a fixed daily measurement set. Tempus Pro (a telemedicine device "
                 "that integrates health data) is the kind of hardware our software could sit on."),
    ("csa_radiation", "Radiation is tracked as a daily dose and a mission total against NASA's career limit. The CSA "
                      "article notes neutrons are about 30% of ISS radiation and that CANS measures them continuously "
                      "and autonomously, so our design note asks for a dosimeter that includes neutrons and runs "
                      "on its own."),
    ("csa_science", "Its list of deep-space risks (more weightlessness, more radiation, longer isolation, longer "
                    "communication delays, less help from Earth) is exactly the case for on-board, self-sufficient "
                    "monitoring; we use it in the problem statement."),
]


def risks_for(decision):
    """NASA HRP risks behind today's findings, with the hazard each belongs to."""
    names = []
    for p in decision.get("patterns", []):
        names += RISK_BY_PATTERN.get(p["id"], [])
    for f in decision.get("flags", []):
        names += RISK_BY_SIGNAL.get(f["signal"], [])
    if any(c.get("level") and c["signal"] == "radiation" for c in decision.get("cabin", [])):
        names.append(CANCER)
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append({"risk": n, "hazard": HAZARD_BY_RISK.get(n, ""), "source": SOURCES["risks"]["url"]})
    return out
