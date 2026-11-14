# Status of the "AEGIS Modifications and Development Plan"

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

## Second round (same plan, remaining items)

| Item | Status | Where |
|---|---|---|
| Data ingestion layer: device ID, own timestamp, paired devices only, duplicates dropped, late samples kept on their day, impossible values dropped | Done and tested | `engine/ingest.py`, `POST /api/ingest`, `GET /api/devices`, `test_ingestion_layer` |
| Signal quality from raw samples: packet loss (longest gap), noise | Done | `engine/ingest.py` (`daily`) |
| Offline-first local storage that survives a restart, with de-duplication | Done: append-only `data/live/ingest_log.jsonl`, reloaded on start | `engine/ingest.py` |
| Audit log of views and crew actions, kept on disk | Done: `POST /api/ack` (crew acknowledges an alert), `data/live/audit_log.jsonl` | `engine/access.py`, `run_offline.py` |
| ESP32 wristband code (heart rate, SpO2, skin temperature, device ID, timestamp, offline buffer) | Written, **not yet tested on a board** | `hardware/esp32_wristband/esp32_wristband.ino` |
| A software stand-in for the device (link loss, duplicate, bad value) | Done | `tools/fake_device.py` |
| Cabin temperature and humidity | Done with a published limit: NASA-STD-3001 [V2 6012] envelope 18 °C/75% to 27 °C/25% (OCHMO-TB-002); a missing sensor shows "unavailable" | `engine/signals.py`, `engine/analysis.py` |

## Roadmap (needs hardware, data or experts)

| Item | Why not now |
|---|---|
| Test the ESP32 code on a real board | Needs the hardware (P1) |
| Cabin O2 partial pressure, total pressure, contaminants | Their limits (NASA-STD-3001 [V2 6003] Table 6.2-1, [V2 6006], [V2 6050]) are not yet sourced into the code; the plan says not to add an indicator without its limits |
| ECG input | Needs a suitable device |
| NASA OSDR real data, clinical review of thresholds and actions | Needs data access and flight-surgeon review (P3) |
| Real log-in, encryption, syncing to Earth | Designed in `docs/PRIVACY_SECURITY.md`, not built |
