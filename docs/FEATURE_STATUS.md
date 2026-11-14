# Feature status: what is real, what is simulated, what is planned

Four labels, used the same way in the README, the slides and the dashboard:

* **Implemented and tested (real input):** works on real input today.
* **Implemented, simulated input:** the software is complete and tested, but the input comes from the mission simulator, not a physical sensor.
* **Designed, not implemented:** described, not built.
* **Out of scope for the prototype:** not attempted; stated so nobody assumes it.

## Software features

| Feature | Status | Where | Evidence |
|---|---|---|---|
| Live webcam: blink rate, PERCLOS, long eye closures, daily summary | Implemented and tested (real input) | `camera/live_camera.py`, `camera/blink_tracker.py` | Tests 10, 11, 20, 30, 31; run `python camera/live_camera.py --band B` |
| Camera pauses with 2+ faces; low-confidence minutes never trigger ACT alone | Implemented and tested (real input) | `camera/blink_tracker.py`, `engine/live.py` | Tests 20, 31 |
| Camera never stores or sends images (only numbers leave) | Implemented and tested | `camera/` | Test 30 (privacy test) |
| Personal normal (days 1-14) + weekly re-learning from NORMAL days only | Implemented, simulated input | `engine/monitor.py` | Tests 6, 8 |
| Fixed-anchor slow-drift check | Implemented, simulated input | `engine/integrity.py` | Test 19 |
| Wristband swap check | Implemented, simulated input | `engine/integrity.py` | Test 18 |
| Sensor quality layer (missing, frozen, impossible values) | Implemented, simulated input | `engine/quality.py` | Tests 21, 22 |
| Data coverage / confidence beside every status | Implemented, simulated input | `engine/quality.py` | Test 24 |
| Readable rules: Normal / Watch / Act with reasons | Implemented, simulated input | `engine/fusion.py` | Tests 1-3, 16 |
| AI double-check (Isolation Forest, plain Python) | Implemented, simulated input | `engine/anomaly.py` | Tests 5, 7; `docs/MODEL_CARD.md` |
| Camera-gap fallback (fatigue from the wristband) | Implemented, simulated input | `engine/monitor.py` | Test 17 |
| Crew-wide vs individual events (cabin CO2) | Implemented, simulated input | `engine/monitor.py` (`crew_wide`) | Test 26 |
| Radiation: daily dose + mission total vs 600 mSv career limit | Implemented, simulated input | `engine/analysis.py` | Test 27 |
| Role-based views (surgeon / commander / astronaut) + audit log | Implemented, simulated input (no real login) | `engine/access.py` | Test 29 |
| Versions of rules, thresholds, model and personal normal on every decision | Implemented and tested | `engine/version.py` | Test 28 |
| Daily report in English and Arabic, PDF via the browser | Implemented and tested | `engine/report.py`, `engine/arabic.py` | Test 15 |
| Exercise adherence for bones and muscles | Implemented, simulated input | `engine/monitor.py` (`exercise`) | Test 32 |
| Runs offline, standard library only | Implemented and tested | `run_offline.py`, `tools/benchmark.py` | `docs/PERFORMANCE.md` |
| Independent evaluation on new labelled missions | Implemented (synthetic data) | `tools/evaluate.py` | `docs/MODEL_CARD.md` |
| Real login, encryption at rest, signed updates | Designed, not implemented | `docs/PRIVACY_SECURITY.md` | - |
| Per-sample timestamps, device buffering, duplicate handling | Designed, not implemented | `docs/DATA_DICTIONARY.md` | - |
| Clinical validation of thresholds and actions | Out of scope for the prototype | - | Needs flight surgeons and real data |

## Devices (hardware)

No physical sensor except the webcam is connected in this prototype. Each device below is a **device class** we would use, not a validated product choice.

| Device | Signals | Status | Main open question (must be answered before flight use) |
|---|---|---|---|
| Webcam / cabin camera | blinks, eye closure | **Real (laptop webcam)** | Lighting, glasses, head pose and camera placement in a spacecraft are not tested; this is a desktop proof of concept |
| Wristband (PPG + skin temperature + accelerometer) | heart rate, HRV, SpO2, wrist skin temperature, sleep, ID | Simulated | Which HRV metric (we assume RMSSD over the night); motion artefacts in SpO2 |
| Chest strap | breathing rate | Simulated | Fit and comfort for months |
| Cuffless blood pressure | systolic, diastolic | Simulated | Accuracy and drift are not proven for cuffless devices. If no validated device exists, blood pressure becomes a **periodic cuff reading** entered by the crew (the system already handles missing days) |
| Glucose patch (continuous glucose monitor, interstitial fluid) | daily average glucose | Simulated | Lag versus blood glucose, warm-up, patch changes; any low reading is confirmed by finger-prick |
| Voice / text daily check-in | mood, stress words | Simulated | Self-report only, optional, private; not a psychological diagnosis |
| Cabin sensors | CO2, radiation dose | Simulated | Real dosimeter quantity and calibration |
| Exercise log | minutes of exercise | Simulated | Would come from the exercise devices' own logs |

## Signal count

**13 personal health signals from 6 personal devices**, plus **2 cabin signals** (CO2, radiation). Camera minutes and exercise minutes are support fields, and the wristband fatigue estimate is a derived backup, not an extra signal. The full numbered list is in `docs/DATA_DICTIONARY.md`, generated from the code.
