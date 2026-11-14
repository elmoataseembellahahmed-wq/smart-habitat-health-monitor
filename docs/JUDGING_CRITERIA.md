# How NABD meets the judging criteria

Each criterion below lists the claim, then the evidence a judge can check in the code or on screen.

## 1. Impact: does it solve a real problem for the crew?
**Claim.** On a Mars mission the crew is up to 20 minutes from Earth one way, and NASA notes that astronauts "must be capable of confronting an array of situations with minimal support from teams on Earth" (HRP, Distance from Earth). NABD lets each astronaut see his own status every day, catches problems early, and tells him what to do before the flight surgeon can answer.

**Evidence.**
* Finds gradual declines early: 26 of 26 on 20 new simulated missions, median 3 days, against 20 of 26 and 9.5 days for fixed limits (`docs/evaluation_results.json`).
* Low alarm fatigue: 0 false ACT and 0.69 false WATCH per 100 healthy days.
* Guidance card for every finding: what it means, do now, improve and prevent, when to call (`engine/guidance.py`).
* Runs offline in a fraction of a second per astronaut per day, on an ordinary laptop.

## 2. Validity: is it correct, honest and testable?
**Claim.** Every decision can be traced and checked, and the system does not pretend to know what it cannot measure.

**Evidence.**
* Safety limits come from NASA-STD-3001 and the OCHMO technical briefs where they exist (CO2, radiation, cabin environment). Every other threshold is marked "project assumption" (`docs/THRESHOLDS.md`).
* Readable rules: every status lists the rules that fired and a plain reason per value. The AI is a second opinion only.
* Entry errors (skipped, copied, typo) are caught before analysis: 0 of 33 read as illness in the evaluation.
* Missing data is said plainly: "not measured", never a guessed value or a false green.
* Every decision carries the versions of the rules, thresholds, model and personal normal.
* 44 automated tests, plus an independent evaluation on missions the system never saw.
* Limits stated openly: simulated data, not clinically validated, no diagnosis, no medicines.

## 3. Creativity: what is new?
* **A personal normal for every astronaut**, re-learned weekly from healthy days only, with a fixed anchor from days 1-14 that catches a decline too slow to show on any single day.
* **Two alert paths:** immediate ACT for verified critical values or severe symptoms; a two-day rule for gradual change.
* **Profile mix-up check:** detects measurements saved in the wrong astronaut's profile from the values alone.
* **Crew-wide vs individual:** when several astronauts change together with high cabin CO2, NABD says "fix the air first", and still flags anyone whose change goes beyond what the air explains.
* **Bilingual by design:** the Arabic report is built from the same computed results, not translated text.
* **Clickable body figure** coloured by status, as the challenge suggests.

## 4. Relevance: does it answer this challenge?
| The challenge asks for | NABD |
|---|---|
| A visual tool that helps astronauts assess their own health | Dashboard with one status per day, colour coding, body figure, charts over time |
| Guidance on treatments and health improvements | Guidance card for every finding, linked to NASA HRP pages, no medicines or doses |
| Input by keyboard, mouse or camera images | Typed measurements and check-in (keyboard and mouse), laptop webcam for fatigue |
| Indicators such as blood pressure, heart rate, blood sugar, body temperature, sleep and mood | All six are inputs, plus blood oxygen and breathing rate |
| When a result needs the crew or the flight surgeon | WATCH vs ACT, the two alert paths, and "call the flight surgeon if" on every card |
| Prompts to take measurements as part of the routine | Morning measurements, weekly glucose-meter check and daily exercise reminders |
| Instructions: do not assume astronauts know how to measure | Every input says how to measure it |
| NASA HRP and partner agency resources | All five resources from the Resources tab are used (`docs/NASA_RESOURCES.md`) |
| Gamification, dynamic charts, colour coding | Normal-day streak, charts against the personal normal, green/amber/red |

## 5. Influence: can it be used and grow beyond the hackathon?
* **Beyond Mars:** the same tool fits a space station, a rover or a lunar base. It also fits isolated places on Earth (Antarctic stations, ships, remote clinics), where the nearest doctor is also far away.
* **Open and easy to run:** MIT licence, Python standard library only, one command to start.
* **Built to be checked by experts:** thresholds are simple settings that flight surgeons can calibrate with real data, and every decision is versioned.
* **Arabic and English:** reaches more crews, analogue missions and students.
* **Next steps:** an analogue mission test (for example in a HERA-like habitat), review of thresholds and guidance by flight surgeons, and real crew data.
