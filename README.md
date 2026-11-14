# AEGIS: Smart Habitat Health Monitor

NASA Space Apps Challenge 2026: *Create Health Monitoring Software for Astronauts on Space Missions*

AEGIS helps an astronaut **assess his own health and act on it**, with no wearables and no
added hardware. Each morning the astronaut **types in** a few measurements taken with the
standard onboard medical kit (pulse, blood oxygen, temperature, breathing, blood pressure,
blood sugar) and a short **check-in** (sleep, mood, symptoms), using the keyboard and mouse.
The laptop **webcam** adds fatigue and blinking while he works.

AEGIS compares every value with that astronaut's **own normal**, gives one status
(**NORMAL / WATCH / ACT**), double-checks it with an **AI anomaly model**, and tells him
**what it means, what to do now, how to prevent it, and when to call the flight surgeon**,
on a clickable body figure and in a daily report in **English or Arabic**. It runs fully
offline, because a message from Mars can take up to 20 minutes to reach Earth.

## How the astronaut knows his health status
1. **One colour per day:** green NORMAL, amber WATCH, red ACT, on his card and on each body system.
2. **What changed:** the signals that moved away from *his* normal, each with a plain reason ("blood pressure 138, 15% above your normal of 120, for 3 days").
3. **How sure:** how many values today's status is based on, and which are missing.
4. **Guidance:** for each finding, a card with *what it means*, *do now*, *improve and prevent*, and *call the flight surgeon if*, linked to the NASA Human Research Program page it comes from. AEGIS never names a medicine or a dose: medicines only by the flight surgeon's instruction.
5. **When to escalate:** ACT tells him to contact the flight surgeon; a severe symptom or a confirmed safety-limit value means ACT at once.
6. **Body self-check:** he clicks the body part where he feels something, ticks the symptoms and their strength, and gets an answer at once.
7. **Today's tasks:** the routine plus the guidance steps, ticked off for points and a streak.
8. **Message to the flight surgeon:** short and prioritised, ready to copy into the next contact window.

## Inputs (no wearables or added hardware)
| Input | Values | How |
|---|---|---|
| Typed measurements (onboard medical kit) | resting heart rate, blood oxygen, body temperature, breathing rate, blood pressure, morning blood sugar | about 5 minutes each morning; every field shows how to measure it |
| Daily check-in (keyboard and mouse) | sleep hours, mood, optional log (stress words), severe symptoms | about 1 minute |
| Laptop webcam | blink rate, eye closure, fatigue | automatic while he works; only numbers leave the camera, never video |
| Habitat data | cabin CO2, radiation, temperature, humidity | from the habitat's own systems |

## One reading is not trusted blindly
* The **morning** reading (rested, before eating, same time every day) is compared with the personal normal, so like is compared with like.
* He can add **evening** readings or readings **when unwell**; any of them past a safety limit counts.
* A value past a safety limit must be **re-measured** after 5 minutes. Confirmed: ACT. Not confirmed: noted as a probable measuring error, no emergency. Until he re-measures, it stays ACT (safety first).

## The two alert paths
* **Immediate safety:** a typed value past a safety limit (blood oxygen below 92%, temperature 38.0 °C or more, blood pressure above 180/120, blood sugar below 54 or above 250, heart rate below 40 or above 130, breathing above 30), cabin CO2 above its ACT limit, or a severe symptom: **ACT the same day**.
* **Slow deterioration:** change against the personal normal. One bad day gives WATCH; ACT needs the change to last 2 or more days. This keeps false alarms low.
* **Entry checks first:** a skipped value, a value copied for 4 days, or a typo (3.67 °C instead of 36.7) is marked "unavailable" and the astronaut is asked to re-enter it. It never becomes a health alarm.
* **Profile mix-up check:** if two astronauts save their values in each other's profile, each profile suddenly matches the other person's normal. AEGIS sets that day aside and asks them to check, with no health alarm.

## Results
**Independent evaluation on 20 new simulated missions** (`tools/evaluate.py`, seeds 1000-1019, data the system never saw):

