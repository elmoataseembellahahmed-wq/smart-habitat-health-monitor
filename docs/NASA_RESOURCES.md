# NASA and space agency resources: what we used and how

The challenge lists five resources. They are knowledge pages, not numeric datasets, so no model is trained on them. They are built into the system as its domain knowledge (`engine/nasa_resources.py`), and every finding in a daily report names the NASA Human Research Program (HRP) risk behind it.

| Resource | Agency | How we use it |
|---|---|---|
| [NASA HRP: 5 Hazards of Human Spaceflight](https://www.nasa.gov/hrp/hazards/) | NASA | Each body system in the dashboard names the HRP hazards behind it (radiation, isolation and confinement, distance from Earth, gravity fields, hostile/closed environments). The distance hazard (Mars about 140 million miles away on average) is why every decision is made on board, offline. |
| [NASA HRP: Risks of Human Spaceflight](https://www.nasa.gov/hrp/risks/) | NASA | We chose the 13 signals to cover HRP risks that daily passive monitoring can watch (cardiovascular, hypoxia, immune/microbial, sleep and schedules, behavioral health, nutrition, fitness and bone, radiation cancer). Every flag and pattern is linked to its HRP risk by name, and the report lists the risks behind today's findings. The project itself answers the Risk of Inadequate Systems Operations Support: crews far from Earth need clear information at the right time. Risks we cannot monitor passively (SANS, decompression sickness, dynamic loads) are stated as out of scope. |
| [NASA HRP: Ongoing HRP Research in Space](https://www.nasa.gov/hrp/ongoing-hrp-research/) | NASA | ARCHeR on Artemis II monitored well-being, activity and sleep, and Standard Measures collect a consistent set of physiological and psychological data: this supports our choice of sleep, activity and mood signals and a fixed daily measurement set. Tempus Pro (a telemedicine device that integrates health data) is the kind of hardware our software could sit on. |
| [CSA: Monitoring radiation for astronaut health](https://www.asc-csa.gc.ca/eng/news/articles/2026/2026-02-26-monitoring-radiation-astronaut-health.asp) | CSA | Radiation is tracked as a daily dose and a mission total against NASA's career limit. The CSA article notes neutrons are about 30% of ISS radiation and that CANS measures them continuously and autonomously, so our design note asks for a dosimeter that includes neutrons and runs on its own. |
| [CSA: Why do we conduct science experiments in space?](https://www.asc-csa.gc.ca/eng/iss/science/why-do-we-conduct-science-experiments-in-space.asp) | CSA | Its list of deep-space risks (more weightlessness, more radiation, longer isolation, longer communication delays, less help from Earth) is exactly the case for on-board, self-sufficient monitoring; we use it in the problem statement. |

## Signal → NASA HRP risk → hazard

| Signal | HRP risk | Hazard |
|---|---|---|
| `heart_rate` | Risk of Cardiovascular Adaptations | Gravity fields |
| `hrv` | Risk of Cardiovascular Adaptations | Gravity fields |
| `hrv` | Risk of Inadequate Sleep and Irregular Schedules | Isolation and confinement |
| `bp_systolic` | Risk of Cardiovascular Adaptations | Gravity fields |
| `bp_diastolic` | Risk of Cardiovascular Adaptations | Gravity fields |
| `spo2` | Risk of Hypoxia | Hostile/closed environments |
| `breathing_rate` | Risk of Hypoxia | Hostile/closed environments |
| `body_temp` | Risk of Altered Immune System Responses | Hostile/closed environments |
| `body_temp` | Risk of Host-Microorganism Interactions | Hostile/closed environments |
| `sleep_hours` | Risk of Inadequate Sleep and Irregular Schedules | Isolation and confinement |
| `fatigue_score` | Risk of Inadequate Sleep and Irregular Schedules | Isolation and confinement |
| `blink_rate` | Risk of Inadequate Sleep and Irregular Schedules | Isolation and confinement |
| `mood_score` | Risk of Behavioral Changes and Psychiatric Disorders | Isolation and confinement |
| `stress_words` | Risk of Behavioral Changes and Psychiatric Disorders | Isolation and confinement |
| `glucose` | Risk of Inadequate Food and Nutrition | Distance from Earth |
| `exercise` | Risk of Reduced Cardiorespiratory and Musculoskeletal Fitness | Gravity fields |
| `exercise` | Risk of Spaceflight-Induced Bone Changes | Gravity fields |
| `radiation` | Risk of Radiation-Induced Cancers | Space radiation |

HRP risks we do **not** monitor, because daily passive sensing cannot: Spaceflight Associated Neuro-ocular Syndrome (SANS), decompression sickness, altered sensorimotor and vestibular function, injury from dynamic loads, injury from spacewalks, inadequate teamwork.

Other NASA references used for limits: NASA-STD-3001 (cabin CO2 3 mmHg, OCHMO-TB-004) and the 600 mSv career radiation limit (OCHMO-TB-020); see `docs/THRESHOLDS.md`.

No real astronaut data was used: health data is simulated (`engine/simulate.py`); only the webcam is a real input. Next step: NASA Open Science Data Repository (OSDR) human data.
