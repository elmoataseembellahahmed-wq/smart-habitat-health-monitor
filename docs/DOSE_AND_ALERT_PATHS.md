# Personal dose source and the two alert paths

This note covers the fixes for problems 1 and 4 of the review document.

## Problem 1: where the personal radiation dose comes from

The personal dose and the cabin radiation are two separate records. They are never mixed.

| Field | Personal dose (`decision.dosimetry.record`) | Cabin radiation (`decision.cabin_radiation`) |
|---|---|---|
| Data type | `personal_cumulative_dose` | `cabin_environment` |
| Source | Personal dosimeter worn by the astronaut | Cabin radiation monitor (habitat, not worn) |
| Device ID | `DOS-<astronaut id>` | `CABIN-RAD-1` |
| Astronaut ID | yes | none (it describes the habitat) |
| Unit | mSv (last 24 h and mission total) | mSv/day |
| Time | mission day, end of day (UTC); period covered | mission day (daily value) |
| Data status | `simulated` / `manually entered` / `real device` | same |

- **Demo mission:** the dose values are **simulated**. Amira's dose rises on her EVA days (60–61) while the cabin value does not, which shows why the two must be kept apart.
- **Manual form or CSV upload:** the values are labelled **manually entered**.
- **Real dosimeter:** none is connected yet, so no value is presented as a real measurement.

## Problem 4: two independent alert paths

Each decision now carries `alert_path`, `alert_path_note` and `immediate_alerts`.

1. **`immediate_safety`:** a verified critical event gives ACT at once, with no 2-day wait. It covers:
   - an absolute safety limit, for example SpO2 below 92 %;
   - the cabin CO2 ACT limit;
   - a severe reported symptom.

   Each alert records the mission day, the astronaut, the trigger signal, its value and unit, the limit used, the data source, the data status, and why the reading is trusted.
2. **`slow_deterioration`:** change against the personal normal. A single day gives WATCH, and ACT needs the change to last 2 or more days.
3. **`environment_watch`:** a cabin reading is out of range but below its ACT limit. This is a problem with the habitat, not with the person.

**Quality gate:** readings that fail the sensor check (missing, out of range, stuck, unpaired device) are set aside before analysis and reported as sensor faults. They can never fire the immediate path. An impossible value such as SpO2 = 40 % is reported as a sensor fault, not as an emergency (see `tests/test_scenario.py::test_two_alert_paths`).

**Limits of this prototype:**
- The alerts give operational steps, not a diagnosis.
- The critical limits are documented in `docs/THRESHOLDS.md`. The CO2 and radiation limits come from NASA-STD-3001. The other limits are project assumptions and still need review by clinical experts.

## Wording for the presentation

> NABD keeps cabin radiation apart from each astronaut's personal cumulative dose. Each personal-dose record is linked to its source, its astronaut and device ID, its unit and its time. Simulated or manually entered values are clearly labelled.
>
> NABD has two independent alert paths: one based on trends, for gradual deterioration, and one for immediate safety, for verified critical limit breaches. The 2-day rule applies only to gradual deterioration. Sensor quality is checked before any alert is classified.