| Measure | AEGIS | Fixed limits for everyone |
|---|---|---|
| Gradual declines found | 26 of 26 (median 3 days) | 20 of 26 (median 9.5 days) |
| False ACT per 100 healthy days | 0 | n/a |
| False WATCH per 100 healthy days | 0.69 | n/a |
| Single bad nights that went to ACT | 0 of 9 | n/a |
| Entry errors read as illness | 0 of 33 | n/a |

This is synthetic data: it checks that the logic works as designed, not clinical validity.

**Demo mission (days 1-125, 3 astronauts):** Ben WATCH on day 120 and ACT from day 121; Chen one bad night (WATCH on 121, NORMAL on 122); cabin CO2 failure on days 123-125 flagged as a crew-wide problem; Amira and Chen's profile mix-up on day 50 caught with no alarm; Amira's spacewalk on days 60-61 shown as "camera not measured". Amira's cold-hand blood oxygen on day 100 is cleared by a re-measure; Chen's evening fever on day 110 is confirmed and gives ACT although his morning value was normal. Over the other healthy crew-days, 2 single-day WATCHes and no ACT. The AI agrees with the rules on 69 of 78 crew-days in days 100-125.

**48 automated tests** pass (`python tests/test_scenario.py`).

## NASA resources used
All five resources on the challenge's Resources tab (`engine/nasa_resources.py`, `engine/guidance.py`, `docs/NASA_RESOURCES.md`):
* **NASA HRP: 5 Hazards** and **Risks of Human Spaceflight:** every body system names its hazards, every finding links to its HRP risk, and every guidance card is written from the hazard pages (for example light and sleep timing for circadian alignment, journaling in isolation, exercise for bone loss).
* **NASA HRP: Ongoing Research:** shapes the design note on monitoring.
* **CSA radiation and CSA space science:** radiation tracked as a personal dose kept separate from the cabin reading, against NASA's 600 mSv career limit.
* **NASA-STD-3001 and OCHMO technical briefs:** the CO2, radiation and cabin limits.

## Run it
You need Python 3.10 or newer.
```bash
python run_offline.py                 # nothing to install
```
Open http://127.0.0.1:8000 and press **Play**. The **Manual test** page (http://127.0.0.1:8000/manual) lets you type one astronaut's values yourself, or upload a whole mission as CSV.

Optional real webcam (second terminal):
```bash
pip install opencv-python
python camera/live_camera.py --astronaut B
```
No webcam: `python camera/demo_camera.py --band B` plays a "getting tired" sequence.

Tests: `python tests/test_scenario.py`. Evaluation: `python tools/evaluate.py`.

## Branches
* **`v3`** (this branch): the astronaut enters his own data (keyboard, mouse, webcam); several readings a day with re-measure confirmation; guidance cards; body self-check; daily tasks with points; message to the flight surgeon; no wearables or hardware.
* **`main` / `v2`**: the submitted version, which used simulated wearables (wristband, glucose patch) and ESP32 code.
* **`v1-original`**: the first version, unchanged.

## Documentation
| Document | What it answers |
|---|---|
| `docs/JUDGING_CRITERIA.md` | How AEGIS meets impact, validity, creativity, relevance and influence |
| `docs/FEATURE_STATUS.md` | What is real, simulated, designed or out of scope |
| `docs/THRESHOLDS.md` | Every threshold, with its source or "project assumption" |
| `docs/RULES.md` | The rule catalogue and decision flow |
| `docs/DOSE_AND_ALERT_PATHS.md` | Personal dose vs cabin radiation, and the two alert paths |
| `docs/NASA_RESOURCES.md` | The challenge's NASA and CSA resources and how each one is used |
| `docs/DATA_DICTIONARY.md` | The numbered signal list (generated from the code) |
| `docs/SCENARIOS.md` | Scenarios, expected vs actual (generated from a run) |
| `docs/MODEL_CARD.md` | The AI model |
| `docs/PRIVACY_SECURITY.md` | Camera data flow, who sees what, retention |
| `docs/TEST_REPORT.md` | Every automated test and its result |

## Honest limits
* The demo data is simulated: day-by-day astronaut data is not public. The webcam input is real.
* The morning measurements take about 5 minutes of the astronaut's time.
* Some thresholds are project assumptions, not clinically validated (`docs/THRESHOLDS.md`).
* AEGIS supports the astronaut and the flight surgeon; it does not diagnose and never prescribes.

## License
MIT. See [LICENSE](LICENSE).
