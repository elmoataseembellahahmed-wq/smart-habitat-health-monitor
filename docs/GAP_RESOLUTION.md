# Gap analysis: what was done about each issue

Response to "Smart Habitat Health Monitor: Complete Idea, Science, Software & Prototype Gap Analysis" (14 Nov 2026), section 3.

**Result: 22 of 35 solved, 12 partly solved, 1 open** (it needs physical hardware). "Solved" means fixed in the code with a test, or, where the report itself recommended it, clearly scoped and documented. "Partly" says what is still missing.

| # | Issue | Severity | Status | What we did | Evidence |
|---|---|---|---|---|---|
| 3.1 | Evidence level of features not separated | Critical | **Solved** | Feature-status matrix with 4 labels; every report says the data is simulated; sensors panel shows live vs simulated | `docs/FEATURE_STATUS.md` |
| 3.2 | No independent validation | Critical | Partly | New evaluation on 20 missions from a separate generator and unseen seeds, with labels, false-alarm rate, detection delay and a fixed-limit baseline. Still synthetic, not clinical | `tools/evaluate.py`, `docs/MODEL_CARD.md` |
| 3.3 | Thresholds without provenance | Critical | **Solved** | Registry: every number marked published / clinical cut-off / project assumption / simulation, with NASA-STD-3001 references; threshold version on every report; "prototype thresholds, not for medical decisions" | `docs/THRESHOLDS.md`, `engine/version.py` |
| 3.4 | Cuffless BP unproven | High | Partly | Stated as unproven; fallback to periodic cuff readings defined (missing days already handled); cuff check reminder. No device chosen | `docs/FEATURE_STATUS.md` |
| 3.5 | Glucose patch unspecified | High | Partly | Device class (CGM, interstitial), lag, patch change and finger-prick confirmation defined; frozen or expired patch detected in code | `engine/quality.py`, test 21 |
| 3.6 | Wrist temp is not core temp | High | **Solved** | Renamed "wrist skin temperature (estimate)"; above 38 °C is a warning to confirm with a thermometer, never an emergency alone | `engine/analysis.py`, test 25 |
| 3.7 | Bone and muscle not measured | High | Partly | Exercise-adherence module (bones turn Watch when exercise drops); UI says "Not measured: adherence only". No strength tests | test 32 |
| 3.8 | Immune health not specified | High | **Solved** (scoped) | Explicitly stated as not monitored in the UI and docs: only a fever warning | `engine/signals.py` (`measured`) |
| 3.9 | Radiation too simple | High | **Solved** | Quantity named (effective dose, mSv); mission total vs NASA's 600 mSv career limit; 250 mSv solar-event limit documented; dosimeter marked simulated | test 27 |
| 3.10 | Mood signals over-interpreted | High | **Solved** | Diary = optional self-report, skippable, never a diagnosis; private to the astronaut and the surgeon (enforced) | tests 23, 29 |
| 3.11 | Isolation and crew relations | Medium-High | Partly | Privacy of self-report enforced; private connection check-in with crew-level average designed, not built | `docs/PRIVACY_SECURITY.md` |
| 3.12 | Camera fatigue not validated | High | Partly | Labelled desktop proof of concept; per-minute confidence; low confidence can never ACT; camera ACT now "check in with the astronaut first". No tests across lighting or eyewear yet | test 31 |
| 3.13 | Camera privacy needs proof | Medium-High | **Solved** | Frame data flow documented; automated test that no image or video is written or sent | test 30 |
| 3.14 | Wristband-camera identity | Medium-High | Partly | 2+ faces: camera pauses; swapped bands found from personal normals with no false alarms. Proximity handshake designed, not built | tests 18, 20 |
| 3.15 | Baseline absorbs slow decline | High | **Solved** | Learns only from NORMAL days; fixed day 1-14 anchor; versioned baseline history; slow-drift test caught on day 71 | test 19 |
| 3.16 | Rules under-specified | High | **Solved** | Full rule catalogue: hard safety rules separate from the score, missing-data behaviour, escalation/de-escalation; tests on every rule path | `docs/RULES.md` |
| 3.17 | Three colours hide uncertainty | Medium | **Solved** | "Status based on N of 13 signals" + full / limited / low confidence on every card and report; a missing safety signal is called out | test 24 |
| 3.18 | Recommendations exceed authority | Critical | Partly | Observation separated from action; every action typed (confirm / equipment / self-care / escalate); "prototype list"; no drugs or doses. Mission-approved protocols need flight-surgeon review | `docs/RULES.md`, test 33 |
| 3.19 | No sensor quality layer | Critical | **Solved** | Missing, frozen and impossible readings become "unavailable", are never scored or learned, and produce a separate sensor check | tests 21, 22 |
| 3.20 | Time handling not described | Medium-High | Partly | Time model documented (mission day, daily values); per-sample timestamps and buffering designed, not built | `docs/DATA_DICTIONARY.md` |
| 3.21 | Offline not demonstrated | High | **Solved** | Benchmark runs the whole mission with every network call blocked; standard library only; deterministic rebuild after restart | `docs/PERFORMANCE.md` |
| 3.22 | Security and access | High | Partly | Roles (surgeon / commander / astronaut) enforced on every request, private data hidden, audit log. No real login or encryption | test 29, `docs/PRIVACY_SECURITY.md` |
| 3.23 | Dashboard too broad | Medium | **Solved** | "View as" roles; astronaut's first box: What changed, How sure, Do next, When to escalate | `frontend/` |
| 3.24 | No human-factors testing | Medium | Partly | Colour always with text labels, keyboard-usable body figure, Arabic right-to-left reports. No user testing yet | - |
| 3.25 | Environmental causal logic | Medium-High | **Solved** | Crew-wide layer: shared change + cabin fault = environmental; shared change without cabin cause = individual; extra signals stay individual | test 26 |
| 3.26 | Narrow scenarios | Medium | **Solved** | Scenario matrix (13 cases, expected vs actual, generated from a run); uncovered cases listed | `docs/SCENARIOS.md` |
| 3.27 | Simulation provenance unclear | High | **Solved** | Generator, seeds, event sizes and labels published; separate evaluation generator | `docs/SIMULATION.md`, `data/events.csv` |
| 3.28 | Performance not measured | Medium | **Solved** | Startup, per-day time, memory, data size measured | `docs/PERFORMANCE.md` |
| 3.29 | No hardware integration | High | Open | Device-class table with open questions; only the webcam is real. Needs hardware (ESP32 wearable next) | `docs/FEATURE_STATUS.md` |
| 3.30 | Signal count ambiguous | Medium | **Solved** | 13 health signals, 6 personal devices, 2 cabin signals; numbered list generated from the code | `docs/DATA_DICTIONARY.md` |
| 3.31 | Tests not documented | Medium | **Solved** | Test report with every test, its purpose and its result (33 passing), generated from a real run | `docs/TEST_REPORT.md` |
| 3.32 | Report lacks provenance | Low-Medium | **Solved** | Reports carry mission day, coverage, missing channels, versions and personal-normal days, plus a disclaimer; Arabic right-to-left | test 28 |
| 3.33 | Data governance | High | **Solved** (policy) | Data inventory, retention, deletion and access table; camera frames and diary text never stored | `docs/PRIVACY_SECURITY.md` |
| 3.34 | Model change control | Medium-High | Partly | Versions of rules, thresholds, model and personal normal on every decision (reproducible). Approval and rollback designed, not built | `engine/version.py`, `docs/MODEL_CARD.md` |
| 3.35 | Title implies more | Low-Medium | **Solved** | Scope stated: habitat monitoring covers CO2 and radiation only | `README.md` |

Regenerate the generated documents with `python tools/make_docs.py`, the evaluation with `python tools/evaluate.py`, and the benchmark with `python tools/benchmark.py`.
