# How NABD meets the judging criteria

Each criterion is built into the software, not only described. For each one: the feature, where it is, and the test that proves it works.

| Criterion | Feature in the software | Where | Proof |
|---|---|---|---|
| Impact | Guidance card for every finding; daily health tasks with points; short message to the flight surgeon | `engine/guidance.py`, `engine/tasks.py`, `engine/earth.py`, dashboard | tests `guidance_on_treatment_and_improvement`, `daily_tasks_and_points`, `message_to_the_flight_surgeon` |
| Validity | Several readings a day; a value past a safety limit is re-measured before it counts; entry checks; profile mix-up check | `engine/readings.py`, `engine/quality.py`, `engine/integrity.py` | tests `remeasure_confirms_or_clears_a_safety_value`, `entry_errors_are_never_read_as_illness` |
| Creativity | Body self-check: click where it hurts, get an answer at once; personal normal with a fixed anchor; crew-wide vs individual | `engine/selfcheck.py`, body figure | test `body_self_check` |
| Relevance | Keyboard, mouse and camera input; the six indicators named in the challenge; how-to-measure for every input; NASA HRP resources in every card | `engine/signals.py`, manual page | test `every_measurement_has_instructions` |
| Influence | Message ready for a 20-minute communication delay; Arabic and English; open, offline, one command to run | `engine/earth.py`, `engine/arabic.py` | test `message_to_the_flight_surgeon` |

## 1. Impact: what effect does the project make?
**The effect.** NABD changes what an astronaut can do alone, far from Earth: he knows his status every day, he finds a problem days earlier, and he knows what to do about it before the flight surgeon can answer. On a Mars mission the crew is up to 20 minutes from Earth one way, and NASA notes that astronauts "must be capable of confronting an array of situations with minimal support from teams on Earth" (HRP, Distance from Earth).

**Evidence.**
* Finds gradual declines early: 26 of 26 on 20 new simulated missions, median 3 days, against 20 of 26 and 9.5 days for fixed limits (`docs/evaluation_results.json`).
* Low alarm fatigue: 0 false ACT and 0.69 false WATCH per 100 healthy days.
* Guidance card for every finding: what it means, do now, improve and prevent, when to call (`engine/guidance.py`).
* Today's health tasks, built from the routine and the guidance, with points and an all-done streak, so the advice turns into action (`engine/tasks.py`).
* A short, prioritised message to the flight surgeon, ready for the next contact window: status, findings with values, what was done on board, what is needed (`engine/earth.py`).
* Runs offline in a fraction of a second per astronaut per day, on an ordinary laptop.

## 2. Validity: is it correct, honest and testable?
**Claim.** Every decision can be traced and checked, and the system does not pretend to know what it cannot measure.

**Evidence.**
* Safety limits come from NASA-STD-3001 and the OCHMO technical briefs where they exist (CO2, radiation, cabin environment). Every other threshold is marked "project assumption" (`docs/THRESHOLDS.md`).
* Readable rules: every status lists the rules that fired and a plain reason per value. The AI is a second opinion only.
* Entry errors (skipped, copied, typo) are caught before analysis: 0 of 33 read as illness in the evaluation.
* **One reading is not trusted blindly.** The morning reading (same conditions every day) is compared with the personal normal; the astronaut can add evening readings or readings when unwell, and any of them past a safety limit counts. A value past a safety limit must be **re-measured**: confirmed, it stays ACT; not confirmed, it is noted as a probable measuring error with no emergency. Demo: Amira's 90.6% blood oxygen (cold hand) is cleared by a re-measure of 97.9%; Chen's evening fever of 38.4 °C is confirmed by 38.3 °C and gives ACT although his morning value was normal (`engine/readings.py`).
* Missing data is said plainly: "not measured", never a guessed value or a false green.
* Every decision carries the versions of the rules, thresholds, model and personal normal.
* 44 automated tests, plus an independent evaluation on missions the system never saw.
* Limits stated openly: simulated data, not clinically validated, no diagnosis, no medicines.

## 3. Creativity: what makes NABD different from other projects?
A typical health dashboard shows numbers against one fixed range for everybody, and stops there. NABD is different in six ways:

| A typical health dashboard | NABD |
|---|---|
| One fixed range for everyone | **A personal normal for every astronaut**, re-learned weekly from healthy days only, with a fixed anchor from days 1-14 that catches a decline too slow to show on any single day |
| One reading is the truth | **A value past a safety limit is re-measured before it counts**; an evening or "feeling unwell" reading counts too |
| A typo or a skipped entry becomes an alarm | **Entry checks and a profile mix-up check** catch them; they never become a health alarm |
| Every person is treated alone | **Crew-wide vs individual:** when several astronauts change together with high cabin CO2, it says "fix the air first", and still flags anyone whose change goes beyond the air |
| Shows numbers; the user must know what to do | **Guidance for every finding**, a **click-where-it-hurts body self-check**, and **today's tasks** with points |
| Assumes a doctor is a call away | **Built for a 20-minute delay:** two alert paths (act now / watch for two days) and a short message ready for the next contact window |

It is also **bilingual by design**: the Arabic report is built from the same computed results, not translated text.

## 4. Relevance: does it answer this challenge?
| The challenge asks for | NABD |
|---|---|
| A visual tool that helps astronauts assess their own health | Dashboard with one status per day, colour coding, body figure with a click-where-it-hurts self-check, charts over time |
| Guidance on treatments and health improvements | Guidance card for every finding, linked to NASA HRP pages, no medicines or doses |
| Input by keyboard, mouse or camera images | Typed measurements and check-in (keyboard and mouse), laptop webcam for fatigue |
| Indicators such as blood pressure, heart rate, blood sugar, body temperature, sleep and mood | All six are inputs, plus blood oxygen and breathing rate |
| When a result needs the crew or the flight surgeon | WATCH vs ACT, the two alert paths, and "call the flight surgeon if" on every card |
| Prompts to take measurements as part of the routine | Morning measurements, weekly glucose-meter check and daily exercise reminders |
| Instructions: do not assume astronauts know how to measure | Every input says how to measure it |
| NASA HRP and partner agency resources | All five resources from the Resources tab are used (`docs/NASA_RESOURCES.md`) |
| Gamification, dynamic charts, colour coding | Daily health tasks with points and an all-done streak, normal-day streak, charts against the personal normal, green/amber/red |
| A human figure where each part is clickable | Each body system shows its function, the space effect, today's values, and a symptom self-check |

## 5. Influence: how far does its effect reach?
* **Built for the communication delay:** the message to the flight surgeon is short and prioritised, so one contact window is enough; the crew sends it, NABD sends nothing by itself.
* **Beyond Mars:** the same tool fits a space station, a rover or a lunar base. It also fits isolated places on Earth (Antarctic stations, ships, remote clinics), where the nearest doctor is also far away.
* **Open and easy to run:** MIT licence, Python standard library only, one command to start.
* **Built to be checked by experts:** thresholds are simple settings that flight surgeons can calibrate with real data, and every decision is versioned.
* **Arabic and English:** reaches more crews, analogue missions and students.
* **Next steps:** an analogue mission test (for example in a HERA-like habitat), review of thresholds and guidance by flight surgeons, and real crew data.
