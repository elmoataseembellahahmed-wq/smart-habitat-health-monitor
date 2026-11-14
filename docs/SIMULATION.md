# How the simulated data is made

Real day-by-day in-flight astronaut data is not public, so the demo uses a simulator. This page lets anyone reproduce it and see exactly what was designed in.

## Reproduce

```
python -c "from engine import simulate; d = simulate.generate(seed=42)"
```

The same seed always gives the same mission. `data/simulated_mission_data.csv` is the result plus the system's decisions, and `data/events.csv` lists every injected event with its days (the labels).

## Demo generator (`engine/simulate.py`, seed 42)

* 3 astronauts, mission days 1-125. Each has a fixed **personal normal** (for example resting heart rate 58 / 64 / 61 bpm) and natural day-to-day noise (a normal distribution; for example heart rate SD 2 bpm, HRV 3 ms, SpO2 0.4%).
* Separate random streams for each part (story, newer devices, early days, camera minutes, exercise), so adding a part never changes the others. Days 100-125 (the story) are identical to the first version.
* Values are clamped to physical ranges and rounded the way a daily summary would be.

## Injected events (the labels)

| Days | Who | Event | What changes |
|---|---|---|---|
| 119-125 | Ben | Gradual stress and fatigue build-up | Linear ramp to full size by day 124: sleep -2.4 h, HRV -22 ms, HR +12, BP +18/+10, glucose +22, breathing +4, mood -30, stress words +9, fatigue +30, blinks +8 |
| 121 | Chen | One bad night | sleep -3 h, fatigue +18, HRV -8, HR +5, BP +6 |
| 123-125 | All | CO2 scrubber degrading | CO2 +0.7 mmHg per day; everyone breathes a little faster |
| 60-61, 122 | Amira, Ben | Camera gap | face in view 0-15 min |
| 50 | Amira + Chen | Profile mix-up | the 7 typed measurements exchanged |
| 40-41 | Amira | Oxygen sensor disconnected | SpO2 missing |
| 30-35 | Chen | Expired glucose patch | glucose frozen at one value |
| 35 | Ben | Band off the skin | wrist temperature 31.2 °C |
| 55, 56-57 | Amira, Chen | Diary skipped | mood and stress words missing |
| 90-96 | Ben | Low exercise | 0-30 min instead of about 90 |

All non-story events are before day 69, so they cannot change the weekly learning used on days 100-125.

## The honest limitation

The demo events were written by the same team that wrote the rules, so the demo **shows** the behaviour; it does not **prove** accuracy. That is why `tools/evaluate.py` uses a **different generator**: random personal normals for each person, random noise levels, and events of random size and timing, on seeds 1000-1019 that were never used to tune anything. Results are in `docs/MODEL_CARD.md`. Even so, it is synthetic data with Gaussian noise; real physiology has artefacts, circadian rhythms and illness patterns that are not simulated.

## Open data we would use next

NASA's Open Science Data Repository (OSDR) and analogue-mission data (for example isolation studies) could be used for a first check on real human variability. They are not integrated in this prototype.
