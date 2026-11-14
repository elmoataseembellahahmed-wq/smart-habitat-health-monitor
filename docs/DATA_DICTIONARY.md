# Data dictionary

Generated from the code by `tools/make_docs.py` (software 1.4.0). **13 health signals** from **6 personal devices**, plus **2 cabin signals**, plus 2 support fields (camera minutes, exercise minutes) and 1 derived backup (wristband fatigue).

| # | Field | Name | Unit | Device | Raw / derived | Required / optional | Unhealthy direction | Plausible range (else sensor error) | Safety limit | Input status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `heart_rate` | Resting heart rate | bpm | Wristband | raw (daily value) | required | high | 25-220 | - | Simulated |
| 2 | `hrv` | Heart rate variability | ms | Wristband | raw (daily value) | required | low | 3-250 | - | Simulated |
| 3 | `spo2` | Blood oxygen | % | Wristband | raw (daily value) | required | low | 60-100 | < 92 | Simulated |
| 4 | `body_temp` | Wrist skin temperature (body temperature estimate) | °C | Wristband | raw (daily value) | required | high | 34-42 | > 38 (estimate: confirm first) | Simulated |
| 5 | `sleep_hours` | Sleep duration | h | Wristband | raw (daily value) | required | low | 0-16 | - | Simulated |
| 6 | `breathing_rate` | Breathing rate | /min | Chest strap | raw (daily value) | required | high | 4-60 | - | Simulated |
| 7 | `bp_systolic` | Blood pressure, systolic | mmHg | Cuffless blood pressure sensor | raw (daily value) | required | high | 60-260 | > 180 | Simulated |
| 8 | `bp_diastolic` | Blood pressure, diastolic | mmHg | Cuffless blood pressure sensor | raw (daily value) | required | high | 30-160 | > 120 | Simulated |
| 9 | `glucose` | Blood sugar (daily average) | mg/dL | Glucose patch | raw (daily value) | required | both | 20-600 | < 54, > 250 | Simulated |
| 10 | `fatigue_score` | Fatigue score (cameras) | /100 | Cabin cameras (work areas) | raw (daily value) | required | high | 0-100 | - | Real (webcam) in live mode; simulated daily values in the mission |
| 11 | `blink_rate` | Blink rate (cameras) | /min | Cabin cameras (work areas) | raw (daily value) | required | high | 0-80 | - | Real (webcam) in live mode; simulated daily values in the mission |
| - | `wrist_fatigue` | Fatigue estimate (wristband) | /100 | Wristband | derived backup | backup only | high |  | - | Simulated |
| 12 | `mood_score` | Mood score (self-report) | /100 | Voice and daily log (optional) | raw (daily value) | optional self-report | low | 0-100 | - | Simulated |
| 13 | `stress_words` | Stress words in daily log | /day | Voice and daily log (optional) | raw (daily value) | optional self-report | high | 0-200 | - | Simulated |

## Cabin signals

| Field | Name | Unit | Watch | Act | Input status |
|---|---|---|---|---|---|
| `co2` | Cabin CO2 | mmHg | 3.0 | 4.0 | Simulated |
| `radiation` | Radiation dose (cabin dosimeter, effective dose) | mSv/day | 1.0 | 2.0 | Simulated |
| `temperature` | Cabin temperature | °C | 27.0 | 30.0 | Simulated |
| `humidity` | Cabin relative humidity | % | 75.0 | 85.0 | Simulated |

## Support fields

| Field | Meaning | Use |
|---|---|---|
| `camera_minutes` | Minutes the cabin cameras saw this face today | < 30 min: camera values not trusted, fatigue estimated from the wristband |
| `exercise_minutes` | Minutes of exercise in the exercise log | Exercise adherence (bones and muscles). Not a bone measurement |
| `wrist_fatigue` | Fatigue estimate from sleep, HRV and heart rate | Backup when the camera saw too little |

## Time model

* The time base is the **mission day** (mission elapsed time, day 1 = launch). Every decision and report carries the mission day and the versions used.
* The prototype works on **one daily value per signal** (for example the day's resting heart rate, last night's sleep, the day's average glucose). The live camera works per frame and per minute.
* Designed for the flight version, not implemented: one on-board clock for all devices, a timestamp on every sample, buffering on each device when the link drops, duplicates removed by (device, timestamp), and late data re-processed for its own day.
* A reading that does not arrive is **missing** (shown as unavailable), never filled in with a guess.
