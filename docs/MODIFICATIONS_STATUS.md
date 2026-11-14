# Status of the "NABD Modifications and Development Plan"

What the plan asked for, and what is in the code now (branch `v2`). "Done" means implemented and tested; "Roadmap" means it needs hardware, real data or clinical review.

## P0 – before judging

| Item | Status | Where |
|---|---|---|
| Separate real from simulated everywhere | Done | `docs/FEATURE_STATUS.md`, reports, slide 7 |
| Sensor quality (missing, frozen, impossible) as a device check, not illness | Done | `engine/quality.py`, tests 21–22 |
| Immediate alert path that does not wait for two days | Done: a safety limit is ACT at once; a reported severe symptom (chest pain, shortness of breath, confusion, fainting, severe headache, vision changes) is ACT at once | `engine/fusion.py`, `engine/monitor.py`, `test_severe_symptom_is_immediate_act` |
| Fever is not an immune measurement | Done: domain renamed "Immune-related warning indicators"; with no test results it shows **unavailable**, never normal | `engine/signals.py`, `engine/monitor.py` |
| Not enough data never reads as NORMAL | Done: "Not enough data to confirm this status" on card and report when confidence is low | `engine/monitor.py` |

## P2 – health gaps that software can close now

| Item | Status | Where |
|---|---|---|
| Bone health: imported periodic results with date, source, change | Done (demo results are simulated and labelled so) | `engine/clinical.py` |
| Muscle health: strength / lean mass results | Done (same store) | `engine/clinical.py` |
| Immune indicators: blood-test results with the lab's own reference range | Done (no demo results on purpose: shows unavailable) | `engine/clinical.py` |
| Data status per domain: measured / imported / self-reported / indirect / unavailable | Done | dashboard body panel |
| Personal dosimetry per astronaut, separate from the cabin monitor | Done (simulated; extra dose on Amira's spacewalk days 60–61) | `engine/clinical.py`, reports |
| Severe symptoms entry | Done: manual page check boxes, CSV `symptoms` column | `frontend/manual.html`, `engine/manual.py` |
| Each finding linked to its NASA HRP risk | Done | `engine/nasa_resources.py` |

## Roadmap (needs hardware, data or experts)

| Item | Why not now |
|---|---|
| ESP32 wristband with real sensors, timestamps, device ID | Needs hardware (P1) |
| Cabin temperature, humidity, O2 partial pressure, contaminants | The plan says: add an indicator only after choosing a reliable sensor and its limits |
| ECG input | Needs a suitable device |
| NASA OSDR real data, clinical review of thresholds and actions | Needs data access and flight-surgeon review (P3) |
| Offline sync with de-duplication, real log-in, encryption | Designed in `docs/PRIVACY_SECURITY.md`, not built |
