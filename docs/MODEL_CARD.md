# Model card and evaluation

## The two layers

| | Rules (`engine/fusion.py`) | AI double-check (`engine/anomaly.py`) |
|---|---|---|
| What | Readable rules on deviations from the personal normal | Isolation Forest on all 13 signals together |
| Decides the state? | **Yes** | No: it agrees, flags alone, or stays quiet, and the report says which |
| Version | `rules-r4`, `thresholds-r3` | `iforest-r2` |

## Isolation Forest

* **Intended use:** notice unusual *combinations* of small changes for one astronaut. Not a diagnosis, not a prediction of illness.
* **Training data:** that astronaut's own NORMAL days only (days 1-14, then the last 30 NORMAL days, retrained every 7 days), with unavailable readings removed. They are resampled with small noise (0.5 SD) into 500 training points, because 14-30 days are too few for a forest.
* **Settings:** 200 trees, 256 samples per tree, seed 7. Threshold = the most unusual training day's score + 0.09; "strong" = threshold + 0.08. The margin was chosen after testing smaller margins, which gave many false AI flags on healthy days.
* **Missing data:** unavailable values are replaced by the personal mean (neutral), so a broken sensor cannot make a day look unusual.
* **Versioning:** every decision records the model version and which days the personal normal and the model were learned from (for example `B-day120`, days 90-119, 30 days), so an old report can be reproduced.
* **Change control (flight design, not built):** a new rule, threshold or model version is approved by the flight surgeon, logged, and can be rolled back to the previous version.

## Evaluation on new data (`tools/evaluate.py`)

**Separate generator**, seeds 1000-1019, 20 missions × 3 astronauts × 125 days. Personal normals are drawn at random from population ranges, noise is scaled 0.8-1.3×, and one event per astronaut is placed at a random day:
* gradual decline: 30-100% of Ben's size, 6-13 random signals, a 5-14-day ramp;
* single bad night;
* 3-day entry error (a value not entered);
* or nothing.

Nothing was tuned on these seeds. The comparison baseline uses fixed population limits with no personal normal (for example heart rate > 85, sleep < 5 h, systolic > 135).

| Measure | Result |
|---|---|
| Healthy astronaut-days | 5,207 |
| False WATCH per 100 healthy days | 0.69 |
| False ACT per 100 healthy days | **0** |
| Gradual declines found (WATCH or ACT) | **26 / 26**, median 3 days after onset, worst 8 days |
| Gradual declines reaching ACT | 22 / 26, median 6 days, worst 16 days |
| AI model flag on declines | 25 / 26, median 5 days, worst 13 days |
| Fixed population limits on declines | 20 / 26, median 9.5 days, worst 41 days |
| Fixed population limits, false flags per 100 healthy days | 0.04 |
| Single bad nights that went to ACT | **0 / 9** (also 0 the next day) |
| Entry-error days read as illness | **0 / 33** (33 / 33 reported as an entry check) |

Raw output: `docs/evaluation_results.json`.

**What this means:** the personal-normal approach finds slow declines that fixed limits miss or find late, at the cost of a few one-day WATCH notes (about one per astronaut every 5 months). False emergencies and entry errors read as illness did not happen.

**What it does not mean:** this is synthetic data from Gaussian noise. It verifies that the logic works on data it was not tuned on. It is **not** clinical validation. The detection numbers depend on how big we made the declines. Real validation needs labelled real or analogue-mission data (held-out people and time periods, no leakage between training and testing) and clinical review.
