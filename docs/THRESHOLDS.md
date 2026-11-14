# Threshold registry

**Every number below is a prototype threshold, not for medical decisions.** Each row says where the number comes from:

* **Published reference:** taken from a named public source (exact wording and version given).
* **Common clinical cut-off:** a widely used medical cut-off on Earth. It still needs flight-surgeon approval for spaceflight and for the device used.
* **Project assumption:** our own starting value, tuned on simulated data to avoid false alarms. It must be calibrated with real data and flight surgeons.
* **Simulation value:** used only to generate the demo data.

Version: `thresholds-r3` (see `engine/version.py`). Each daily report prints the threshold version it used. Approval needed for flight use: flight surgeon (health limits) and environmental systems lead (cabin limits).

## Personal-normal rules (all signals)

| Rule | Value | Type | Rationale |
|---|---|---|---|
| Mild deviation | 2.5 SD from the astronaut's own normal, unhealthy direction | Project assumption | With 13 signals checked daily, 2 SD would raise a false flag on most days from noise alone |
| Strong deviation | 3.5 SD | Project assumption | Rare from noise |
| Smallest spread allowed | 3% of the mean (min 0.5), SpO2 0.3, temperature 0.15 °C | Project assumption | Stops a very steady baseline making tiny changes look huge |
| Baseline window | days 1-14 | Project assumption | Two weeks covers work and rest days; needs real-data justification |
| Re-learning | every 7 days, last 30 NORMAL days, at least 7 usable days | Project assumption | Follows adaptation to space without learning bad days |
| Slow-drift anchor | current normal 1.5 anchor SD from days 1-14 | Project assumption | Never fires on the demo data; catches a slow test decline by day 71 |
| Wristband swap | swapped fit at most 0.5 of the "as labelled" fit, and at least 12 better (sum of squared z) | Project assumption | Zero false swaps on all demo days |
| Frozen sensor | 4 identical daily values in a row | Project assumption | Zero false "stuck" readings on the demo data |
| Camera trusted | 30+ minutes of face time in a day | Project assumption | Too little face time gives unreliable daily eye measures |

## Decision scores

| Rule | Value | Type |
|---|---|---|
| Points | mild 1, strong 2, safety limit 5, +1 if 3+ days in a row | Project assumption |
| WATCH | score 3+, or a known risk pattern | Project assumption |
| ACT | safety limit broken; or score 8+ with a signal off 2+ days; or combined stress 3+ days; or cabin CO2 at the ACT limit | Project assumption |

On 20 new evaluation missions these gave 0.56 false WATCH and 0 false ACT per 100 healthy astronaut-days (`docs/MODEL_CARD.md`). That supports them as starting values only.

## Absolute safety limits

| Signal | Limit | Type | Source / note |
|---|---|---|---|
| Blood oxygen (SpO2) | below 92% | Common clinical cut-off | Widely used pulse-oximetry concern level on Earth. Wrist PPG is affected by motion, so the first action is to re-measure and check sensor fit |
| Wrist skin temperature (estimate) | above 38.0 °C | Common clinical cut-off (fever) | The wrist value is an **estimate, not core temperature**: crossing it gives a *strong* warning to confirm with an oral or ear thermometer, never an emergency by itself |
| Blood pressure | above 180 systolic or 120 diastolic | Common clinical cut-off | Hypertensive-crisis level used by the American Heart Association; must be confirmed with a cuff |
| Blood glucose | below 54 mg/dL | Common clinical cut-off | American Diabetes Association "level 2" (clinically important) hypoglycaemia; confirm by finger-prick (the patch reads interstitial fluid, which lags blood) |
| Blood glucose | above 250 mg/dL | Project assumption | Placeholder high limit; confirm by finger-prick |

## Cabin limits

| Signal | Value | Type | Source / note |
|---|---|---|---|
| CO2, WATCH | 3.0 mmHg | Published reference | NASA-STD-3001 Vol. 2 Rev D [V2 6004]: the average **one-hour** CO2 partial pressure in the habitable volume no more than 3 mmHg (OCHMO-TB-004). Our prototype checks a daily value, which is less strict than a 1-hour average |
| CO2, ACT | 4.0 mmHg | Project assumption | Above the standard, where crew symptoms are more likely |
| CO2, 7-day average reference | 2.5 mmHg | Published reference | OCHMO-TB-004: keeping the 7-day average below 2.5 mmHg keeps headache risk below about 1%. Shown as context, not an alarm |
| Cabin temperature, WATCH | below 18 °C or above 27 °C | Published reference | NASA-STD-3001 Vol. 2 [V2 6012] crew health environmental limits, operating envelope 18 °C/75% humidity to 27 °C/25% humidity (OCHMO-TB-002). ACT at 15 / 30 °C is a project assumption. Informational: it does not change a health status |
| Cabin humidity, WATCH | below 25% or above 75% | Published reference | Same envelope. ACT at 15 / 85% is a project assumption |
| Radiation, WATCH / ACT | 1.0 / 2.0 mSv per day | Project assumption | A day far above the normal ~0.5 mSv/day suggests a solar particle event: go to the shelter and follow mission procedures |
| Radiation, mission total | shown against 600 mSv | Published reference | NASA-STD-3001 Vol. 1: career effective dose below 600 mSv; one solar particle event below 250 mSv (OCHMO-TB-020). Our dosimeter values are simulated |

## Simulation values (demo data only)

Personal normals (for example Amira's heart rate 58, Ben's 64), noise levels and event sizes are in `engine/simulate.py` and `docs/SIMULATION.md`. They are not medical reference ranges.

## Sources

* NASA OCHMO Technical Brief OCHMO-TB-004, Carbon Dioxide (NASA-STD-3001 Vol. 2 Rev D [V2 6004]): https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-004-carbon-dioxide.pdf
* NASA OCHMO Technical Brief OCHMO-TB-002, ECLSS (NASA-STD-3001 Vol. 2 Rev D [V2 6012]): https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-002-eclss.pdf
* NASA OCHMO Technical Brief OCHMO-TB-020, Design for Ionizing Radiation Protection (NASA-STD-3001 Vol. 1 Rev C): https://www.nasa.gov/sites/default/files/atoms/files/radiation_protection_technical_brief_ochmo.pdf
* American Heart Association, blood pressure categories (hypertensive crisis above 180/120).
* American Diabetes Association, Standards of Care: level 2 hypoglycaemia below 54 mg/dL.
