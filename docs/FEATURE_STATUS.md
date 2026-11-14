# Feature status: what is real, what is simulated, what is planned

Four labels, used the same way in the README, the slides and the dashboard:

* **Implemented and tested (real input):** works on real input today.
* **Implemented, simulated input:** the software is complete and tested, but the demo values come from the mission simulator instead of an astronaut typing them in.
* **Designed, not implemented:** described, not built.
* **Out of scope for the prototype:** not attempted; stated so nobody assumes it.

## Software features

| Feature | Status | Where | Evidence |
|---|---|---|---|
| Live webcam: blink rate, PERCLOS, long eye closures, daily summary | Implemented and tested (real input) | `camera/live_camera.py`, `camera/blink_tracker.py` | Tests 10, 11, 20, 30, 31; run `python camera/live_camera.py --astronaut B` |
| Camera pauses with 2+ faces; low-confidence minutes never trigger ACT alone | Implemented and tested (real input) | `camera/blink_tracker.py`, `engine/live.py` | Tests 20, 31 |
| Camera never stores or sends images (only numbers leave) | Implemented and tested | `camera/` | Test 30 (privacy test) |
| Personal normal (days 1-14) + weekly re-learning from NORMAL days only | Implemented, simulated input | `engine/monitor.py` | Tests 6, 8 |
| Fixed-anchor slow-drift check | Implemented, simulated input | `engine/integrity.py` | Test 19 |
| Profile mix-up check (values saved in another astronaut's profile) | Implemented, simulated input | `engine/integrity.py` | Test 18 |
| Entry quality layer (skipped, copied, impossible values) | Implemented, simulated input | `engine/quality.py` | Tests 21, 22 |
| Data coverage / confidence beside every status | Implemented, simulated input | `engine/quality.py` | Test 24 |
| Readable rules: Normal / Watch / Act with reasons | Implemented, simulated input | `engine/fusion.py` | Tests 1-3, 16 |
| AI double-check (Isolation Forest, plain Python) | Implemented, simulated input | `engine/anomaly.py` | Tests 5, 7; `docs/MODEL_CARD.md` |
| Camera gap said plainly ("not measured", never guessed) | Implemented, simulated input | `engine/monitor.py` | Test 17 |
| Guidance on treatment and improvement for every finding (EN/AR, NASA HRP sources, no medicines) | Implemented and tested | `engine/guidance.py` | Test 43 |
| How-to-measure instructions for every typed value | Implemented and tested | `engine/signals.py` (`how`), manual page | Test 44 |
| Crew-wide vs individual events (cabin CO2) | Implemented, simulated input | `engine/monitor.py` (`crew_wide`) | Test 26 |
| Radiation: daily dose + mission total vs 600 mSv career limit | Implemented, simulated input | `engine/analysis.py` | Test 27 |
| Role-based views (surgeon / commander / astronaut) + audit log | Implemented, simulated input (no real login) | `engine/access.py` | Test 29 |
| Versions of rules, thresholds, model and personal normal on every decision | Implemented and tested | `engine/version.py` | Test 28 |
| Daily report in English and Arabic, PDF via the browser | Implemented and tested | `engine/report.py`, `engine/arabic.py` | Test 15 |
| Exercise adherence for bones and muscles | Implemented, simulated input | `engine/monitor.py` (`exercise`) | Test 32 |
| Runs offline, standard library only | Implemented and tested | `run_offline.py`, `tools/benchmark.py` | `docs/PERFORMANCE.md` |
| Independent evaluation on new labelled missions | Implemented (synthetic data) | `tools/evaluate.py` | `docs/MODEL_CARD.md` |
| Real login, encryption at rest, signed updates | Designed, not implemented | `docs/PRIVACY_SECURITY.md` | - |
| Timestamps, buffering and duplicate handling for entries sent from crew laptops | Implemented and tested | `engine/ingest.py` | Ingestion test |
| Clinical validation of thresholds and actions | Out of scope for the prototype | - | Needs flight surgeons and real data |

## Inputs (no wearables or added hardware)

NABD adds no hardware. The astronaut enters the values himself with the keyboard and mouse, and the laptop webcam adds fatigue.

| Input | Signals | Status | Open question |
|---|---|---|---|
| Typed measurements from the standard onboard medical kit (pulse oximeter, thermometer, blood pressure cuff, glucose meter, a watch to count breaths) | heart rate, blood oxygen, body temperature, breathing rate, blood pressure, morning blood sugar | Software done; demo values simulated | Takes about 5 minutes each morning; typing errors are caught by the entry checks |
| Daily check-in (keyboard and mouse) | sleep hours, mood, stress words, severe symptoms | Software done; demo values simulated | Self-report only, optional, private; not a psychological diagnosis |
| Laptop webcam | blinks, eye closure, fatigue | **Real (laptop webcam)** | Lighting, glasses and head pose in a spacecraft are not tested |
| Habitat environment data | CO2, radiation, temperature, humidity | Simulated | Read from the habitat's own systems |
| Exercise log | minutes of exercise | Simulated | Typed in or read from the exercise devices' logs |

## Signal count

**12 personal health signals** (7 typed measurements, 3 check-in values, 2 from the webcam), plus the cabin values (CO2, radiation, temperature, humidity). Camera minutes and exercise minutes are support fields. The full numbered list is in `docs/DATA_DICTIONARY.md`, generated from the code.
